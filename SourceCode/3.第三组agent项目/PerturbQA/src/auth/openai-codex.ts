import { existsSync } from "fs";
import { readFile } from "fs/promises";
import { homedir } from "os";
import { join } from "path";

interface CodexAuthFile {
  OPENAI_API_KEY?: unknown;
  tokens?: {
    access_token?: unknown;
  };
  auth_mode?: unknown;
  last_refresh?: unknown;
}

export const CODEX_AUTH_PATH = join(homedir(), ".codex", "auth.json");

export interface OpenAIAuthStatus {
  source: "env" | "codex-api-key" | "codex-chatgpt";
  secretPreview: string;
  authMode?: string;
  lastRefresh?: string;
}

export type OpenAIAuthCredential =
  | { kind: "api-key"; value: string; source: "env" | "codex-api-key" }
  | { kind: "codex-chatgpt"; value: string };

function previewSecret(value: string): string {
  if (value.length <= 12) return "********";
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

async function loadCodexAuth(): Promise<CodexAuthFile | null> {
  if (!existsSync(CODEX_AUTH_PATH)) return null;
  const raw = await readFile(CODEX_AUTH_PATH, "utf-8");
  return JSON.parse(raw) as CodexAuthFile;
}

export async function getOpenAIAuthCredential(): Promise<OpenAIAuthCredential> {
  if (process.env.OPENAI_API_KEY) {
    return { kind: "api-key", value: process.env.OPENAI_API_KEY, source: "env" };
  }

  const codexAuth = await loadCodexAuth();
  if (typeof codexAuth?.OPENAI_API_KEY === "string" && codexAuth.OPENAI_API_KEY.trim()) {
    return { kind: "api-key", value: codexAuth.OPENAI_API_KEY, source: "codex-api-key" };
  }

  if (typeof codexAuth?.tokens?.access_token === "string" && codexAuth.tokens.access_token.trim()) {
    return { kind: "codex-chatgpt", value: codexAuth.tokens.access_token };
  }

  throw new Error(
    "OpenAI API key not found. Set OPENAI_API_KEY in .env, or run:\n\n" +
      "  codex login\n\n" +
      `Then retry. PerturbQA will read Codex credentials from ${CODEX_AUTH_PATH}.`
  );
}

export async function getOpenAIApiKey(): Promise<string> {
  const credential = await getOpenAIAuthCredential();
  if (credential.kind !== "api-key") {
    throw new Error(
      "Codex ChatGPT login was found, but this provider needs an OpenAI platform API key.\n" +
        "Use PERTURBQA_PROVIDER=codex to run through Codex CLI, or set OPENAI_API_KEY in .env."
    );
  }
  return credential.value;
}

export async function getOpenAIAuthStatus(): Promise<OpenAIAuthStatus | null> {
  if (process.env.OPENAI_API_KEY) {
    return {
      source: "env",
      secretPreview: previewSecret(process.env.OPENAI_API_KEY),
    };
  }

  const codexAuth = await loadCodexAuth();
  if (typeof codexAuth?.OPENAI_API_KEY === "string" && codexAuth.OPENAI_API_KEY.trim()) {
    return {
      source: "codex-api-key",
      secretPreview: previewSecret(codexAuth.OPENAI_API_KEY),
      authMode: typeof codexAuth.auth_mode === "string" ? codexAuth.auth_mode : undefined,
      lastRefresh: typeof codexAuth.last_refresh === "string" ? codexAuth.last_refresh : undefined,
    };
  }

  if (typeof codexAuth?.tokens?.access_token === "string" && codexAuth.tokens.access_token.trim()) {
    return {
      source: "codex-chatgpt",
      secretPreview: previewSecret(codexAuth.tokens.access_token),
      authMode: typeof codexAuth.auth_mode === "string" ? codexAuth.auth_mode : undefined,
      lastRefresh: typeof codexAuth.last_refresh === "string" ? codexAuth.last_refresh : undefined,
    };
  }

  return null;
}
