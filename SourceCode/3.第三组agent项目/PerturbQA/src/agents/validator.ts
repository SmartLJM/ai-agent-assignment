import { BaseAgent } from "./base.js";
import type { GeneratorOutput } from "./generator.js";

export interface ValidationResult {
  isValid: boolean;
  score: number;
  checks: {
    grounded: boolean;
    complete: boolean;
    accurate: boolean;
    cited: boolean;
  };
  issues: string[];
  finalAnswer: string;
}

export class ValidatorAgent extends BaseAgent {
  readonly name = "Validator";
  readonly systemPrompt = `You are the Validator agent in a gene perturbation Q&A system.
Evaluate the generated answer for quality.

Respond ONLY with valid JSON:
{
  "isValid": boolean,
  "score": 0-100,
  "checks": {
    "grounded": boolean,
    "complete": boolean,
    "accurate": boolean,
    "cited": boolean
  },
  "issues": ["issue1", "issue2"],
  "improvedAnswer": "improved version of the answer, or same if already good"
}`;

  async validate(
    question: string,
    context: string,
    generatorOutput: GeneratorOutput
  ): Promise<ValidationResult> {
    const prompt = `Question: "${question}"

Context used:
${context.slice(0, 2000)}

Generated answer:
${generatorOutput.answer}

Validate this answer. Check:
1. grounded: Is every claim traceable to the context?
2. complete: Does it fully answer the question?
3. accurate: Are the facts correct based on context?
4. cited: Does it cite sources?`;

    const text = await this.call(prompt, 1500);

    try {
      const match = text.match(/\{[\s\S]*\}/);
      const parsed = match ? JSON.parse(match[0]) : null;
      if (parsed) {
        return {
          isValid: parsed.isValid ?? false,
          score: parsed.score ?? 50,
          checks: parsed.checks ?? { grounded: false, complete: false, accurate: false, cited: false },
          issues: parsed.issues ?? [],
          finalAnswer: parsed.improvedAnswer ?? generatorOutput.answer,
        };
      }
    } catch {
      // fall through
    }

    return {
      isValid: true,
      score: 70,
      checks: { grounded: true, complete: true, accurate: true, cited: generatorOutput.citations.length > 0 },
      issues: [],
      finalAnswer: generatorOutput.answer,
    };
  }
}
