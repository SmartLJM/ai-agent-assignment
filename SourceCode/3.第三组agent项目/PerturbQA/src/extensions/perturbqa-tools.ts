/**
 * PerturbQA pi extension — exposes knowledge-base and domain tools
 * to the pi TUI as registered tools and slash commands.
 *
 * Loaded by the pi subprocess via --extension flag.
 * Must export a default function matching ExtensionFactory.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { defineTool } from "@earendil-works/pi-coding-agent";
import { Type } from "@earendil-works/pi-ai";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..", "..");

function ok(text: string) {
  return { content: [{ type: "text" as const, text }], details: null };
}

function buildHelpText(kbCount: number): string {
  return `# PerturbQA Help

**Domain**: Gene Perturbation Research
**Knowledge Base**: ${kbCount} papers · 82 vector chunks

## Domain Tools

| Tool | Description |
|------|-------------|
| \`perturbqa_search(query)\` | Semantic + BM25 hybrid search over 82 paper chunks |
| \`gene_info(symbol)\` | Gene name, Entrez ID, description (NCBI / MyGene.info) |
| \`protein_interactions(symbol)\` | Top-10 interaction partners (STRING-DB, score ≥ 0.7) |
| \`paper_capability_matrix(slug)\` | 6-question capability evaluation for a paper |

## Slash Commands

| Command | Description |
|---------|-------------|
| \`/paper\` | Select a paper → evaluate with 6 capability questions |
| \`/bench [ids…]\` | Run benchmark — \`/bench\` (all 22) or \`/bench gp-001 gp-002\` |
| \`/help\` | Show this help without invoking the LLM |
| \`/model\` | Switch LLM provider / model (built-in pi) |
| \`/commands\` | List all available slash commands (built-in pi) |

## The 6 Capability Questions

1. **Unseen perturbation** — Can it predict unseen perturbations?
2. **Cross-cell-line (gene intersection)** — Cross-cell-line on shared gene sets?
3. **Zero-shot unseen cell line** — Generalise to new cell lines without fine-tuning?
4. **Cross-perturbation-technology** — Transfer across CRISPR / RNAi / OE?
5. **Zero-shot gene misalignment** — Works with no shared gene vocabulary?
6. **Perturbation specificity** — Outperforms mean-shift baseline?

## Tips

- Ask questions naturally; the LLM calls \`perturbqa_search\` automatically when needed.
- Use \`/paper\` for structured capability analysis of a specific paper.
- Use \`/bench\` to evaluate system performance on the 22-question benchmark.
`;
}

// ── Lazy store ────────────────────────────────────────────────────────────────

let _store: Awaited<ReturnType<typeof loadStore>> | null = null;

async function loadStore() {
  const { VectorStore } = await import("../rag/vector-store.js");
  const storePath = resolve(ROOT, ".vector-store");
  const store = new VectorStore(storePath);
  if (existsSync(storePath)) await store.load();
  return store;
}

async function getStore() {
  if (!_store) _store = await loadStore();
  return _store;
}

// ── Tools ─────────────────────────────────────────────────────────────────────

const searchTool = defineTool({
  name: "perturbqa_search",
  label: "PerturbQA Knowledge Base Search",
  description:
    "Search the PerturbQA knowledge base (51 gene-perturbation paper summaries). " +
    "Use when the user asks about perturbation prediction methods, cell-line models, " +
    "foundation models, benchmarks, or specific papers.",
  promptSnippet: "perturbqa_search(query) — semantic search over 51 perturbation-research papers",
  parameters: Type.Object({
    query: Type.String({ description: "Search query about gene perturbation methods or concepts" }),
  }),
  async execute(_id, { query }) {
    const store = await getStore();
    if (store.count === 0) return ok("Knowledge base empty. Run: npm run index");
    const { getQueryEmbedding } = await import("../rag/embedder.js");
    const embedding = await getQueryEmbedding(query);
    const results = store.search(embedding, 5);
    const text = results
      .map(
        (r, i) =>
          `### Result ${i + 1}: ${r.document.metadata.knowledgeSet} — ${r.document.metadata.title ?? ""}\n\n${r.document.text}`,
      )
      .join("\n\n---\n\n");
    return ok(text);
  },
});

const geneInfoTool = defineTool({
  name: "gene_info",
  label: "Gene Information (MyGene.info / NCBI)",
  description: "Look up a gene's symbol, Entrez ID, full name, and description from NCBI.",
  parameters: Type.Object({
    symbol: Type.String({ description: 'Gene symbol, e.g. "TP53", "BRCA1"' }),
  }),
  async execute(_id, { symbol }) {
    const { searchGeneInfo } = await import("../mcp/tools/ncbi-gene.js");
    return ok(JSON.stringify(await searchGeneInfo(symbol), null, 2));
  },
});

const interactionsTool = defineTool({
  name: "protein_interactions",
  label: "Protein–Protein Interactions (STRING-DB)",
  description: "Get top-10 interaction partners from STRING-DB (score ≥ 0.7).",
  parameters: Type.Object({
    symbol: Type.String({ description: "Gene / protein symbol" }),
  }),
  async execute(_id, { symbol }) {
    const { getProteinInteractions } = await import("../mcp/tools/string-db.js");
    return ok(JSON.stringify(await getProteinInteractions(symbol), null, 2));
  },
});

const paperCapabilityTool = defineTool({
  name: "paper_capability_matrix",
  label: "Paper Capability Matrix (6 questions)",
  description:
    "Evaluate a paper against 6 standard capability questions: " +
    "unseen perturbation, cross-cell-line, zero-shot cell line, cross-technology, " +
    "gene misalignment, and perturbation specificity.",
  parameters: Type.Object({
    slug: Type.String({
      description: 'Paper slug, e.g. "gears", "cpa". Use perturbqa_search first to find slugs.',
    }),
  }),
  async execute(_id, { slug }) {
    const store = await getStore();
    const { SIX_QUESTIONS, interrogateQuestion, parseCapabilitySummary } = await import(
      "../agents/interrogation.js"
    );
    const contentPath = join(ROOT, "knowledge_base", slug, "content", `${slug}.md`);
    if (existsSync(contentPath)) {
      const parsed = parseCapabilitySummary(readFileSync(contentPath, "utf-8"));
      if (parsed) {
        const rows = parsed.answers
          .map((a) => `- **${a.question}**: ${a.verdict} — ${a.evidence}`)
          .join("\n");
        return ok(`## Capability Matrix: ${slug}\n\n${rows}\n\n**Overall tier**: ${parsed.tier}`);
      }
    }
    const results: string[] = [];
    for (const q of SIX_QUESTIONS) {
      try {
        const a = await interrogateQuestion(store, slug, slug, q);
        results.push(`- **${a.question}**: ${a.verdict} — ${a.evidence}`);
      } catch (e) {
        results.push(`- **${q.label}**: error — ${e instanceof Error ? e.message : String(e)}`);
      }
    }
    return ok(`## Capability Matrix: ${slug} (LLM-analyzed)\n\n${results.join("\n")}`);
  },
});

// ── Default export (pi ExtensionFactory) ─────────────────────────────────────

export default async function perturbqaExtension(pi: ExtensionAPI): Promise<void> {
  getStore().catch(() => {});

  pi.registerTool(searchTool);
  pi.registerTool(geneInfoTool);
  pi.registerTool(interactionsTool);
  pi.registerTool(paperCapabilityTool);

  pi.registerCommand("bench", {
    description: "Run PerturbQA benchmark evaluation (all 22 or specific IDs)",
    handler: async (args, ctx) => {
      ctx.ui.notify("Running benchmark…", "info");
      const ids = args.trim() ? args.trim().split(/\s+/).filter(Boolean) : undefined;
      const { runBenchmark } = await import("../evaluation/runner.js");
      await runBenchmark(ids);
      ctx.ui.notify("Benchmark complete.", "info");
    },
  });

  pi.registerCommand("paper", {
    description: "Deep-interrogate a paper with the 6 capability questions",
    handler: async (_args, ctx) => {
      const kbDir = join(ROOT, "knowledge_base");
      if (!existsSync(kbDir)) {
        ctx.ui.notify("Knowledge base not found. Run: npm run index", "error");
        return;
      }
      const papers = readdirSync(kbDir, { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => {
          const slug = d.name;
          let title = slug;
          let year = "";
          try {
            const kw = JSON.parse(readFileSync(join(kbDir, slug, "keywords.json"), "utf-8")) as {
              title?: string;
            };
            title = kw.title ?? slug;
          } catch { /* skip */ }
          try {
            const src = JSON.parse(readFileSync(join(kbDir, slug, "source.json"), "utf-8")) as {
              year?: unknown;
            };
            year = String(src.year ?? "");
          } catch { /* skip */ }
          return `${year.padStart(4)}  ${title.slice(0, 70)}  [${slug}]`;
        })
        .sort();

      const selected = await ctx.ui.select("Select paper to interrogate:", papers);
      if (!selected) return;
      const m = selected.match(/\[([^\]]+)\]$/);
      if (!m) return;
      pi.sendUserMessage(
        `Run paper_capability_matrix for slug "${m[1]}" and present the full results table.`,
      );
    },
  });

  pi.registerCommand("help", {
    description: "Show PerturbQA domain tools and slash commands",
    handler: async (_args, ctx) => {
      const kbDir = join(ROOT, "knowledge_base");
      const kbCount = existsSync(kbDir)
        ? readdirSync(kbDir, { withFileTypes: true }).filter((d) => d.isDirectory()).length
        : 0;

      pi.sendMessage({
        customType: "perturbqa-help",
        content: buildHelpText(kbCount),
        display: true,
        details: null,
      });
    },
  });
}
