import type { LLMProvider, ProviderName } from "./types.js";
import { AnthropicProvider } from "./anthropic.js";

let _provider: LLMProvider | null = null;

// pi provider id → perturbqa ProviderName
const PI_PROVIDER_MAP: Record<string, ProviderName> = {
  anthropic: "anthropic",
  openai: "openai",
  "openai-codex": "codex",
};

export function setProvider(p: LLMProvider): void {
  _provider = p;
}

export async function getProvider(): Promise<LLMProvider> {
  if (_provider) return _provider;

  // 1. Try pi's settings (shared with feynman)
  try {
    const { getCurrentModelSpec } = await import("../model/commands.js");
    const { getPerturbQASettingsPath } = await import("../config/paths.js");
    const spec = getCurrentModelSpec(getPerturbQASettingsPath());
    if (spec) {
      const [piProvider, ...rest] = spec.split("/");
      const modelId = rest.join("/");
      const perturbProvider = PI_PROVIDER_MAP[piProvider ?? ""] as ProviderName | undefined;
      if (perturbProvider && modelId) {
        _provider = await makeProvider(perturbProvider, modelId);
        return _provider;
      }
    }
  } catch {
    // fall through
  }

  // 2. Fall back to perturbqa's own settings
  const { loadSettings } = await import("../config/settings.js");
  const { hasAnthropicAuth, hasOpenAIAuth } = await import("../auth/setup.js");
  const settings = await loadSettings();
  let name = (process.env.PERTURBQA_PROVIDER ?? settings.provider) as ProviderName | undefined;
  if (!name) {
    name = (await hasAnthropicAuth()) ? "anthropic" : (await hasOpenAIAuth()) ? "codex" : "anthropic";
  }
  const model = process.env.PERTURBQA_MODEL ?? settings.model;
  _provider = await makeProvider(name, model);
  return _provider;
}

export async function makeProvider(name: ProviderName, modelOverride?: string): Promise<LLMProvider> {
  if (name === "openai") {
    const { OpenAIProvider } = await import("./openai.js");
    return new OpenAIProvider(modelOverride ?? "gpt-4o", "chat");
  }
  if (name === "codex") {
    const { OpenAIProvider } = await import("./openai.js");
    return new OpenAIProvider(modelOverride ?? "codex-mini-latest", "responses");
  }
  // Default: anthropic
  const { CONFIG } = await import("../config.js");
  return new AnthropicProvider(modelOverride ?? CONFIG.model);
}

export type { LLMProvider, ProviderName };
