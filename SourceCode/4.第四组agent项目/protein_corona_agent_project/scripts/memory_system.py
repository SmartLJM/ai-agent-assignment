from __future__ import annotations

import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import MEMORY_DB_PATH, MEMORY_RETRIEVAL_LIMIT, MEMORY_WORKING_MAX_ITEMS  # noqa: E402


DEFAULT_SESSION_ID = "default"
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "what",
    "which",
    "this",
    "that",
    "about",
    "into",
    "between",
    "怎么",
    "什么",
    "哪些",
    "这个",
    "那个",
    "一下",
    "请问",
    "论文",
    "系统",
}


@dataclass(frozen=True)
class MemorySearchResult:
    working: list[dict[str, Any]]
    episodic: list[dict[str, Any]]
    semantic: list[dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(MEMORY_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def init_memory_db() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS working_memory (
                memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS episodic_memory (
                episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer_summary TEXT NOT NULL,
                mode TEXT NOT NULL,
                source_ids TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS semantic_memory (
                semantic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                evidence TEXT NOT NULL,
                source_episode_id INTEGER REFERENCES episodic_memory(episode_id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                UNIQUE(subject, predicate, object)
            );

            CREATE INDEX IF NOT EXISTS idx_working_session_turn
                ON working_memory(session_id, turn_index);
            CREATE INDEX IF NOT EXISTS idx_episodic_session_created
                ON episodic_memory(session_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_episodic_question
                ON episodic_memory(question);
            CREATE INDEX IF NOT EXISTS idx_semantic_subject
                ON semantic_memory(subject);
            CREATE INDEX IF NOT EXISTS idx_semantic_object
                ON semantic_memory(object);
            """
        )


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9\-]{2,}|[\u4e00-\u9fff]{2,}", lowered)
    return [token for token in tokens if token not in STOPWORDS]


def score_text(query_tokens: set[str], *values: str) -> int:
    if not query_tokens:
        return 0
    haystack = " ".join(values).lower()
    score = 0
    compact_haystack = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", haystack)
    for token in query_tokens:
        compact_token = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", token.lower())
        if token.lower() in haystack or compact_token in compact_haystack:
            score += 1
    return score


def next_turn_index(connection: sqlite3.Connection, session_id: str) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(turn_index), 0) + 1 FROM working_memory WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return int(row[0])


def prune_working_memory(
    connection: sqlite3.Connection,
    session_id: str,
    max_items: int = MEMORY_WORKING_MAX_ITEMS,
) -> None:
    connection.execute(
        """
        DELETE FROM working_memory
        WHERE session_id = ?
          AND memory_id NOT IN (
              SELECT memory_id
              FROM working_memory
              WHERE session_id = ?
              ORDER BY turn_index DESC, memory_id DESC
              LIMIT ?
          )
        """,
        (session_id, session_id, max_items),
    )


def write_working_memory(session_id: str, role: str, content: str) -> int:
    init_memory_db()
    content = content.strip()
    if not content:
        raise ValueError("Working memory content is empty.")

    with connect() as connection:
        turn_index = next_turn_index(connection, session_id)
        cursor = connection.execute(
            """
            INSERT INTO working_memory(session_id, role, content, turn_index, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, content, turn_index, utc_now()),
        )
        prune_working_memory(connection, session_id)
        return int(cursor.lastrowid)


def summarize_answer(answer: str, max_chars: int = 420) -> str:
    text = " ".join(answer.strip().split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def normalize_source_ids(sources: list[dict[str, Any]] | None) -> list[str]:
    ids: list[str] = []
    for source in sources or []:
        knowledge_set_id = str(source.get("knowledge_set_id") or "").strip()
        if knowledge_set_id and knowledge_set_id not in ids:
            ids.append(knowledge_set_id)
    return ids


def write_episodic_memory(
    session_id: str,
    question: str,
    answer: str,
    *,
    mode: str,
    sources: list[dict[str, Any]] | None = None,
) -> int:
    init_memory_db()
    source_ids = normalize_source_ids(sources)
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO episodic_memory(session_id, question, answer_summary, mode, source_ids, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                question.strip(),
                summarize_answer(answer),
                mode,
                json.dumps(source_ids, ensure_ascii=False),
                utc_now(),
            ),
        )
        return int(cursor.lastrowid)


def upsert_semantic_memory(
    subject: str,
    predicate: str,
    object_value: str,
    *,
    evidence: str,
    source_episode_id: int | None = None,
) -> None:
    init_memory_db()
    subject = subject.strip()
    predicate = predicate.strip()
    object_value = object_value.strip()
    if not subject or not predicate or not object_value:
        return
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO semantic_memory(subject, predicate, object, evidence, source_episode_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(subject, predicate, object)
            DO UPDATE SET
                evidence = excluded.evidence,
                source_episode_id = COALESCE(excluded.source_episode_id, semantic_memory.source_episode_id),
                created_at = excluded.created_at
            """,
            (subject, predicate, object_value, evidence.strip(), source_episode_id, utc_now()),
        )


def title_from_source(source: dict[str, Any]) -> str:
    title = str(source.get("title") or "").strip()
    return title or str(source.get("knowledge_set_id") or "").strip()


def extract_semantic_triples(
    question: str,
    answer: str,
    sources: list[dict[str, Any]] | None,
) -> list[tuple[str, str, str, str]]:
    triples: list[tuple[str, str, str, str]] = []
    source_ids = normalize_source_ids(sources)
    answer_text = answer.lower()

    for source in sources or []:
        title = title_from_source(source)
        knowledge_set_id = str(source.get("knowledge_set_id") or "").strip()
        if title and knowledge_set_id:
            triples.append((title, "has_knowledge_set_id", knowledge_set_id, question))
        if title and source.get("doi"):
            triples.append((title, "has_doi", str(source["doi"]), question))

    known_entities = {
        "Nicheformer": "foundation model",
        "CONCORD": "cell state landscape model",
        "bge-m3": "embedding model",
        "DeepSeek-V4-Flash": "external LLM",
        "细胞生物化学原理": "cell biochemistry textbook",
        "细胞编程与重编程的表观遗传机制": "epigenetic reprogramming textbook",
    }
    combined = f"{question}\n{answer}"
    for entity, object_value in known_entities.items():
        if entity.lower() in combined.lower():
            triples.append((entity, "is_a", object_value, summarize_answer(answer, 220)))

    for source_id in source_ids:
        if "foundation" in answer_text or "基础模型" in answer:
            triples.append((source_id, "mentioned_topic", "foundation-model", question))
        if "spatial" in answer_text or "空间" in answer:
            triples.append((source_id, "mentioned_topic", "spatial-omics", question))
        if "表观遗传" in answer or "epigenetic" in answer_text:
            triples.append((source_id, "mentioned_topic", "epigenetics", question))
        if "线粒体" in answer or "mitochondria" in answer_text:
            triples.append((source_id, "mentioned_topic", "mitochondria", question))

    deduped: list[tuple[str, str, str, str]] = []
    seen = set()
    for triple in triples:
        key = triple[:3]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(triple)
    return deduped[:12]


def record_interaction(
    *,
    session_id: str,
    question: str,
    answer: str,
    mode: str,
    sources: list[dict[str, Any]] | None = None,
) -> int:
    write_working_memory(session_id, "user", question)
    write_working_memory(session_id, "assistant", summarize_answer(answer, 1200))
    episode_id = write_episodic_memory(session_id, question, answer, mode=mode, sources=sources)
    for subject, predicate, object_value, evidence in extract_semantic_triples(question, answer, sources):
        upsert_semantic_memory(
            subject,
            predicate,
            object_value,
            evidence=evidence,
            source_episode_id=episode_id,
        )
    return episode_id


def search_working_memory(
    session_id: str,
    *,
    limit: int = MEMORY_RETRIEVAL_LIMIT,
) -> list[dict[str, Any]]:
    init_memory_db()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT memory_id, session_id, role, content, turn_index, created_at
            FROM working_memory
            WHERE session_id = ?
            ORDER BY turn_index DESC, memory_id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    return [row_to_dict(row) for row in reversed(rows)]


def search_episodic_memory(
    query: str,
    *,
    session_id: str | None = None,
    limit: int = MEMORY_RETRIEVAL_LIMIT,
) -> list[dict[str, Any]]:
    init_memory_db()
    query_tokens = set(tokenize(query))
    with connect() as connection:
        if session_id:
            rows = connection.execute(
                """
                SELECT episode_id, session_id, question, answer_summary, mode, source_ids, created_at
                FROM episodic_memory
                WHERE session_id = ?
                ORDER BY created_at DESC, episode_id DESC
                LIMIT 80
                """,
                (session_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT episode_id, session_id, question, answer_summary, mode, source_ids, created_at
                FROM episodic_memory
                ORDER BY created_at DESC, episode_id DESC
                LIMIT 120
                """
            ).fetchall()

    candidates = []
    for row in rows:
        item = row_to_dict(row)
        score = score_text(query_tokens, item["question"], item["answer_summary"], item["source_ids"])
        if score > 0:
            item["match_score"] = score
            try:
                item["source_ids"] = json.loads(item["source_ids"])
            except json.JSONDecodeError:
                item["source_ids"] = []
            candidates.append(item)
    candidates.sort(key=lambda item: (-item["match_score"], item["created_at"]), reverse=False)
    return candidates[:limit]


def search_semantic_memory(
    query: str,
    *,
    limit: int = MEMORY_RETRIEVAL_LIMIT,
) -> list[dict[str, Any]]:
    init_memory_db()
    query_tokens = set(tokenize(query))
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT semantic_id, subject, predicate, object, evidence, source_episode_id, created_at
            FROM semantic_memory
            ORDER BY created_at DESC, semantic_id DESC
            LIMIT 200
            """
        ).fetchall()

    candidates = []
    for row in rows:
        item = row_to_dict(row)
        score = score_text(query_tokens, item["subject"], item["predicate"], item["object"], item["evidence"])
        if score > 0:
            item["match_score"] = score
            candidates.append(item)
    candidates.sort(key=lambda item: (-item["match_score"], item["created_at"]), reverse=False)
    return candidates[:limit]


def search_memory(
    query: str,
    *,
    session_id: str = DEFAULT_SESSION_ID,
    limit: int = MEMORY_RETRIEVAL_LIMIT,
) -> MemorySearchResult:
    return MemorySearchResult(
        working=search_working_memory(session_id, limit=limit),
        episodic=search_episodic_memory(query, session_id=None, limit=limit),
        semantic=search_semantic_memory(query, limit=limit),
    )


def format_memory_context(result: MemorySearchResult, max_chars: int = 3500) -> str:
    sections: list[str] = []
    if result.working:
        lines = ["### Working Memory"]
        for item in result.working:
            lines.append(f"- {item['role']}: {item['content']}")
        sections.append("\n".join(lines))

    if result.episodic:
        lines = ["### Episodic Memory"]
        for item in result.episodic:
            source_ids = ", ".join(item.get("source_ids") or [])
            lines.append(
                f"- Q: {item['question']}\n"
                f"  Summary: {item['answer_summary']}\n"
                f"  Mode: {item['mode']}; Sources: {source_ids}"
            )
        sections.append("\n".join(lines))

    if result.semantic:
        lines = ["### Semantic Memory"]
        for item in result.semantic:
            lines.append(f"- {item['subject']} --{item['predicate']}--> {item['object']}")
        sections.append("\n".join(lines))

    text = "\n\n".join(sections)
    return text[:max_chars]


def memory_stats() -> dict[str, Any]:
    init_memory_db()
    with connect() as connection:
        return {
            "db_path": str(MEMORY_DB_PATH),
            "working_memory": connection.execute("SELECT COUNT(*) FROM working_memory").fetchone()[0],
            "episodic_memory": connection.execute("SELECT COUNT(*) FROM episodic_memory").fetchone()[0],
            "semantic_memory": connection.execute("SELECT COUNT(*) FROM semantic_memory").fetchone()[0],
        }


def print_memory_result(result: MemorySearchResult) -> None:
    print(format_memory_context(result) or "No memory matched.")


def main() -> None:
    init_memory_db()
    print("Memory database ready.")
    for key, value in memory_stats().items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
