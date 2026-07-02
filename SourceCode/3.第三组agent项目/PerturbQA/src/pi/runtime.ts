import { existsSync, readFileSync } from "node:fs";
import { delimiter, dirname, isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";

export type PiRuntimeOptions = {
  appRoot: string;
  workingDir: string;
  sessionDir: string;
  agentDir: string;
  mode?: "text" | "json" | "rpc";
  explicitModelSpec?: string;
  oneShotPrompt?: string;
  initialPrompt?: string;
};

export function resolvePiPaths(appRoot: string) {
  return {
    piCliPath: resolve(appRoot, "node_modules", "@earendil-works", "pi-coding-agent", "dist", "cli.js"),
    piMainPath: resolve(appRoot, "node_modules", "@earendil-works", "pi-coding-agent", "dist", "main.js"),
    piCliWrapperPath: resolve(appRoot, "dist", "pi", "pi-cli-wrapper.js"),
    piCliWrapperSourcePath: resolve(appRoot, "src", "pi", "pi-cli-wrapper.ts"),
    promisePolyfillPath: resolve(appRoot, "dist", "system", "promise-polyfill.js"),
    promisePolyfillSourcePath: resolve(appRoot, "src", "system", "promise-polyfill.ts"),
    tsxLoaderPath: resolve(appRoot, "node_modules", "tsx", "dist", "loader.mjs"),
    extensionPath: resolve(appRoot, "src", "extensions", "perturbqa-tools.ts"),
    systemPromptPath: resolve(appRoot, "SYSTEM.md"),
    nodeModulesBinPath: resolve(appRoot, "node_modules", ".bin"),
  };
}

export type PiPaths = ReturnType<typeof resolvePiPaths>;

export function toNodeImportSpecifier(modulePath: string): string {
  return isAbsolute(modulePath) ? pathToFileURL(modulePath).href : modulePath;
}

export function buildPiArgs(
  options: PiRuntimeOptions,
  paths: PiPaths = resolvePiPaths(options.appRoot),
): string[] {
  const args = ["--session-dir", options.sessionDir];

  if (existsSync(paths.extensionPath)) {
    args.push("--extension", paths.extensionPath);
  }

  if (existsSync(paths.systemPromptPath)) {
    args.push("--system-prompt", readFileSync(paths.systemPromptPath, "utf8").trim());
  }

  if (options.mode) args.push("--mode", options.mode);
  if (options.explicitModelSpec) args.push("--model", options.explicitModelSpec);
  if (options.oneShotPrompt) args.push("-p", options.oneShotPrompt);
  else if (options.initialPrompt) args.push(options.initialPrompt);

  return args;
}

export function buildPiEnv(
  options: PiRuntimeOptions,
  paths: PiPaths = resolvePiPaths(options.appRoot),
): NodeJS.ProcessEnv {
  const currentPath = process.env.PATH ?? "";
  return {
    ...process.env,
    PATH: `${paths.nodeModulesBinPath}${delimiter}${currentPath}`,
    PI_CODING_AGENT_DIR: options.agentDir,
    PI_SKIP_VERSION_CHECK: "1",
    PI_HARDWARE_CURSOR: process.env.PI_HARDWARE_CURSOR ?? "1",
  };
}
