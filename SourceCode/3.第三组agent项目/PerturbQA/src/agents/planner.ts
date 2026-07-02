import { BaseAgent } from "./base.js";

export interface Plan {
  questionType: "factual" | "mechanistic" | "comparative" | "procedural" | "analytical";
  complexity: "simple" | "moderate" | "complex";
  focusAreas: string[];
  retrievalKeywords: string[];
  expectedAnswerFormat: string;
  reasoning: string;
}

export class PlannerAgent extends BaseAgent {
  readonly name = "Planner";
  readonly systemPrompt = `You are the Planner agent in a gene perturbation Q&A system.
Your job: analyze the user question and create a structured retrieval plan.

Respond ONLY with valid JSON:
{
  "questionType": "factual" | "mechanistic" | "comparative" | "procedural" | "analytical",
  "complexity": "simple" | "moderate" | "complex",
  "focusAreas": ["area1", "area2"],
  "retrievalKeywords": ["keyword1", "keyword2", "keyword3"],
  "expectedAnswerFormat": "brief description of expected answer format",
  "reasoning": "why you chose these focus areas and keywords"
}`;

  async plan(question: string): Promise<Plan> {
    const text = await this.call(`User question: "${question}"`, 512);
    try {
      const match = text.match(/\{[\s\S]*\}/);
      return match ? JSON.parse(match[0]) : this.fallbackPlan(question);
    } catch {
      return this.fallbackPlan(question);
    }
  }

  private fallbackPlan(question: string): Plan {
    const keywords = question
      .split(/\s+/)
      .filter((w) => w.length > 4)
      .slice(0, 5);
    return {
      questionType: "factual",
      complexity: "moderate",
      focusAreas: ["gene perturbation", "mechanism"],
      retrievalKeywords: keywords,
      expectedAnswerFormat: "Structured explanation with evidence",
      reasoning: "Fallback plan using question keywords.",
    };
  }
}
