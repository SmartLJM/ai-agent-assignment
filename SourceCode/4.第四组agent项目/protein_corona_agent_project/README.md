# Single-Cell Omics RAG Project

This project stores single-cell/spatial omics knowledge assets and provides a simple RAG question-answering pipeline.

## Current Runtime

- Local embedding: `bge-m3` through Ollama
- Vector store: `storage/vector_store_bge_m3/`
- External LLM: OpenAI-compatible API
- Default external model: `deepseek-ai/DeepSeek-V4-Flash`

## Directory Layout

```text
protein_corona_agent_project/
├── data/                    # Course knowledge assets
├── scripts/
│   ├── build_index.py        # Optional Chroma builder
│   ├── build_vector_store.py # RAG vector store builder
│   ├── build_structured_kb.py # Structured SQLite KB builder
│   ├── query_structured_kb.py # Structured KB query examples
│   ├── hybrid_rag.py         # Structured KB + vector retrieval
│   ├── memory_system.py      # Multi-level persistent memory
│   ├── memory_demo.py        # Memory write/search demo
│   ├── rag_core.py           # Retrieval + generation logic
│   ├── rag_chat.py           # PyCharm-friendly question runner
│   ├── rag_web.py            # Local browser app for demo/testing
│   ├── agentic_rag.py        # LLM-planned multi-step RAG
│   ├── agentic_hybrid_rag.py # Memory + Agentic planner + Structured KB + vector retrieval
│   ├── skills/               # External tool/skill integrations
│   ├── check_ollama.py       # Check local embedding service
│   └── check_external_llm.py # Check external LLM API
├── storage/
│   ├── chroma/               # Chroma data, kept for compatibility
│   ├── memory.sqlite3        # Persistent working/episodic/semantic memory
│   ├── structured_kb.sqlite3 # Structured KB generated from source/keywords metadata
│   └── vector_store_bge_m3/  # Runtime RAG vector store
├── .env.example
├── config.py
└── requirements.txt
```

## Knowledge Set Format

Each knowledge set should follow:

```text
data/
└── 01-academic/
    └── example-paper-id/
        ├── content/
        │   └── paper.pdf
        ├── keywords.json
        └── source.json
```

Supported content files:

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.pdf`
- `.epub`

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create `.env` from `.env.example` and put the external LLM API key there:

```text
EXTERNAL_LLM_BASE_URL=https://api.siliconflow.cn/v1/chat/completions
EXTERNAL_LLM_MODEL=deepseek-ai/DeepSeek-V4-Flash
EXTERNAL_LLM_API_KEY=your-key-here
```

`.env` is ignored by git.

## Health Checks

Check local Ollama embedding:

```powershell
python scripts/check_ollama.py
```

Check external LLM:

```powershell
python scripts/check_external_llm.py
```

## Build RAG Vector Store

Run:

```powershell
python scripts/build_vector_store.py
```

This writes:

```text
storage/vector_store_bge_m3/
├── chunks.jsonl
├── vectors.npy
└── manifest.json
```

## Ask Questions

Open `scripts/rag_chat.py` in PyCharm and edit:

```python
QUESTION = "Nicheformer 这篇论文主要解决了单细胞和空间组学中的什么问题？"
```

Then run:

```powershell
python scripts/rag_chat.py
```

Set `INTERACTIVE = True` in `rag_chat.py` if you want to type questions in the PyCharm console.

## Local Web App

Run this file directly in PyCharm:

```powershell
python scripts/rag_web.py
```

Then open the URL printed by the script, usually:

```text
http://127.0.0.1:8000
```

The web app has six actions:

- `只检索`: embed the question and show the most relevant chunks.
- `问答`: retrieve chunks and ask the external LLM to answer with citations.
- `协作问答`: combine memory retrieval, Agentic planning, structured KB filtering, vector retrieval, UniProt Skill calls, and LLM generation.
- `UniProt Skill`: call the external UniProtProteinSkill for protein/gene lookup.
- `Agentic 问答`: ask the LLM planner to create a retrieval plan, run multi-step retrieval, then answer with citations.
- `Hybrid 问答`: use the structured SQLite KB to select candidate papers first, then run filtered vector retrieval and answer with citations.

## Agentic RAG

Run this file directly in PyCharm:

```powershell
python scripts/agentic_rag.py
```

The Agentic RAG flow is:

```text
question -> LLM planner -> retrieval plan JSON -> multi-step retrieval -> evidence deduplication -> final answer
```

The planner output and retrieval trace are printed so the decision process can be shown for the optional module.
If the external LLM API is temporarily unstable, the script keeps the retrieval trace and evidence output instead of crashing.

See `docs/AGENTIC_RAG.md` and `data/benchmark/agentic_rag_questions.json`.

## Agentic Hybrid RAG

Run the integrated collaborative mode:

```powershell
python scripts/agentic_hybrid_rag.py
```

This mode combines the optional modules instead of treating them as isolated features:

```text
question -> memory search -> Agentic planner -> structured KB candidate lookup per step
         -> filtered vector retrieval or plain vector retrieval -> answer -> memory write-back
```

The local web app exposes this path through the `协作问答` button. The separate `问答`, `Agentic 问答`, and `Hybrid 问答` buttons are kept as ablation baselines.

## Benchmark

The main 20-question benchmark is:

```text
data/benchmark/single_cell_omics_rag_benchmark_20.json
```

It includes expected answer points, required source IDs, retrieval expectations, and scoring weights so different RAG variants can be compared consistently.

## Structured Knowledge Base

Build the structured SQLite knowledge base:

```powershell
python scripts/build_structured_kb.py
```

Query it by method, theme, keyword, year, journal, or text:

```powershell
python scripts/query_structured_kb.py
```

The generated database is:

```text
storage/structured_kb.sqlite3
```

See `docs/STRUCTURED_KB.md`.

Run hybrid retrieval plus generation:

```powershell
python scripts/hybrid_rag.py
```

The same Hybrid RAG path is also available in the local web app through the `Hybrid 问答` button.

## Memory System

Initialize and inspect the three-layer persistent memory system:

```powershell
python scripts/memory_system.py
```

Run a standalone memory write/search demo:

```powershell
python scripts/memory_demo.py
```

The memory database is:

```text
storage/memory.sqlite3
```

Normal RAG and Hybrid RAG now retrieve relevant memory before answering and write the interaction back into working, episodic, and semantic memory after answering.

See `docs/MEMORY_SYSTEM.md`.

## Skill System

This project includes a real external database skill:

```text
UniProtProteinSkill
```

It queries the public UniProt REST API without an API key.

Run the natural-language skill demo:

```powershell
python scripts/skills/skill_agent.py
```

Run the lower-level UniProt wrapper demo:

```powershell
python scripts/skills/uniprot_protein_skill.py
```

Skill calls are logged to:

```text
storage/runtime/skill_call_log.jsonl
```

See `docs/SKILL_SYSTEM.md`.

The local web app exposes this through the standalone `UniProt Skill` button and `/api/skill_uniprot`. The collaborative `协作问答` path also calls the skill automatically when it detects protein or gene mentions such as `OCT4`, `SOX2`, or `TP53`.

## Notes

`build_index.py` still exists for Chroma experiments, but the runtime RAG path uses the lightweight NumPy vector store because it is more reliable in this Windows environment and is fast enough for a few thousand chunks.
