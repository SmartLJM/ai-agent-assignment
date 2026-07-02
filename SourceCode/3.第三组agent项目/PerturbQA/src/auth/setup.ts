import {
  isInteractiveTerminal,
  promptIntro,
  promptOutro,
  SetupCancelledError,
} from "../cli/setup/prompts.js";
import { printInfo, printSection, printError } from "../cli/ui.js";
import {
  getPerturbQAAuthPath,
  getPerturbQASettingsPath,
  ensurePerturbQADirs,
} from "../config/paths.js";
import { runModelSetup, getCurrentModelSpec } from "../model/commands.js";
import { getAvailableModelRecords } from "../model/catalog.js";

export async function hasAnthropicAuth(): Promise<boolean> {
  if (process.env.ANTHROPIC_API_KEY) return true;
  try {
    const { createModelRegistry } = await import("../model/registry.js");
    const reg = createModelRegistry(getPerturbQAAuthPath());
    return reg.getAvailable().some((m) => m.provider === "anthropic");
  } catch {
    return false;
  }
}

export async function hasOpenAIAuth(): Promise<boolean> {
  if (process.env.OPENAI_API_KEY) return true;
  try {
    const { createModelRegistry } = await import("../model/registry.js");
    const reg = createModelRegistry(getPerturbQAAuthPath());
    return reg.getAvailable().some(
      (m) => m.provider === "openai" || m.provider === "openai-codex",
    );
  } catch {
    const { getOpenAIAuthStatus } = await import("./openai-codex.js");
    return Boolean(await getOpenAIAuthStatus());
  }
}

export async function hasAnyModelAuth(): Promise<boolean> {
  return (await hasAnthropicAuth()) || (await hasOpenAIAuth());
}

export async function ensureModelAuth(): Promise<void> {
  ensurePerturbQADirs();

  const authPath = getPerturbQAAuthPath();
  const settingsPath = getPerturbQASettingsPath();

  // Already configured and valid?
  const currentSpec = getCurrentModelSpec(settingsPath);
  const available = getAvailableModelRecords(authPath);
  const currentValid = currentSpec
    ? available.some(
        (m: { provider: string; id: string }) =>
          `${m.provider}/${m.id}` === currentSpec,
      )
    : false;

  if (currentValid) return;
  if ((await hasAnyModelAuth()) && currentSpec) return;

  // Non-interactive: require env var
  if (!isInteractiveTerminal()) {
    if (await hasAnyModelAuth()) return;
    throw new Error(
      "PerturbQA needs a model login before starting.\n" +
        "Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or run npm run dev interactively.\n" +
        "Credentials are stored in ~/.perturbqa/agent/",
    );
  }

  // Interactive setup wizard (same as feynman's)
  try {
    await promptIntro("PerturbQA · Model Setup");
    printSection("Authentication");
    printInfo("Credentials will be stored in ~/.perturbqa/agent/");
    printInfo("Supports OAuth (Claude Pro/Max, ChatGPT Plus, Copilot…)");
    printInfo("and API keys (Anthropic, OpenAI, Google, Groq, Mistral, Ollama…)");

    await runModelSetup(settingsPath, authPath);

    await promptOutro("PerturbQA is ready");
  } catch (error) {
    if (error instanceof SetupCancelledError) {
      printError("Setup cancelled.");
      process.exit(0);
    }
    throw error;
  }
}
