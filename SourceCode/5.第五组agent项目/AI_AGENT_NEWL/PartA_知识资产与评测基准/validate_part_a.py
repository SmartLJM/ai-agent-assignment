from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
BENCHMARK_FILE = ROOT / "benchmark" / "qa_dataset.json"
OUTPUT_FILE = ROOT / "validation_summary.json"
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED = {"id", "question", "type", "difficulty", "answer", "sources", "theme"}


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", str(value)).lower()


def theme_valid(theme) -> bool:
    if theme == "medical-image-segmentation":
        return True
    return isinstance(theme, list) and any(
        isinstance(entry, dict) and "medical-image-segmentation" in entry
        for entry in theme
    )


def is_asset_dir(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "content").is_dir()
        and (path / "keywords.json").is_file()
        and (path / "source.json").is_file()
    )


def iter_assets() -> list[Path]:
    assets = {}
    for source_path in sorted(DATA_DIR.rglob("source.json")):
        asset = source_path.parent
        if is_asset_dir(asset):
            assets[asset.name] = asset
    return [assets[key] for key in sorted(assets)]


def main() -> int:
    assets = iter_assets()
    structure_ok = 0
    content_ok = 0
    keywords_ok = 0
    url_ok = 0
    direct_urls = 0
    fallback_urls = 0
    academic_papers = 0
    academic_with_doi = 0
    source_types = {}
    contents = {}
    issues = []

    for asset in assets:
        content_path = asset / "content" / "content.txt"
        keywords_path = asset / "keywords.json"
        source_path = asset / "source.json"
        if not (content_path.is_file() and keywords_path.is_file() and source_path.is_file()):
            issues.append({"asset": asset.name, "issue": "missing-required-file"})
            continue
        structure_ok += 1
        content = content_path.read_text(encoding="utf-8", errors="ignore").strip()
        contents[asset.name] = content
        content_ok += bool(content)

        keywords = json.loads(keywords_path.read_text(encoding="utf-8"))
        values = [keyword for group in keywords.values() for keyword in group] if isinstance(keywords, dict) else []
        if values and all(KEBAB.fullmatch(keyword) for keyword in values):
            keywords_ok += 1
        else:
            issues.append({"asset": asset.name, "issue": "invalid-keywords"})

        source = json.loads(source_path.read_text(encoding="utf-8"))
        source_type = source.get("type", "missing")
        source_types[source_type] = source_types.get(source_type, 0) + 1
        url = str(source.get("url", ""))
        url_ok += url.startswith(("http://", "https://"))
        if source.get("url_kind") == "title-search-fallback":
            fallback_urls += 1
        elif url.startswith(("http://", "https://")):
            direct_urls += 1
        if source.get("type") == "academic-paper":
            academic_papers += 1
            academic_with_doi += bool(source.get("doi"))

    questions = json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
    schema_ok = 0
    source_links_ok = 0
    quote_matches_ok = 0
    themes_ok = 0
    ids = []
    for item in questions:
        if not isinstance(item, dict) or not REQUIRED <= set(item):
            issues.append({"id": item.get("id") if isinstance(item, dict) else None, "issue": "invalid-schema"})
            continue
        schema_ok += 1
        ids.append(item["id"])
        themes_ok += theme_valid(item["theme"])
        sources = item.get("sources") or []
        if sources and all(source.get("knowledge_set_id") in contents for source in sources):
            source_links_ok += 1
        else:
            issues.append({"id": item["id"], "issue": "unlinked-source"})
        if sources and all(
            source.get("original_text")
            and normalized(source["original_text"]) in normalized(contents.get(source.get("knowledge_set_id"), ""))
            for source in sources
        ):
            quote_matches_ok += 1
        else:
            issues.append({"id": item["id"], "issue": "quote-not-found"})

    summary = {
        "knowledge_assets": {
            "count": len(assets),
            "structure_ok": structure_ok,
            "nonempty_content": content_ok,
            "keywords_kebab_case": keywords_ok,
            "valid_url": url_ok,
            "direct_url": direct_urls,
            "title_search_fallback": fallback_urls,
            "academic_papers": academic_papers,
            "academic_papers_with_doi": academic_with_doi,
            "source_types": source_types,
            "official_source_folders": {
                path.name: len([item for item in path.iterdir() if item.is_dir()])
                for path in sorted(DATA_DIR.iterdir()) if path.is_dir()
            },
        },
        "benchmark": {
            "count": len(questions),
            "schema_ok": schema_ok,
            "unique_ids": len(set(ids)),
            "source_links_ok": source_links_ok,
            "quoted_evidence_matches": quote_matches_ok,
            "themes_ok": themes_ok,
        },
        "structural_pass": (
            len(assets) >= 20
            and structure_ok == len(assets)
            and content_ok == len(assets)
            and keywords_ok == len(assets)
            and len(questions) >= 20
            and schema_ok == len(questions)
            and len(set(ids)) == len(questions)
            and source_links_ok == len(questions)
            and quote_matches_ok == len(questions)
            and themes_ok == len(questions)
        ),
        "quality_warnings": [
            f"{fallback_urls} 个来源仍为题名检索回退页，已在 source.json 中标记 source_quality_note。"
        ] if fallback_urls else [],
        "issues": issues,
    }
    OUTPUT_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["structural_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
