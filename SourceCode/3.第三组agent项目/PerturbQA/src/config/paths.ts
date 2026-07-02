import { mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";

// PerturbQA uses its own credential directory: ~/.perturbqa/agent/
// Set PERTURBQA_AUTH_DIR env var to override.

export function getPerturbQAHome(): string {
  return resolve(homedir(), ".perturbqa");
}

export function getPerturbQAAuthDir(): string {
  const override = process.env.PERTURBQA_AUTH_DIR;
  return override ? resolve(override) : resolve(getPerturbQAHome(), "agent");
}

export function getPerturbQAAuthPath(): string {
  return resolve(getPerturbQAAuthDir(), "auth.json");
}

export function getPerturbQASettingsPath(): string {
  return resolve(getPerturbQAAuthDir(), "settings.json");
}

export function ensurePerturbQADirs(): void {
  mkdirSync(getPerturbQAAuthDir(), { recursive: true });
  mkdirSync(resolve(getPerturbQAHome(), "sessions"), { recursive: true });
}
