import type { LLMProvider, ProviderName } from "./types.js";
import { mkdtemp, readFile, rm } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";
import { runCodexCli as runCodexCliCommand } from "../auth/codex-cli.js";

export class OpenAIProvider implements LLMProvider {
  readonly modelLabel: string;
  private model: string;
  private mode: "chat" | "responses";

  constructor(model: string, mode: "chat" | "responses" = "chat") {
    this.model = model;
    this.mode = mode;
    this.modelLabel = mode === "responses" ? `OpenAI Codex / ${model}` : `OpenAI / ${model}`;
  }

  async chat(system: string, user: string, maxTokens: number): Promise<string> {
    const { getOpenAIAuthCredential } = await import("../auth/openai-codex.js");
    const credential = await getOpenAIAuthCredential();

    if (credential.kind === "codex-chatgpt") {
      if (this.mode !== "responses") {
        throw new Error(
          "Codex ChatGPT login is only supported with PERTURBQA_PROVIDER=codex. " +
            "Set OPENAI_API_KEY to use the standard OpenAI provider."
        );
      }
      return runCodexCli(system, user, this.model, maxTokens);
    }

    const { default: OpenAI } = await import("openai");
    const client = new OpenAI({ apiKey: credential.value });

    if (this.mode === "responses") {
      // OpenAI Codex Agent — Responses API (2025)
      const response = await client.responses.create({
        model: this.model,
        instructions: system,
        input: user,
        max_output_tokens: maxTokens,
      });
      const output = response.output.find((o: { type: string }) => o.type === "message");
      if (!output || output.type !== "message") return "";
      const content = (output as { type: "message"; content: Array<{ type: string; text: string }> }).content;
      return content.find((c) => c.type === "output_text")?.text ?? "";
    } else {
      // Standard Chat Completions API
      const response = await client.chat.completions.create({
        model: this.model,
        max_tokens: maxTokens,
        messages: [
          { role: "system", content: system },
          { role: "user", content: user },
        ],
      });
      return response.choices[0]?.message?.content ?? "";
    }
  }
}

async function runCodexCli(system: string, user: string, model: string, maxTokens: number): Promise<string> {
  const tempDir = await mkdtemp(join(tmpdir(), "perturbqa-codex-"));
  const outputPath = join(tempDir, "answer.txt");
  const prompt =
    `${system}\n\n` +
    "Return only the final answer text. Do not run shell commands, inspect files, or modify the workspace.\n" +
    `Keep the answer within about ${maxTokens} tokens.\n\n` +
    `User question:\n${user}`;

  const args = [
    "exec",
    "--ephemeral",
    "--skip-git-repo-check",
    "--sandbox",
    "read-only",
    "--output-last-message",
    outputPath,
  ];

  if (model && model !== "codex-mini-latest") {
    args.push("--model", model);
  }

  args.push("-");

  try {
    await new Promise<void>((resolve, reject) => {
      runCodexCliCommand(args, { stdin: prompt }).then(() => resolve()).catch((err) => reject(err));
    });

    return (await readFile(outputPath, "utf-8")).trim();
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
}

export function makeOpenAIProvider(name: ProviderName): OpenAIProvider {
  if (name === "codex") {
    return new OpenAIProvider("codex-mini-latest", "responses");
  }
  return new OpenAIProvider("gpt-4o", "chat");
}
