import { readFile, writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import { homedir } from "os";

export interface StoredCredentials {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

// Where PerturbQA stores its own credentials
const PERTURBQA_CREDS = join(homedir(), ".config", "perturbqa", "credentials.json");

// Where Claude Code stores its credentials (share if available)
const CLAUDE_CODE_CREDS = join(homedir(), ".claude", ".credentials.json");

export async function loadCredentials(): Promise<StoredCredentials | null> {
  // 1. Try Claude Code credentials first (user is already logged in via Claude Code)
  if (existsSync(CLAUDE_CODE_CREDS)) {
    try {
      const raw = await readFile(CLAUDE_CODE_CREDS, "utf-8");
      const parsed = JSON.parse(raw);
      const oauth = parsed?.claudeAiOauth;
      if (oauth?.accessToken && oauth?.refreshToken && oauth?.expiresAt) {
        return {
          accessToken: oauth.accessToken,
          refreshToken: oauth.refreshToken,
          expiresAt: oauth.expiresAt,
        };
      }
    } catch {
      // fall through
    }
  }

  // 2. Try PerturbQA's own stored credentials
  if (existsSync(PERTURBQA_CREDS)) {
    try {
      const raw = await readFile(PERTURBQA_CREDS, "utf-8");
      return JSON.parse(raw) as StoredCredentials;
    } catch {
      // fall through
    }
  }

  return null;
}

export async function saveCredentials(creds: StoredCredentials): Promise<void> {
  await mkdir(join(homedir(), ".config", "perturbqa"), { recursive: true });
  await writeFile(PERTURBQA_CREDS, JSON.stringify(creds, null, 2), "utf-8");
}

export async function clearCredentials(): Promise<void> {
  if (existsSync(PERTURBQA_CREDS)) {
    const { unlink } = await import("fs/promises");
    await unlink(PERTURBQA_CREDS);
  }
}

export function isExpired(creds: StoredCredentials): boolean {
  // Give 5-minute buffer before expiry
  return Date.now() >= creds.expiresAt - 5 * 60 * 1000;
}
