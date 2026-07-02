import type { LLMProvider } from "./types.js";

export class AnthropicProvider implements LLMProvider {
  readonly modelLabel: string;
  private model: string;

  constructor(model: string) {
    this.model = model;
    this.modelLabel = `Anthropic / ${model}`;
  }

  async chat(system: string, user: string, maxTokens: number): Promise<string> {
    const { createClient } = await import("../config.js");
    const client = await createClient();
    for (let attempt = 0; attempt <= 3; attempt++) {
      try {
        const response = await client.messages.create({
          model: this.model,
          max_tokens: maxTokens,
          system,
          messages: [{ role: "user", content: user }],
        });
        return response.content[0].type === "text" ? response.content[0].text : "";
      } catch (err: unknown) {
        const status = (err as { status?: number }).status;
        if ((status === 429 || status === 529) && attempt < 3) {
          await new Promise((r) => setTimeout(r, Math.pow(2, attempt) * 5000));
          continue;
        }
        throw err;
      }
    }
    throw new Error("Unreachable");
  }
}
