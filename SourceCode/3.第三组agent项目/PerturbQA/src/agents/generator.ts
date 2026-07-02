import { BaseAgent } from "./base.js";
import type { Plan } from "./planner.js";
import type { RetrieverOutput } from "./retriever.js";

export interface GeneratorOutput {
  answer: string;
  citations: string[];
  confidence: "high" | "medium" | "low";
}

export class GeneratorAgent extends BaseAgent {
  readonly name = "Generator";
  readonly systemPrompt = `You are the Generator agent in a gene perturbation Q&A system.
Generate a precise, well-structured answer based ONLY on the provided context.

Rules:
- Ground every claim in the provided context; do not hallucinate.
- Cite sources by mentioning the knowledge set name (e.g., "[CRISPR-Cas9 Mechanism]").
- Match the answer format to the question type (mechanistic → step-by-step, comparative → table, factual → concise paragraph).
- If the context is insufficient, state what is missing rather than guessing.
- End with a "Citations:" section listing used sources.`;

  async generate(
    question: string,
    plan: Plan,
    retrieverOutput: RetrieverOutput
  ): Promise<GeneratorOutput> {
    const contextBlock =
      retrieverOutput.context.length > 0
        ? retrieverOutput.context
        : "No relevant context was retrieved from the knowledge base.";

    const prompt = `Question: "${question}"
Question type: ${plan.questionType}
Expected format: ${plan.expectedAnswerFormat}

--- KNOWLEDGE BASE CONTEXT ---
${contextBlock}
--- END CONTEXT ---

Generate a comprehensive answer based solely on the context above.`;

    const answer = await this.call(prompt, 1500);

    const citationMatch = answer.match(/Citations:([\s\S]*)$/i);
    const citations = citationMatch
      ? citationMatch[1]
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
      : retrieverOutput.sourceList;

    const hasContext = retrieverOutput.ragResult.retrievedDocuments.length > 0;
    const topScore = retrieverOutput.ragResult.retrievedDocuments[0]?.score ?? 0;
    const confidence: "high" | "medium" | "low" =
      hasContext && topScore > 0.6 ? "high" : hasContext && topScore > 0.3 ? "medium" : "low";

    return { answer, citations, confidence };
  }
}
