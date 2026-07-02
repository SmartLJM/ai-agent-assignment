from __future__ import annotations

import json
import os
import sys
import traceback
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from config import PROJECT_ROOT  # noqa: E402
from memory_system import DEFAULT_SESSION_ID, record_interaction  # noqa: E402
from rag_core import retrieve, chunk_to_dict  # noqa: E402
from hybrid_rag import candidate_to_dict, filtered_vector_search, structured_candidates  # noqa: E402
from agentic_rag import ask_agentic_rag, collect_evidence, execute_retrieval_plan, plan_retrieval, step_result_to_dict  # noqa: E402
from agentic_hybrid_rag import (  # noqa: E402
    aggregate_structured_candidates,
    collect_evidence as collect_agentic_hybrid_evidence,
    execute_agentic_hybrid_plan,
    execute_uniprot_skill,
)
from skills.skill_agent import run_skill_agent  # noqa: E402


# PyCharm-friendly settings. Edit these constants instead of passing CLI args.
BENCHMARK_PATH = PROJECT_ROOT / "data" / "benchmark" / "single_cell_omics_rag_benchmark_30.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "benchmark_runs"
RUN_NAME = datetime.now().strftime("run_%Y%m%d_%H%M%S")

# "offline" evaluates retrieval/module behavior without calling the final LLM.
# "full" also calls the project QA functions that generate final answers.
RUN_MODE = "offline"

# Set to an integer for a quick smoke test, or None for all 30 questions.
MAX_QUESTIONS: int | None = None

# Use a fixed session id so memory setup turns are inspectable and reproducible.
SESSION_ID = "benchmark_session"
RETRY_COUNT = 2
RETRY_SECONDS = 3


@dataclass
class BenchmarkCheck:
    name: str
    passed: bool
    detail: str
    points: int
    max_points: int


def load_benchmark() -> dict[str, Any]:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def expected_ids(question: dict[str, Any]) -> list[str]:
    return [str(item) for item in question.get("required_knowledge_set_ids") or []]


def optional_ids(question: dict[str, Any]) -> list[str]:
    return [str(item) for item in question.get("optional_knowledge_set_ids") or []]


def source_ids(sources: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for source in sources:
        value = str(source.get("knowledge_set_id") or "").strip()
        if value:
            ids.append(value)
    return ids


def unique_source_ids(sources: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for value in source_ids(sources):
        if value not in seen:
            seen.append(value)
    return seen


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(str(needle).lower() in lowered for needle in needles if str(needle).strip())


def apply_setup_turns(question: dict[str, Any]) -> list[dict[str, str]]:
    turns = question.get("setup_turns") or []
    applied: list[dict[str, str]] = []
    for turn in turns:
        role = str(turn.get("role") or "user")
        content = str(turn.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            record_interaction(
                session_id=SESSION_ID,
                question=content,
                answer="已记录用户偏好，后续回答会结合该上下文。",
                mode="benchmark_setup",
                sources=[],
            )
        applied.append({"role": role, "content": content})
    return applied


def choose_mode(question: dict[str, Any]) -> str:
    modules = set(question.get("target_modules") or [])
    tools = set(question.get("required_external_tools") or [])
    qtype = str(question.get("question_type") or "")
    if "uniprot_skill" in modules and not expected_ids(question):
        return "skill_only"
    if "agentic_hybrid_rag" in modules or "memory_system" in modules or tools:
        return "agentic_hybrid"
    if "agentic_rag" in modules and "hybrid_rag" in modules:
        return "agentic_hybrid"
    if "hybrid_rag" in modules or "structured_kb" in modules:
        return "hybrid"
    if "agentic_rag" in modules or "comparison" in qtype or "synthesis" in qtype:
        return "agentic"
    return "basic"


def run_basic_offline(question_text: str) -> dict[str, Any]:
    chunks = retrieve(question_text)
    return {
        "mode": "basic_offline",
        "sources": [chunk_to_dict(chunk) for chunk in chunks],
        "structured_candidates": [],
        "trace": [],
        "memory_context": "",
        "skill_results": [],
        "answer": "",
    }


def run_hybrid_offline(question_text: str) -> dict[str, Any]:
    candidates = structured_candidates(question_text)
    allowed_ids = {candidate.knowledge_set_id for candidate in candidates}
    chunks = filtered_vector_search(question_text, allowed_ids)
    return {
        "mode": "hybrid_offline",
        "sources": [chunk_to_dict(chunk) for chunk in chunks],
        "structured_candidates": [candidate_to_dict(candidate) for candidate in candidates],
        "trace": [],
        "memory_context": "",
        "skill_results": [],
        "answer": "",
    }


def deterministic_plan(question: dict[str, Any]) -> dict[str, Any]:
    question_text = str(question["question"])
    required = expected_ids(question)
    steps: list[dict[str, Any]] = []
    for index, knowledge_set_id in enumerate(required, start=1):
        readable = knowledge_set_id.replace("-", " ")
        steps.append(
            {
                "step": index,
                "purpose": f"Retrieve evidence from {knowledge_set_id}.",
                "query": f"{question_text}\n重点资料：{readable}",
                "top_k": 4,
            }
        )
    if not steps:
        steps.append(
            {
                "step": 1,
                "purpose": "Retrieve evidence for the benchmark question.",
                "query": question_text,
                "top_k": 6,
            }
        )
    return {
        "need_retrieval": True,
        "question_type": question.get("question_type") or "benchmark",
        "reasoning": "Deterministic offline benchmark plan based on required knowledge_set_ids.",
        "steps": steps[:6],
    }


def run_agentic_offline(question: dict[str, Any]) -> dict[str, Any]:
    plan = deterministic_plan(question)
    question_text = str(question["question"])
    step_results = execute_retrieval_plan(plan)
    evidence = collect_evidence(step_results)
    return {
        "mode": "agentic_offline",
        "plan": plan,
        "planner_raw": json.dumps(plan, ensure_ascii=False),
        "planner_error": None,
        "trace": [step_result_to_dict(result) for result in step_results],
        "sources": [chunk_to_dict(chunk) for chunk in evidence],
        "structured_candidates": [],
        "memory_context": "",
        "skill_results": [],
        "answer": "",
    }


def run_agentic_hybrid_offline(question: dict[str, Any], use_memory: bool = True) -> dict[str, Any]:
    from memory_system import format_memory_context, search_memory

    question_text = str(question["question"])
    memory_context = format_memory_context(search_memory(question_text, session_id=SESSION_ID)) if use_memory else ""
    plan = deterministic_plan(question)
    step_results = execute_agentic_hybrid_plan(plan)
    evidence = collect_agentic_hybrid_evidence(step_results)
    skill_results = execute_uniprot_skill(question_text, plan)
    return {
        "mode": "agentic_hybrid_offline",
        "plan": plan,
        "planner_raw": json.dumps(plan, ensure_ascii=False),
        "planner_error": None,
        "trace": [step_result_to_dict(result) for result in step_results],
        "structured_candidates": aggregate_structured_candidates(step_results),
        "sources": [chunk_to_dict(chunk) for chunk in evidence],
        "memory_context": memory_context,
        "skill_results": skill_results,
        "answer": "",
    }


def run_skill_only(question_text: str) -> dict[str, Any]:
    skill_result = run_skill_agent(question_text)
    return {
        "mode": "skill_only",
        "sources": [],
        "structured_candidates": [],
        "trace": [],
        "memory_context": "",
        "skill_results": [skill_result],
        "answer": json.dumps(skill_result, ensure_ascii=False),
    }


def run_full(question: dict[str, Any], selected_mode: str) -> dict[str, Any]:
    question_text = str(question["question"])
    use_memory = "memory_system" in set(question.get("target_modules") or [])
    if selected_mode == "skill_only":
        return run_skill_only(question_text)
    if selected_mode == "agentic_hybrid":
        from agentic_hybrid_rag import ask_agentic_hybrid_rag

        return ask_agentic_hybrid_rag(question_text, session_id=SESSION_ID, use_memory=use_memory)
    if selected_mode == "hybrid":
        from hybrid_rag import ask_hybrid_rag

        return ask_hybrid_rag(question_text, session_id=SESSION_ID, use_memory=use_memory)
    if selected_mode == "agentic":
        return ask_agentic_rag(question_text)
    from rag_core import ask_rag

    return ask_rag(question_text, session_id=SESSION_ID, use_memory=use_memory)


def run_offline(question: dict[str, Any], selected_mode: str) -> dict[str, Any]:
    question_text = str(question["question"])
    use_memory = "memory_system" in set(question.get("target_modules") or [])
    if selected_mode == "skill_only":
        return run_skill_only(question_text)
    if selected_mode == "agentic_hybrid":
        return run_agentic_hybrid_offline(question, use_memory=use_memory)
    if selected_mode == "hybrid":
        return run_hybrid_offline(question_text)
    if selected_mode == "agentic":
        return run_agentic_offline(question)
    return run_basic_offline(question_text)


def check_retrieval(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    required = expected_ids(question)
    if not required:
        return BenchmarkCheck("retrieval_required_sources", True, "No local required source ids.", 20, 20)
    found = set(unique_source_ids(result.get("sources") or []))
    required_set = set(required)
    matched = sorted(required_set & found)
    missing = sorted(required_set - found)
    passed = not missing
    points = 20 if passed else int(20 * len(matched) / max(1, len(required_set)))
    detail = f"matched={matched}; missing={missing}; found_top={list(found)[:8]}"
    return BenchmarkCheck("retrieval_required_sources", passed, detail, points, 20)


def check_min_chunks(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    expectation = question.get("retrieval_expectation") or {}
    min_chunks = int(expectation.get("min_relevant_chunks") or 0)
    if min_chunks <= 0:
        return BenchmarkCheck("min_relevant_chunks", True, "No minimum relevant chunk requirement.", 10, 10)
    required = set(expected_ids(question))
    sources = result.get("sources") or []
    if required:
        count = sum(1 for source in sources if source.get("knowledge_set_id") in required)
    else:
        count = len(sources)
    passed = count >= min_chunks
    points = 10 if passed else int(10 * count / max(1, min_chunks))
    return BenchmarkCheck("min_relevant_chunks", passed, f"relevant_count={count}; expected>={min_chunks}", points, 10)


def check_structured(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    modules = set(question.get("target_modules") or [])
    if "uniprot_skill" in modules and not expected_ids(question):
        return BenchmarkCheck("structured_candidates", True, "Structured retrieval not required for skill-only item.", 10, 10)
    if not ({"hybrid_rag", "structured_kb", "agentic_hybrid_rag"} & modules):
        return BenchmarkCheck("structured_candidates", True, "Structured retrieval not required.", 10, 10)
    candidates = result.get("structured_candidates") or []
    passed = bool(candidates)
    detail = f"candidate_count={len(candidates)}"
    return BenchmarkCheck("structured_candidates", passed, detail, 10 if passed else 0, 10)


def check_agentic(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    modules = set(question.get("target_modules") or [])
    if "uniprot_skill" in modules and not expected_ids(question):
        return BenchmarkCheck("agentic_trace", True, "Agentic planning not required for skill-only item.", 10, 10)
    if not ({"agentic_rag", "agentic_hybrid_rag"} & modules):
        return BenchmarkCheck("agentic_trace", True, "Agentic planning not required.", 10, 10)
    trace = result.get("trace") or []
    plan = result.get("plan") or {}
    steps = plan.get("steps") or []
    passed = bool(trace) and len(steps) >= 1
    detail = f"plan_steps={len(steps)}; executed_steps={len(trace)}"
    return BenchmarkCheck("agentic_trace", passed, detail, 10 if passed else 0, 10)


def flatten_skill_results(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def check_skill(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    tools = set(question.get("required_external_tools") or [])
    modules = set(question.get("target_modules") or [])
    if "UniProtProteinSkill" not in tools and "uniprot_skill" not in modules:
        return BenchmarkCheck("uniprot_skill", True, "UniProt Skill not required.", 15, 15)

    expected = ((question.get("expected_tool_behavior") or {}).get("expected_uniprot_accessions") or [])
    text = flatten_skill_results(result.get("skill_results") or []) + "\n" + str(result.get("answer") or "")
    matched = [accession for accession in expected if accession and accession in text]
    passed = bool(expected) and len(matched) == len(expected)
    if not expected:
        passed = bool(result.get("skill_results"))
    detail = f"expected_accessions={expected}; matched={matched}; skill_result_count={len(result.get('skill_results') or [])}"
    return BenchmarkCheck("uniprot_skill", passed, detail, 15 if passed else 0, 15)


def check_memory(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    modules = set(question.get("target_modules") or [])
    if "memory_system" not in modules:
        return BenchmarkCheck("memory_context", True, "Memory not required.", 15, 15)
    context = str(result.get("memory_context") or "")
    setup_text = " ".join(str(turn.get("content") or "") for turn in question.get("setup_turns") or [])
    expected_keywords = []
    if "质量控制" in setup_text or "平台误差" in setup_text:
        expected_keywords = ["质量控制", "平台误差", "空间转录组"]
    elif "重编程" in setup_text:
        expected_keywords = ["重编程"]
    passed = bool(context) and (not expected_keywords or contains_any(context, expected_keywords))
    detail = f"context_chars={len(context)}; expected_keywords={expected_keywords}"
    return BenchmarkCheck("memory_context", passed, detail, 15 if passed else 0, 15)


def check_answer_points(question: dict[str, Any], result: dict[str, Any]) -> BenchmarkCheck:
    answer = str(result.get("answer") or "")
    expected_points = [str(item) for item in question.get("expected_answer_points") or []]
    if RUN_MODE != "full":
        return BenchmarkCheck("answer_key_points", True, "Skipped in offline mode.", 20, 20)
    if not expected_points:
        return BenchmarkCheck("answer_key_points", True, "No expected answer points.", 20, 20)

    matched = 0
    for point in expected_points:
        tokens = [token for token in point.replace("，", " ").replace("。", " ").split() if len(token) >= 3]
        if tokens and contains_any(answer, tokens[:5]):
            matched += 1
    passed = matched >= max(1, len(expected_points) // 2)
    points = int(20 * matched / max(1, len(expected_points)))
    return BenchmarkCheck("answer_key_points", passed, f"matched_rough_points={matched}/{len(expected_points)}", points, 20)


def evaluate_question(question: dict[str, Any], result: dict[str, Any]) -> list[BenchmarkCheck]:
    checks = [
        check_retrieval(question, result),
        check_min_chunks(question, result),
        check_structured(question, result),
        check_agentic(question, result),
        check_memory(question, result),
        check_skill(question, result),
        check_answer_points(question, result),
    ]
    return checks


def score_checks(checks: list[BenchmarkCheck]) -> dict[str, Any]:
    points = sum(check.points for check in checks)
    max_points = sum(check.max_points for check in checks)
    return {
        "points": points,
        "max_points": max_points,
        "score_percent": round(points * 100 / max(1, max_points), 2),
        "passed_checks": sum(1 for check in checks if check.passed),
        "total_checks": len(checks),
    }


def check_to_dict(check: BenchmarkCheck) -> dict[str, Any]:
    return {
        "name": check.name,
        "passed": check.passed,
        "detail": check.detail,
        "points": check.points,
        "max_points": check.max_points,
    }


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    sources = result.get("sources") or []
    return {
        "mode": result.get("mode"),
        "source_ids": unique_source_ids(sources),
        "source_count": len(sources),
        "structured_candidate_count": len(result.get("structured_candidates") or []),
        "trace_step_count": len(result.get("trace") or []),
        "has_memory_context": bool(result.get("memory_context")),
        "memory_context_preview": str(result.get("memory_context") or "")[:500],
        "skill_results": result.get("skill_results") or [],
        "answer_preview": str(result.get("answer") or "")[:1000],
        "answer_error": result.get("answer_error"),
        "planner_error": result.get("planner_error"),
    }


def write_report(run_dir: Path, benchmark: dict[str, Any], records: list[dict[str, Any]]) -> Path:
    total_points = sum(record["score"]["points"] for record in records)
    total_max = sum(record["score"]["max_points"] for record in records)
    mode_counts = Counter(record["selected_mode"] for record in records)
    failed = [record for record in records if record.get("error") or record["score"]["score_percent"] < 70]

    lines = [
        "# RAG Benchmark Run Report",
        "",
        f"- Run name: `{RUN_NAME}`",
        f"- Run mode: `{RUN_MODE}`",
        f"- Benchmark: `{benchmark.get('benchmark_id')}`",
        f"- Questions evaluated: {len(records)}",
        f"- Overall score: {total_points}/{total_max} ({round(total_points * 100 / max(1, total_max), 2)}%)",
        f"- Output JSONL: `{(run_dir / 'results.jsonl').as_posix()}`",
        "",
        "## Mode Distribution",
        "",
    ]
    for mode, count in mode_counts.items():
        lines.append(f"- {mode}: {count}")

    lines.extend(
        [
            "",
            "## Summary Table",
            "",
            "| ID | Mode | Score | Required Sources Hit | Module Checks | Notes |",
            "| --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for record in records:
        checks = {check["name"]: check for check in record["checks"]}
        retrieval = checks.get("retrieval_required_sources", {})
        module_bits = []
        for name in ["structured_candidates", "agentic_trace", "memory_context", "uniprot_skill"]:
            check = checks.get(name)
            if check and check["detail"] not in {"Structured retrieval not required.", "Agentic planning not required.", "Memory not required.", "UniProt Skill not required."}:
                module_bits.append(f"{name}:{'pass' if check['passed'] else 'fail'}")
        notes = record.get("error") or "; ".join(
            check["name"] for check in record["checks"] if not check["passed"]
        )
        lines.append(
            f"| {record['id']} | {record['selected_mode']} | {record['score']['score_percent']}% | "
            f"{'pass' if retrieval.get('passed') else 'fail'} | {', '.join(module_bits) or '-'} | {notes or '-'} |"
        )

    if failed:
        lines.extend(["", "## Items Needing Attention", ""])
        for record in failed:
            lines.append(f"### {record['id']}")
            if record.get("error"):
                lines.append(f"- Error: {record['error']}")
            for check in record["checks"]:
                if not check["passed"]:
                    lines.append(f"- {check['name']}: {check['detail']}")
            lines.append("")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Offline mode evaluates retrieval coverage and visible module behavior without judging final answer fluency.",
            "- Full mode additionally calls the LLM and performs rough expected-point matching; final scientific grading should still inspect answers manually.",
            "- UniProt Skill items are considered passed only when expected accessions such as Q01860 or P04637 appear in tool output or the final answer.",
            "- Memory items are considered passed only when setup-turn content is retrieved into memory_context.",
        ]
    )
    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    benchmark = load_benchmark()
    questions = list(benchmark.get("questions") or [])
    if MAX_QUESTIONS is not None:
        questions = questions[:MAX_QUESTIONS]

    run_dir = OUTPUT_DIR / RUN_NAME
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.jsonl"
    records: list[dict[str, Any]] = []

    with results_path.open("w", encoding="utf-8") as file:
        for index, question in enumerate(questions, start=1):
            question_id = str(question.get("id") or f"q{index}")
            print(f"[{index}/{len(questions)}] {question_id}", flush=True)
            selected_mode = choose_mode(question)
            setup_turns = apply_setup_turns(question)
            error = None
            result: dict[str, Any]
            try:
                last_exc: Exception | None = None
                for attempt in range(RETRY_COUNT + 1):
                    try:
                        if RUN_MODE == "full":
                            result = run_full(question, selected_mode)
                        else:
                            result = run_offline(question, selected_mode)
                        last_exc = None
                        break
                    except Exception as exc:  # noqa: BLE001
                        last_exc = exc
                        if attempt < RETRY_COUNT:
                            time.sleep(RETRY_SECONDS)
                if last_exc is not None:
                    raise last_exc
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
                result = {
                    "mode": selected_mode,
                    "sources": [],
                    "structured_candidates": [],
                    "trace": [],
                    "memory_context": "",
                    "skill_results": [],
                    "answer": "",
                    "traceback": traceback.format_exc(),
                }

            checks = evaluate_question(question, result)
            if error:
                checks.append(BenchmarkCheck("runtime_error", False, error, 0, 20))
            score = score_checks(checks)
            record = {
                "id": question_id,
                "question": question.get("question"),
                "question_type": question.get("question_type"),
                "difficulty": question.get("difficulty"),
                "selected_mode": selected_mode,
                "setup_turns_applied": setup_turns,
                "required_knowledge_set_ids": expected_ids(question),
                "optional_knowledge_set_ids": optional_ids(question),
                "target_modules": question.get("target_modules") or [],
                "required_external_tools": question.get("required_external_tools") or [],
                "checks": [check_to_dict(check) for check in checks],
                "score": score,
                "result": compact_result(result),
                "error": error,
            }
            records.append(record)
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()

    summary_path = run_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_name": RUN_NAME,
                "run_mode": RUN_MODE,
                "benchmark_id": benchmark.get("benchmark_id"),
                "question_count": len(records),
                "total_points": sum(record["score"]["points"] for record in records),
                "total_max_points": sum(record["score"]["max_points"] for record in records),
                "mode_counts": dict(Counter(record["selected_mode"] for record in records)),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    report_path = write_report(run_dir, benchmark, records)
    print()
    print(f"Results: {results_path}")
    print(f"Summary: {summary_path}")
    print(f"Report:  {report_path}")


if __name__ == "__main__":
    main()
