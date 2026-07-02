import { BaseAgent } from "./base.js";
import { VectorStore } from "../rag/vector-store.js";
import { agenticRetrieve, type AgenticRAGResult } from "../rag/agentic-rag.js";
import type { Plan } from "./planner.js";

export interface RetrieverOutput {
  ragResult: AgenticRAGResult;
  context: string;
  sourceList: string[];
}

export class RetrieverAgent extends BaseAgent {
  readonly name = "Retriever";
  readonly systemPrompt = "You are the Retriever agent. Use Agentic RAG to find relevant context.";

  constructor(private store: VectorStore) {
    super();
  }

  async retrieve(question: string, plan: Plan): Promise<RetrieverOutput> {
    // Use plan keywords to augment the question for retrieval
    const augmentedQuestion =
      plan.retrievalKeywords.length > 0
        ? `${question} [focus: ${plan.focusAreas.join(", ")}]`
        : question;

    const ragResult = await agenticRetrieve(augmentedQuestion, this.store);

    const sourceList = [
      ...new Set(ragResult.retrievedDocuments.map((r) => r.document.metadata.title ?? r.document.metadata.knowledgeSet)),
    ];

    return {
      ragResult,
      context: ragResult.context,
      sourceList,
    };
  }
}
