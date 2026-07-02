import { readFile, writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import chalk from "chalk";
import { CONFIG } from "../config.js";
import { VectorStore } from "../rag/vector-store.js";
import { runWithPiAgent } from "../agents/pi-agent.js";
import { callPiModel } from "../providers/pi-bridge.js";

const __filename = fileURLToPath(import.meta.url);

interface BenchmarkQuestion {
  id: string;
  question: string;
  answer: string;
  difficulty: "easy" | "medium" | "hard";
  type: string;
  topic: string;
}

interface QuestionResult {
  id: string;
  question: string;
  difficulty: string;
  generatedAnswer: string;
  autoScore: number;
  searchQueries: string[];
  turns: number;
  passed: boolean;
}

async function autoScore(
  question: string,
  referenceAnswer: string,
  generatedAnswer: string
): Promise<number> {
  const raw = await callPiModel(
    `You are a grader scoring an AI-generated answer against a reference answer.
Score 0-100 based on factual accuracy and completeness.
Reply with ONLY a single integer (0-100), nothing else.`,
    `Question: "${question}"\n\nReference answer: "${referenceAnswer.slice(0, 600)}"\n\nGenerated answer: "${generatedAnswer.slice(0, 600)}"`,
    16
  );
  const n = parseInt(raw.trim().match(/\d+/)?.[0] ?? "50", 10);
  return Math.min(100, Math.max(0, isNaN(n) ? 50 : n));
}

export async function runBenchmark(questionIds?: string[]): Promise<void> {
  if (!existsSync(CONFIG.vectorStorePath)) {
    console.error(chalk.red("Vector store not found. Run `npm run index` first."));
    process.exit(1);
  }

  const store = new VectorStore(CONFIG.vectorStorePath);
  await store.load();
  console.log(chalk.green(`Loaded vector store: ${store.count} documents\n`));

  const raw = await readFile(CONFIG.benchmarkPath, "utf-8");
  const benchmark = JSON.parse(raw) as { questions: BenchmarkQuestion[] };

  let questions = benchmark.questions;
  const validIds = questionIds?.filter(id => /^gp-\d+$/.test(id.trim()));
  if (validIds && validIds.length > 0) {
    questions = questions.filter((q) => validIds.includes(q.id));
    if (questions.length === 0) {
      console.log(chalk.yellow(`No questions matched IDs: ${validIds.join(", ")}\n`));
      return;
    }
  }

  console.log(chalk.bold(`Running benchmark: ${questions.length} questions  [pi-agent mode]\n`));

  const results: QuestionResult[] = [];
  let totalScore = 0;
  let passed = 0;

  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    console.log(chalk.yellow(`[${i + 1}/${questions.length}] ${q.id}: ${q.question.slice(0, 60)}...`));

    try {
      const agentResult = await runWithPiAgent(q.question, store);

      await new Promise((r) => setTimeout(r, 600));

      const score = await autoScore(q.question, q.answer, agentResult.answer);

      const result: QuestionResult = {
        id: q.id,
        question: q.question,
        difficulty: q.difficulty,
        generatedAnswer: agentResult.answer.slice(0, 500),
        autoScore: score,
        searchQueries: agentResult.searchQueries,
        turns: agentResult.turns,
        passed: score >= 60,
      };
      results.push(result);
      totalScore += score;
      if (result.passed) passed++;

      console.log(
        chalk.gray(
          `  score=${score} turns=${agentResult.turns} searches=${agentResult.searchQueries.length} ` +
          (result.passed ? chalk.green("PASS") : chalk.red("FAIL"))
        )
      );

      if (i < questions.length - 1) {
        await new Promise((r) => setTimeout(r, 1000));
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(chalk.red(`  ERROR: ${msg}`));
      if (msg.includes("429") || msg.includes("rate_limit")) {
        console.log(chalk.gray("  Rate limited — waiting 15s..."));
        await new Promise((r) => setTimeout(r, 15000));
      }
      results.push({
        id: q.id,
        question: q.question,
        difficulty: q.difficulty,
        generatedAnswer: "ERROR",
        autoScore: 0,
        searchQueries: [],
        turns: 0,
        passed: false,
      });
    }
  }

  const avgScore = results.length > 0 ? totalScore / results.length : 0;
  const passRate = results.length > 0 ? (passed / results.length) * 100 : 0;

  console.log("\n" + chalk.bold("═══════════════════ BENCHMARK RESULTS ═══════════════════"));
  console.log(`Total questions:  ${results.length}`);
  console.log(`Passed (≥60):     ${passed} (${passRate.toFixed(1)}%)`);
  console.log(`Average score:    ${avgScore.toFixed(1)}/100`);

  const byDifficulty = ["easy", "medium", "hard"].map((d) => {
    const qs = results.filter((r) => r.difficulty === d);
    const avg = qs.length > 0 ? qs.reduce((s, r) => s + r.autoScore, 0) / qs.length : 0;
    return `  ${d}: ${avg.toFixed(1)}/100 (${qs.filter((r) => r.passed).length}/${qs.length} passed)`;
  });
  console.log("\nBy difficulty:\n" + byDifficulty.join("\n"));

  const outputDir = join(dirname(__filename), "../../benchmark");
  await mkdir(outputDir, { recursive: true });
  const outputPath = join(outputDir, `results_${Date.now()}.json`);
  await writeFile(
    outputPath,
    JSON.stringify(
      { timestamp: new Date().toISOString(), mode: "pi-agent", summary: { totalQuestions: results.length, passed, passRate, avgScore }, results },
      null, 2
    ),
    "utf-8"
  );
  console.log(`\nResults saved to: ${outputPath}`);
}

if (process.argv[1] === __filename) {
  const ids = process.argv.slice(2).filter(id => /^gp-\d+$/.test(id));
  runBenchmark(ids.length > 0 ? ids : undefined).catch(console.error);
}
