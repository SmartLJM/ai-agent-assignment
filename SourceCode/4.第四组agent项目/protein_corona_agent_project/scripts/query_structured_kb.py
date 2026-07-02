from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import STRUCTURED_KB_PATH  # noqa: E402


# PyCharm can run this file directly. Change MODE and QUERY_TEXT for quick tests.
MODE = "method"
QUERY_TEXT = "Nicheformer"


def connect() -> sqlite3.Connection:
    if not STRUCTURED_KB_PATH.exists():
        raise RuntimeError("Structured KB is missing. Run scripts/build_structured_kb.py first.")
    connection = sqlite3.connect(STRUCTURED_KB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def query_by_method(text: str) -> list[dict[str, Any]]:
    pattern = f"%{text.lower()}%"
    sql = """
    SELECT p.knowledge_set_id, p.title, p.journal, p.publication_year, p.doi, m.display_name AS method
    FROM papers p
    JOIN paper_methods pm ON p.knowledge_set_id = pm.knowledge_set_id
    JOIN methods m ON pm.method_id = m.method_id
    WHERE lower(m.method_id) LIKE ? OR lower(m.display_name) LIKE ? OR lower(p.title) LIKE ?
    ORDER BY p.publication_year DESC, p.title
    """
    with connect() as connection:
        return [row_to_dict(row) for row in connection.execute(sql, (pattern, pattern, pattern))]


def query_by_theme(text: str) -> list[dict[str, Any]]:
    pattern = f"%{text.lower()}%"
    sql = """
    SELECT DISTINCT p.knowledge_set_id, p.title, p.journal, p.publication_year, p.doi, pt.theme
    FROM papers p
    JOIN paper_themes pt ON p.knowledge_set_id = pt.knowledge_set_id
    WHERE lower(pt.theme) LIKE ?
    ORDER BY p.publication_year DESC, p.title
    """
    with connect() as connection:
        return [row_to_dict(row) for row in connection.execute(sql, (pattern,))]


def query_by_keyword(text: str) -> list[dict[str, Any]]:
    pattern = f"%{text.lower()}%"
    sql = """
    SELECT DISTINCT p.knowledge_set_id, p.title, p.journal, p.publication_year, p.doi, pk.theme, pk.keyword
    FROM papers p
    JOIN paper_keywords pk ON p.knowledge_set_id = pk.knowledge_set_id
    WHERE lower(pk.keyword) LIKE ?
    ORDER BY p.publication_year DESC, p.title
    """
    with connect() as connection:
        return [row_to_dict(row) for row in connection.execute(sql, (pattern,))]


def query_by_year(text: str) -> list[dict[str, Any]]:
    year = int(text)
    sql = """
    SELECT knowledge_set_id, title, journal, publication_date, publication_year, doi
    FROM papers
    WHERE publication_year = ?
    ORDER BY journal, title
    """
    with connect() as connection:
        return [row_to_dict(row) for row in connection.execute(sql, (year,))]


def query_by_journal(text: str) -> list[dict[str, Any]]:
    pattern = f"%{text.lower()}%"
    sql = """
    SELECT knowledge_set_id, title, journal, publication_date, publication_year, doi
    FROM papers
    WHERE lower(journal) LIKE ?
    ORDER BY publication_year DESC, title
    """
    with connect() as connection:
        return [row_to_dict(row) for row in connection.execute(sql, (pattern,))]


def query_by_text(text: str) -> list[dict[str, Any]]:
    pattern = f"%{text.lower()}%"
    sql = """
    SELECT knowledge_set_id, title, journal, publication_date, publication_year, doi, url
    FROM papers
    WHERE lower(title) LIKE ? OR lower(doi) LIKE ? OR lower(knowledge_set_id) LIKE ?
    ORDER BY publication_year DESC, title
    """
    with connect() as connection:
        return [row_to_dict(row) for row in connection.execute(sql, (pattern, pattern, pattern))]


def query(mode: str, text: str) -> list[dict[str, Any]]:
    mode = mode.lower().strip()
    if mode == "method":
        return query_by_method(text)
    if mode == "theme":
        return query_by_theme(text)
    if mode == "keyword":
        return query_by_keyword(text)
    if mode == "year":
        return query_by_year(text)
    if mode == "journal":
        return query_by_journal(text)
    if mode == "text":
        return query_by_text(text)
    raise ValueError(f"Unknown query mode: {mode}")


def print_results(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No structured KB results.")
        return
    for index, row in enumerate(rows, start=1):
        print(f"\n[{index}] {row.get('title')}")
        print(f"    id: {row.get('knowledge_set_id')}")
        print(f"    journal: {row.get('journal')}, year: {row.get('publication_year')}")
        print(f"    doi: {row.get('doi')}")
        for key in ("method", "theme", "keyword"):
            if row.get(key):
                print(f"    {key}: {row[key]}")


def main() -> None:
    rows = query(MODE, QUERY_TEXT)
    print(f"Mode: {MODE}")
    print(f"Query: {QUERY_TEXT}")
    print(f"Results: {len(rows)}")
    print_results(rows)


if __name__ == "__main__":
    main()
