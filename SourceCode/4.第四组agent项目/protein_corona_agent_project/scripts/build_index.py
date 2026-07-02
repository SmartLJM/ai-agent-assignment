from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
import pymupdf
import requests
from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT
from ebooklib import epub

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DATA_DIR,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_TEXT_LENGTH,
    EMBEDDING_MODEL,
    EMBEDDING_RETRY_COUNT,
    EMBEDDING_RETRY_SECONDS,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
    PROJECT_ROOT,
)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".pdf", ".epub"}


@dataclass(frozen=True)
class TextBlock:
    text: str
    source_file: Path
    page: int | None = None
    section: str = ""


@dataclass(frozen=True)
class Chunk:
    text: str
    source_file: Path
    chunk_index: int
    page: int | None
    section: str


@dataclass(frozen=True)
class IndexedBatch:
    ids: list[str]
    documents: list[str]
    metadatas: list[dict[str, Any]]


class OllamaEmbeddingFunction:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 120,
        retry_count: int = EMBEDDING_RETRY_COUNT,
        retry_seconds: int = EMBEDDING_RETRY_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_seconds = retry_seconds

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in input:
            embeddings.append(self.embed(text))
        return embeddings

    def embed(self, text: str) -> list[float]:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=self.timeout,
                )
                if response.status_code >= 500 and attempt < self.retry_count:
                    time.sleep(self.retry_seconds)
                    continue
                if response.status_code >= 400:
                    response_text = response.text.strip().replace("\n", " ")
                    raise RuntimeError(
                        f"Ollama embedding HTTP {response.status_code}: "
                        f"{response_text[:500] or '<empty response>'}"
                    )
                payload = response.json()
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retry_count:
                    time.sleep(self.retry_seconds)
                    continue
                raise RuntimeError(f"Ollama embedding request failed after {self.retry_count} attempts: {exc}") from exc
        else:
            raise RuntimeError(f"Ollama embedding request failed: {last_error}")

        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError(f"Ollama returned an invalid embedding payload: {payload}")
        return embedding


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_text_file(path: Path) -> list[TextBlock]:
    return [TextBlock(text=normalize_text(path.read_text(encoding="utf-8", errors="ignore")), source_file=path)]


def read_html_file(path: Path) -> list[TextBlock]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text("\n")
    return [TextBlock(text=normalize_text(text), source_file=path)]


def read_pdf_file(path: Path) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    with pymupdf.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            text = normalize_text(page.get_text("text"))
            if text:
                blocks.append(TextBlock(text=text, source_file=path, page=page_index))
    return blocks


def read_epub_file(path: Path) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    book = epub.read_epub(str(path))
    section_index = 0

    for item in book.get_items():
        if item.get_type() != ITEM_DOCUMENT:
            continue

        section_index += 1
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        title = ""
        heading = soup.find(["h1", "h2", "h3"])
        if heading:
            title = normalize_text(heading.get_text(" "))

        text = normalize_text(soup.get_text("\n"))
        if text:
            blocks.append(
                TextBlock(
                    text=text,
                    source_file=path,
                    page=section_index,
                    section=title or f"epub-section-{section_index}",
                )
            )

    return blocks


def extract_text_blocks(content_dir: Path) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for path in sorted(content_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        if path.suffix.lower() == ".pdf":
            blocks.extend(read_pdf_file(path))
        elif path.suffix.lower() == ".epub":
            blocks.extend(read_epub_file(path))
        elif path.suffix.lower() in {".html", ".htm"}:
            blocks.extend(read_html_file(path))
        else:
            blocks.extend(read_text_file(path))

    return [block for block in blocks if block.text]


def split_paragraphs(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(paragraphs) > 1:
        return paragraphs

    # Fallback for PDFs that lose paragraph breaks.
    sentences = re.split(r"(?<=[。！？.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def split_long_text(text: str, max_length: int) -> list[str]:
    if len(text) <= max_length:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_length, len(text))
        if end < len(text):
            boundary = max(
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("。", start, end),
                text.rfind("; ", start, end),
            )
            if boundary > start + max_length // 2:
                end = boundary + 1

        part = text[start:end].strip()
        if part:
            parts.append(part)
        start = end

    return parts


def append_chunk(
    chunks: list[Chunk],
    *,
    text: str,
    source_file: Path,
    page: int | None,
    section: str,
    next_index: int,
    max_text_length: int,
) -> int:
    for part in split_long_text(text, max_text_length):
        chunks.append(
            Chunk(
                text=part,
                source_file=source_file,
                chunk_index=next_index,
                page=page,
                section=section,
            )
        )
        next_index += 1
    return next_index


def chunk_text_blocks(
    blocks: list[TextBlock],
    *,
    chunk_size: int = 900,
    overlap: int = 120,
    max_text_length: int = EMBEDDING_MAX_TEXT_LENGTH,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunk_index = 0

    for block in blocks:
        current = ""
        for paragraph in split_paragraphs(block.text):
            if not current:
                current = paragraph
                continue

            if len(current) + 2 + len(paragraph) <= chunk_size:
                current = f"{current}\n\n{paragraph}"
                continue

            chunk_index = append_chunk(
                chunks,
                text=current,
                source_file=block.source_file,
                page=block.page,
                section=block.section,
                next_index=chunk_index,
                max_text_length=max_text_length,
            )
            current = f"{current[-overlap:]}\n\n{paragraph}" if overlap > 0 else paragraph

        if current:
            chunk_index = append_chunk(
                chunks,
                text=current,
                source_file=block.source_file,
                page=block.page,
                section=block.section,
                next_index=chunk_index,
                max_text_length=max_text_length,
            )

    return chunks


def iter_knowledge_sets(data_dir: Path) -> list[Path]:
    knowledge_sets: list[Path] = []
    for path in sorted(data_dir.glob("*/*")):
        if not path.is_dir():
            continue
        if (path / "content").is_dir() and (path / "keywords.json").is_file() and (path / "source.json").is_file():
            knowledge_sets.append(path)
    return knowledge_sets


def make_chunk_id(knowledge_set_id: str, chunk: Chunk) -> str:
    digest_source = f"{knowledge_set_id}|{chunk.source_file.as_posix()}|{chunk.page}|{chunk.chunk_index}|{chunk.text}"
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]
    return f"{knowledge_set_id}-chunk-{chunk.chunk_index:05d}-{digest}"


def build_metadata(
    *,
    knowledge_set_path: Path,
    chunk: Chunk,
    keywords: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    relative_file = chunk.source_file.relative_to(PROJECT_ROOT).as_posix()
    themes = sorted(keywords.keys())

    return {
        "knowledge_set_id": knowledge_set_path.name,
        "knowledge_set_type": knowledge_set_path.parent.name,
        "source_file": relative_file,
        "page": chunk.page if chunk.page is not None else "",
        "section": chunk.section,
        "chunk_index": chunk.chunk_index,
        "themes": json.dumps(themes, ensure_ascii=False),
        "keywords": json.dumps(keywords, ensure_ascii=False),
        "title": str(source.get("title", "")),
        "doi": str(source.get("doi", "")),
        "url": str(source.get("url", "")),
    }


def batched(values: list[Any], batch_size: int) -> list[list[Any]]:
    return [values[index : index + batch_size] for index in range(0, len(values), batch_size)]


def existing_ids(collection: Any, ids: list[str]) -> set[str]:
    existing: set[str] = set()
    for id_batch in batched(ids, 500):
        if not id_batch:
            continue
        result = collection.get(ids=id_batch, include=[])
        existing.update(result.get("ids", []))
    return existing


def delete_stale_chunks(collection: Any, knowledge_set_id: str, current_ids: set[str]) -> int:
    result = collection.get(where={"knowledge_set_id": knowledge_set_id}, include=[])
    stored_ids = set(result.get("ids", []))
    stale_ids = sorted(stored_ids - current_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)
    return len(stale_ids)


def index_batches(
    *,
    collection: Any,
    embedding_fn: OllamaEmbeddingFunction,
    embedding_model: str,
    knowledge_set_id: str,
    batches: list[IndexedBatch],
) -> int:
    indexed_count = 0
    total = sum(len(batch.documents) for batch in batches)
    done = 0

    for batch in batches:
        print(
            f"Embedding {knowledge_set_id}: "
            f"{done + 1}-{done + len(batch.documents)} / {total} chunks with {embedding_model}"
        )
        try:
            embeddings = embedding_fn(batch.documents)
        except Exception as exc:
            lengths = [len(document) for document in batch.documents]
            first_metadata = batch.metadatas[0] if batch.metadatas else {}
            raise RuntimeError(
                f"Embedding failed for knowledge_set={knowledge_set_id}, "
                f"batch_start={done + 1}, batch_size={len(batch.documents)}, "
                f"text_lengths={lengths}, "
                f"first_source={first_metadata.get('source_file')}, "
                f"first_page={first_metadata.get('page')}: {exc}"
            ) from exc
        collection.upsert(
            ids=batch.ids,
            documents=batch.documents,
            embeddings=embeddings,
            metadatas=batch.metadatas,
        )
        indexed_count += len(batch.documents)
        done += len(batch.documents)

    return indexed_count


def build_index(
    *,
    reset: bool = False,
    collection_name: str = COLLECTION_NAME,
    ollama_base_url: str = OLLAMA_BASE_URL,
    embedding_model: str = EMBEDDING_MODEL,
    ollama_timeout: int = OLLAMA_TIMEOUT,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    max_text_length: int = EMBEDDING_MAX_TEXT_LENGTH,
) -> None:
    if reset and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    embedding_fn = OllamaEmbeddingFunction(
        base_url=ollama_base_url,
        model=embedding_model,
        timeout=ollama_timeout,
    )
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Course knowledge asset vector index"},
    )

    knowledge_sets = iter_knowledge_sets(DATA_DIR)
    if not knowledge_sets:
        print(f"No valid knowledge sets found under {DATA_DIR}")
        print("Expected: data/<source-type>/<knowledge_set_id>/{content/,keywords.json,source.json}")
        return

    total_chunks = 0
    skipped_chunks = 0
    deleted_chunks = 0
    indexed_sets = 0
    skipped_sets = 0

    for knowledge_set_path in knowledge_sets:
        keywords = load_json(knowledge_set_path / "keywords.json")
        source = load_json(knowledge_set_path / "source.json")
        blocks = extract_text_blocks(knowledge_set_path / "content")
        chunks = chunk_text_blocks(
            blocks,
            chunk_size=chunk_size,
            overlap=overlap,
            max_text_length=max_text_length,
        )

        if not chunks:
            print(f"Skipped {knowledge_set_path.name}: no supported text content found")
            continue

        ids = [make_chunk_id(knowledge_set_path.name, chunk) for chunk in chunks]
        id_set = set(ids)
        removed = delete_stale_chunks(collection, knowledge_set_path.name, id_set)
        deleted_chunks += removed
        if removed:
            print(f"Removed stale chunks for {knowledge_set_path.name}: {removed}")

        stored_ids = existing_ids(collection, ids)
        missing_indexes = [index for index, chunk_id in enumerate(ids) if chunk_id not in stored_ids]
        skipped_for_set = len(ids) - len(missing_indexes)
        skipped_chunks += skipped_for_set

        if not missing_indexes:
            skipped_sets += 1
            print(f"Skipped {knowledge_set_path.name}: already indexed ({len(ids)} chunks)")
            continue

        documents = [chunk.text for chunk in chunks]
        metadatas = [
            build_metadata(
                knowledge_set_path=knowledge_set_path,
                chunk=chunk,
                keywords=keywords,
                source=source,
            )
            for chunk in chunks
        ]

        missing_batches: list[IndexedBatch] = []
        for index_batch in batched(missing_indexes, batch_size):
            missing_batches.append(
                IndexedBatch(
                    ids=[ids[index] for index in index_batch],
                    documents=[documents[index] for index in index_batch],
                    metadatas=[metadatas[index] for index in index_batch],
                )
            )

        indexed_count = index_batches(
            collection=collection,
            embedding_fn=embedding_fn,
            embedding_model=embedding_model,
            knowledge_set_id=knowledge_set_path.name,
            batches=missing_batches,
        )
        total_chunks += indexed_count
        indexed_sets += 1
        print(
            f"Indexed {knowledge_set_path.name}: "
            f"{indexed_count} new chunks, {skipped_for_set} existing chunks"
        )

    print()
    print(f"New or changed knowledge sets indexed: {indexed_sets}")
    print(f"Unchanged knowledge sets skipped: {skipped_sets}")
    print(f"New chunks indexed: {total_chunks}")
    print(f"Existing chunks skipped: {skipped_chunks}")
    print(f"Stale chunks deleted: {deleted_chunks}")
    print(f"Chroma path: {CHROMA_DIR}")
    print(f"Collection: {collection_name}")
    print(f"Embedding model: {embedding_model}")
    print(f"Ollama base URL: {ollama_base_url}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a persistent Chroma vector index from course knowledge sets.")
    parser.add_argument("--reset", action="store_true", help="Delete the existing Chroma database before indexing.")
    parser.add_argument("--collection", default=COLLECTION_NAME, help="Chroma collection name.")
    parser.add_argument("--ollama-base-url", default=OLLAMA_BASE_URL, help="Ollama server base URL.")
    parser.add_argument("--embedding-model", default=EMBEDDING_MODEL, help="Ollama embedding model.")
    parser.add_argument("--ollama-timeout", type=int, default=OLLAMA_TIMEOUT, help="Ollama request timeout in seconds.")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Approximate chunk size in characters.")
    parser.add_argument("--overlap", type=int, default=CHUNK_OVERLAP, help="Character overlap between adjacent chunks.")
    parser.add_argument("--batch-size", type=int, default=EMBEDDING_BATCH_SIZE, help="Chunks to embed before each upsert.")
    parser.add_argument(
        "--max-text-length",
        type=int,
        default=EMBEDDING_MAX_TEXT_LENGTH,
        help="Maximum characters sent to Ollama for one embedding request.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    build_index(
        reset=cli_args.reset,
        collection_name=cli_args.collection,
        ollama_base_url=cli_args.ollama_base_url,
        embedding_model=cli_args.embedding_model,
        ollama_timeout=cli_args.ollama_timeout,
        chunk_size=cli_args.chunk_size,
        overlap=cli_args.overlap,
        batch_size=cli_args.batch_size,
        max_text_length=cli_args.max_text_length,
    )
