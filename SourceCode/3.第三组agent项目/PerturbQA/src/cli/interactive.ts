import { select, input, confirm } from "@inquirer/prompts";
import chalk from "chalk";
import { readFile } from "fs/promises";
import { existsSync } from "fs";
import { CONFIG } from "../config.js";
import { setProvider, makeProvider } from "../providers/index.js";
import type { ProviderName } from "../providers/types.js";
import { ensureModelAuth, hasAnthropicAuth, hasOpenAIAuth } from "../auth/setup.js";
import { loadSettings, updateSettings } from "../config/settings.js";

interface BenchmarkQuestion {
  id: string;
  question: string;
  type: string;
  difficulty: string;
}

interface BenchmarkFile {
  questions: BenchmarkQuestion[];
}

interface ModelChoice {
  name: string;
  value: { provider: ProviderName; model: string };
  needs: "anthropic" | "openai-api-key" | "codex";
}

const MODEL_CHOICES: ModelChoice[] = [
  {
    name: "Claude Sonnet 4.6  (Anthropic — fastest, requires ANTHROPIC_API_KEY or OAuth)",
    value: { provider: "anthropic" as ProviderName, model: "claude-sonnet-4-6" },
    needs: "anthropic",
  },
  {
    name: "Claude Haiku 4.5   (Anthropic — cheapest, requires ANTHROPIC_API_KEY or OAuth)",
    value: { provider: "anthropic" as ProviderName, model: "claude-haiku-4-5-20251001" },
    needs: "anthropic",
  },
  {
    name: "GPT-4o             (OpenAI — requires OPENAI_API_KEY)",
    value: { provider: "openai" as ProviderName, model: "gpt-4o" },
    needs: "openai-api-key",
  },
  {
    name: "Codex              (OpenAI Codex — uses OPENAI_API_KEY or codex login)",
    value: { provider: "codex" as ProviderName, model: "codex-mini-latest" },
    needs: "codex",
  },
];

async function pickModel(): Promise<void> {
  const settings = await loadSettings();
  const anthropicAuthed = await hasAnthropicAuth();
  const openaiStatus = await (await import("../auth/openai-codex.js")).getOpenAIAuthStatus();
  const hasOpenAIPlatformKey = Boolean(process.env.OPENAI_API_KEY || openaiStatus?.source === "codex-api-key");
  const openaiAuthed = await hasOpenAIAuth();

  const isAvailable = (choice: ModelChoice) => {
    if (choice.needs === "anthropic") return anthropicAuthed;
    if (choice.needs === "openai-api-key") return hasOpenAIPlatformKey;
    return openaiAuthed;
  };

  const choices = MODEL_CHOICES.map((choice) => ({
    ...choice,
    disabled: isAvailable(choice) ? false : "not authenticated",
  }));

  const defaultChoice =
    MODEL_CHOICES.find((choice) => choice.value.provider === settings.provider && choice.value.model === settings.model && isAvailable(choice)) ??
    MODEL_CHOICES.find(isAvailable);

  const choice = await select({
    message: "Select the model to use:",
    choices,
    default: defaultChoice?.value,
  });

  const provider = await makeProvider(choice.provider, choice.model);
  setProvider(provider);
  await updateSettings({ provider: choice.provider, model: choice.model });
  console.log(chalk.green(`\nUsing: ${provider.modelLabel}\n`));
}

async function pickQuestion(): Promise<string> {
  const mode = await select({
    message: "How do you want to ask a question?",
    choices: [
      { name: "Choose from benchmark questions", value: "benchmark" },
      { name: "Type my own question", value: "custom" },
    ],
  });

  if (mode === "custom") {
    return input({ message: "Enter your question:" });
  }

  // Load benchmark questions
  if (!existsSync(CONFIG.benchmarkPath)) {
    console.log(chalk.yellow("Benchmark file not found, switching to custom input.\n"));
    return input({ message: "Enter your question:" });
  }

  const raw = await readFile(CONFIG.benchmarkPath, "utf-8");
  const data: BenchmarkFile = JSON.parse(raw);

  // Group by type
  const byType = new Map<string, BenchmarkQuestion[]>();
  for (const q of data.questions) {
    const group = byType.get(q.type) ?? [];
    group.push(q);
    byType.set(q.type, group);
  }

  const typeChoice = await select({
    message: "Select category:",
    choices: [
      { name: "All questions", value: "all" },
      ...[...byType.keys()].map((t) => ({
        name: `${t} (${byType.get(t)!.length})`,
        value: t,
      })),
    ],
  });

  const pool =
    typeChoice === "all"
      ? data.questions
      : (byType.get(typeChoice) ?? data.questions);

  const qChoice = await select({
    message: "Select question:",
    choices: pool.map((q) => ({
      name: `[${q.id}] ${q.question.slice(0, 70)}${q.question.length > 70 ? "…" : ""}  (${q.difficulty})`,
      value: q.question,
    })),
    pageSize: 12,
  });

  return qChoice;
}

export async function runInteractive(): Promise<void> {
  console.log(chalk.bold("\nPerturbQA — Interactive Mode\n"));

  if (!existsSync(CONFIG.vectorStorePath)) {
    console.log(chalk.yellow("Knowledge base not indexed. Run: npm run index\n"));
  }

  await ensureModelAuth();
  await pickModel();

  const { VectorStore } = await import("../rag/vector-store.js");
  const { QAOrchestrator } = await import("../agents/orchestrator.js");

  const store = new VectorStore(CONFIG.vectorStorePath);
  await store.load();

  if (store.count > 0) {
    console.log(chalk.gray(`Loaded ${store.count} indexed chunks from knowledge base.\n`));
  }

  const orchestrator = new QAOrchestrator(store);

  while (true) {
    const question = await pickQuestion();
    console.log(chalk.bold("\nQuestion:"), question, "\n");

    const showTrace = await confirm({ message: "Show retrieval trace?", default: false });

    console.log(chalk.gray("\nRunning pipeline...\n"));
    const result = await orchestrator.run(question);

    if (showTrace) {
      console.log("\n" + chalk.bold("── Retrieval Trace ──────────────────────────"));
      console.log(result.traceLog);
    }

    console.log("\n" + chalk.bold("── Final Answer ─────────────────────────────"));
    console.log(result.finalAnswer);

    console.log("\n" + chalk.bold("── Summary ───────────────────────────────────"));
    console.log(`Validator score:  ${result.validation.score}/100`);
    console.log(`Sources:          ${result.retrieverOutput.sourceList.join(", ") || "none"}`);

    const again = await confirm({ message: "\nAsk another question?", default: true });
    if (!again) break;

    const switchModel = await confirm({ message: "Switch model?", default: false });
    if (switchModel) await pickModel();
    console.log();
  }

  console.log(chalk.bold("\nGoodbye!\n"));
}
