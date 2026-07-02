from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import DATA_DIR, STRUCTURED_KB_PATH  # noqa: E402


KNOWN_METHOD_ALIASES = {
    "3d-ot": ["3D-OT", "3d-OT"],
    "cellxgene": ["CELLxGENE", "cellxgene"],
    "concord": ["CONCORD"],
    "cytosignal": ["CytoSignal"],
    "ghist": ["GHIST"],
    "human-cell-atlas": ["Human Cell Atlas"],
    "iscale": ["iSCALE"],
    "nicheformer": ["Nicheformer"],
    "remap": ["REMAP"],
    "spatialglue": ["SpatialGlue"],
    "splisosm": ["SPLISOSM"],
    "spotiphy": ["Spotiphy"],
    "systema": ["Systema"],
    "xenium": ["Xenium"],
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def iter_knowledge_sets(data_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(data_dir.glob("*/*")):
        if not path.is_dir():
            continue
        if (path / "source.json").is_file() and (path / "keywords.json").is_file():
            paths.append(path)
    return paths


def normalize_publication_year(source: dict[str, Any]) -> int | None:
    value = str(source.get("publication_date") or source.get("year") or "").strip()
    match = re.search(r"(20\d{2}|19\d{2})", value)
    if not match:
        return None
    return int(match.group(1))


def content_file_summary(knowledge_set_path: Path) -> tuple[int, str]:
    content_dir = knowledge_set_path / "content"
    if not content_dir.is_dir():
        return 0, ""
    files = [path for path in sorted(content_dir.iterdir()) if path.is_file()]
    extensions = sorted({path.suffix.lower().lstrip(".") or "no-extension" for path in files})
    return len(files), ",".join(extensions)


def detect_methods(knowledge_set_id: str, source: dict[str, Any], keywords: dict[str, Any]) -> list[tuple[str, str]]:
    haystack = " ".join(
        [
            knowledge_set_id,
            str(source.get("title", "")),
            json.dumps(keywords, ensure_ascii=False),
        ]
    ).lower()

    methods: list[tuple[str, str]] = []
    for canonical, aliases in KNOWN_METHOD_ALIASES.items():
        for alias in aliases:
            if alias.lower() in haystack:
                methods.append((canonical, aliases[0]))
                break
    return sorted(set(methods))


def connect() -> sqlite3.Connection:
    STRUCTURED_KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(STRUCTURED_KB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS paper_methods;
        DROP TABLE IF EXISTS paper_keywords;
        DROP TABLE IF EXISTS paper_themes;
        DROP TABLE IF EXISTS paper_authors;
        DROP TABLE IF EXISTS methods;
        DROP TABLE IF EXISTS keywords;
        DROP TABLE IF EXISTS themes;
        DROP TABLE IF EXISTS authors;
        DROP TABLE IF EXISTS papers;

        CREATE TABLE papers (
            knowledge_set_id TEXT PRIMARY KEY,
            knowledge_set_type TEXT NOT NULL,
            title TEXT NOT NULL,
            doi TEXT,
            url TEXT,
            journal TEXT,
            publisher TEXT,
            publication_date TEXT,
            publication_year INTEGER,
            volume TEXT,
            issue TEXT,
            page TEXT,
            citation_count INTEGER,
            source_type TEXT,
            content_file_count INTEGER NOT NULL,
            content_extensions TEXT NOT NULL
        );

        CREATE TABLE authors (
            author_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE paper_authors (
            knowledge_set_id TEXT NOT NULL REFERENCES papers(knowledge_set_id) ON DELETE CASCADE,
            author_id INTEGER NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
            author_order INTEGER NOT NULL,
            PRIMARY KEY (knowledge_set_id, author_id)
        );

        CREATE TABLE themes (
            theme TEXT PRIMARY KEY
        );

        CREATE TABLE paper_themes (
            knowledge_set_id TEXT NOT NULL REFERENCES papers(knowledge_set_id) ON DELETE CASCADE,
            theme TEXT NOT NULL REFERENCES themes(theme) ON DELETE CASCADE,
            PRIMARY KEY (knowledge_set_id, theme)
        );

        CREATE TABLE keywords (
            keyword TEXT PRIMARY KEY
        );

        CREATE TABLE paper_keywords (
            knowledge_set_id TEXT NOT NULL REFERENCES papers(knowledge_set_id) ON DELETE CASCADE,
            theme TEXT NOT NULL,
            keyword TEXT NOT NULL REFERENCES keywords(keyword) ON DELETE CASCADE,
            PRIMARY KEY (knowledge_set_id, theme, keyword)
        );

        CREATE TABLE methods (
            method_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL
        );

        CREATE TABLE paper_methods (
            knowledge_set_id TEXT NOT NULL REFERENCES papers(knowledge_set_id) ON DELETE CASCADE,
            method_id TEXT NOT NULL REFERENCES methods(method_id) ON DELETE CASCADE,
            PRIMARY KEY (knowledge_set_id, method_id)
        );

        CREATE INDEX idx_papers_year ON papers(publication_year);
        CREATE INDEX idx_papers_journal ON papers(journal);
        CREATE INDEX idx_papers_title ON papers(title);
        CREATE INDEX idx_paper_keywords_keyword ON paper_keywords(keyword);
        CREATE INDEX idx_paper_themes_theme ON paper_themes(theme);
        """
    )


def insert_author(connection: sqlite3.Connection, name: str) -> int:
    connection.execute("INSERT OR IGNORE INTO authors(name) VALUES (?)", (name,))
    row = connection.execute("SELECT author_id FROM authors WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise RuntimeError(f"Could not insert author: {name}")
    return int(row[0])


def build_structured_kb() -> dict[str, int]:
    with connect() as connection:
        create_schema(connection)

        paper_count = 0
        author_link_count = 0
        theme_link_count = 0
        keyword_link_count = 0
        method_link_count = 0

        for knowledge_set_path in iter_knowledge_sets(DATA_DIR):
            knowledge_set_id = knowledge_set_path.name
            knowledge_set_type = knowledge_set_path.parent.name
            source = load_json(knowledge_set_path / "source.json")
            keywords = load_json(knowledge_set_path / "keywords.json")
            content_file_count, content_extensions = content_file_summary(knowledge_set_path)

            title = str(source.get("title") or knowledge_set_id)
            connection.execute(
                """
                INSERT INTO papers (
                    knowledge_set_id, knowledge_set_type, title, doi, url, journal, publisher,
                    publication_date, publication_year, volume, issue, page, citation_count,
                    source_type, content_file_count, content_extensions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    knowledge_set_id,
                    knowledge_set_type,
                    title,
                    str(source.get("doi", "")),
                    str(source.get("url", "")),
                    str(source.get("journal", "")),
                    str(source.get("publisher", "")),
                    str(source.get("publication_date") or source.get("year") or ""),
                    normalize_publication_year(source),
                    str(source.get("volume", "")),
                    str(source.get("issue", "")),
                    str(source.get("page", "")),
                    int(source.get("citation_count") or 0),
                    str(source.get("source_type", "")),
                    content_file_count,
                    content_extensions,
                ),
            )
            paper_count += 1

            for index, author in enumerate(source.get("authors") or [], start=1):
                author_name = str(author).strip()
                if not author_name:
                    continue
                author_id = insert_author(connection, author_name)
                connection.execute(
                    """
                    INSERT OR IGNORE INTO paper_authors(knowledge_set_id, author_id, author_order)
                    VALUES (?, ?, ?)
                    """,
                    (knowledge_set_id, author_id, index),
                )
                author_link_count += 1

            for theme, values in keywords.items():
                theme = str(theme).strip()
                if not theme:
                    continue
                connection.execute("INSERT OR IGNORE INTO themes(theme) VALUES (?)", (theme,))
                connection.execute(
                    "INSERT OR IGNORE INTO paper_themes(knowledge_set_id, theme) VALUES (?, ?)",
                    (knowledge_set_id, theme),
                )
                theme_link_count += 1

                for keyword in values if isinstance(values, list) else []:
                    keyword = str(keyword).strip()
                    if not keyword:
                        continue
                    connection.execute("INSERT OR IGNORE INTO keywords(keyword) VALUES (?)", (keyword,))
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO paper_keywords(knowledge_set_id, theme, keyword)
                        VALUES (?, ?, ?)
                        """,
                        (knowledge_set_id, theme, keyword),
                    )
                    keyword_link_count += 1

            for method_id, display_name in detect_methods(knowledge_set_id, source, keywords):
                connection.execute(
                    "INSERT OR IGNORE INTO methods(method_id, display_name) VALUES (?, ?)",
                    (method_id, display_name),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO paper_methods(knowledge_set_id, method_id) VALUES (?, ?)",
                    (knowledge_set_id, method_id),
                )
                method_link_count += 1

    return {
        "papers": paper_count,
        "author_links": author_link_count,
        "theme_links": theme_link_count,
        "keyword_links": keyword_link_count,
        "method_links": method_link_count,
    }


def main() -> None:
    stats = build_structured_kb()
    print("Structured KB built.")
    print(f"Path: {STRUCTURED_KB_PATH}")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
