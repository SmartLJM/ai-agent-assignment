import { spawn } from "child_process";

export interface CodexRunResult {
  stdout: string;
  stderr: string;
}

function npxCommand(): string {
  return process.platform === "win32" ? "npx.cmd" : "npx";
}

function isNotFoundError(err: unknown): boolean {
  return err instanceof Error && "code" in err && err.code === "ENOENT";
}

function spawnAndWait(command: string, args: string[], inherit = false, stdin?: string): Promise<CodexRunResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: inherit ? "inherit" : ["pipe", "pipe", "pipe"] });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];

    if (!inherit) {
      child.stdout?.on("data", (chunk: Buffer) => stdout.push(chunk));
      child.stderr?.on("data", (chunk: Buffer) => stderr.push(chunk));
      child.stdin?.end(stdin ?? "");
    }

    child.on("error", (err) => reject(err));
    child.on("close", (code) => {
      const out = Buffer.concat(stdout).toString("utf-8");
      const err = Buffer.concat(stderr).toString("utf-8");
      if (code === 0) resolve({ stdout: out, stderr: err });
      else reject(new Error(`${command} ${args.join(" ")} exited with code ${code ?? "unknown"}${err ? `:\n${err}` : ""}`));
    });
  });
}

export async function runCodexCli(args: string[], options: { inherit?: boolean; stdin?: string } = {}): Promise<CodexRunResult> {
  const configured = process.env.CODEX_BIN?.trim();
  if (configured) {
    return spawnAndWait(configured, args, options.inherit, options.stdin);
  }

  try {
    return await spawnAndWait("codex", args, options.inherit, options.stdin);
  } catch (err) {
    if (!isNotFoundError(err)) throw err;
  }

  return spawnAndWait(npxCommand(), ["-y", "@openai/codex@latest", ...args], options.inherit, options.stdin);
}
