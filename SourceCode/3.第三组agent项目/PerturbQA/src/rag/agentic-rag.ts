import { CONFIG } from "../config.js";
import { callPiModel } from "../providers/pi-bridge.js";
import { VectorStore, type SearchResult } from "./vector-store.js";
import { getQueryEmbedding } from "./embedder.js";

async function callLLM(system: string, user: string, maxTokens: number): Promise<string> {
  return callPiModel(system, user, maxTokens);
}

export interface RetrievalDecision {
  needsRetrieval: boolean;
  reason: string;
  queries: string[];
  strategy: "semantic" | "keyword" | "hybrid" | "none";
}

export interface RetrievalStep {
  round: number;
  decision: RetrievalDecision;
  query: string;
  resultsCount: number;
  resultsSummary: string;
  sufficient: boolean;
}

export interface AgenticRAGResult {
  question: string;
  steps: RetrievalStep[];
  retrievedDocuments: SearchResult[];
  context: string;
}

async function analyzeQuestion(question: string): Promise<RetrievalDecision> {
  const text = await callLLM(
    `You are a retrieval decision agent for a gene perturbation knowledge base.
Analyze the user question and decide what to retrieve.
Respond ONLY with valid JSON matching this schema:
{
  "needsRetrieval": boolean,
  "reason": "brief explanation",
  "queries": ["query1", "query2"],
  "strategy": "semantic" | "keyword" | "hybrid" | "none"
}
Use "semantic" for conceptual questions, "keyword" for specific terms/genes, "hybrid" for mixed.
"none" only if the question is a simple greeting or clearly off-topic.`,
    `Question: "${question}"`,
    512
  );

  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    return jsonMatch ? JSON.parse(jsonMatch[0]) : defaultDecision(question);
  } catch {
    return defaultDecision(question);
  }
}

function defaultDecision(question: string): RetrievalDecision {
  return {
    needsRetrieval: true,
    reason: "Fallback: attempting retrieval for all domain questions.",
    queries: [question],
    strategy: "hybrid",
  };
}

async function checkSufficiency(
  question: string,
  results: SearchResult[],
  round: number
): Promise<{ sufficient: boolean; refinedQuery?: string }> {
  if (results.length === 0) return { sufficient: false, refinedQuery: question + " mechanism" };
  if (results[0].score < 0.2) return { sufficient: false, refinedQuery: question.split(" ").slice(0, 4).join(" ") };

  const snippets = results
    .slice(0, 3)
    .map((r, i) => `[${i + 1}] ${r.document.text.slice(0, 200)}`)
    .join("\n");

  const text = await callLLM(
    "Answer ONLY with JSON: {\"sufficient\": boolean, \"refinedQuery\": \"string or null\"}",
    `Question: "${question}"\nRetrieved snippets:\n${snippets}\nAre these snippets sufficient to answer the question?`,
    128
  );

  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    return jsonMatch ? JSON.parse(jsonMatch[0]) : { sufficient: round >= 2 };
  } catch {
    return { sufficient: round >= 2 };
  }
}

export async function agenticRetrieve(
  question: string,
  store: VectorStore
): Promise<AgenticRAGResult> {
  const steps: RetrievalStep[] = [];
  let allResults: SearchResult[] = [];
  const seenIds = new Set<string>();

  const decision = await analyzeQuestion(question);

  if (!decision.needsRetrieval) {
    return {
      question,
      steps: [{ round: 0, decision, query: "", resultsCount: 0, resultsSummary: "No retrieval needed.", sufficient: true }],
      retrievedDocuments: [],
      context: "",
    };
  }

  for (let round = 0; round < CONFIG.maxRetrievalRounds; round++) {
    const query = decision.queries[round] ?? decision.queries[0];

    let results: SearchResult[] = [];

    if (decision.strategy === "semantic" || decision.strategy === "hybrid") {
      const embedding = await getQueryEmbedding(query);
      results = store.search(embedding, CONFIG.topK);
    }

    if (decision.strategy === "keyword" || decision.strategy === "hybrid") {
      // Always include original question tokens for exact model/method name matching
      const queryTokens = query.toLowerCase().split(/\s+/).filter((w) => w.length > 3);
      const questionTokens = question.toLowerCase().split(/[\s\[\],]+/).filter((w) => w.length > 3);
      const keywords = [...new Set([...queryTokens, ...questionTokens])];
      const kwResults = store.keywordSearch(keywords, CONFIG.topK);
      for (const r of kwResults) {
        const existing = results.find((x) => x.document.id === r.document.id);
        if (existing) {
          // Boost score if keyword match is stronger than semantic match
          existing.score = Math.max(existing.score, r.score);
        } else {
          results.push(r);
        }
      }
    }

    // Deduplicate across rounds
    const newResults = results.filter((r) => !seenIds.has(r.document.id));
    for (const r of newResults) seenIds.add(r.document.id);
    allResults = [...allResults, ...newResults].sort((a, b) => b.score - a.score).slice(0, CONFIG.topK * 2);

    const summary =
      results.length > 0
        ? results
            .slice(0, 2)
            .map((r) => `"${r.document.metadata.title ?? r.document.metadata.knowledgeSet}" (score: ${r.score.toFixed(3)})`)
            .join(", ")
        : "No results found.";

    const sufficiency = await checkSufficiency(question, allResults, round);

    steps.push({
      round: round + 1,
      decision: round === 0 ? decision : { ...decision, queries: [query] },
      query,
      resultsCount: results.length,
      resultsSummary: summary,
      sufficient: sufficiency.sufficient,
    });

    if (sufficiency.sufficient) break;

    // Refine query for next round
    if (sufficiency.refinedQuery && round + 1 < CONFIG.maxRetrievalRounds) {
      decision.queries[round + 1] = sufficiency.refinedQuery;
    }
  }

  const topDocs = allResults.slice(0, CONFIG.topK);
  const context = topDocs
    .map((r) => `### ${r.document.metadata.title ?? r.document.metadata.knowledgeSet}\n${r.document.text}`)
    .join("\n\n---\n\n");

  return { question, steps, retrievedDocuments: topDocs, context };
}

export function formatRetrievalTrace(result: AgenticRAGResult): string {
  const lines: string[] = [`**Retrieval Decision Process for:** "${result.question}"\n`];

  const header = "| Step | Decision | Query | Retrieved | Sufficient |";
  const divider = "|------|----------|-------|-----------|------------|";
  lines.push(header, divider);

  for (const step of result.steps) {
    lines.push(
      `| ${step.round} | ${step.decision.strategy} (${step.decision.needsRetrieval ? "retrieve" : "skip"}) | ${step.query.slice(0, 40)}... | ${step.resultsCount} docs | ${step.sufficient ? "✓" : "✗"} |`
    );
  }
  return lines.join("\n");
}
