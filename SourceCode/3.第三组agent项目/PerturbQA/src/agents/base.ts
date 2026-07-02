import { callPiModel } from "../providers/pi-bridge.js";

export abstract class BaseAgent {
  abstract readonly name: string;
  abstract readonly systemPrompt: string;

  protected async call(userMessage: string, maxTokens = 1024): Promise<string> {
    return callPiModel(this.systemPrompt, userMessage, maxTokens);
  }
}
