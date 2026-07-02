import { existsSync, readFileSync } from "node:fs";

export function readJson(path: string): Record<string, unknown> {
  if (!existsSync(path)) {
    return {};
  }
  try {
    return JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
  } catch {
    return {};
  }
}
