from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_TEXT_LENGTH,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
    PROJECT_ROOT,
    VECTOR_STORE_DIR,
)

sys.path.append(str(Path(__file__).resolve().parent))
from build_index import (  # noqa: E402
    OllamaEmbeddingFunction,
    build_metadata,
    chunk_text_blocks,
    extract_text_blocks,
    iter_knowledge_sets,
    load_json,
    make_chunk_id,
)


CHUNKS_PATH = VECTOR_STORE_DIR / "chunks.jsonl"
VECTORS_PATH = VECTOR_STORE_DIR / "vectors.npy"
MANIFEST_PATH = VECTOR_STORE_DIR / "manifest.json"


def is_placeholder_document(text: str, metadata: dict[str, Any]) -> bool:
    normalized = " ".join(text.strip().split()).lower()
    source_file = str(metadata.get("source_file", "")).lower()
    return (
        normalized == "put the source txt, md, html, pdf, or epub file here."
        or "/put-" in source_file
        or source_file.endswith("\\put-source-here.txt")
    )


def batched(values: list[Any], batch_size: int) -> list[list[Any]]:
    return [values[index : index + batch_size] for index in range(0, len(values), batch_size)]


def collect_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for knowledge_set_path in iter_knowledge_sets(DATA_DIR):
        keywords = load_json(knowledge_set_path / "keywords.json")
        source = load_json(knowledge_set_path / "source.json")
        blocks = extract_text_blocks(knowledge_set_path / "content")
        chunks = chunk_text_blocks(
            blocks,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP,
            max_text_length=EMBEDDING_MAX_TEXT_LENGTH,
        )

        if not chunks:
            print(f"Skipped {knowledge_set_path.name}: no supported text content found")
            continue

        kept = 0
        for chunk in chunks:
            metadata = build_metadata(
                knowledge_set_path=knowledge_set_path,
                chunk=chunk,
                keywords=keywords,
                source=source,
            )
            if is_placeholder_document(chunk.text, metadata):
                continue

            records.append(
                {
                    "id": make_chunk_id(knowledge_set_path.name, chunk),
                    "document": chunk.text,
                    "metadata": metadata,
                }
            )
            kept += 1

        print(f"Collected {knowledge_set_path.name}: {kept} chunks")

    return records


def write_chunks(records: list[dict[str, Any]]) -> None:
    with CHUNKS_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=True) + "\n")


def main() -> None:
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    records = collect_records()
    if not records:
        raise RuntimeError("No chunks collected. Check data/ knowledge sets first.")

    embedding_fn = OllamaEmbeddingFunction(
        base_url=OLLAMA_BASE_URL,
        model=EMBEDDING_MODEL,
        timeout=OLLAMA_TIMEOUT,
    )

    vectors: list[list[float]] = []
    for batch_index, batch in enumerate(batched(records, EMBEDDING_BATCH_SIZE), start=1):
        start = len(vectors) + 1
        end = len(vectors) + len(batch)
        print(f"Embedding vector store: {start}-{end} / {len(records)} chunks with {EMBEDDING_MODEL}")
        vectors.extend(embedding_fn([record["document"] for record in batch]))

    vector_array = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vector_array, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    vector_array = vector_array / norms

    write_chunks(records)
    np.save(VECTORS_PATH, vector_array)
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "embedding_model": EMBEDDING_MODEL,
                "vector_shape": list(vector_array.shape),
                "chunk_count": len(records),
                "project_root": str(PROJECT_ROOT),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(f"Vector store chunks: {len(records)}")
    print(f"Vector shape: {vector_array.shape}")
    print(f"Chunks path: {CHUNKS_PATH}")
    print(f"Vectors path: {VECTORS_PATH}")


if __name__ == "__main__":
    main()
