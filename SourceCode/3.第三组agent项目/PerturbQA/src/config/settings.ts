import { existsSync } from "fs";
import { mkdir, readFile, writeFile } from "fs/promises";
import { homedir } from "os";
import { join } from "path";
import type { ProviderName } from "../providers/types.js";

export interface AppSettings {
  provider?: ProviderName;
  model?: string;
}

export const SETTINGS_DIR = join(homedir(), ".config", "perturbqa");
export const SETTINGS_PATH = join(SETTINGS_DIR, "settings.json");

export async function loadSettings(): Promise<AppSettings> {
  if (!existsSync(SETTINGS_PATH)) return {};
  try {
    const raw = await readFile(SETTINGS_PATH, "utf-8");
    return JSON.parse(raw) as AppSettings;
  } catch {
    return {};
  }
}

export async function saveSettings(settings: AppSettings): Promise<void> {
  await mkdir(SETTINGS_DIR, { recursive: true });
  await writeFile(SETTINGS_PATH, JSON.stringify(settings, null, 2), "utf-8");
}

export async function updateSettings(patch: AppSettings): Promise<AppSettings> {
  const next = { ...(await loadSettings()), ...patch };
  await saveSettings(next);
  return next;
}
