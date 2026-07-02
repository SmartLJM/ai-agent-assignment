# Structured Knowledge Base

This Lv.1 optional module transforms the course knowledge assets into a structured SQLite knowledge base.

## Structure Choice

The implementation uses a hybrid structure:

- Attribute-value tables for paper metadata.
- Hierarchical topic/keyword tables from `keywords.json`.
- Entity-relation links between papers, authors, topics, keywords, and method entities.

This is suitable for single-cell/spatial omics because the assets have rich metadata, strong method entities, and clear topic labels.

## Build Flow

```mermaid
flowchart TD
    A["data/**/source.json"] --> C["build_structured_kb.py"]
    B["data/**/keywords.json"] --> C
    D["content/ files"] --> C
    C --> E["papers table"]
    C --> F["authors + paper_authors"]
    C --> G["themes + paper_themes"]
    C --> H["keywords + paper_keywords"]
    C --> I["methods + paper_methods"]
    E --> J["storage/structured_kb.sqlite3"]
    F --> J
    G --> J
    H --> J
    I --> J
```

## Database Diagram

```mermaid
erDiagram
    papers ||--o{ paper_authors : has
    authors ||--o{ paper_authors : writes
    papers ||--o{ paper_themes : classified_as
    themes ||--o{ paper_themes : contains
    papers ||--o{ paper_keywords : tagged_with
    keywords ||--o{ paper_keywords : contains
    papers ||--o{ paper_methods : mentions
    methods ||--o{ paper_methods : method_entity

    papers {
        text knowledge_set_id PK
        text knowledge_set_type
        text title
        text doi
        text journal
        integer publication_year
        text url
    }
```

## Run

Build the database:

```powershell
python scripts/build_structured_kb.py
```

Run a direct query:

```powershell
python scripts/query_structured_kb.py
```

Edit `MODE` and `QUERY_TEXT` in `scripts/query_structured_kb.py`.

Supported modes:

- `method`
- `theme`
- `keyword`
- `year`
- `journal`
- `text`

Example queries:

- `MODE = "method"; QUERY_TEXT = "Nicheformer"`
- `MODE = "theme"; QUERY_TEXT = "spatial-omics"`
- `MODE = "year"; QUERY_TEXT = "2026"`
- `MODE = "journal"; QUERY_TEXT = "Nature Biotechnology"`

## Hybrid RAG Use

The structured database can also constrain RAG retrieval:

```powershell
python scripts/hybrid_rag.py
```

Hybrid flow:

```mermaid
flowchart TD
    A["User question"] --> B["Structured KB candidate lookup"]
    B --> C["Candidate paper IDs"]
    C --> D["Filtered vector retrieval"]
    D --> E["Evidence chunks"]
    B --> F["Structured metadata summary"]
    E --> G["LLM answer"]
    F --> G
```

This makes the structured KB collaborate with vector search: SQL handles exact metadata constraints such as year, journal, method name, topic, or keyword; vector search handles paragraph-level evidence.

The local web app exposes the same pipeline through `Hybrid 问答`. Its trace panel shows the structured candidate papers and the matched reasons, for example `year:2026`, `journal:Nature Biotechnology`, `keyword:foundation-model`, and `theme:interpretability`.

## Query Methods Covered

- Direct SQL-style lookup through `scripts/query_structured_kb.py`.
- Hybrid RAG candidate lookup through `scripts/hybrid_rag.py`.
- Browser demo through `scripts/rag_web.py` and the `Hybrid 问答` button.
