from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(Path(__file__).resolve().parent))

from agentic_rag import (  # noqa: E402
    AGENTIC_MAX_CONTEXT_CHARS,
    MAX_EVIDENCE_CHUNKS,
    RetrievalStep,
    build_fallback_answer,
    plan_retrieval,
    plan_steps,
    summarize_chunk,
)
from config import RAG_MAX_CONTEXT_CHARS, RAG_TOP_K  # noqa: E402
from hybrid_rag import candidate_to_dict, filtered_vector_search, structured_candidates  # noqa: E402
from memory_system import DEFAULT_SESSION_ID, format_memory_context, record_interaction, search_memory  # noqa: E402
from rag_core import RetrievedChunk, call_external_llm, chunk_to_dict, format_context, retrieve, source_label  # noqa: E402
from skills.skill_agent import KNOWN_ALIASES, ACCESSION_PATTERN, run_skill_agent  # noqa: E402
from skills.uniprot_protein_skill import canonical_gene_query  # noqa: E402


# PyCharm can run this file directly. Edit this question for a one-shot run.
QUESTION = "比较 Nicheformer 和 CONCORD 在单细胞组学中的作用差异。"
INTERACTIVE = False
MAX_SKILL_CALLS = 4


GENERIC_UPPERCASE_TOKENS = {
    "AI",
    "API",
    "ATAC",
    "BAM",
    "BED",
    "CPU",
    "CSV",
    "DNA",
    "EM",
    "EPUB",
    "FASTQ",
    "GPU",
    "GTF",
    "HTTP",
    "HTTPS",
    "JSON",
    "LLM",
    "PDF",
    "QC",
    "RAG",
    "RNA",
    "SC",
    "SQL",
    "TSV",
    "UMAP",
    "URL",
}


@dataclass(frozen=True)
class AgenticHybridStepResult:
    step: int
    query: str
    purpose: str
    top_k: int
    retrieval_mode: str
    structured_candidates: list[dict[str, Any]]
    chunks: list[RetrievedChunk]


def extract_skill_queries(question: str, plan: dict[str, Any]) -> list[str]:
    text = question
    for raw_step in plan.get("steps", []):
        if isinstance(raw_step, dict):
            text += " " + str(raw_step.get("query", ""))

    queries: list[str] = []
    seen_canonical: set[str] = set()
    upper_text = text.upper()
    for alias, normalized in KNOWN_ALIASES.items():
        if re.search(rf"(?<![A-Z0-9]){re.escape(alias)}(?![A-Z0-9])", upper_text):
            canonical = canonical_gene_query(normalized).upper()
            if canonical not in seen_canonical:
                seen_canonical.add(canonical)
                queries.append(normalized)

    for match in ACCESSION_PATTERN.findall(text):
        accession = match.upper()
        if accession not in seen_canonical:
            seen_canonical.add(accession)
            queries.append(accession)

    for candidate in re.findall(r"\b[A-Z][A-Z0-9-]{1,11}\b", text):
        normalized = candidate.strip("-")
        if normalized in GENERIC_UPPERCASE_TOKENS:
            continue
        canonical = canonical_gene_query(normalized).upper()
        if canonical not in seen_canonical and any(char.isdigit() for char in normalized):
            seen_canonical.add(canonical)
            queries.append(normalized)

    return queries[:MAX_SKILL_CALLS]


def execute_uniprot_skill(question: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    skill_results: list[dict[str, Any]] = []
    for query in extract_skill_queries(question, plan):
        try:
            result = run_skill_agent(f"{query} 的功能和生物学角色是什么？请查 UniProt。")
            skill_results.append(
                {
                    "query": query,
                    "ok": True,
                    "selected_tool": result.get("selected_tool"),
                    "selection_reason": result.get("selection_reason"),
                    "result": result.get("result"),
                }
            )
        except Exception as exc:  # noqa: BLE001
            skill_results.append(
                {
                    "query": query,
                    "ok": False,
                    "error": str(exc),
                }
            )
    return skill_results


def compact_skill_results(skill_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for item in skill_results:
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        protein = result.get("protein") if isinstance(result.get("protein"), dict) else None
        if protein is None and isinstance(result.get("results"), list) and result["results"]:
            protein = result["results"][0]
        compacted.append(
            {
                "query": item.get("query"),
                "ok": item.get("ok"),
                "selected_tool": item.get("selected_tool"),
                "selected_accession": result.get("selected_accession") or (protein or {}).get("accession"),
                "protein_name": (protein or {}).get("protein_name"),
                "genes": (protein or {}).get("genes", [])[:6],
                "organism": (protein or {}).get("organism"),
                "function": (protein or {}).get("function"),
                "subcellular_location": (protein or {}).get("subcellular_location"),
                "uniprot_url": (protein or {}).get("uniprot_url"),
                "error": item.get("error"),
            }
        )
    return compacted


def chunk_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata
    parts = [
        str(metadata.get("knowledge_set_id", "")),
        str(metadata.get("source_file", "")),
        str(metadata.get("page", "")),
        str(metadata.get("chunk_index", "")),
    ]
    key = "|".join(parts)
    if key.strip("|"):
        return key
    return chunk.text[:240]


def execute_agentic_hybrid_step(step: RetrievalStep) -> AgenticHybridStepResult:
    candidates = structured_candidates(step.query)
    candidate_ids = {candidate.knowledge_set_id for candidate in candidates}

    if candidate_ids:
        chunks = filtered_vector_search(step.query, candidate_ids, top_k=step.top_k)
        retrieval_mode = "structured_filtered_vector"
    else:
        chunks = retrieve(step.query, top_k=step.top_k)
        retrieval_mode = "plain_vector"

    return AgenticHybridStepResult(
        step=step.step,
        query=step.query,
        purpose=step.purpose,
        top_k=step.top_k,
        retrieval_mode=retrieval_mode,
        structured_candidates=[candidate_to_dict(candidate) for candidate in candidates],
        chunks=chunks,
    )


def execute_agentic_hybrid_plan(plan: dict[str, Any]) -> list[AgenticHybridStepResult]:
    if not plan.get("need_retrieval", True):
        return []
    return [execute_agentic_hybrid_step(step) for step in plan_steps(plan)]


def collect_evidence(step_results: list[AgenticHybridStepResult]) -> list[RetrievedChunk]:
    seen: set[str] = set()
    evidence: list[RetrievedChunk] = []

    for step_result in step_results:
        for chunk in step_result.chunks:
            key = chunk_key(chunk)
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                RetrievedChunk(
                    index=len(evidence) + 1,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    distance=chunk.distance,
                )
            )
            if len(evidence) >= MAX_EVIDENCE_CHUNKS:
                return evidence
    return evidence


def step_result_to_dict(result: AgenticHybridStepResult) -> dict[str, Any]:
    return {
        "step": result.step,
        "query": result.query,
        "purpose": result.purpose,
        "top_k": result.top_k,
        "retrieval_mode": result.retrieval_mode,
        "structured_candidates": result.structured_candidates,
        "result_count": len(result.chunks),
        "results": [summarize_chunk(chunk) for chunk in result.chunks],
    }


def aggregate_structured_candidates(step_results: list[AgenticHybridStepResult]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for step_result in step_results:
        for candidate in step_result.structured_candidates:
            key = str(candidate.get("knowledge_set_id") or candidate.get("title") or "")
            if not key:
                continue
            if key not in by_id:
                by_id[key] = candidate
    return list(by_id.values())


def format_execution_trace(plan: dict[str, Any], step_results: list[AgenticHybridStepResult]) -> str:
    lines = [
        f"Question type: {plan.get('question_type', 'general')}",
        f"Need retrieval: {plan.get('need_retrieval', True)}",
        f"Planner reasoning: {plan.get('reasoning', '')}",
    ]

    if not step_results:
        lines.append("No retrieval steps were executed.")
        return "\n".join(lines)

    for result in step_results:
        lines.append("")
        lines.append(f"Step {result.step}")
        lines.append(f"Purpose: {result.purpose}")
        lines.append(f"Query: {result.query}")
        lines.append(f"Retrieval mode: {result.retrieval_mode}")
        if result.structured_candidates:
            lines.append("Structured candidates:")
            for candidate in result.structured_candidates[:4]:
                title = candidate.get("title") or candidate.get("knowledge_set_id")
                matched = ", ".join(candidate.get("matched_by") or [])
                lines.append(f"- {title}; matched_by: {matched}")
        lines.append("Top evidence:")
        for chunk in result.chunks[:3]:
            lines.append(f"- {source_label(chunk)}")
    return "\n".join(lines)


def build_agentic_hybrid_messages(
    question: str,
    plan: dict[str, Any],
    step_results: list[AgenticHybridStepResult],
    evidence: list[RetrievedChunk],
    memory_context: str,
    skill_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
    trace = format_execution_trace(plan, step_results)
    context = format_context(evidence, max_chars=min(RAG_MAX_CONTEXT_CHARS, AGENTIC_MAX_CONTEXT_CHARS))
    structured_summary = json.dumps(aggregate_structured_candidates(step_results), ensure_ascii=False, indent=2)
    skill_summary = json.dumps(compact_skill_results(skill_results), ensure_ascii=False, indent=2)

    system_prompt = (
        "你是一个面向细胞组学课程项目的协作式 Agentic Hybrid RAG 助手。"
        "你同时使用三类能力：历史记忆用于上下文，Agentic planner 用于拆解问题，"
        "结构化知识库用于精确过滤论文/年份/期刊/主题，向量检索用于寻找原文证据，"
        "UniProt Skill 用于补充蛋白/基因的标准条目、功能注释和链接。"
        "回答文献事实时必须以证据片段为准，结构化候选、记忆和 UniProt 都不能替代文献证据。"
        "回答蛋白/基因标准功能时可以引用 UniProt Skill 结果，但要说明它来自外部数据库。"
        "回答必须使用中文，关键事实后必须使用 [1]、[2] 这样的来源编号。"
        "如果证据不足，必须明确说明不能得出结论。"
    )
    memory_block = f"相关历史记忆：\n{memory_context}\n\n" if memory_context else ""
    user_prompt = (
        f"原始问题：{question}\n\n"
        f"{memory_block}"
        f"Agentic 检索计划：\n{plan_json}\n\n"
        f"结构化候选汇总：\n{structured_summary}\n\n"
        f"UniProt Skill 结果：\n{skill_summary}\n\n"
        f"协作检索轨迹：\n{trace}\n\n"
        f"证据片段：\n{context}\n\n"
        "请先用一小段说明本次使用了哪些协作能力，然后给出最终答案。"
        "如果使用了 UniProt Skill，请在答案中单独点明对应 accession 和 UniProt 链接。"
        "答案要结论优先、结构紧凑；如果使用表格，控制在 4 行以内。"
        "最后列出使用到的来源。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def ask_agentic_hybrid_rag(
    question: str,
    *,
    session_id: str = DEFAULT_SESSION_ID,
    use_memory: bool = True,
    verbose: bool = False,
) -> dict[str, Any]:
    if verbose:
        print("Searching memory and planning retrieval...", flush=True)
    memory_context = ""
    if use_memory:
        memory_context = format_memory_context(search_memory(question, session_id=session_id))

    plan, planner_raw, planner_error = plan_retrieval(question)
    if verbose:
        print("Executing agentic hybrid retrieval plan...", flush=True)
    step_results = execute_agentic_hybrid_plan(plan)
    evidence = collect_evidence(step_results)
    skill_results = execute_uniprot_skill(question, plan)

    messages = build_agentic_hybrid_messages(question, plan, step_results, evidence, memory_context, skill_results)
    answer_error = None
    try:
        answer = call_external_llm(messages, max_tokens=1100, timeout=70, retry_count=1)
    except Exception as exc:  # noqa: BLE001
        answer_error = str(exc)
        answer = build_fallback_answer(question, evidence, exc)

    sources = [chunk_to_dict(chunk) for chunk in evidence]
    episode_id = None
    if use_memory:
        episode_id = record_interaction(
            session_id=session_id,
            question=question,
            answer=answer,
            mode="agentic_hybrid_rag",
            sources=sources,
        )

    return {
        "question": question,
        "mode": "agentic_hybrid_rag",
        "plan": plan,
        "planner_raw": planner_raw,
        "planner_error": planner_error,
        "trace": [step_result_to_dict(result) for result in step_results],
        "structured_candidates": aggregate_structured_candidates(step_results),
        "skill_results": skill_results,
        "memory_context": memory_context,
        "memory_episode_id": episode_id,
        "answer": answer,
        "answer_error": answer_error,
        "sources": sources,
    }


def print_agentic_hybrid_result(result: dict[str, Any]) -> None:
    print()
    print("Question:")
    print(result["question"])
    print()
    print("Plan:")
    print(json.dumps(result["plan"], ensure_ascii=False, indent=2))
    print()
    print("Trace:")
    for step in result["trace"]:
        print(f"- Step {step['step']}: {step['purpose']}")
        print(f"  Query: {step['query']}")
        print(f"  Retrieval mode: {step['retrieval_mode']}")
        for candidate in step.get("structured_candidates", [])[:3]:
            print(f"  Candidate: {candidate.get('title')}")
        for item in step.get("results", [])[:3]:
            title = item.get("title") or item.get("knowledge_set_id") or "untitled"
            page = item.get("page")
            page_text = f", page={page}" if page not in ("", None) else ""
            score = item.get("similarity")
            score_text = f", score={score:.4f}" if isinstance(score, float) else ""
            print(f"  Evidence: {title}{page_text}{score_text}")
    print()
    print("Answer:")
    if result.get("answer_error"):
        print(f"Answer warning: {result['answer_error']}")
        print()
    print(result["answer"])
    print()
    print("Memory episode id:", result.get("memory_episode_id"))


def run_one_question(question: str) -> None:
    print_agentic_hybrid_result(ask_agentic_hybrid_rag(question, verbose=True))


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
