# Rubric Alignment

## Foundational module: Knowledge Assets

- Requirement: at least 20 valid knowledge sets with `content/`, `keywords.json`, and `source.json`.
- This submission: 25 knowledge sets under `content/drug-discovery/`.
- Format: topic and all keywords are kebab-case.
- Sources: source metadata includes DOI or URL.

## Foundational module: Evaluation Benchmark

- Requirement: at least 20 valid questions with answer, sources, theme, difficulty, and type.
- This submission: 30 questions stored independently as `Q0001.json` through `Q0030.json`.
- Question types: short-answer, true-false, single-choice, and multiple-choice.

## Optional module: Multi-level Persistent Memory System

Implemented files:

```text
memory/working_memory.json
memory/episodic_memory.jsonl
memory/semantic_memory.json
```

The implementation supports write and retrieval mechanisms for all three layers.

## Optional module: Advanced Dynamic Orchestration

Implemented in `src/orchestrator.py`.

Evidence:

- dynamic planning from task input,
- workflow adjustment after validation,
- loop/retry with larger retrieval depth,
- error recovery when PubChem skill fails,
- execution traces in `logs/execution_trace.jsonl`.

## Optional module: PubChem SKILL

Implemented in `src/skills/pubchem_skill.py`.

Exposed interfaces:

- `search_compound(name)`
- `get_compound_properties(name)`
- `get_synonyms(name)`

Invocation logs are written to `logs/skill_invocations.jsonl`.
