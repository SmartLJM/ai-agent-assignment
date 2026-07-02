import { config } from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

config(); // load .env if present

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, "..");

export const CONFIG = {
  // API key can be set via .env or resolved from OAuth at runtime (see getApiKey())
  anthropicApiKey: process.env.ANTHROPIC_API_KEY ?? "",
  openaiApiKey: process.env.OPENAI_API_KEY ?? "",
  ncbiApiKey: process.env.NCBI_API_KEY ?? "",
  model: (process.env.PERTURBQA_MODEL ?? "claude-sonnet-4-6") as "claude-sonnet-4-6" | "claude-haiku-4-5-20251001",
  provider: (process.env.PERTURBQA_PROVIDER ?? "anthropic") as "anthropic" | "openai" | "codex",
  embeddingModel: "Xenova/all-MiniLM-L6-v2" as const,
  knowledgeBasePath: join(ROOT, "knowledge_base"),
  vectorStorePath: join(ROOT, ".vector-store"),
  benchmarkPath: join(ROOT, "benchmark", "questions.json"),
  maxRetrievalRounds: 3,
  topK: 5,
};

/**
 * Resolve a valid Anthropic API key (or OAuth access token, same format).
 *
 * Priority:
 *   1. ANTHROPIC_API_KEY env var
 *   2. Claude Code OAuth credentials (~/.claude/.credentials.json)
 *   3. PerturbQA own OAuth credentials (~/.config/perturbqa/credentials.json)
 *   4. Prompt user to run `npm run dev login`
 */
export async function getApiKey(): Promise<string> {
  // 1. Env var / .env file
  if (CONFIG.anthropicApiKey) return CONFIG.anthropicApiKey;

  // 2. Try pi/feynman's shared auth (~/.feynman/agent/auth.json)
  try {
    const { createModelRegistry } = await import("./model/registry.js");
    const { getPerturbQAAuthPath } = await import("./config/paths.js");
    const reg = createModelRegistry(getPerturbQAAuthPath());
    const key = await reg.getApiKeyForProvider("anthropic");
    if (key) return key;
  } catch {
    // no pi auth, continue
  }

  // 3. Try stored credentials (Claude Code / perturbqa own OAuth)
  const { loadCredentials, saveCredentials, isExpired } = await import("./auth/credentials.js");
  let creds = await loadCredentials();

  if (creds) {
    if (!isExpired(creds)) {
      return creds.accessToken;
    }
    // Expired — try to refresh
    try {
      const { refreshToken } = await import("./auth/oauth.js");
      console.log("Refreshing expired OAuth token...");
      creds = await refreshToken(creds.refreshToken);
      await saveCredentials(creds);
      return creds.accessToken;
    } catch {
      // refresh failed, fall through to login
    }
  }

  // 4. No credentials — tell user to login
  throw new AuthRequiredError();
}

/**
 * Create an Anthropic client using the right auth header for the token type.
 * - API keys (sk-ant-api03-...)  → x-api-key header
 * - OAuth tokens (sk-ant-oat01-...) → Authorization: Bearer header
 */
export async function createClient() {
  const { default: Anthropic } = await import("@anthropic-ai/sdk");
  const token = await getApiKey();
  // OAuth access tokens use Bearer auth; classic API keys use x-api-key
  if (token.startsWith("sk-ant-oat")) {
    return new Anthropic({ authToken: token });
  }
  return new Anthropic({ apiKey: token });
}

export class AuthRequiredError extends Error {
  constructor() {
    super(
      "Not authenticated. Run the following command to log in:\n\n" +
        "  npm run dev -- login\n\n" +
        "This opens claude.ai in your browser for one-click authorization (Claude Pro/Max account required)."
    );
    this.name = "AuthRequiredError";
  }
}
