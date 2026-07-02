# Drug Discovery Agentic Q&A Assignment 

## Selected topic and optional modules

- Research topic: `drug-discovery`
- Memory module: `multi-level-persistent-memory-system` — difficulty 1
- Orchestration module: `advanced-dynamic-orchestration` — difficulty 3
- Skill module: `deploy-or-integrate-mcp-tool-skill` — difficulty 1
- Total difficulty: 5

## How to run

```bash
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Quick test without UI

```bash
python validate_submission.py
python evaluate_benchmark.py
python demo_orchestration_cases.py
python demo_memory.py
```

## Optional Phi-3 model

The model file is intentionally not included because it is large. Put it here:

```text
models/Phi-3-mini-4k-instruct.Q4_0.gguf
```

The default system works without the local model using deterministic RAG, memory, orchestration, and PubChem skill calls. If you later extend generation with the model, set:

```bash
export USE_LLM=true
export MODEL_PATH=./models/Phi-3-mini-4k-instruct.Q4_0.gguf
```

## Important files

```text
content/drug-discovery/        # 25 valid knowledge sets
benchmark/drug-discovery/      # 30 benchmark questions
benchmark/orchestration-dynamic/ # 10 dynamic orchestration tests
src/orchestrator.py            # advanced dynamic orchestration engine
src/memory_system.py           # working + episodic + semantic memory
src/skills/pubchem_skill.py    # PubChem SKILL integration
logs/                          # execution traces and skill invocations
reports/                       # benchmark and rubric-alignment outputs
```

