from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(Path(__file__).resolve().parent))

from config import RAG_MAX_CONTEXT_CHARS, RAG_TOP_K  # noqa: E402
from rag_core import (  # noqa: E402
    RetrievedChunk,
    call_external_llm,
    chunk_to_dict,
    format_context,
    retrieve,
    source_label,
)


# PyCharm can run this file directly. Edit this question for a one-shot run.
QUESTION = "比较 Nicheformer 和 CONCORD 在单细胞组学中的作用差异。"

# Set to True if you want to type questions in the PyCharm console.
INTERACTIVE = False

MAX_PLAN_STEPS = 5
MAX_TOP_K_PER_STEP = 3
MAX_EVIDENCE_CHUNKS = 6
AGENTIC_MAX_CONTEXT_CHARS = 7000
SNIPPET_CHARS = 360
PLAN_CACHE_PATH = PROJECT_ROOT / "storage" / "runtime" / "agentic_plan_cache.json"


@dataclass(frozen=True)
class RetrievalStep:
    step: int
    query: str
    purpose: str
    top_k: int


@dataclass(frozen=True)
class RetrievalStepResult:
    step: int
    query: str
    purpose: str
    top_k: int
    chunks: list[RetrievedChunk]


def default_plan(question: str, reason: str = "planner fallback") -> dict[str, Any]:
    return {
        "need_retrieval": True,
        "question_type": "general",
        "reasoning": reason,
        "steps": [
            {
                "step": 1,
                "query": question,
                "purpose": "Use the original question as the retrieval query.",
                "top_k": min(RAG_TOP_K, MAX_TOP_K_PER_STEP),
            }
        ],
    }


def plan_cache_key(question: str) -> str:
    return " ".join(question.strip().split()).lower()


def load_plan_cache() -> dict[str, Any]:
    if not PLAN_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(PLAN_CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_plan_cache(cache: dict[str, Any]) -> None:
    PLAN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAN_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cached_plan(question: str, reason: str) -> dict[str, Any] | None:
    item = load_plan_cache().get(plan_cache_key(question))
    if not isinstance(item, dict):
        return None
    plan = item.get("plan")
    if not isinstance(plan, dict):
        return None
    copied = json.loads(json.dumps(plan, ensure_ascii=False))
    old_reasoning = str(copied.get("reasoning", "")).strip()
    copied["reasoning"] = f"{reason} Reused cached LLM plan. Cached reasoning: {old_reasoning}"
    return copied


def remember_plan(question: str, plan: dict[str, Any]) -> None:
    cache = load_plan_cache()
    cache[plan_cache_key(question)] = {
        "question": question,
        "saved_at": int(time.time()),
        "plan": plan,
    }
    save_plan_cache(cache)


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    if not cleaned.startswith("{"):
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in planner output: {text[:500]}")
        cleaned = match.group(0)

    return json.loads(cleaned)


def normalize_plan(plan: dict[str, Any], question: str) -> dict[str, Any]:
    normalized = {
        "need_retrieval": bool(plan.get("need_retrieval", True)),
        "question_type": str(plan.get("question_type", "general")).strip() or "general",
        "reasoning": str(plan.get("reasoning", "")).strip(),
        "steps": [],
    }

    if not normalized["need_retrieval"]:
        return normalized

    raw_steps = plan.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        return default_plan(question, reason="planner produced no usable steps")

    for index, raw_step in enumerate(raw_steps[:MAX_PLAN_STEPS], start=1):
        if not isinstance(raw_step, dict):
            continue
        query = str(raw_step.get("query", "")).strip()
        if not query:
            continue
        purpose = str(raw_step.get("purpose") or raw_step.get("reason") or "").strip()
        if not purpose:
            purpose = "Retrieve evidence for this sub-question."
        try:
            top_k = int(raw_step.get("top_k", min(RAG_TOP_K, MAX_TOP_K_PER_STEP)))
        except (TypeError, ValueError):
            top_k = min(RAG_TOP_K, MAX_TOP_K_PER_STEP)
        top_k = max(1, min(MAX_TOP_K_PER_STEP, top_k))
        normalized["steps"].append(
            {
                "step": index,
                "query": query,
                "purpose": purpose,
                "top_k": top_k,
            }
        )

    if not normalized["steps"]:
        return default_plan(question, reason="planner steps were invalid")

    return normalized


def plan_retrieval(question: str) -> tuple[dict[str, Any], str, str | None]:
    system_prompt = (
        "你是 Agentic RAG 检索规划器，只制定检索计划，不回答问题。"
        "只返回 JSON 对象，不要 Markdown。"
        "字段：need_retrieval, question_type, reasoning, steps。"
        "steps 每项：step, query, purpose, top_k。"
        "比较题要分别检索每个对象，再按需增加综合检索。"
        "机制/原因/优缺点/综述题要拆成可检索子问题。"
        "query 优先保留论文名、方法名和英文关键词，可混合中文。"
        f"最多 {MAX_PLAN_STEPS} 步；top_k 为 1 到 {MAX_TOP_K_PER_STEP}。"
    )
    user_prompt = f"用户问题：{question}"

    try:
        raw = call_external_llm(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=550,
        timeout=35,
        retry_count=1,
        )
    except Exception as exc:  # noqa: BLE001
        reason = f"planner LLM request failed: {exc}"
        fallback = cached_plan(question, reason) or default_plan(question, reason=reason)
        return fallback, "", str(exc)

    try:
        parsed = extract_json_object(raw)
        normalized = normalize_plan(parsed, question)
        remember_plan(question, normalized)
        return normalized, raw, None
    except Exception as exc:  # noqa: BLE001
        reason = f"planner output could not be parsed: {exc}"
        fallback = cached_plan(question, reason) or default_plan(question, reason=reason)
        return fallback, raw, str(exc)


def plan_steps(plan: dict[str, Any]) -> list[RetrievalStep]:
    steps: list[RetrievalStep] = []
    for raw_step in plan.get("steps", []):
        steps.append(
            RetrievalStep(
                step=int(raw_step["step"]),
                query=str(raw_step["query"]),
                purpose=str(raw_step["purpose"]),
                top_k=int(raw_step["top_k"]),
            )
        )
    return steps


def execute_retrieval_plan(plan: dict[str, Any]) -> list[RetrievalStepResult]:
    results: list[RetrievalStepResult] = []
    if not plan.get("need_retrieval", True):
        return results

    for step in plan_steps(plan):
        chunks = retrieve(step.query, top_k=step.top_k)
        results.append(
            RetrievalStepResult(
                step=step.step,
                query=step.query,
                purpose=step.purpose,
                top_k=step.top_k,
                chunks=chunks,
            )
        )
    return results


def chunk_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata
    parts = [
        str(metadata.get("knowledge_set_id", "")),
        str(metadata.get("source_file", "")),
        str(metadata.get("page", "")),
        str(metadata.get("chunk_index", "")),
    ]
    key = "|".join(parts)
    if key.strip("|"):
        return key
    return chunk.text[:240]


def collect_evidence(step_results: list[RetrievalStepResult]) -> list[RetrievedChunk]:
    seen: set[str] = set()
    evidence: list[RetrievedChunk] = []

    for step_result in step_results:
        for chunk in step_result.chunks:
            key = chunk_key(chunk)
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                RetrievedChunk(
                    index=len(evidence) + 1,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    distance=chunk.distance,
                )
            )
            if len(evidence) >= MAX_EVIDENCE_CHUNKS:
                return evidence

    return evidence


def summarize_chunk(chunk: RetrievedChunk) -> dict[str, Any]:
    data = chunk_to_dict(chunk)
    data["text"] = data["text"].strip()[:SNIPPET_CHARS]
    return data


def step_result_to_dict(result: RetrievalStepResult) -> dict[str, Any]:
    return {
        "step": result.step,
        "query": result.query,
        "purpose": result.purpose,
        "top_k": result.top_k,
        "result_count": len(result.chunks),
        "results": [summarize_chunk(chunk) for chunk in result.chunks],
    }


def format_trace(plan: dict[str, Any], step_results: list[RetrievalStepResult]) -> str:
    lines = [
        f"Question type: {plan.get('question_type', 'general')}",
        f"Need retrieval: {plan.get('need_retrieval', True)}",
        f"Planner reasoning: {plan.get('reasoning', '')}",
    ]

    if not step_results:
        lines.append("No retrieval steps were executed.")
        return "\n".join(lines)

    for result in step_results:
        lines.append("")
        lines.append(f"Step {result.step}")
        lines.append(f"Purpose: {result.purpose}")
        lines.append(f"Query: {result.query}")
        lines.append("Top results:")
        for chunk in result.chunks[:3]:
            lines.append(f"- {source_label(chunk)}")
    return "\n".join(lines)


def build_agentic_messages(
    question: str,
    plan: dict[str, Any],
    step_results: list[RetrievalStepResult],
    evidence: list[RetrievedChunk],
) -> list[dict[str, str]]:
    trace = format_trace(plan, step_results)
    context = format_context(evidence, max_chars=min(RAG_MAX_CONTEXT_CHARS, AGENTIC_MAX_CONTEXT_CHARS))
    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)

    system_prompt = (
        "你是一个面向细胞组学课程项目的 Agentic RAG 问答助手。\n"
        "你必须依据检索计划、检索轨迹和证据片段回答问题。\n"
        "如果证据不足以支持结论，必须明确说明知识库中没有足够依据。\n"
        "回答必须使用中文；关键事实后必须使用 [1]、[2] 这样的来源编号引用。\n"
        "不要编造论文、数据、实验结果、作者或 DOI。"
    )
    user_prompt = (
        f"原始问题：{question}\n\n"
        f"检索计划 JSON：\n{plan_json}\n\n"
        f"检索决策与执行轨迹：\n{trace}\n\n"
        f"证据片段：\n{context}\n\n"
        "请先用简洁语言说明你如何利用这些检索步骤，然后给出最终答案。"
        "最后列出使用到的来源。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_fallback_answer(question: str, evidence: list[RetrievedChunk], error: Exception) -> str:
    lines = [
        "外部 LLM 生成最终答案时失败，因此这里只展示已经完成的 Agentic RAG 检索结果。",
        f"失败原因：{error}",
        "",
        f"原始问题：{question}",
        "",
        "已检索到的主要证据：",
    ]
    for chunk in evidence[:5]:
        metadata = chunk.metadata
        title = metadata.get("title") or metadata.get("knowledge_set_id") or "untitled"
        page = metadata.get("page")
        page_text = f"，page {page}" if page not in ("", None) else ""
        text = " ".join(chunk.text.strip().split())[:260]
        lines.append(f"[{chunk.index}] {title}{page_text}：{text}")
    lines.append("")
    lines.append("检索链路已经完成；需要在外部 LLM 接口恢复后重新运行以生成正式中文答案。")
    return "\n".join(lines)


def ask_agentic_rag(question: str, *, verbose: bool = False) -> dict[str, Any]:
    if verbose:
        print("Planning retrieval steps...", flush=True)
    plan, planner_raw, planner_error = plan_retrieval(question)
    if verbose:
        print("Executing retrieval plan...", flush=True)
    step_results = execute_retrieval_plan(plan)
    evidence = collect_evidence(step_results)
    if verbose:
        print(f"Generating answer from {len(evidence)} evidence chunks...", flush=True)
    messages = build_agentic_messages(question, plan, step_results, evidence)
    answer_error = None
    try:
        answer = call_external_llm(messages, max_tokens=520, timeout=45, retry_count=1)
    except Exception as exc:  # noqa: BLE001
        answer_error = str(exc)
        answer = build_fallback_answer(question, evidence, exc)

    return {
        "question": question,
        "mode": "agentic_rag",
        "plan": plan,
        "planner_raw": planner_raw,
        "planner_error": planner_error,
        "trace": [step_result_to_dict(result) for result in step_results],
        "answer": answer,
        "answer_error": answer_error,
        "sources": [chunk_to_dict(chunk) for chunk in evidence],
    }


def print_agentic_result(result: dict[str, Any]) -> None:
    print()
    print("Question:")
    print(result["question"])

    print()
    print("Planner:")
    print(json.dumps(result["plan"], ensure_ascii=False, indent=2))
    if result.get("planner_error"):
        print()
        print(f"Planner warning: {result['planner_error']}")

    print()
    print("Retrieval trace:")
    for step in result["trace"]:
        print(f"- Step {step['step']}: {step['purpose']}")
        print(f"  Query: {step['query']}")
        for item in step["results"][:3]:
            title = item.get("title") or item.get("knowledge_set_id") or "untitled"
            page = item.get("page")
            score = item.get("similarity")
            score_text = f", score={score:.4f}" if isinstance(score, float) else ""
            page_text = f", page={page}" if page not in ("", None) else ""
            print(f"  - {title}{page_text}{score_text}")

    print()
    print("Answer:")
    if result.get("answer_error"):
        print(f"Answer warning: {result['answer_error']}")
        print()
    print(result["answer"])

    print()
    print("Evidence sources:")
    for source in result["sources"]:
        page = source.get("page")
        page_text = f", page={page}" if page not in ("", None) else ""
        score = source.get("similarity")
        score_text = f", score={score:.4f}" if isinstance(score, float) else ""
        print(f"- [{source['rank']}] {source.get('title') or source.get('knowledge_set_id')}{page_text}{score_text}")


def run_one_question(question: str) -> None:
    result = ask_agentic_rag(question, verbose=True)
    print_agentic_result(result)


def main() -> None:
    if INTERACTIVE:
        while True:
            question = input("\n请输入问题，直接回车退出：").strip()
            if not question:
                break
            run_one_question(question)
        return

    run_one_question(QUESTION)


if __name__ == "__main__":
    main()
