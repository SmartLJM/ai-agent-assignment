import { readFile, writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";

export interface VectorDocument {
  id: string;
  text: string;
  embedding: number[];
  metadata: {
    knowledgeSet: string;
    sourceFile: string;
    keywords: string[];
    topic: string;
    title?: string;
  };
}

export interface SearchResult {
  document: VectorDocument;
  score: number;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

/** Extract unigrams and bigrams from a text for BM25-style matching. */
function extractNgrams(text: string): string[] {
  const tokens = text
    .toLowerCase()
    .split(/[\s\-_/]+/)
    .map((t) => t.replace(/[^a-z0-9]/g, ""))
    .filter((t) => t.length > 1);
  const unigrams = tokens;
  const bigrams = tokens.slice(0, -1).map((t, i) => `${t} ${tokens[i + 1]}`);
  return [...unigrams, ...bigrams];
}

export class VectorStore {
  private documents: VectorDocument[] = [];
  private storePath: string;

  constructor(storePath: string) {
    this.storePath = storePath;
  }

  async load(): Promise<void> {
    const indexPath = join(this.storePath, "index.json");
    if (!existsSync(indexPath)) {
      this.documents = [];
      return;
    }
    const raw = await readFile(indexPath, "utf-8");
    this.documents = JSON.parse(raw);
  }

  async save(): Promise<void> {
    await mkdir(this.storePath, { recursive: true });
    const indexPath = join(this.storePath, "index.json");
    await writeFile(indexPath, JSON.stringify(this.documents, null, 2), "utf-8");
  }

  add(doc: VectorDocument): void {
    const existing = this.documents.findIndex((d) => d.id === doc.id);
    if (existing >= 0) {
      this.documents[existing] = doc;
    } else {
      this.documents.push(doc);
    }
  }

  search(queryEmbedding: number[], topK: number = 5): SearchResult[] {
    return this.documents
      .map((doc) => ({ document: doc, score: cosineSimilarity(queryEmbedding, doc.embedding) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  keywordSearch(queryTerms: string[], topK: number = 5): SearchResult[] {
    // Build query ngrams (unigrams + bigrams)
    const queryNgrams = new Set(extractNgrams(queryTerms.join(" ")));

    const scores = this.documents.map((doc) => {
      const docText = (
        doc.text + " " +
        doc.metadata.keywords.join(" ") + " " +
        (doc.metadata.title ?? "") + " " +
        doc.metadata.knowledgeSet
      ).toLowerCase();
      const titleSlug = (doc.metadata.title ?? doc.metadata.knowledgeSet ?? "").toLowerCase();
      const docNgrams = new Set(extractNgrams(docText));

      let hits = 0;
      let phraseBonus = 0;
      let titleBonus = 0;

      for (const ng of queryNgrams) {
        if (docNgrams.has(ng)) {
          // Bigram match (phrase) is worth more than unigram
          const weight = ng.includes(" ") ? 2 : 1;
          hits += weight;
          if (ng.includes(" ") && titleSlug.includes(ng)) phraseBonus += 3;
        }
        if (ng.length > 3 && titleSlug.includes(ng)) titleBonus += 2;
      }

      const total = queryNgrams.size > 0 ? (hits + phraseBonus + titleBonus) / queryNgrams.size : 0;
      return { document: doc, score: Math.min(1, total) };
    });

    return scores
      .filter((r) => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  get count(): number {
    return this.documents.length;
  }

  clear(): void {
    this.documents = [];
  }
}
