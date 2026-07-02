import { CONFIG } from "../config.js";

// BGE models need a specific prefix on query strings for retrieval.
// Passage/document embeddings use no prefix.
const BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: ";

function isBgeModel(model: string): boolean {
  return model.toLowerCase().includes("bge");
}

let pipelineInstance: unknown = null;

async function getPipeline() {
  if (!pipelineInstance) {
    const { pipeline } = await import("@xenova/transformers");
    pipelineInstance = await pipeline("feature-extraction", CONFIG.embeddingModel, {
      quantized: true,
    });
  }
  return pipelineInstance as (text: string, opts: Record<string, unknown>) => Promise<{ data: Float32Array }>;
}

/** Embed a passage/document (no prefix). */
export async function getEmbedding(text: string): Promise<number[]> {
  const pipe = await getPipeline();
  const output = await pipe(text, { pooling: "mean", normalize: true });
  return Array.from(output.data) as number[];
}

/** Embed a search query (adds BGE retrieval prefix when applicable). */
export async function getQueryEmbedding(text: string): Promise<number[]> {
  const queryText = isBgeModel(CONFIG.embeddingModel)
    ? BGE_QUERY_PREFIX + text
    : text;
  return getEmbedding(queryText);
}
