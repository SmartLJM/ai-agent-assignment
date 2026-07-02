import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { constants } from "node:os";
import {
  buildPiArgs,
  buildPiEnv,
  type PiRuntimeOptions,
  resolvePiPaths,
  toNodeImportSpecifier,
} from "./runtime.js";

export function exitCodeFromSignal(signal: NodeJS.Signals): number {
  const signalNumber = constants.signals[signal];
  return typeof signalNumber === "number" ? 128 + signalNumber : 1;
}

export async function launchPiChat(options: PiRuntimeOptions): Promise<void> {
  const paths = resolvePiPaths(options.appRoot);

  if (!existsSync(paths.piCliPath)) throw new Error(`Pi CLI not found: ${paths.piCliPath}`);
  if (!existsSync(paths.piMainPath)) throw new Error(`Pi main not found: ${paths.piMainPath}`);

  const useBuiltWrapper = existsSync(paths.piCliWrapperPath);
  const useDevWrapper =
    !useBuiltWrapper &&
    existsSync(paths.piCliWrapperSourcePath) &&
    existsSync(paths.tsxLoaderPath);
  if (!useBuiltWrapper && !useDevWrapper) {
    throw new Error(`Pi CLI wrapper not found: ${paths.piCliWrapperPath}`);
  }

  const useBuiltPolyfill = existsSync(paths.promisePolyfillPath);
  const useDevPolyfill =
    !useBuiltPolyfill &&
    existsSync(paths.promisePolyfillSourcePath) &&
    existsSync(paths.tsxLoaderPath);
  if (!useBuiltPolyfill && !useDevPolyfill) {
    throw new Error(`Promise polyfill not found: ${paths.promisePolyfillPath}`);
  }

  // Clear screen before handing off to pi TUI
  if (process.stdout.isTTY && options.mode !== "rpc") {
    process.stdout.write("\x1b[2J\x1b[3J\x1b[H");
  }

  const wrapperPath = useBuiltWrapper ? paths.piCliWrapperPath : paths.piCliWrapperSourcePath;
  const importArgs = useDevPolyfill
    ? [
        "--import",
        toNodeImportSpecifier(paths.tsxLoaderPath),
        "--import",
        toNodeImportSpecifier(paths.promisePolyfillSourcePath),
      ]
    : ["--import", toNodeImportSpecifier(paths.promisePolyfillPath)];

  const child = spawn(
    process.execPath,
    [...importArgs, wrapperPath, paths.piMainPath, ...buildPiArgs(options, paths)],
    {
      cwd: options.workingDir,
      stdio: "inherit",
      env: buildPiEnv(options, paths),
    },
  );

  await new Promise<void>((resolve, reject) => {
    child.on("error", reject);
    child.on("exit", (code, signal) => {
      if (signal) {
        process.exitCode = exitCodeFromSignal(signal);
        resolve();
        return;
      }
      process.exitCode = code ?? 0;
      resolve();
    });
  });
}
