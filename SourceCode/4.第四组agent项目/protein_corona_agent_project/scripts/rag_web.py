from __future__ import annotations

import json
import os
import socket
import sys
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    EMBEDDING_MODEL,
    EXTERNAL_LLM_MODEL,
    RAG_TOP_K,
    VECTOR_STORE_DIR,
)

sys.path.append(str(Path(__file__).resolve().parent))
from agentic_hybrid_rag import ask_agentic_hybrid_rag  # noqa: E402
from agentic_rag import ask_agentic_rag  # noqa: E402
from hybrid_rag import ask_hybrid_rag  # noqa: E402
from memory_system import format_memory_context, memory_stats, search_memory  # noqa: E402
from rag_core import ask_rag, search_knowledge  # noqa: E402
from skills.skill_agent import run_skill_agent  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
START_PORT = 8000
MAX_PORT_TRIES = 20
MAX_QUESTION_CHARS = 2000
MAX_TOP_K = 12
RUNTIME_INFO_PATH = PROJECT_ROOT / "storage" / "runtime" / "rag_web.json"


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Single-Cell Omics RAG</title>
  <style>
    :root {
      --bg: #f7f8fa;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #5f6b7a;
      --border: #d9dee6;
      --accent: #1b6fd8;
      --accent-dark: #155db8;
      --green: #0f766e;
      --danger: #b42318;
      --code: #f0f4f8;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      font-size: 15px;
      line-height: 1.55;
    }

    .app {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }

    header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }

    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0;
    }

    .status {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
    }

    .pill {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--panel);
      padding: 4px 10px;
      white-space: nowrap;
    }

    main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 18px;
      margin-top: 18px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }

    label {
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }

    textarea {
      width: 100%;
      min-height: 132px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      color: var(--text);
      font: inherit;
      outline: none;
    }

    textarea:focus,
    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(27, 111, 216, 0.12);
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin-top: 12px;
    }

    input[type="number"] {
      width: 72px;
      height: 38px;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0 10px;
      color: var(--text);
      font: inherit;
    }

    button {
      height: 38px;
      border: 1px solid transparent;
      border-radius: 8px;
      padding: 0 14px;
      color: #ffffff;
      background: var(--accent);
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }

    button.secondary {
      color: var(--accent);
      background: #ffffff;
      border-color: var(--accent);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.68;
    }

    button:hover:not(:disabled) {
      background: var(--accent-dark);
    }

    button.secondary:hover:not(:disabled) {
      color: #ffffff;
    }

    .answer {
      margin-top: 16px;
      min-height: 220px;
      white-space: pre-wrap;
    }

    .answer.empty {
      color: var(--muted);
    }

    .error {
      margin-top: 12px;
      color: var(--danger);
      white-space: pre-wrap;
    }

    .trace {
      display: none;
      margin-top: 14px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 12px;
    }

    .trace.visible {
      display: block;
    }

    .trace h2 {
      margin: 0 0 8px;
      font-size: 15px;
      letter-spacing: 0;
    }

    .trace pre {
      overflow: auto;
      margin: 0;
      border-radius: 6px;
      background: var(--code);
      padding: 9px;
      color: #26323f;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
    }

    .source-list {
      display: grid;
      gap: 10px;
      max-height: calc(100vh - 150px);
      overflow: auto;
      padding-right: 2px;
    }

    .source {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      background: #ffffff;
    }

    .source h2 {
      margin: 0 0 6px;
      font-size: 14px;
      line-height: 1.35;
      letter-spacing: 0;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 12px;
    }

    .snippet {
      max-height: 180px;
      overflow: auto;
      border-radius: 6px;
      background: var(--code);
      padding: 9px;
      color: #26323f;
      font-size: 13px;
      white-space: pre-wrap;
    }

    .side-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }

    .side-title h2 {
      margin: 0;
      font-size: 16px;
      letter-spacing: 0;
    }

    .count {
      color: var(--green);
      font-size: 13px;
      font-weight: 700;
    }

    @media (max-width: 860px) {
      header,
      main {
        display: block;
      }

      .status {
        justify-content: flex-start;
        margin-top: 12px;
      }

      .panel + .panel {
        margin-top: 16px;
      }

      .source-list {
        max-height: none;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>Single-Cell Omics RAG</h1>
      <div class="status" id="status">
        <span class="pill">embedding: loading</span>
        <span class="pill">llm: loading</span>
        <span class="pill">chunks: loading</span>
      </div>
    </header>

    <main>
      <section class="panel">
        <label for="question">问题</label>
        <textarea id="question">Nicheformer 这篇论文主要解决了单细胞和空间组学中的什么问题？</textarea>
        <div class="controls">
          <label for="topK">Top K</label>
          <input id="topK" type="number" min="1" max="12" value="6" />
          <button id="askBtn" type="button">问答</button>
          <button id="collabBtn" type="button">协作问答</button>
          <button id="skillBtn" type="button">UniProt Skill</button>
          <button id="agenticBtn" type="button">Agentic 问答</button>
          <button id="hybridBtn" type="button">Hybrid 问答</button>
          <button id="searchBtn" class="secondary" type="button">只检索</button>
        </div>
        <div id="error" class="error" hidden></div>
        <div id="trace" class="trace"></div>
        <div id="answer" class="answer empty">等待提问。</div>
      </section>

      <aside class="panel">
        <div class="side-title">
          <h2>证据片段</h2>
          <span class="count" id="sourceCount">0</span>
        </div>
        <div id="sources" class="source-list"></div>
      </aside>
    </main>
  </div>

  <script>
    const questionEl = document.getElementById("question");
    const topKEl = document.getElementById("topK");
    const askBtn = document.getElementById("askBtn");
    const collabBtn = document.getElementById("collabBtn");
    const skillBtn = document.getElementById("skillBtn");
    const agenticBtn = document.getElementById("agenticBtn");
    const hybridBtn = document.getElementById("hybridBtn");
    const searchBtn = document.getElementById("searchBtn");
    const answerEl = document.getElementById("answer");
    const errorEl = document.getElementById("error");
    const traceEl = document.getElementById("trace");
    const sourcesEl = document.getElementById("sources");
    const sourceCountEl = document.getElementById("sourceCount");
    const statusEl = document.getElementById("status");

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function setBusy(isBusy) {
      askBtn.disabled = isBusy;
      collabBtn.disabled = isBusy;
      skillBtn.disabled = isBusy;
      agenticBtn.disabled = isBusy;
      hybridBtn.disabled = isBusy;
      searchBtn.disabled = isBusy;
    }

    function setError(message) {
      if (!message) {
        errorEl.hidden = true;
        errorEl.textContent = "";
        return;
      }
      errorEl.hidden = false;
      errorEl.textContent = message;
    }

    function requestPayload() {
      return {
        question: questionEl.value.trim(),
        top_k: Number(topKEl.value || 6)
      };
    }

    async function postJson(path, payload) {
      const response = await fetch(path, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const text = await response.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = {error: text};
      }
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      return data;
    }

    function renderSources(sources) {
      sourceCountEl.textContent = String(sources.length);
      sourcesEl.innerHTML = sources.map((source) => {
        const title = source.title || source.knowledge_set_id || "untitled";
        const page = source.page === "" || source.page === null ? "" : `page ${source.page}`;
        const score = typeof source.similarity === "number" ? `score ${source.similarity.toFixed(3)}` : "";
        const meta = [page, score, source.doi].filter(Boolean).map(escapeHtml).join(" · ");
        return `
          <article class="source">
            <h2>[${escapeHtml(source.rank)}] ${escapeHtml(title)}</h2>
            <div class="meta">${meta}</div>
            <div class="snippet">${escapeHtml(source.text)}</div>
          </article>
        `;
      }).join("");
    }

    function renderTrace(data) {
      if (!data || (!data.plan && !data.structured_candidates)) {
        traceEl.classList.remove("visible");
        traceEl.innerHTML = "";
        return;
      }

      const lines = [];
      if (data.plan) {
        lines.push(`question_type: ${data.plan.question_type || "unknown"}`);
        lines.push(`need_retrieval: ${data.plan.need_retrieval}`);
        if (data.plan.reasoning) {
          lines.push(`reasoning: ${data.plan.reasoning}`);
        }
        lines.push("");
        for (const step of data.trace || []) {
          lines.push(`Step ${step.step}: ${step.purpose}`);
          lines.push(`Query: ${step.query}`);
          if (step.retrieval_mode) {
            lines.push(`Retrieval mode: ${step.retrieval_mode}`);
          }
          if (step.structured_candidates) {
            for (const candidate of (step.structured_candidates || []).slice(0, 3)) {
              const title = candidate.title || candidate.knowledge_set_id || "untitled";
              const matched = (candidate.matched_by || []).join(", ");
              lines.push(`  candidate: ${title}${matched ? ` (${matched})` : ""}`);
            }
          }
          for (const item of (step.results || []).slice(0, 3)) {
            const title = item.title || item.knowledge_set_id || "untitled";
            const page = item.page === "" || item.page === null ? "" : `, page ${item.page}`;
            const score = typeof item.similarity === "number" ? `, score ${item.similarity.toFixed(3)}` : "";
            lines.push(`  - ${title}${page}${score}`);
          }
          lines.push("");
        }
      }

      if (data.structured_candidates) {
        lines.push("Structured candidates:");
        for (const item of data.structured_candidates || []) {
          const title = item.title || item.knowledge_set_id || "untitled";
          const year = item.publication_year || "";
          const journal = item.journal || "";
          const matched = (item.matched_by || []).join(", ");
          lines.push(`- ${title}`);
          lines.push(`  id: ${item.knowledge_set_id}`);
          lines.push(`  journal/year: ${journal} / ${year}`);
          lines.push(`  matched_by: ${matched}`);
        }
        lines.push("");
      }

      if (data.skill_results && data.skill_results.length) {
        lines.push("UniProt Skill calls:");
        for (const item of data.skill_results) {
          const result = item.result || {};
          const protein = result.protein || (result.results && result.results[0]) || {};
          const accession = result.selected_accession || protein.accession || "";
          const name = protein.protein_name || "";
          const ok = item.ok ? "ok" : "failed";
          lines.push(`- ${item.query}: ${ok}${accession ? `, ${accession}` : ""}${name ? `, ${name}` : ""}`);
          if (item.error) {
            lines.push(`  error: ${item.error}`);
          }
        }
        lines.push("");
      }

      traceEl.classList.add("visible");
      traceEl.innerHTML = `<h2>检索决策过程</h2><pre>${escapeHtml(lines.join("\n"))}</pre>`;
    }

    async function runAsk() {
      setBusy(true);
      setError("");
      renderTrace(null);
      answerEl.classList.remove("empty");
      answerEl.textContent = "生成中...";
      try {
        const data = await postJson("/api/ask", requestPayload());
        answerEl.textContent = data.answer || "";
        renderSources(data.sources || []);
      } catch (error) {
        answerEl.textContent = "";
        setError(error.message);
      } finally {
        setBusy(false);
      }
    }

    async function runAgenticAsk() {
      setBusy(true);
      setError("");
      renderTrace(null);
      answerEl.classList.remove("empty");
      answerEl.textContent = "规划检索并生成中...";
      try {
        const data = await postJson("/api/agentic_ask", requestPayload());
        renderTrace(data);
        answerEl.textContent = data.answer || "";
        renderSources(data.sources || []);
      } catch (error) {
        answerEl.textContent = "";
        setError(error.message);
      } finally {
        setBusy(false);
      }
    }

    async function runCollabAsk() {
      setBusy(true);
      setError("");
      renderTrace(null);
      answerEl.classList.remove("empty");
      answerEl.textContent = "协作规划、结构化检索并生成中...";
      try {
        const data = await postJson("/api/agentic_hybrid_ask", requestPayload());
        renderTrace(data);
        answerEl.textContent = data.answer || "";
        renderSources(data.sources || []);
      } catch (error) {
        answerEl.textContent = "";
        setError(error.message);
      } finally {
        setBusy(false);
      }
    }

    async function runSkillAsk() {
      setBusy(true);
      setError("");
      renderTrace(null);
      answerEl.classList.remove("empty");
      answerEl.textContent = "调用 UniProt Skill 中...";
      try {
        const data = await postJson("/api/skill_uniprot", requestPayload());
        const resultText = JSON.stringify(data.result, null, 2);
        answerEl.textContent = [
          `selected_skill: ${data.selected_skill}`,
          `selected_tool: ${data.selected_tool}`,
          `reason: ${data.selection_reason}`,
          "",
          resultText
        ].join("\n");
        renderSources([]);
      } catch (error) {
        answerEl.textContent = "";
        setError(error.message);
      } finally {
        setBusy(false);
      }
    }

    async function runHybridAsk() {
      setBusy(true);
      setError("");
      renderTrace(null);
      answerEl.classList.remove("empty");
      answerEl.textContent = "结构化检索并生成中...";
      try {
        const data = await postJson("/api/hybrid_ask", requestPayload());
        renderTrace(data);
        answerEl.textContent = data.answer || "";
        renderSources(data.sources || []);
      } catch (error) {
        answerEl.textContent = "";
        setError(error.message);
      } finally {
        setBusy(false);
      }
    }

    async function runSearch() {
      setBusy(true);
      setError("");
      renderTrace(null);
      answerEl.classList.add("empty");
      answerEl.textContent = "已完成检索。";
      try {
        const data = await postJson("/api/search", requestPayload());
        renderSources(data.sources || []);
      } catch (error) {
        answerEl.textContent = "";
        setError(error.message);
      } finally {
        setBusy(false);
      }
    }

    async function loadHealth() {
      try {
        const response = await fetch("/health");
        const data = await response.json();
        statusEl.innerHTML = `
          <span class="pill">embedding: ${escapeHtml(data.embedding_model)}</span>
          <span class="pill">llm: ${escapeHtml(data.llm_model)}</span>
          <span class="pill">chunks: ${escapeHtml(data.chunk_count)}</span>
        `;
      } catch {
        statusEl.innerHTML = '<span class="pill">health: unavailable</span>';
      }
    }

    askBtn.addEventListener("click", runAsk);
    collabBtn.addEventListener("click", runCollabAsk);
    skillBtn.addEventListener("click", runSkillAsk);
    agenticBtn.addEventListener("click", runAgenticAsk);
    hybridBtn.addEventListener("click", runHybridAsk);
    searchBtn.addEventListener("click", runSearch);
    loadHealth();
  </script>
</body>
</html>
"""


def json_bytes(payload: dict[str, Any], status: int = 200) -> tuple[int, bytes]:
    return status, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def read_manifest() -> dict[str, Any]:
    path = VECTOR_STORE_DIR / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def health_payload() -> dict[str, Any]:
    manifest = read_manifest()
    return {
        "ok": True,
        "embedding_model": EMBEDDING_MODEL,
        "llm_model": EXTERNAL_LLM_MODEL,
        "vector_store_dir": str(VECTOR_STORE_DIR),
        "chunk_count": manifest.get("chunk_count", "unknown"),
        "vector_shape": manifest.get("vector_shape", []),
        "memory": memory_stats(),
    }


def parse_payload(raw_body: bytes) -> tuple[str, int]:
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON.") from exc

    question = str(payload.get("question", "")).strip()
    if not question:
        raise ValueError("Question is empty.")
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"Question is too long. Max length is {MAX_QUESTION_CHARS} characters.")

    try:
        top_k = int(payload.get("top_k", RAG_TOP_K))
    except (TypeError, ValueError) as exc:
        raise ValueError("top_k must be an integer.") from exc
    top_k = max(1, min(MAX_TOP_K, top_k))
    return question, top_k


class RAGRequestHandler(BaseHTTPRequestHandler):
    server_version = "SingleCellRAG/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_bytes(
        self,
        body: bytes,
        *,
        status: int = 200,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        _, body = json_bytes(payload, status=status)
        self.send_bytes(body, status=status)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.send_bytes(INDEX_HTML.encode("utf-8"), content_type="text/html; charset=utf-8")
            return
        if path == "/health":
            self.send_json(health_payload())
            return
        if path == "/api/memory_stats":
            self.send_json(memory_stats())
            return
        self.send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        try:
            if path == "/api/memory_stats":
                self.send_json(memory_stats())
                return

            question, top_k = parse_payload(raw_body)
            if path == "/api/search":
                self.send_json({"question": question, "sources": search_knowledge(question, top_k=top_k)})
                return
            if path == "/api/ask":
                self.send_json(ask_rag(question, top_k=top_k))
                return
            if path == "/api/agentic_ask":
                self.send_json(ask_agentic_rag(question))
                return
            if path == "/api/agentic_hybrid_ask":
                self.send_json(ask_agentic_hybrid_rag(question))
                return
            if path == "/api/skill_uniprot":
                self.send_json(run_skill_agent(question))
                return
            if path == "/api/hybrid_ask":
                self.send_json(ask_hybrid_rag(question, top_k=top_k))
                return
            if path == "/api/memory_search":
                result = search_memory(question)
                self.send_json(
                    {
                        "question": question,
                        "memory_context": format_memory_context(result),
                        "working": result.working,
                        "episodic": result.episodic,
                        "semantic": result.semantic,
                    }
                )
                return
            self.send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            print(traceback.format_exc())
            self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def build_server() -> ThreadingHTTPServer:
    last_error: OSError | None = None
    for port in range(START_PORT, START_PORT + MAX_PORT_TRIES):
        try:
            return ThreadingHTTPServer((HOST, port), RAGRequestHandler)
        except OSError as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Could not bind {HOST}:{START_PORT}-{START_PORT + MAX_PORT_TRIES - 1}") from last_error


def write_runtime_info(server: ThreadingHTTPServer) -> str:
    host, port = server.server_address
    url = f"http://{host}:{port}"
    RUNTIME_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_INFO_PATH.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "host": host,
                "port": port,
                "url": url,
                "embedding_model": EMBEDDING_MODEL,
                "llm_model": EXTERNAL_LLM_MODEL,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return url


def main() -> None:
    socket.setdefaulttimeout(120)
    server = build_server()
    url = write_runtime_info(server)
    print(f"RAG web app: {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping RAG web app.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
