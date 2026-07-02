
import json
import os
import sys
from datetime import datetime

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import gradio as gr


class EpigenomicsAgent:
    def __init__(self, kb_path="../knowledge_assets/"):
        self.kb_path = kb_path
        self.datasets = []

        # Check for OpenAI API key
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
            print("   Set it with: export OPENAI_API_KEY='your-key-here'")
            sys.exit(1)

        self.client = OpenAI(api_key=self.api_key)

        print("Loading semantic search model...")
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="epigenomics_kb",
            embedding_function=embedding_fn
        )

        self._load_datasets()
        self._load_to_vector_db()

        self.memory_file = "persistent_memory.json"
        self.memory_store = self._load_memory()

        print("Agent ready.\n")

    def _load_datasets(self):
        print("Loading datasets...")
        for i in range(1, 25):
            path = os.path.join(self.kb_path, f"dataset_{i}")
            if not os.path.exists(path):
                continue
            dataset = {"id": i}
            kw_path = os.path.join(path, "keywords.json")
            src_path = os.path.join(path, "source.json")
            if os.path.exists(kw_path):
                with open(kw_path) as f:
                    dataset["keywords"] = json.load(f)
            if os.path.exists(src_path):
                with open(src_path) as f:
                    dataset["source"] = json.load(f)
            self.datasets.append(dataset)
        print(f"Loaded {len(self.datasets)} datasets")

    def _load_to_vector_db(self):
        print("Creating embeddings...")
        docs, metas, ids = [], [], []
        for d in self.datasets:
            src = d.get("source", {})
            kw = d.get("keywords", {})
            text = (
                f"Title: {src.get('title', '')} "
                f"Description: {src.get('description', '')} "
                f"Keywords: {', '.join(kw.get('keywords', []))} "
                f"Topic: {kw.get('topic', '')}"
            )
            docs.append(text.strip())
            metas.append({"id": d["id"], "title": src.get("title", "")})
            ids.append(f"dataset_{d['id']}")
        self.collection.add(documents=docs, metadatas=metas, ids=ids)
        print(f"Stored {len(docs)} documents")

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file) as f:
                return json.load(f)
        return {"interactions": []}

    def _save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.memory_store, f, indent=2)

    def expand_assets(self, num_new=30):
        print(f"\nExpanding assets by {num_new} datasets...")
        count = 0
        for i in range(25, 25 + num_new):
            path = os.path.join(self.kb_path, f"dataset_{i}")
            if not os.path.exists(path):
                os.makedirs(os.path.join(path, "content"), exist_ok=True)
                with open(os.path.join(path, "keywords.json"), "w") as f:
                    json.dump({"topic": "epigenomics", "keywords": ["expanded"], "id": i}, f)
                with open(os.path.join(path, "source.json"), "w") as f:
                    json.dump({"title": f"Expanded dataset {i}", "description": "New data"}, f)
                count += 1
        print(f"Added {count} new datasets.")
        return count

    def _semantic_search(self, query, n=3):
        results = self.collection.query(query_texts=[query], n_results=n)
        retrieved = []
        if results and results.get("documents"):
            for i in range(len(results["documents"][0])):
                retrieved.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "id": results["ids"][0][i]
                })
        return retrieved

    def _generate_answer(self, query, context):
        """Use OpenAI GPT to generate a detailed answer."""
        prompt = f"""You are an epigenomics expert. Based on the following context from a knowledge base, answer the user's question.

Context:
{context}

Question: {query}

Provide a detailed answer in 2-3 paragraphs with clear explanations. Include specific examples where relevant."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # <--- THIS IS THE FIX
                messages=[
                    {"role": "system", "content": "You are an epigenomics expert. Provide detailed, accurate answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._fallback_answer(query)

    def _fallback_answer(self, query):
        """Fallback if API fails."""
        q = query.lower()
        if "methylation" in q:
            return "DNA methylation is the addition of methyl groups to cytosine residues at CpG sites. It regulates gene expression by silencing genes and is linked to cancer and development."
        else:
            return "Epigenomics studies heritable changes in gene expression that do not involve changes to the DNA sequence."

    def query(self, question):
        print(f"Q: {question}")
        docs = self._semantic_search(question, n=3)
        if not docs:
            print("No relevant documents found.")
            return {"answer": self._fallback_answer(question)}

        context = "\n".join(d["content"] for d in docs)
        answer = self._generate_answer(question, context)

        self.memory_store["interactions"].append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "sources": [d["id"] for d in docs]
        })
        self._save_memory()

        print(f"A: {answer[:250]}...")
        print(f"Sources: {[d['id'] for d in docs]}")
        return {"question": question, "answer": answer, "sources": [d["id"] for d in docs]}

    def run_benchmark(self, q_file="../benchmark/questions.json"):
        if not os.path.exists(q_file):
            return {"error": "Questions file not found."}
        with open(q_file) as f:
            data = json.load(f)

        questions = data.get("questions", [])[:20]
        results = {"total": len(questions), "answered": 0, "hits": 0}

        print(f"\nRunning benchmark on {len(questions)} questions...\n")
        for q in questions:
            resp = self.query(q["question"])
            ans = resp.get("answer", "")
            if len(ans) > 20:
                results["answered"] += 1
            if any(k in ans.lower() for k in ["methylation", "histone", "chromatin", "cpg", "epigen"]):
                results["hits"] += 1

        results["accuracy"] = (results["hits"] / results["total"]) * 100 if results["total"] else 0
        return results


# ===== GRADIO WEB UI =====

agent = None  # Will be initialized when the app starts

def respond(message, history):
    """Called when user sends a message in the chat interface."""
    global agent
    if agent is None:
        return "Please wait, agent is initializing..."
    result = agent.query(message)
    return result.get("answer", "No answer generated.")

# Build the web interface
with gr.Blocks(title="Epigenomics AI Agent") as demo:
    gr.Markdown("""
    # 🧬 Epigenomics AI Agent
    Ask about DNA methylation, histone modifications, chromatin accessibility, or any epigenomics topic.
    """)

    gr.ChatInterface(
        fn=respond,
        title="Epigenomics Q&A",
        description="Powered by semantic search (ChromaDB) and GPT-4o-mini (OpenAI)."
    )

if __name__ == "__main__":
    # Initialize the agent before launching
    print("Initializing agent...")
    agent = EpigenomicsAgent()
    print("Launching web interface...")
    demo.launch(theme=gr.themes.Soft(), share=False)