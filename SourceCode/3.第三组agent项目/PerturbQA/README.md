# PerturbQA

A domain Q&A system for gene perturbation research, built as a **pi extension** on top of
the same engine feynman and waddington use. Running `npm run dev` spawns pi's full TUI
as a subprocess — streaming output, markdown rendering, session persistence, `/model`
switching — all inherited for free.

**Knowledge Base**: 51 sets · 47 papers · 82 vector chunks  
**Benchmark**: 22 questions · 5 types · 3 difficulty levels  
**Best result**: 54.5% pass rate · 62.0/100 avg (pi-agent mode, Claude Sonnet 4.6)

---

## Quick Start

```bash
cd perturbqa
npm install          # install dependencies
npm run index        # build vector store (~2 min, first time only)
npm run dev          # launch pi TUI
```

On first run PerturbQA detects that no credentials are configured and launches an
interactive model setup wizard. Credentials are stored in `~/.perturbqa/agent/` and
are completely independent of any other tool.

---

## Authentication

PerturbQA uses its own credential store at `~/.perturbqa/agent/`. It does **not**
share credentials with feynman or any other tool.

### First run — interactive setup wizard

```
┌  PerturbQA · Model Setup

◆ Authentication
  Credentials will be stored in ~/.perturbqa/agent/
  Supports OAuth (Claude Pro/Max, ChatGPT Plus, Copilot…)
  and API keys (Anthropic, OpenAI, Google, Groq, Mistral, Ollama…)

? Choose how to configure model access:
❯ OAuth login (Claude Pro/Max, ChatGPT Plus, GitHub Copilot, …)
  API key or custom provider (Anthropic, OpenAI, Google, local/self-hosted, …)
  Cancel

└  PerturbQA is ready
```

The wizard is identical to feynman's `feynman setup` — it handles OAuth browser flows,
API key storage, and custom/local provider configuration.

### Option B — env var (skip wizard)

Create a `.env` file inside `perturbqa/`:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
# or
OPENAI_API_KEY=sk-...
```

### Credential paths

| Path | Contents |
|------|----------|
| `~/.perturbqa/agent/auth.json` | OAuth tokens and API keys |
| `~/.perturbqa/agent/settings.json` | Currently selected model |
| `~/.perturbqa/agent/models.json` | Custom provider configuration |
| `~/.perturbqa/sessions/` | Conversation session history |

Override the credential directory with `PERTURBQA_AUTH_DIR=<path>`.

---

## How It Works

`npm run dev` does three things:

1. **Prints the PerturbQA banner** briefly before pi clears the screen
2. **Runs auth setup** — wizard on first run, instant skip if already configured
3. **Spawns pi as a subprocess** with:
   - `--extension src/extensions/perturbqa-tools.ts` — 4 domain tools + 2 slash commands
   - `--system-prompt SYSTEM.md` — gene perturbation domain expert instructions
   - `--session-dir ~/.perturbqa/sessions` — isolated session storage
   - `PI_CODING_AGENT_DIR=~/.perturbqa/agent` — PerturbQA's own auth and model settings

The subprocess uses `@earendil-works/pi-coding-agent 0.75.x`, so globally installed pi
extensions load without conflicts.

---

## Domain Tools

Four tools registered in the pi TUI that the LLM calls automatically:

| Tool | Description |
|------|-------------|
| `perturbqa_search(query)` | Hybrid semantic + BM25 bigram search over 82 chunks from 51 papers |
| `gene_info(symbol)` | Gene name, Entrez ID, description from NCBI / MyGene.info |
| `protein_interactions(symbol)` | Top-10 interaction partners from STRING-DB (score ≥ 0.7) |
| `paper_capability_matrix(slug)` | 6-question capability evaluation for a specific paper |

---

## Slash Commands

In addition to all standard pi slash commands (`/model`, `/new`, `/resume`, `/share`, …):

| Command | Description |
|---------|-------------|
| `/paper` | Interactive paper selector → capability matrix evaluation |
| `/bench [ids…]` | Run the 22-question benchmark (`/bench gp-001 gp-002` or all) |

---

## The 6 Capability Questions

Standard criteria used by `paper_capability_matrix` and `/paper`:

1. **Unseen perturbation** — Can it predict effects of perturbations not seen during training?
2. **Cross-cell-line (gene intersection)** — Does it support cross-cell-line prediction on shared gene sets?
3. **Zero-shot unseen cell line (gene intersection)** — Can it generalise to entirely new cell lines?
4. **Cross-perturbation-technology (gene intersection)** — Can it transfer across CRISPR, RNAi, or OE?
5. **Zero-shot gene misalignment** — Can it operate when source and target share no gene sets?
6. **Perturbation specificity** — Does it outperform a mean-shift baseline?

`paper_capability_matrix` reads pre-computed answers when available (41 of 51 papers),
otherwise runs LLM interrogation with vector-store evidence retrieval.

---

## Architecture

```
npm run dev
     │
     ├─ printAsciiHeader()
     ├─ ensureModelAuth()     ← wizard on first run, instant skip if configured
     │       stores creds in ~/.perturbqa/agent/
     └─ launchPiChat()        ← spawn pi subprocess
          │  PI_CODING_AGENT_DIR=~/.perturbqa/agent
          │  --extension perturbqa-tools.ts
          │  --system-prompt SYSTEM.md
          │  --session-dir ~/.perturbqa/sessions
          ▼
     ┌────────────────────────────────────────────────────────┐
     │  pi TUI  (@earendil-works/pi-coding-agent 0.75.x)     │
     │  streaming · markdown · session · /model · /share      │
     │  ──────────────────────────────────────────────────    │
     │  PerturbQA Extension                                   │
     │    perturbqa_search · gene_info                        │
     │    protein_interactions · paper_capability_matrix      │
     │    /paper · /bench                                     │
     │  ──────────────────────────────────────────────────    │
     │  System Prompt  (SYSTEM.md)                            │
     └────────────────────────────────────────────────────────┘
                    │ LLM calls tools iteratively
                    ▼
     ┌─────────────────────┐   ┌────────────────────────────────┐
     │  RAG / VectorStore  │   │  Domain MCP Tools              │
     │  82 chunks          │   │  MyGene.info · STRING-DB       │
     │  cosine + BM25      │   └────────────────────────────────┘
     └─────────────────────┘

  Benchmark runner (runner.ts) uses pi-agent:
  LLM → perturbqa_search() → results → LLM → … → final answer
  (up to 6 turns / 4 searches per question)
```

---

## Benchmark Results

Evaluated on 22 domain questions (5 types × 3 difficulty levels).

| Run | Model | Pipeline | Pass Rate | Avg Score |
|-----|-------|----------|-----------|-----------|
| 1 | GPT-5.5 Codex | QAOrchestrator | 40.9% | 46.2 |
| 2 | Claude Sonnet 4.6 | QAOrchestrator | 40.9% | 42.5 |
| 3 | Claude Sonnet 4.6 | QAOrchestrator + BM25 bigram | 40.9% | 41.5 |
| **4** | **Claude Sonnet 4.6** | **pi-agent (iterative tool-calling)** | **54.5%** | **62.0** |

By difficulty (best run — pi-agent):

| Difficulty | Questions | Pass Rate | Avg Score |
|------------|-----------|-----------|-----------|
| Easy | 3 | 66.7% | 64.0 |
| Medium | 11 | 63.6% | 66.1 |
| Hard | 8 | 37.5% | 55.5 |

See [REPORT.md](REPORT.md) for the full experimental report.

---

## Knowledge Base

**51 knowledge sets** across 8 categories:

| Category | Count | Examples |
|----------|-------|---------|
| Prediction — GNN / graph | 9 | GEARS, TxPert, scBIG, AdaPert, PDGrapher |
| Prediction — VAE / generative | 6 | CPA, CRADLE-VAE, GPO-VAE, PerturbedVAE |
| Prediction — diffusion & flow | 6 | CellFlow, PerturbDiff, Squidiff, Unlasting |
| Prediction — drug response | 5 | TranSiGen, PRnet, XPert, PrePR-CT |
| Foundation models | 8 | scGPT, CellFM, GeneCompass, scFoundation, scLong |
| Evaluation frameworks | 9 | GGE, AUPRC, Systema, 27-method benchmark |
| Analysis tools | 4 | Pertpy, scDNS, River, MorphDiff |
| Core mechanism & experimental | 4 | CRISPR-Cas9, Perturb-seq, GRN inference |

Each entry: `content/<slug>.md` (800–2000 words) · `keywords.json` · `source.json`.  
**41 of 51** have a pre-computed **Capability Summary** with the full 6-question ability matrix.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic platform key; takes precedence over OAuth |
| `OPENAI_API_KEY` | — | OpenAI platform key |
| `PERTURBQA_AUTH_DIR` | `~/.perturbqa/agent` | Override the credential directory |
| `PI_HARDWARE_CURSOR` | `1` | Hardware cursor in pi TUI |
| `NCBI_API_KEY` | — | Optional; raises MyGene.info rate limits |

---

## Project Structure

```
perturbqa/
├── src/
│   ├── main.ts                        # Entry: banner → auth → launchPiChat()
│   ├── pi/
│   │   ├── launch.ts                  # launchPiChat() — spawns pi subprocess
│   │   ├── runtime.ts                 # resolvePiPaths(), buildPiArgs(), buildPiEnv()
│   │   └── pi-cli-wrapper.ts          # Wrapper imported before pi main
│   ├── extensions/
│   │   └── perturbqa-tools.ts         # default ExtensionFactory: 4 tools + /paper + /bench
│   ├── agents/
│   │   ├── pi-agent.ts                # Iterative tool-calling agent (used by benchmark)
│   │   ├── base.ts                    # BaseAgent — callPiModel()
│   │   ├── orchestrator.ts            # QAOrchestrator (legacy 4-agent pipeline)
│   │   └── interrogation.ts           # SIX_QUESTIONS + capability summary parser
│   ├── rag/
│   │   ├── vector-store.ts            # Cosine + BM25 bigram hybrid search
│   │   ├── embedder.ts                # Xenova/all-MiniLM-L6-v2 (local, no API needed)
│   │   ├── indexer.ts                 # Indexes knowledge_base/ into vector store
│   │   └── agentic-rag.ts             # 3-round adaptive retrieval loop
│   ├── providers/
│   │   └── pi-bridge.ts               # callPiModel() — all LLM calls via pi-ai
│   ├── model/                         # Pi model management (ported from feynman/waddington)
│   │   ├── commands.ts                # runModelSetup(), authenticateModelProvider()
│   │   ├── catalog.ts                 # getAvailableModelRecords()
│   │   └── registry.ts                # ModelRegistry wrapping pi-coding-agent
│   ├── auth/
│   │   └── setup.ts                   # ensureModelAuth() — wizard on first run
│   ├── config/
│   │   └── paths.ts                   # ~/.perturbqa/ credential paths
│   ├── mcp/tools/                     # MyGene.info, STRING-DB, NCBI tools
│   └── evaluation/
│       └── runner.ts                  # Benchmark runner (pi-agent mode)
├── SYSTEM.md                          # Gene perturbation domain system prompt
├── REPORT.md                          # Detailed experimental report
├── knowledge_base/                    # 51 knowledge sets
├── benchmark/questions.json           # 22 benchmark questions + reference answers
└── .vector-store/                     # Auto-generated; rebuild with npm run index
```

---

## Report

See [REPORT.md](REPORT.md) for the full experimental report including agent architecture,
ablation study, embedding model comparison, and per-question analysis.
