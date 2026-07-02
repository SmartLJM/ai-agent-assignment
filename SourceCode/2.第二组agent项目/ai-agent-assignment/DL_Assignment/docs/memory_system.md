# Multi-level Persistent Memory System

```mermaid
flowchart LR
    Q[Question/Answer] --> W[Working Memory JSON]
    Q --> E[Episodic Memory JSONL]
    Q --> X[Entity extractor]
    X --> S[Semantic Memory JSON]
    S --> R[Semantic retrieval]
    W --> R
    E --> R
    R --> O[Orchestrator]
```

## Layers

1. Working memory stores recent turns with a capacity limit.
2. Episodic memory stores cross-session interaction summaries in JSONL.
3. Semantic memory stores entities and relations extracted from interactions.

Run:

```bash
python demo_memory.py
```
