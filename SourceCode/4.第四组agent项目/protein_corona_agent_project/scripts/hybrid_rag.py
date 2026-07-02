from __future__ import annotations

import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import RAG_MAX_CONTEXT_CHARS, RAG_TOP_K, STRUCTURED_KB_PATH  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parent))
from memory_system import DEFAULT_SESSION_ID, format_memory_context, record_interaction, search_memory  # noqa: E402
from rag_core import (  # noqa: E402
    RetrievedChunk,
    call_external_llm,
    chunk_to_dict,
    embed_query,
    format_context,
    load_vector_store,
    retrieve,
)


# PyCharm can run this file directly. Edit this question for a one-shot run.
QUESTION = "哪些 2026 年 Nature Biotechnology 论文涉及 foundation model 或 interpretability？"
INTERACTIVE = False

MAX_CANDIDATE_PAPERS = 12
MAX_STRUCTURED_SUMMARY_CHARS = 4500


THEME_ALIASES = {
    "单细胞": ["single-cell-omics"],
    "空间": ["spatial-omics", "spatial-biology"],
    "空间转录组": ["spatial-omics", "spatial-biology"],
    "空间组学": ["spatial-omics", "spatial-biology"],
    "基础模型": ["foundation-model"],
    "foundation model": ["foundation-model"],
    "foundation-model": ["foundation-model"],
    "解释": ["interpretability"],
    "可解释": ["interpretability"],
    "interpretability": ["interpretability"],
    "interpretable": ["interpretability"],
    "质量控制": ["quality-control"],
    "标准化": ["benchmark", "quality-control"],
    "评估": ["benchmark"],
    "benchmark": ["benchmark"],
    "整合": ["data-integration"],
    "多组学": ["multi-omics"],
    "通信": ["cell-communication"],
    "信号": ["cell-communication"],
    "配体": ["cell-communication"],
    "受体": ["cell-communication"],
    "疾病": ["disease-context"],
    "调控": ["regulation"],
    "转录组": ["transcriptomics"],
}


@dataclass(frozen=True)
class StructuredCandidate:
    knowledge_set_id: str
    title: str
    journal: str
    publication_year: int | None
    doi: str
    url: str
    matched_by: list[str]
    methods: list[str]
    themes: list[str]
    keywords: list[str]


def connect() -> sqlite3.Connection:
    if not STRUCTURED_KB_PATH.exists():
        raise RuntimeError("Structured KB is missing. Run scripts/build_structured_kb.py first.")
    connection = sqlite3.connect(STRUCTURED_KB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in row.keys()} for row in rows]


def query_rows(connection: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    return rows_to_dicts(connection.execute(sql, params).fetchall())


def paper_details(connection: sqlite3.Connection, knowledge_set_id: str, matched_by: list[str]) -> StructuredCandidate:
    paper = connection.execute(
        """
        SELECT knowledge_set_id, title, journal, publication_year, doi, url
        FROM papers
        WHERE knowledge_set_id = ?
        """,
        (knowledge_set_id,),
    ).fetchone()
    if paper is None:
        raise RuntimeError(f"Missing paper row: {knowledge_set_id}")

    methods = [
        row["display_name"]
        for row in connection.execute(
            """
            SELECT m.display_name
            FROM methods m
            JOIN paper_methods pm ON m.method_id = pm.method_id
            WHERE pm.knowledge_set_id = ?
            ORDER BY m.display_name
            """,
            (knowledge_set_id,),
        ).fetchall()
    ]
    themes = [
        row["theme"]
        for row in connection.execute(
            "SELECT theme FROM paper_themes WHERE knowledge_set_id = ? ORDER BY theme",
            (knowledge_set_id,),
        ).fetchall()
    ]
    keywords = [
        row["keyword"]
        for row in connection.execute(
            "SELECT keyword FROM paper_keywords WHERE knowledge_set_id = ? ORDER BY keyword",
            (knowledge_set_id,),
        ).fetchall()
    ]

    return StructuredCandidate(
        knowledge_set_id=paper["knowledge_set_id"],
        title=paper["title"],
        journal=paper["journal"],
        publication_year=paper["publication_year"],
        doi=paper["doi"],
        url=paper["url"],
        matched_by=sorted(set(matched_by)),
        methods=methods,
        themes=themes,
        keywords=keywords,
    )


def add_candidate(matches: dict[str, list[str]], knowledge_set_id: str, reason: str) -> None:
    matches.setdefault(knowledge_set_id, []).append(reason)


def normalize_lookup_text(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def text_mentions(normalized_question: str, candidate_text: str) -> bool:
    normalized_candidate = normalize_lookup_text(candidate_text)
    if not normalized_candidate:
        return False
    if normalized_candidate in normalized_question:
        return True
    return normalized_candidate.replace(" ", "") in normalized_question.replace(" ", "")


def structured_candidates(question: str) -> list[StructuredCandidate]:
    text = question.lower()
    normalized_question = normalize_lookup_text(question)
    hard_matches: dict[str, list[str]] = {}
    soft_matches: dict[str, list[str]] = {}

    with connect() as connection:
        all_ids = {
            row["knowledge_set_id"]
            for row in query_rows(connection, "SELECT knowledge_set_id FROM papers", ())
        }
        allowed_ids = set(all_ids)

        year_filters = sorted({int(year) for year in re.findall(r"(20\d{2}|19\d{2})", question)})
        if year_filters:
            year_ids = {
                row["knowledge_set_id"]
                for row in query_rows(
                    connection,
                    "SELECT knowledge_set_id FROM papers WHERE publication_year IN (%s)"
                    % ",".join("?" for _ in year_filters),
                    tuple(year_filters),
                )
            }
            allowed_ids &= year_ids
            for paper_id in year_ids:
                add_candidate(hard_matches, paper_id, "year:" + ",".join(str(year) for year in year_filters))

        journal_filters = []
        for journal in ["Nature Biotechnology", "Nature Methods", "Nature Genetics"]:
            if journal.lower() in text:
                journal_filters.append(journal)
        if not journal_filters and re.search(r"\bnature\b", text):
            journal_filters.append("Nature")

        if journal_filters:
            journal_ids = {
                row["knowledge_set_id"]
                for row in query_rows(
                    connection,
                    "SELECT knowledge_set_id FROM papers WHERE lower(journal) IN (%s)"
                    % ",".join("?" for _ in journal_filters),
                    tuple(journal.lower() for journal in journal_filters),
                )
            }
            allowed_ids &= journal_ids
            for paper_id in journal_ids:
                add_candidate(hard_matches, paper_id, "journal:" + ",".join(journal_filters))

        method_rows = query_rows(
            connection,
            """
            SELECT pm.knowledge_set_id, m.method_id, m.display_name
            FROM methods m
            JOIN paper_methods pm ON m.method_id = pm.method_id
            """,
            (),
        )
        for row in method_rows:
            method_id = str(row["method_id"])
            display_name = str(row["display_name"])
            if text_mentions(normalized_question, method_id) or text_mentions(normalized_question, display_name):
                if row["knowledge_set_id"] in allowed_ids:
                    add_candidate(soft_matches, row["knowledge_set_id"], f"method:{row['display_name']}")

        for alias, themes in THEME_ALIASES.items():
            if not text_mentions(normalized_question, alias):
                continue
            for theme in themes:
                for row in query_rows(
                    connection,
                    "SELECT knowledge_set_id FROM paper_themes WHERE theme = ?",
                    (theme,),
                ):
                    if row["knowledge_set_id"] in allowed_ids:
                        add_candidate(soft_matches, row["knowledge_set_id"], f"theme:{theme}")

        theme_rows = query_rows(
            connection,
            "SELECT knowledge_set_id, theme FROM paper_themes",
            (),
        )
        for row in theme_rows:
            theme = str(row["theme"])
            if text_mentions(normalized_question, theme):
                if row["knowledge_set_id"] in allowed_ids:
                    add_candidate(soft_matches, row["knowledge_set_id"], f"theme:{theme}")

        keyword_rows = query_rows(
            connection,
            "SELECT knowledge_set_id, keyword FROM paper_keywords",
            (),
        )
        for row in keyword_rows:
            keyword = str(row["keyword"])
            if text_mentions(normalized_question, keyword):
                if row["knowledge_set_id"] in allowed_ids:
                    add_candidate(soft_matches, row["knowledge_set_id"], f"keyword:{row['keyword']}")

        title_rows = query_rows(
            connection,
            "SELECT knowledge_set_id, title FROM papers",
            (),
        )
        for row in title_rows:
            title = str(row["title"]).lower()
            title_terms = [term for term in re.split(r"[^a-z0-9]+", title) if len(term) >= 5]
            if any(text_mentions(normalized_question, term) for term in title_terms[:8]):
                if row["knowledge_set_id"] in allowed_ids:
                    add_candidate(soft_matches, row["knowledge_set_id"], "title-term")

        if soft_matches:
            selected_ids = set(soft_matches)
        elif year_filters or journal_filters:
            selected_ids = set(allowed_ids)
        else:
            selected_ids = set()

        candidates = [
            paper_details(
                connection,
                paper_id,
                hard_matches.get(paper_id, []) + soft_matches.get(paper_id, []),
            )
            for paper_id in selected_ids
            if paper_id in allowed_ids
        ]

    def rank_key(item: StructuredCandidate) -> tuple[int, int, int, str]:
        soft_count = sum(
            1
            for reason in item.matched_by
            if not reason.startswith("year:") and not reason.startswith("journal:")
        )
        hard_count = len(item.matched_by) - soft_count
        return (-soft_count, -hard_count, -(item.publication_year or 0), item.title)

    candidates.sort(key=rank_key)
    return candidates[:MAX_CANDIDATE_PAPERS]


def filtered_vector_search(
    question: str,
    allowed_knowledge_set_ids: set[str],
    top_k: int = RAG_TOP_K,
) -> list[RetrievedChunk]:
    if not allowed_knowledge_set_ids:
        return retrieve(question, top_k=top_k)

    records, vectors = load_vector_store()
    query_embedding = np.asarray(embed_query(question), dtype=np.float32)
    norm = np.linalg.norm(query_embedding)
    if norm == 0:
        raise RuntimeError("Query embedding has zero norm.")
    query_embedding = query_embedding / norm

    filtered_records: list[dict[str, Any]] = []
    filtered_vectors: list[np.ndarray] = []
    for record, vector in zip(records, vectors):
        metadata = record.get("metadata", {})
        if metadata.get("knowledge_set_id") not in allowed_knowledge_set_ids:
            continue
        filtered_records.append(record)
        filtered_vectors.append(vector)

    if not filtered_vectors:
        return retrieve(question, top_k=top_k)

    matrix = np.vstack(filtered_vectors)
    similarities = matrix @ query_embedding
    top_indexes = np.argsort(-similarities)[:top_k]

    chunks: list[RetrievedChunk] = []
    for rank, record_index in enumerate(top_indexes, start=1):
        record = filtered_records[int(record_index)]
        similarity = float(similarities[record_index])
        chunks.append(
            RetrievedChunk(
                index=rank,
                text=record["document"],
                metadata=record["metadata"],
                distance=1.0 - similarity,
            )
        )
    return chunks


def structured_summary(candidates: list[StructuredCandidate]) -> str:
    items = []
    for candidate in candidates:
        items.append(
            {
                "knowledge_set_id": candidate.knowledge_set_id,
                "title": candidate.title,
                "journal": candidate.journal,
                "publication_year": candidate.publication_year,
                "doi": candidate.doi,
                "matched_by": candidate.matched_by,
                "methods": candidate.methods,
                "themes": candidate.themes,
                "keywords": candidate.keywords[:10],
            }
        )
    text = json.dumps(items, ensure_ascii=False, indent=2)
    return text[:MAX_STRUCTURED_SUMMARY_CHARS]


def build_hybrid_messages(
    question: str,
    candidates: list[StructuredCandidate],
    chunks: list[RetrievedChunk],
    memory_context: str = "",
) -> list[dict[str, str]]:
    system_prompt = (
        "你是一个面向细胞组学课程项目的 Hybrid RAG 问答助手。"
        "你会同时使用结构化知识库结果和向量检索证据回答问题。"
        "结构化知识库用于确定论文、年份、期刊、主题、方法实体；向量证据用于支撑具体事实。"
        "历史记忆只用于理解上下文和复用已知用户偏好，不能替代文献证据。"
        "回答必须使用中文，关键事实后必须使用 [1]、[2] 这样的来源编号。"
        "如果证据不足，必须明确说明不能得出结论。"
    )
    memory_block = f"相关历史记忆：\n{memory_context}\n\n" if memory_context else ""
    user_prompt = (
        f"问题：{question}\n\n"
        f"{memory_block}"
        f"结构化知识库候选结果：\n{structured_summary(candidates)}\n\n"
        f"向量检索证据：\n{format_context(chunks, max_chars=RAG_MAX_CONTEXT_CHARS)}\n\n"
        "请综合结构化结果和原文证据回答。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def candidate_to_dict(candidate: StructuredCandidate) -> dict[str, Any]:
    return {
        "knowledge_set_id": candidate.knowledge_set_id,
        "title": candidate.title,
        "journal": candidate.journal,
        "publication_year": candidate.publication_year,
        "doi": candidate.doi,
        "url": candidate.url,
        "matched_by": candidate.matched_by,
        "methods": candidate.methods,
        "themes": candidate.themes,
        "keywords": candidate.keywords,
    }


def ask_hybrid_rag(
    question: str,
    top_k: int = RAG_TOP_K,
    *,
    session_id: str = DEFAULT_SESSION_ID,
    use_memory: bool = True,
) -> dict[str, Any]:
    candidates = structured_candidates(question)
    allowed_ids = {candidate.knowledge_set_id for candidate in candidates}
    chunks = filtered_vector_search(question, allowed_ids, top_k=top_k)
    memory_context = ""
    if use_memory:
        memory_context = format_memory_context(search_memory(question, session_id=session_id))
    answer = call_external_llm(
        build_hybrid_messages(question, candidates, chunks, memory_context=memory_context),
        max_tokens=900,
        timeout=90,
    )
    sources = [chunk_to_dict(chunk) for chunk in chunks]
    episode_id = None
    if use_memory:
        episode_id = record_interaction(
            session_id=session_id,
            question=question,
            answer=answer,
            mode="hybrid_rag",
            sources=sources,
        )
    return {
        "question": question,
        "mode": "hybrid_rag",
        "structured_candidates": [candidate_to_dict(candidate) for candidate in candidates],
        "answer": answer,
        "sources": sources,
        "memory_context": memory_context,
        "memory_episode_id": episode_id,
    }


def print_hybrid_result(result: dict[str, Any]) -> None:
    print()
    print("Question:")
    print(result["question"])
    print()
    print("Structured candidates:")
    for index, candidate in enumerate(result["structured_candidates"], start=1):
        print(f"- [{index}] {candidate['title']}")
        print(f"  id: {candidate['knowledge_set_id']}")
        print(f"  journal/year: {candidate['journal']} / {candidate['publication_year']}")
        print(f"  matched_by: {', '.join(candidate['matched_by'])}")
    print()
    print("Answer:")
    print(result["answer"])
    print()
    print("Sources:")
    for source in result["sources"]:
        page = source.get("page")
        page_text = f", page={page}" if page not in ("", None) else ""
        score = source.get("similarity")
        score_text = f", score={score:.4f}" if isinstance(score, float) else ""
        print(f"- [{source['rank']}] {source.get('title')}{page_text}{score_text}")


def run_one_question(question: str) -> None:
    print_hybrid_result(ask_hybrid_rag(question))


def main() -> None:
    if INTERACTIVE:
        while True:
            question = input("\n请输入问题，直接回车退出：").strip()
            if not question:
                break
            run_one_question(question)
        return
    run_one_question(QUESTION)


if __name__ == "__main__":
    main()
