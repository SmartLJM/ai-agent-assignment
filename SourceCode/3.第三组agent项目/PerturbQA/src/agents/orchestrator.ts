import chalk from "chalk";
import { VectorStore } from "../rag/vector-store.js";
import { PlannerAgent } from "./planner.js";
import { RetrieverAgent } from "./retriever.js";
import { GeneratorAgent } from "./generator.js";
import { ValidatorAgent } from "./validator.js";
import { formatRetrievalTrace } from "../rag/agentic-rag.js";
import type { Plan } from "./planner.js";
import type { RetrieverOutput } from "./retriever.js";
import type { GeneratorOutput } from "./generator.js";
import type { ValidationResult } from "./validator.js";

export interface PipelineResult {
  question: string;
  plan: Plan;
  retrieverOutput: RetrieverOutput;
  generatorOutput: GeneratorOutput;
  validation: ValidationResult;
  finalAnswer: string;
  traceLog: string;
}

export class QAOrchestrator {
  private planner = new PlannerAgent();
  private generator = new GeneratorAgent();
  private validator = new ValidatorAgent();
  private retriever: RetrieverAgent;

  constructor(store: VectorStore) {
    this.retriever = new RetrieverAgent(store);
  }

  async run(question: string, verbose = true): Promise<PipelineResult> {
    const log = (agent: string, msg: string) => {
      if (verbose) console.log(chalk.cyan(`[${agent}]`) + " " + msg);
    };

    // ── Step 1: Planner ─────────────────────────────────────────────────────
    log("Planner", "Analyzing question and creating retrieval plan...");
    const plan = await this.planner.plan(question);
    if (verbose) {
      console.log(chalk.gray(`  → type: ${plan.questionType}, complexity: ${plan.complexity}`));
      console.log(chalk.gray(`  → focus: ${plan.focusAreas.join(", ")}`));
    }

    // ── Step 2: Retriever (Agentic RAG) ─────────────────────────────────────
    log("Retriever", "Running Agentic RAG...");
    const retrieverOutput = await this.retriever.retrieve(question, plan);
    if (verbose) {
      const { steps } = retrieverOutput.ragResult;
      for (const step of steps) {
        console.log(
          chalk.gray(
            `  [Round ${step.round}] ${step.decision.strategy} | found: ${step.resultsCount} | sufficient: ${step.sufficient ? "✓" : "✗"}`
          )
        );
      }
      console.log(chalk.gray(`  → Sources: ${retrieverOutput.sourceList.join(", ") || "none"}`));
    }

    // ── Step 3: Generator ────────────────────────────────────────────────────
    log("Generator", "Generating answer from retrieved context...");
    const generatorOutput = await this.generator.generate(question, plan, retrieverOutput);
    if (verbose) {
      console.log(chalk.gray(`  → Confidence: ${generatorOutput.confidence}`));
    }

    // ── Step 4: Validator ────────────────────────────────────────────────────
    log("Validator", "Validating answer quality...");
    const validation = await this.validator.validate(
      question,
      retrieverOutput.context,
      generatorOutput
    );
    if (verbose) {
      console.log(
        chalk.gray(
          `  → Score: ${validation.score}/100 | Valid: ${validation.isValid} | Issues: ${validation.issues.length}`
        )
      );
    }

    const traceLog = [
      formatRetrievalTrace(retrieverOutput.ragResult),
      "",
      `**Generator confidence:** ${generatorOutput.confidence}`,
      `**Validator score:** ${validation.score}/100`,
      validation.issues.length > 0 ? `**Issues:** ${validation.issues.join("; ")}` : "",
    ]
      .filter((l) => l !== undefined)
      .join("\n");

    return {
      question,
      plan,
      retrieverOutput,
      generatorOutput,
      validation,
      finalAnswer: validation.finalAnswer,
      traceLog,
    };
  }
}
