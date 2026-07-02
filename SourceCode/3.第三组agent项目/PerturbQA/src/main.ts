import "dotenv/config";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { launchPiChat } from "./pi/launch.js";
import {
  ensurePerturbQADirs,
  getPerturbQAAuthDir,
  getPerturbQAHome,
} from "./config/paths.js";
import { printAsciiHeader } from "./cli/ui.js";
import { isInteractiveTerminal } from "./cli/setup/prompts.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const APP_ROOT = resolve(__dirname, "..");

async function main(): Promise<void> {
  ensurePerturbQADirs();

  // Show banner before pi clears the screen
  if (isInteractiveTerminal() && !process.argv.includes("--mode")) {
    printAsciiHeader([
      "Gene Perturbation Knowledge Q&A",
      "Agentic RAG · Multi-Agent · Domain MCP · 51 papers",
    ]);
  }

  // Auth setup — uses ~/.perturbqa/agent/ by default.
  // On first run offers to import feynman credentials or set up fresh.
  const { ensureModelAuth } = await import("./auth/setup.js");
  await ensureModelAuth();

  const agentDir = getPerturbQAAuthDir();
  const sessionDir = resolve(getPerturbQAHome(), "sessions");

  await launchPiChat({
    appRoot: APP_ROOT,
    workingDir: process.cwd(),
    sessionDir,
    agentDir,
  });
}

main().catch((err) => {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes("User force closed")) process.exit(0);
  process.stderr.write(`\nError: ${message}\n`);
  process.exit(1);
});
