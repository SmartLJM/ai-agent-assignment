# Multi-Level Persistent Memory System

This Lv.1 optional module adds a persistent three-layer memory system to the single-cell/spatial omics RAG agent.

## Memory Layers

- Working memory: recent messages in the current session, with a capacity limit.
- Episodic memory: cross-session question-answer experiences with answer summaries, source IDs, and RAG mode.
- Semantic memory: structured triples distilled from interactions, such as method-topic or paper-identifier relations.

## Architecture

```mermaid
flowchart TD
    A["User question"] --> B["Search memory_system.py"]
    B --> C["Working memory: recent session context"]
    B --> D["Episodic memory: similar historical QA"]
    B --> E["Semantic memory: entity-relation triples"]
    C --> F["Memory context"]
    D --> F
    E --> F
    A --> G["RAG / Hybrid RAG retrieval"]
    G --> H["Evidence chunks"]
    F --> I["LLM answer prompt"]
    H --> I
    I --> J["Answer with citations"]
    J --> K["record_interaction"]
    K --> L["Write working memory"]
    K --> M["Write episodic memory"]
    K --> N["Upsert semantic memory"]
    L --> O["storage/memory.sqlite3"]
    M --> O
    N --> O
```

## Storage Structure

```mermaid
erDiagram
    working_memory {
        integer memory_id PK
        text session_id
        text role
        text content
        integer turn_index
        text created_at
    }

    episodic_memory {
        integer episode_id PK
        text session_id
        text question
        text answer_summary
        text mode
        text source_ids
        text created_at
    }

    semantic_memory {
        integer semantic_id PK
        text subject
        text predicate
        text object
        text evidence
        integer source_episode_id FK
        text created_at
    }

    episodic_memory ||--o{ semantic_memory : distills
```

The database file is:

```text
storage/memory.sqlite3
```

## Run

Initialize the database:

```powershell
python scripts/memory_system.py
```

Run a standalone memory write/search demo:

```powershell
python scripts/memory_demo.py
```

Run normal RAG. The RAG path now retrieves memory before generation and records memory after answering:

```powershell
python scripts/rag_chat.py
```

The web app exposes memory in `/health`, and provides:

- `POST /api/memory_search`
- `POST /api/memory_stats`

## Retrieval Strategy

Working memory uses recency retrieval. Episodic and semantic memory use deterministic keyword matching over question text, answer summaries, source IDs, subjects, predicates, objects, and evidence. This keeps the Lv.1 module explainable and independent from extra embedding rebuilds.

## Write Strategy

Each RAG interaction writes:

- the user question and assistant answer summary into working memory;
- a cross-session episode summary into episodic memory;
- deterministic semantic triples into semantic memory.

The semantic triples are intentionally conservative. They capture source identifiers, DOI relations, known method entities, and important topics such as `foundation-model`, `spatial-omics`, `epigenetics`, and `mitochondria`.
