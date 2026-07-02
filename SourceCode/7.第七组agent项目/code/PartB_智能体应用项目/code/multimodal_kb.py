from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import numpy as np

from path_config import (
    DEFAULT_NPC_DATASET_DIR,
    EVALUATION_DIR,
    KNOWLEDGE_BASE_DIR,
    PROJECT_ROOT,
    iter_knowledge_asset_dirs,
)
from segmentation_visualizer import list_available_cases, load_case


class _MultimodalHTMLParser(HTMLParser):
    """Extract visible text, image references, and table rows from an HTML document."""

    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self.images: list[dict] = []
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"script", "style"}:
            self._ignored_depth += 1
        elif tag == "img" and attrs_dict.get("src"):
            self.images.append({"src": attrs_dict["src"], "alt": attrs_dict.get("alt", "")})
        elif tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if any(self._row):
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._cell is not None:
            self._cell.append(value)
        else:
            self.text_parts.append(value)


@dataclass
class KnowledgeRecord:
    record_id: str
    modality: str
    title: str
    text: str
    source: str
    metadata: dict


def _portable_path(path: str | Path) -> str:
    path = Path(path).resolve()
    try:
        return path.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _read_asset_text(asset_dir: Path) -> str:
    path = asset_dir / "content" / "content.txt"
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _case_statistics(case_id: str, dataset_dir: str | Path) -> dict:
    image, mask = load_case(case_id, dataset_dir)
    foreground = mask > 0
    coords = np.argwhere(foreground)
    bbox = []
    if coords.size:
        bbox = [*coords.min(axis=0).tolist(), *coords.max(axis=0).tolist()]
    return {
        "case_id": case_id,
        "shape": list(image.shape),
        "image_mean": round(float(np.mean(image)), 6),
        "image_std": round(float(np.std(image)), 6),
        "mask_voxels": int(foreground.sum()),
        "mask_ratio": round(float(foreground.mean()), 6),
        "mask_bbox": bbox,
    }


class MultiModalKnowledgeBase:
    """A reproducible local index over text, 3D image volumes, and case tables."""

    def __init__(
        self,
        knowledge_dir: str | Path = KNOWLEDGE_BASE_DIR,
        dataset_dir: str | Path = DEFAULT_NPC_DATASET_DIR,
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.dataset_dir = Path(dataset_dir)
        self.records: list[KnowledgeRecord] = []

    def build(self, text_limit: int = 75, case_limit: int = 10) -> list[KnowledgeRecord]:
        records: list[KnowledgeRecord] = []
        for asset_dir in iter_knowledge_asset_dirs(self.knowledge_dir)[:text_limit]:
            text = re.sub(r"\s+", " ", _read_asset_text(asset_dir)).strip()
            source_path = asset_dir / "source.json"
            source = json.loads(source_path.read_text(encoding="utf-8")) if source_path.is_file() else {}
            records.append(
                KnowledgeRecord(
                    record_id=f"text:{asset_dir.name}",
                    modality="text",
                    title=source.get("title", asset_dir.name),
                    text=text[:6000],
                    source=source.get("url", str(source_path)),
                    metadata={"knowledge_set_id": asset_dir.name},
                )
            )

        for case_id in list_available_cases(self.dataset_dir)[:case_limit]:
            stats = _case_statistics(case_id, self.dataset_dir)
            shape = "×".join(map(str, stats["shape"]))
            records.append(
                KnowledgeRecord(
                    record_id=f"image:{case_id}",
                    modality="image",
                    title=f"病例 {case_id} 的 3D 医学影像",
                    text=(
                        f"3D 医学影像病例 {case_id}，体数据尺寸 {shape}，"
                        f"归一化后均值 {stats['image_mean']}，标准差 {stats['image_std']}。"
                    ),
                    source=_portable_path(self.dataset_dir / case_id / "image_processed.npy"),
                    metadata=stats,
                )
            )
            records.append(
                KnowledgeRecord(
                    record_id=f"table:{case_id}",
                    modality="table",
                    title=f"病例 {case_id} 的分割统计表",
                    text=(
                        f"病例 {case_id} 分割统计：前景体素 {stats['mask_voxels']}，"
                        f"前景占比 {stats['mask_ratio']}，包围盒 {stats['mask_bbox']}。"
                    ),
                    source=_portable_path(EVALUATION_DIR / "case_statistics.csv"),
                    metadata=stats,
                )
            )
        self.records = records
        return records

    def ingest_html_document(self, source: str | Path) -> list[KnowledgeRecord]:
        """Extract text, image references, and tables from a local HTML file."""
        source_text = str(source)
        if source_text.startswith(("http://", "https://")):
            raise ValueError("当前提交采用完全本地模式，不允许在线网页抓取。")
        path = Path(source).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"找不到本地 HTML 文档：{path}")
        html_text = path.read_text(encoding="utf-8", errors="ignore")
        base = path.as_uri()
        source_text = _portable_path(path)
        document_id = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") or "html-document"

        parser = _MultimodalHTMLParser()
        parser.feed(html_text)
        extracted: list[KnowledgeRecord] = []
        visible_text = " ".join(parser.text_parts).strip()
        if visible_text:
            extracted.append(
                KnowledgeRecord(
                    record_id=f"document-text:{document_id}",
                    modality="text",
                    title=f"{document_id} 网页文本",
                    text=visible_text[:6000],
                    source=source_text,
                    metadata={"document_id": document_id, "extractor": "html-parser"},
                )
            )
        for index, image in enumerate(parser.images, start=1):
            extracted.append(
                KnowledgeRecord(
                    record_id=f"document-image:{document_id}:{index}",
                    modality="image",
                    title=image.get("alt") or f"{document_id} 图像 {index}",
                    text=f"网页图像；替代文本：{image.get('alt', '')}",
                    source=urljoin(base, image["src"]),
                    metadata={"document_id": document_id, "src": image["src"], "alt": image.get("alt", "")},
                )
            )
        for index, rows in enumerate(parser.tables, start=1):
            extracted.append(
                KnowledgeRecord(
                    record_id=f"document-table:{document_id}:{index}",
                    modality="table",
                    title=f"{document_id} 表格 {index}",
                    text=json.dumps(rows, ensure_ascii=False),
                    source=source_text,
                    metadata={"document_id": document_id, "rows": rows, "row_count": len(rows)},
                )
            )
        self.records.extend(extracted)
        return extracted

    @staticmethod
    def _terms(query: str) -> list[str]:
        terms = re.findall(r"[a-z0-9][a-z0-9\-_.]*|[\u4e00-\u9fff]{2,}", query.lower())
        expanded = []
        for term in terms:
            expanded.append(term)
            if re.fullmatch(r"[\u4e00-\u9fff]+", term):
                expanded.extend(term[index : index + 2] for index in range(max(0, len(term) - 1)))
        return list(dict.fromkeys(expanded))

    def search(self, query: str, top_k: int = 5, modalities: Iterable[str] | None = None) -> list[dict]:
        if not self.records:
            self.build()
        allowed = set(modalities or ("text", "image", "table"))
        terms = self._terms(query)
        modality_hints = {
            "image": ("图像", "影像", "切片", "image", "volume"),
            "table": ("表", "统计", "体素", "占比", "table", "metric"),
            "text": ("论文", "文献", "方法", "原理", "text", "paper"),
        }
        ranked = []
        for record in self.records:
            if record.modality not in allowed:
                continue
            haystack = f"{record.title} {record.text} {record.record_id}".lower()
            score = sum(haystack.count(term) * (3 if len(term) >= 4 else 1) for term in terms)
            if any(hint in query.lower() for hint in modality_hints[record.modality]):
                score += 4
            if score > 0:
                ranked.append((score, record))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].record_id))
        return [{**asdict(record), "score": score} for score, record in ranked[:top_k]]

    def answer(self, query: str, top_k: int = 5) -> dict:
        results = self.search(query, top_k=top_k)
        if not results:
            return {"query": query, "answer": "本地多模态知识库未检索到相关证据。", "evidence": []}
        lines = [f"[{item['modality']}] {item['title']}：{item['text'][:220]}" for item in results]
        return {
            "query": query,
            "answer": "检索到以下本地多模态证据：\n" + "\n".join(lines),
            "evidence": results,
            "modalities": sorted({item["modality"] for item in results}),
        }

    def save(self, output_dir: str | Path = EVALUATION_DIR) -> dict:
        if not self.records:
            self.build()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        index_path = output_dir / "multimodal_index.json"
        index_path.write_text(
            json.dumps([asdict(record) for record in self.records], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        table_rows = [record.metadata for record in self.records if record.modality == "table"]
        csv_path = output_dir / "case_statistics.csv"
        if table_rows:
            with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=table_rows[0].keys())
                writer.writeheader()
                writer.writerows(table_rows)
        counts = {modality: sum(record.modality == modality for record in self.records) for modality in ("text", "image", "table")}
        return {"index": _portable_path(index_path), "table": _portable_path(csv_path), "counts": counts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="比较病例影像与分割统计表，并检索相关医学图像分割文献")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_NPC_DATASET_DIR))
    args = parser.parse_args()
    kb = MultiModalKnowledgeBase(dataset_dir=args.dataset_dir)
    kb.build()
    print(json.dumps(kb.save(), ensure_ascii=False, indent=2))
    print(json.dumps(kb.answer(args.query), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
