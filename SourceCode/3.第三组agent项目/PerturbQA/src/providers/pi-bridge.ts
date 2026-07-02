/**
 * Pi-ai bridge — all LLM calls go through pi-ai's completeSimple().
 * This gives us automatic OAuth refresh, rate-limit retry, and access to
 * every provider feynman supports without any custom SDK code.
 */

import { AuthStorage, ModelRegistry } from "@earendil-works/pi-coding-agent";
import { completeSimple } from "@earendil-works/pi-ai";
import type { Model } from "@earendil-works/pi-ai";
import { getPerturbQAAuthPath, getPerturbQASettingsPath } from "../config/paths.js";
import { getCurrentModelSpec } from "../model/commands.js";
import { getModelsJsonPath } from "../model/registry.js";

type CachedState = {
  reg: ModelRegistry;
  model: Model<string>;
  spec: string;
};

let _cache: CachedState | null = null;

function buildRegistry(): ModelRegistry {
  const authPath = getPerturbQAAuthPath();
  return ModelRegistry.create(
    AuthStorage.create(authPath),
    getModelsJsonPath(authPath),
  );
}

function resolveModel(reg: ModelRegistry): { model: Model<string>; spec: string } {
  const settingsPath = getPerturbQASettingsPath();
  const spec = getCurrentModelSpec(settingsPath);
  const available = reg.getAvailable();

  if (spec) {
    const [provider, ...rest] = spec.split("/");
    const modelId = rest.join("/");
    const found = available.find(
      (m) => m.provider === provider && m.id === modelId,
    );
    if (found) return { model: found as Model<string>, spec };
  }

  // Fall back to first available model
  const first = available[0];
  if (!first) {
    throw new Error(
      "No authenticated models available. " +
        "Run `feynman model login` or set ANTHROPIC_API_KEY.",
    );
  }
  return { model: first as Model<string>, spec: `${first.provider}/${first.id}` };
}

/** Invalidate cache after a model switch so the next call picks up the new model. */
export function invalidatePiCache(): void {
  _cache = null;
}

export function getPiModelLabel(): string {
  try {
    const reg = buildRegistry();
    const { model } = resolveModel(reg);
    return `${model.name ?? model.id}  (${model.provider})`;
  } catch {
    return "unknown model";
  }
}

export async function callPiModel(
  systemPrompt: string,
  userMessage: string,
  maxTokens = 1024,
): Promise<string> {
  // Rebuild cache if missing
  if (!_cache) {
    const reg = buildRegistry();
    const { model, spec } = resolveModel(reg);
    _cache = { reg, model, spec };
  }

  const { reg, model } = _cache;
  const apiKey = (await reg.getApiKeyForProvider(model.provider)) ?? undefined;

  const msg = await completeSimple(
    model,
    {
      systemPrompt,
      messages: [{ role: "user", content: userMessage, timestamp: Date.now() }],
    },
    { apiKey, maxTokens },
  );

  const text = msg.content.find((c) => c.type === "text");
  if (!text || text.type !== "text") return "";
  return text.text;
}
