import { readdir, readFile } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import { CONFIG } from "../config.js";
import { VectorStore, type VectorDocument } from "./vector-store.js";
import { getEmbedding } from "./embedder.js";

interface KeywordsJson {
  topic: string;
  keywords: string[];
  title?: string;
}

interface SourceJson {
  type: string;
  doi?: string;
  url?: string;
  title?: string;
  authors?: string[];
  year?: number;
}

async function readJson<T>(path: string): Promise<T | null> {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(await readFile(path, "utf-8")) as T;
  } catch {
    return null;
  }
}

async function indexKnowledgeSet(
  store: VectorStore,
  setName: string,
  setPath: string
): Promise<number> {
  const keywords = await readJson<KeywordsJson>(join(setPath, "keywords.json"));
  const source = await readJson<SourceJson>(join(setPath, "source.json"));

  const contentDir = join(setPath, "content");
  if (!existsSync(contentDir)) return 0;

  const files = await readdir(contentDir);
  let indexed = 0;

  for (const file of files) {
    if (!file.endsWith(".md") && !file.endsWith(".txt")) continue;
    const filePath = join(contentDir, file);
    const rawText = await readFile(filePath, "utf-8");

    const chunks = chunkText(rawText, 800, 100);

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const id = `${setName}::${file}::${i}`;
      const textForEmbedding = [
        keywords?.title ?? setName,
        keywords?.keywords?.join(", ") ?? "",
        chunk,
      ]
        .filter(Boolean)
        .join("\n");

      const embedding = await getEmbedding(textForEmbedding);

      const doc: VectorDocument = {
        id,
        text: chunk,
        embedding,
        metadata: {
          knowledgeSet: setName,
          sourceFile: file,
          keywords: keywords?.keywords ?? [],
          topic: keywords?.topic ?? "gene-perturbation",
          title: keywords?.title ?? source?.title ?? setName,
        },
      };
      store.add(doc);
      indexed++;
    }
  }
  return indexed;
}

function chunkText(text: string, chunkSize: number, overlap: number): string[] {
  const words = text.split(/\s+/);
  const chunks: string[] = [];
  let start = 0;
  while (start < words.length) {
    const end = Math.min(start + chunkSize, words.length);
    chunks.push(words.slice(start, end).join(" "));
    if (end === words.length) break;
    start += chunkSize - overlap;
  }
  return chunks.filter((c) => c.trim().length > 20);
}

export async function buildIndex(): Promise<void> {
  console.log("Building knowledge base index...");

  const store = new VectorStore(CONFIG.vectorStorePath);
  store.clear();

  if (!existsSync(CONFIG.knowledgeBasePath)) {
    console.error(`Knowledge base not found at: ${CONFIG.knowledgeBasePath}`);
    process.exit(1);
  }

  const sets = await readdir(CONFIG.knowledgeBasePath);
  let total = 0;

  for (const setName of sets) {
    const setPath = join(CONFIG.knowledgeBasePath, setName);
    const count = await indexKnowledgeSet(store, setName, setPath);
    if (count > 0) {
      console.log(`  ✓ ${setName}: ${count} chunks`);
      total += count;
    }
  }

  await store.save();
  console.log(`\nIndex built: ${total} chunks from ${sets.length} knowledge sets.`);
  console.log(`Saved to: ${CONFIG.vectorStorePath}`);
}

// Allow running directly
if (import.meta.url === new URL(import.meta.url).href) {
  buildIndex().catch(console.error);
}
