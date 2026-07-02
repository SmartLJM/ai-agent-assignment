/**
 * Pi-based agent runner for benchmark evaluation.
 *
 * Replaces the rigid Planner→Retriever→Generator→Validator pipeline with an
 * iterative tool-calling loop: the LLM decides when to call perturbqa_search,
 * how many times, and with what queries, before writing the final answer.
 */

import { complete } from "@earendil-works/pi-ai";
import { Type } from "@earendil-works/pi-ai";
import type { Message, AssistantMessage, ToolResultMessage } from "@earendil-works/pi-ai";
import { AuthStorage, ModelRegistry } from "@earendil-works/pi-coding-agent";
import { getPerturbQAAuthPath, getPerturbQASettingsPath } from "../config/paths.js";
import { getCurrentModelSpec } from "../model/commands.js";
import { getModelsJsonPath } from "../model/registry.js";
import type { VectorStore } from "../rag/vector-store.js";
import { getQueryEmbedding } from "../rag/embedder.js";

const MAX_TURNS = 6;
const LLM_TIMEOUT_MS = 90_000; // 90s per call — hangs killed here

const SYSTEM_PROMPT = `You are PerturbQA, a domain expert in gene perturbation research.

When answering questions:
1. ALWAYS call perturbqa_search first with a precise query to retrieve relevant knowledge.
2. If the first search is insufficient, call perturbqa_search again with a refined or different query.
3. You may search up to 3 times. After gathering context, write a comprehensive, factually grounded answer.
4. Cite the specific papers/methods from the retrieved context.
5. If context is truly insufficient, state clearly what is missing.

Be precise and technical. Ground every claim in the retrieved context.`;

const SEARCH_TOOL = {
  name: "perturbqa_search",
  description:
    "Search the PerturbQA knowledge base (51 gene-perturbation paper summaries). " +
    "Call this with a focused query to retrieve relevant chunks. " +
    "You can call it multiple times with different queries to gather more context.",
  parameters: Type.Object({
    query: Type.String({ description: "Focused search query about gene perturbation methods or concepts" }),
  }),
};

async function getModel() {
  const authPath = getPerturbQAAuthPath();
  const settingsPath = getPerturbQASettingsPath();
  const reg = ModelRegistry.create(
    AuthStorage.create(authPath),
    getModelsJsonPath(authPath),
  );
  const spec = getCurrentModelSpec(settingsPath) ?? "anthropic/claude-sonnet-4-6";
  const [provider, ...rest] = spec.split("/");
  const modelId = rest.join("/");
  const model = reg.getAvailable().find(
    (m) => m.provider === provider && m.id === modelId,
  ) ?? reg.getAvailable()[0];
  if (!model) throw new Error("No model available");
  const apiKey = (await reg.getApiKeyForProvider(model.provider)) ?? undefined;
  return { model, apiKey };
}

async function executeSearch(query: string, store: VectorStore): Promise<string> {
  const embedding = await getQueryEmbedding(query);
  const results = store.search(embedding, 5);

  // Also run bigram keyword search and merge
  const kwTokens = query.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
  const kwResults = store.keywordSearch(kwTokens, 5);
  const seen = new Set(results.map((r) => r.document.id));
  const merged = [...results];
  for (const r of kwResults) {
    if (!seen.has(r.document.id)) {
      merged.push(r);
      seen.add(r.document.id);
    }
  }
  const top5 = merged.sort((a, b) => b.score - a.score).slice(0, 5);

  if (top5.length === 0) return "No relevant documents found for this query.";
  return top5
    .map(
      (r, i) =>
        `### [${i + 1}] ${r.document.metadata.title ?? r.document.metadata.knowledgeSet} (score: ${r.score.toFixed(3)})\n\n${r.document.text}`,
    )
    .join("\n\n---\n\n");
}

/** Wrap complete() with a hard timeout so a hung API call doesn't block forever. */
async function completeWithTimeout(
  ...args: Parameters<typeof complete>
): Promise<AssistantMessage> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), LLM_TIMEOUT_MS);
  try {
    const [model, context, options] = args;
    return await complete(model, context, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export interface PiAgentResult {
  answer: string;
  searchQueries: string[];
  turns: number;
}

export async function runWithPiAgent(
  question: string,
  store: VectorStore,
): Promise<PiAgentResult> {
  const { model, apiKey } = await getModel();
  const searchQueries: string[] = [];

  const messages: Message[] = [
    { role: "user", content: question, timestamp: Date.now() },
  ];

  let turns = 0;

  for (turns = 0; turns < MAX_TURNS; turns++) {
    const response: AssistantMessage = await completeWithTimeout(
      model,
      {
        systemPrompt: SYSTEM_PROMPT,
        messages,
        tools: [SEARCH_TOOL],
      },
      { apiKey, maxTokens: 2048 },
    );

    messages.push(response);

    // No tool calls — final answer
    if (response.stopReason !== "toolUse") {
      const text = response.content.find((c) => c.type === "text");
      return {
        answer: text?.type === "text" ? text.text : "",
        searchQueries,
        turns: turns + 1,
      };
    }

    // Execute each tool call
    const toolCalls = response.content.filter((c) => c.type === "toolCall");
    for (const tc of toolCalls) {
      if (tc.type !== "toolCall") continue;

      let resultText: string;
      if (tc.name === "perturbqa_search") {
        const query = (tc.arguments as { query?: string }).query ?? question;
        searchQueries.push(query);
        resultText = await executeSearch(query, store);
      } else {
        resultText = `Unknown tool: ${tc.name}`;
      }

      const toolResult: ToolResultMessage = {
        role: "toolResult",
        toolCallId: tc.id,
        toolName: tc.name,
        content: [{ type: "text", text: resultText }],
        isError: false,
        timestamp: Date.now(),
      };
      messages.push(toolResult);
    }
  }

  // Fallback: extract last text from messages
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant") as AssistantMessage | undefined;
  const text = lastAssistant?.content.find((c) => c.type === "text");
  return {
    answer: text?.type === "text" ? text.text : "No answer generated.",
    searchQueries,
    turns,
  };
}
