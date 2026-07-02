import * as readline from "readline/promises";
import { stdin as input, stdout as output } from "process";
import { existsSync } from "fs";
import { CONFIG } from "../config.js";
import {
  C,
  printBanner,
  printHelp,
  printSection,
  printInfo,
  createSpinner,
} from "./ui.js";
import { promptSelect, SetupCancelledError } from "./setup/prompts.js";
import { authenticateModelProvider, setDefaultModelSpec } from "../model/commands.js";
import { getAvailableModelRecords } from "../model/catalog.js";
import { getPerturbQAAuthPath, getPerturbQASettingsPath } from "../config/paths.js";
import { updateSettings } from "../config/settings.js";
import { getPiModelLabel, invalidatePiCache } from "../providers/pi-bridge.js";

export async function runRepl(): Promise<void> {
  printBanner();

  // ── Bootstrap ──────────────────────────────────────────────────────────────
  const { ensureModelAuth } = await import("../auth/setup.js");
  await ensureModelAuth();

  if (!existsSync(CONFIG.vectorStorePath)) {
    console.log(C.warn("Knowledge base not indexed. Run: npm run index\n"));
  }

  const { VectorStore } = await import("../rag/vector-store.js");
  const { QAOrchestrator } = await import("../agents/orchestrator.js");

  const store = new VectorStore(CONFIG.vectorStorePath);
  await store.load();
  console.log(C.dim(`Loaded ${store.count} chunks from knowledge base.\n`));

  console.log(C.dim(`Model: ${getPiModelLabel()}`));
  console.log(C.dim(`Type \\help for commands, \\exit to quit.\n`));

  const orchestrator = new QAOrchestrator(store);

  // ── REPL loop ──────────────────────────────────────────────────────────────
  const rl = readline.createInterface({ input, output, terminal: true });
  const prompt = () => `${C.prompt}\x1b[38;2;133;146;137m › \x1b[0m`;

  process.on("SIGINT", () => {
    console.log(C.dim("\n\nBye!"));
    rl.close();
    process.exit(0);
  });

  while (true) {
    let line: string;
    try {
      line = await rl.question(prompt());
    } catch {
      break;
    }

    line = line.trim();
    if (!line) continue;

    // ── Command dispatch ─────────────────────────────────────────────────────
    if (line.startsWith("\\")) {
      const [cmd, ...args] = line.slice(1).split(/\s+/);
      const rest = args.join(" ");

      switch (cmd.toLowerCase()) {
        case "exit":
        case "quit":
          console.log(C.dim("\nBye!"));
          rl.close();
          process.exit(0);

        case "help":
          printHelp();
          break;

        case "model":
          await handleModelSwitch();
          break;

        case "bench":
        case "benchmark": {
          const rawIds = rest
            ? rest.split(/\s+/).filter((id) => /^gp-\d+$/i.test(id))
            : [];
          const { runBenchmark } = await import("../evaluation/runner.js");
          await runBenchmark(rawIds.length > 0 ? rawIds : undefined);
          break;
        }

        case "paper": {
          const { paperCommand } = await import("./commands/paper.js");
          await paperCommand(store);
          break;
        }

        default:
          console.log(C.warn(`Unknown command: \\${cmd}  (type \\help)\n`));
      }
      continue;
    }

    // ── Free-text → Q&A pipeline ─────────────────────────────────────────────
    await runQA(orchestrator, line);
  }

  rl.close();
}

async function handleModelSwitch(): Promise<void> {
  const authPath = getPerturbQAAuthPath();
  const settingsPath = getPerturbQASettingsPath();

  try {
    const available = getAvailableModelRecords(authPath);

    if (available.length === 0) {
      printSection("No authenticated models");
      printInfo("Run `feynman model login` to set up a provider, then restart PerturbQA.");
      const { promptConfirm } = await import("./setup/prompts.js");
      const doLogin = await promptConfirm("Open feynman model setup now?", true);
      if (doLogin) await authenticateModelProvider(authPath, settingsPath);
      return;
    }

    type Opt = { spec: string; piProvider: string; modelId: string };

    // All providers — pi-ai handles the rest natively
    const choices: Array<{ value: Opt; label: string; hint: string }> = available.map(
      (m) => ({
        value: { spec: `${m.provider}/${m.id}`, piProvider: m.provider, modelId: m.id },
        label: m.name ?? m.id,
        hint: m.provider,
      }),
    );

    // Append login option
    choices.push({
      value: { spec: "__add__", piProvider: "", modelId: "" },
      label: "Login / add a provider…",
      hint: "OAuth or API key",
    });

    const selected = await promptSelect<Opt>("Select model:", choices);

    if (selected.spec === "__add__") {
      await authenticateModelProvider(authPath, settingsPath);
      invalidatePiCache();
      return;
    }

    // Persist to pi settings (shared with feynman)
    setDefaultModelSpec(settingsPath, authPath, selected.spec);

    // Also persist to perturbqa legacy settings for env-var fallback
    const perturbProvider =
      selected.piProvider === "openai-codex"
        ? "codex"
        : (selected.piProvider as "anthropic" | "openai" | "codex");
    await updateSettings({ provider: perturbProvider, model: selected.modelId });

    // Invalidate pi-bridge cache so next call uses the new model
    invalidatePiCache();

    console.log(C.success(`\nModel set to: ${getPiModelLabel()}\n`));
  } catch (error) {
    if (error instanceof SetupCancelledError) {
      console.log(C.dim("  Model switch cancelled.\n"));
    } else {
      throw error;
    }
  }
}

async function runQA(
  orchestrator: InstanceType<
    typeof import("../agents/orchestrator.js").QAOrchestrator
  >,
  question: string,
): Promise<void> {
  const spin = createSpinner("Running pipeline…");
  let result;
  try {
    result = await orchestrator.run(question, false);
  } catch (err) {
    spin.stop();
    console.log(C.error(`Error: ${err instanceof Error ? err.message : err}\n`));
    return;
  }
  spin.stop();

  console.log();
  console.log(C.sep());
  console.log(C.bold("Answer"));
  console.log(C.sep());
  console.log(result.finalAnswer);
  console.log();
  console.log(
    C.dim(`Score: ${result.validation.score}/100`) +
      "  " +
      C.dim(
        `Sources: ${result.retrieverOutput.sourceList.join(", ") || "none"}`,
      ),
  );
  console.log();
}
