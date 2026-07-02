import { getProvider } from "../providers/index.js";
import { VectorStore } from "../rag/vector-store.js";
import { getEmbedding } from "../rag/embedder.js";

export interface CapabilityAnswer {
  question: string;
  verdict: "Yes" | "Partial" | "No" | "Not evaluated";
  evidence: string;
  confidence: "high" | "medium" | "low";
}

export interface InterrogationResult {
  paperSlug: string;
  paperTitle: string;
  tier: string;
  answers: CapabilityAnswer[];
  rawSummary: string | null;
}

export const SIX_QUESTIONS = [
  {
    id: "q1",
    label: "Unseen perturbation prediction",
    query: "unseen perturbation OOD out-of-distribution generalization held-out novel genes",
  },
  {
    id: "q2",
    label: "Cross cell-line (gene intersection)",
    query: "cross cell line transfer prediction gene intersection shared genes",
  },
  {
    id: "q3",
    label: "Zero-shot unseen cell line (gene intersection)",
    query: "zero-shot unseen cell line no fine-tuning gene intersection",
  },
  {
    id: "q4",
    label: "Cross perturbation technology (gene intersection)",
    query: "cross perturbation technology CRISPRi overexpression knockdown different modality",
  },
  {
    id: "q5",
    label: "Zero-shot gene misalignment (no intersection)",
    query: "zero-shot gene misalignment no shared genes different gene vocabulary",
  },
  {
    id: "q6",
    label: "Perturbation-specificity vs. simple baseline",
    query: "perturbation specific outperform linear baseline mean expression simple baseline",
  },
] as const;

// Parse pre-computed Capability Summary from content markdown
export function parseCapabilitySummary(content: string): {
  answers: Array<{ question: string; verdict: string; evidence: string }>;
  tier: string;
} | null {
  const summaryMatch = content.match(/## Capability Summary\n+([\s\S]*?)(?:\n---|\n## |\s*$)/);
  if (!summaryMatch) return null;

  const block = summaryMatch[1];

  // Extract table rows
  const rows: Array<{ question: string; verdict: string; evidence: string }> = [];
  const tableRows = block.match(/\|([^|]+)\|([^|]+)\|([^|]+)\|/g) ?? [];
  for (const row of tableRows) {
    const cells = row.split("|").map((c) => c.trim()).filter(Boolean);
    if (cells.length < 3) continue;
    const question = cells[0];
    const verdict = cells[1];
    const evidence = cells[2];
    // Skip header and separator rows
    if (question === "Question" || question.startsWith("-")) continue;
    rows.push({ question, verdict, evidence });
  }

  // Extract tier
  const tierMatch = block.match(/\*\*Overall capability tier\*\*[:\s]+([^\n]+)/);
  const tier = tierMatch ? tierMatch[1].trim().replace(/^\[|\]$/g, "") : "Unknown";

  return rows.length > 0 ? { answers: rows, tier } : null;
}

// Deep LLM interrogation for a single question using vector store context
export async function interrogateQuestion(
  store: VectorStore,
  paperSlug: string,
  paperTitle: string,
  question: (typeof SIX_QUESTIONS)[number],
): Promise<CapabilityAnswer> {
  // Build targeted query: paper + question keywords
  const query = `${paperTitle} ${question.query} capability summary`;
  const embedding = await getEmbedding(query);

  // Semantic + keyword search
  const semResults = store.search(embedding, 4);
  const kwResults = store.keywordSearch(
    [paperSlug, ...question.query.split(" ").filter((w) => w.length > 3)],
    4
  );

  // Merge, prefer paper-specific chunks
  const seen = new Set<string>();
  const merged = [...semResults, ...kwResults]
    .sort((a, b) => {
      const aMatch = a.document.metadata.knowledgeSet === paperSlug ? 1 : 0;
      const bMatch = b.document.metadata.knowledgeSet === paperSlug ? 1 : 0;
      return bMatch - aMatch || b.score - a.score;
    })
    .filter((r) => {
      if (seen.has(r.document.id)) return false;
      seen.add(r.document.id);
      return true;
    })
    .slice(0, 4);

  const context = merged
    .map((r) => `[${r.document.metadata.knowledgeSet}]\n${r.document.text.slice(0, 600)}`)
    .join("\n\n---\n\n");

  const provider = await getProvider();
  const system = `You are a scientific evidence extractor for gene perturbation prediction models.
Answer ONLY with valid JSON: {"verdict":"Yes"|"Partial"|"No"|"Not evaluated","evidence":"<one sentence from context>","confidence":"high"|"medium"|"low"}
Rules:
- "Yes": explicitly demonstrated in experiments
- "Partial": partially addressed or tested in limited settings
- "No": explicitly stated as not supported, or clear limitations mentioned
- "Not evaluated": no mention in context
- evidence must be a direct quote or close paraphrase from the context`;

  const user = `Paper: "${paperTitle}" (slug: ${paperSlug})
Question: "${question.label}"
Context:\n${context}
Does this paper demonstrate: ${question.query}?`;

  const raw = await provider.chat(system, user, 200);
  try {
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        question: question.label,
        verdict: parsed.verdict ?? "Not evaluated",
        evidence: parsed.evidence ?? "",
        confidence: parsed.confidence ?? "low",
      };
    }
  } catch { /* fall through */ }

  return { question: question.label, verdict: "Not evaluated", evidence: "", confidence: "low" };
}
