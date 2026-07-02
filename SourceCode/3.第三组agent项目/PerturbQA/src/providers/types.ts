export interface LLMProvider {
  chat(system: string, user: string, maxTokens: number): Promise<string>;
  readonly modelLabel: string;
}

export type ProviderName = "anthropic" | "openai" | "codex";
