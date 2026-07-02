from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path = PROJECT_ROOT / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()
sys.path.append(str(PROJECT_ROOT))

from config import (  # noqa: E402
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EXTERNAL_LLM_API_KEY,
    EXTERNAL_LLM_BASE_URL,
    EXTERNAL_LLM_MAX_TOKENS,
    EXTERNAL_LLM_MODEL,
    EXTERNAL_LLM_TEMPERATURE,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
    RAG_MAX_CONTEXT_CHARS,
    RAG_TOP_K,
    VECTOR_STORE_DIR,
)

sys.path.append(str(Path(__file__).resolve().parent))
from memory_system import (  # noqa: E402
    DEFAULT_SESSION_ID,
    format_memory_context,
    record_interaction,
    search_memory,
)


@dataclass(frozen=True)
class RetrievedChunk:
    index: int
    text: str
    metadata: dict[str, Any]
    distance: float | None


def embed_query(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=OLLAMA_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(f"Ollama embedding failed: HTTP {response.status_code} {response.text[:500]}")

    payload = response.json()
    embedding = payload.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise RuntimeError(f"Ollama returned invalid embedding payload: {payload}")
    return embedding


def get_collection() -> Any:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    try:
        count = collection.count()
    except Exception as exc:
        raise RuntimeError(
            f"Chroma collection '{COLLECTION_NAME}' cannot be read. "
            "Run scripts/build_index.py to create a fresh index."
        ) from exc

    if count == 0:
        raise RuntimeError(
            f"Chroma collection '{COLLECTION_NAME}' is empty. "
            "Run scripts/build_index.py before asking questions."
        )
    return collection


def collection_id_by_name() -> str:
    sqlite_path = CHROMA_DIR / "chroma.sqlite3"
    with sqlite3.connect(sqlite_path) as connection:
        row = connection.execute("SELECT id FROM collections WHERE name = ?", (COLLECTION_NAME,)).fetchone()
    if not row:
        raise RuntimeError(f"Chroma collection '{COLLECTION_NAME}' does not exist. Run scripts/build_index.py first.")
    return str(row[0])


def metadata_value(row: sqlite3.Row) -> Any:
    for key in ("string_value", "int_value", "float_value", "bool_value"):
        value = row[key]
        if value is not None:
            return bool(value) if key == "bool_value" else value
    return ""


def sqlite_vector_search(question: str, top_k: int = RAG_TOP_K) -> list[RetrievedChunk]:
    collection_id = collection_id_by_name()
    topic = f"persistent://default/default/{collection_id}"
    query_embedding = np.asarray(embed_query(question), dtype=np.float32)
    query_norm = np.linalg.norm(query_embedding)
    if query_norm == 0:
        raise RuntimeError("Query embedding has zero norm.")
    query_embedding = query_embedding / query_norm

    sqlite_path = CHROMA_DIR / "chroma.sqlite3"
    vectors: list[np.ndarray] = []
    ids: list[str] = []
    metadatas: list[dict[str, Any]] = []
    documents: list[str] = []

    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, vector, metadata
            FROM embeddings_queue
            WHERE topic = ? AND vector IS NOT NULL AND operation != 1
            ORDER BY seq_id
            """,
            (topic,),
        ).fetchall()

    latest_by_id: dict[str, sqlite3.Row] = {}
    for row in rows:
        latest_by_id[str(row["id"])] = row

    for row in latest_by_id.values():
        vector = np.frombuffer(row["vector"], dtype=np.float32)
        if vector.size != query_embedding.size:
            continue
        norm = np.linalg.norm(vector)
        if norm == 0:
            continue
        metadata = json.loads(row["metadata"] or "{}")
        document = str(metadata.pop("chroma:document", ""))
        ids.append(str(row["id"]))
        vectors.append(vector / norm)
        metadatas.append(metadata)
        documents.append(document)

    if not vectors:
        raise RuntimeError(f"No usable vectors found for collection '{COLLECTION_NAME}'. Run scripts/build_index.py.")

    matrix = np.vstack(vectors)
    similarities = matrix @ query_embedding
    top_indexes = np.argsort(-similarities)[:top_k]

    chunks: list[RetrievedChunk] = []
    for rank, vector_index in enumerate(top_indexes, start=1):
        similarity = float(similarities[vector_index])
        chunks.append(
            RetrievedChunk(
                index=rank,
                text=documents[vector_index],
                metadata=metadatas[vector_index],
                distance=1.0 - similarity,
            )
        )
    return chunks


def retrieve(question: str, top_k: int = RAG_TOP_K) -> list[RetrievedChunk]:
    vector_store_chunks = VECTOR_STORE_DIR / "chunks.jsonl"
    vector_store_vectors = VECTOR_STORE_DIR / "vectors.npy"
    if vector_store_chunks.exists() and vector_store_vectors.exists():
        return vector_store_search(question, top_k=top_k)

    try:
        collection = get_collection()
        query_embedding = embed_query(question)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[RetrievedChunk] = []
        for index, document in enumerate(documents, start=1):
            chunks.append(
                RetrievedChunk(
                    index=index,
                    text=document,
                    metadata=metadatas[index - 1] or {},
                    distance=distances[index - 1] if index - 1 < len(distances) else None,
                )
            )
        return chunks
    except Exception:
        return sqlite_vector_search(question, top_k=top_k)


@lru_cache(maxsize=1)
def load_vector_store() -> tuple[list[dict[str, Any]], np.ndarray]:
    chunks_path = VECTOR_STORE_DIR / "chunks.jsonl"
    vectors_path = VECTOR_STORE_DIR / "vectors.npy"
    if not chunks_path.exists() or not vectors_path.exists():
        raise RuntimeError("Vector store is missing. Run scripts/build_vector_store.py first.")

    records = [
        json.loads(line)
        for line in chunks_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    vectors = np.load(vectors_path)
    if len(records) != len(vectors):
        raise RuntimeError(
            f"Vector store is inconsistent: {len(records)} records but {len(vectors)} vectors."
        )
    return records, vectors


def vector_store_search(question: str, top_k: int = RAG_TOP_K) -> list[RetrievedChunk]:
    records, vectors = load_vector_store()
    query_embedding = np.asarray(embed_query(question), dtype=np.float32)
    norm = np.linalg.norm(query_embedding)
    if norm == 0:
        raise RuntimeError("Query embedding has zero norm.")
    query_embedding = query_embedding / norm

    if vectors.shape[1] != query_embedding.size:
        raise RuntimeError(
            f"Vector dimension mismatch: store={vectors.shape[1]}, query={query_embedding.size}. "
            "Rebuild the vector store with scripts/build_vector_store.py."
        )

    similarities = vectors @ query_embedding
    top_indexes = np.argsort(-similarities)[:top_k]

    chunks: list[RetrievedChunk] = []
    for rank, record_index in enumerate(top_indexes, start=1):
        record = records[int(record_index)]
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


def source_label(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata
    title = metadata.get("title") or metadata.get("knowledge_set_id") or "untitled"
    page = metadata.get("page")
    page_text = f", page {page}" if page not in ("", None) else ""
    doi = metadata.get("doi")
    doi_text = f", DOI: {doi}" if doi else ""
    return f"[{chunk.index}] {title}{page_text}{doi_text}"


def format_context(chunks: list[RetrievedChunk], max_chars: int = RAG_MAX_CONTEXT_CHARS) -> str:
    parts: list[str] = []
    used_chars = 0

    for chunk in chunks:
        metadata = chunk.metadata
        header = {
            "citation_id": chunk.index,
            "knowledge_set_id": metadata.get("knowledge_set_id", ""),
            "title": metadata.get("title", ""),
            "doi": metadata.get("doi", ""),
            "source_file": metadata.get("source_file", ""),
            "page": metadata.get("page", ""),
            "distance": chunk.distance,
        }
        text = chunk.text.strip()
        block = f"### Source [{chunk.index}]\nMetadata: {json.dumps(header, ensure_ascii=False)}\nText:\n{text}\n"

        if used_chars + len(block) > max_chars:
            remaining = max_chars - used_chars
            if remaining > 500:
                parts.append(block[:remaining])
            break

        parts.append(block)
        used_chars += len(block)

    return "\n".join(parts)


def build_messages(
    question: str,
    chunks: list[RetrievedChunk],
    memory_context: str = "",
) -> list[dict[str, str]]:
    context = format_context(chunks)
    system_prompt = (
        "你是一个面向细胞组学课程项目的RAG问答助手。"
        "回答事实问题时必须优先依据给定的检索片段；记忆只用于理解上下文、用户偏好和历史问答线索。"
        "如果检索片段不足以支持结论，就明确说知识库中没有足够依据。"
        "回答要用中文，关键事实后必须用 [1]、[2] 这样的来源编号引用。"
        "不要编造论文、数据、实验结果或DOI。"
    )
    memory_block = f"相关历史记忆：\n{memory_context}\n\n" if memory_context else ""
    user_prompt = (
        f"问题：{question}\n\n"
        f"{memory_block}"
        "下面是从知识库检索到的片段：\n"
        f"{context}\n\n"
        "请给出结构清晰的中文答案，并在最后列出使用到的来源。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_external_llm(
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: int = 120,
    retry_count: int = 3,
) -> str:
    api_key = os.getenv("EXTERNAL_LLM_API_KEY", EXTERNAL_LLM_API_KEY)
    if not api_key:
        raise RuntimeError("EXTERNAL_LLM_API_KEY is not set. Put it in .env or the environment.")

    response = None
    last_error: Exception | None = None
    for attempt in range(1, retry_count + 1):
        try:
            response = requests.post(
                chat_completions_url(EXTERNAL_LLM_BASE_URL),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": EXTERNAL_LLM_MODEL,
                    "messages": messages,
                    "temperature": EXTERNAL_LLM_TEMPERATURE if temperature is None else temperature,
                    "max_tokens": EXTERNAL_LLM_MAX_TOKENS if max_tokens is None else max_tokens,
                },
                timeout=timeout,
            )
            retryable_statuses = {401, 403, 408, 409, 429}
            if (response.status_code >= 500 or response.status_code in retryable_statuses) and attempt < retry_count:
                time.sleep(3 * attempt)
                continue
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retry_count:
                time.sleep(3 * attempt)
                continue
            raise RuntimeError(f"External LLM request failed after {retry_count} attempts: {exc}") from exc

    if response is None:
        raise RuntimeError(f"External LLM request failed: {last_error}")

    if not response.ok:
        raise RuntimeError(f"External LLM failed: HTTP {response.status_code} {response.text[:1000]}")

    payload = response.json()
    return payload.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return normalized + "/chat/completions"


def answer_question(
    question: str,
    top_k: int = RAG_TOP_K,
    *,
    session_id: str = DEFAULT_SESSION_ID,
    use_memory: bool = True,
) -> tuple[str, list[RetrievedChunk], str]:
    chunks = retrieve(question, top_k=top_k)
    memory_context = ""
    if use_memory:
        memory_context = format_memory_context(search_memory(question, session_id=session_id))
    messages = build_messages(question, chunks, memory_context=memory_context)
    answer = call_external_llm(messages)
    return answer, chunks, memory_context


def chunk_to_dict(chunk: RetrievedChunk) -> dict[str, Any]:
    metadata = chunk.metadata
    similarity = None if chunk.distance is None else 1.0 - chunk.distance
    return {
        "rank": chunk.index,
        "similarity": similarity,
        "distance": chunk.distance,
        "text": chunk.text,
        "knowledge_set_id": metadata.get("knowledge_set_id", ""),
        "knowledge_set_type": metadata.get("knowledge_set_type", ""),
        "title": metadata.get("title", ""),
        "doi": metadata.get("doi", ""),
        "url": metadata.get("url", ""),
        "source_file": metadata.get("source_file", ""),
        "page": metadata.get("page", ""),
        "section": metadata.get("section", ""),
        "chunk_index": metadata.get("chunk_index", ""),
    }


def search_knowledge(question: str, top_k: int = RAG_TOP_K) -> list[dict[str, Any]]:
    return [chunk_to_dict(chunk) for chunk in retrieve(question, top_k=top_k)]


def ask_rag(
    question: str,
    top_k: int = RAG_TOP_K,
    *,
    session_id: str = DEFAULT_SESSION_ID,
    use_memory: bool = True,
) -> dict[str, Any]:
    answer, chunks, memory_context = answer_question(
        question,
        top_k=top_k,
        session_id=session_id,
        use_memory=use_memory,
    )
    sources = [chunk_to_dict(chunk) for chunk in chunks]
    episode_id = None
    if use_memory:
        episode_id = record_interaction(
            session_id=session_id,
            question=question,
            answer=answer,
            mode="rag",
            sources=sources,
        )
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "memory_context": memory_context,
        "memory_episode_id": episode_id,
    }


def print_answer(question: str, answer: str, chunks: list[RetrievedChunk]) -> None:
    print()
    print("Question:")
    print(question)
    print()
    print("Answer:")
    print(answer)
    print()
    print("Retrieved sources:")
    for chunk in chunks:
        distance = f", distance={chunk.distance:.4f}" if chunk.distance is not None else ""
        print(f"- {source_label(chunk)}{distance}")
