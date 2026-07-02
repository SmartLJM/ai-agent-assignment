from __future__ import annotations

import json
import io
import unittest
from pathlib import Path

from flowchart_generator import generate_flowcharts
from multimodal_kb import MultiModalKnowledgeBase
from path_config import DEFAULT_NPC_DATASET_DIR, EVALUATION_DIR, PART_B_DIR
from segmentation_visualizer import list_available_cases
from workflow_engine import WorkflowEngine


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def evaluate_multimodal(kb: MultiModalKnowledgeBase) -> dict:
    questions = json.loads((EVALUATION_DIR / "multimodal_benchmark.json").read_text(encoding="utf-8"))
    results = []
    for item in questions:
        evidence = []
        missing = []
        for modality in item["expected_modalities"]:
            hits = kb.search(item["question"], top_k=2, modalities=[modality])
            if hits:
                evidence.extend(hits)
            else:
                missing.append(modality)
        results.append(
            {
                "id": item["id"],
                "passed": not missing,
                "expected_modalities": item["expected_modalities"],
                "missing_modalities": missing,
                "evidence_ids": [hit["record_id"] for hit in evidence],
            }
        )
    passed = sum(item["passed"] for item in results)
    return {"total": len(results), "passed": passed, "pass_rate": passed / len(results), "results": results}


def evaluate_document_extraction(kb: MultiModalKnowledgeBase, case_id: str) -> dict:
    table_record = next(
        record for record in kb.records
        if record.modality == "table" and record.metadata.get("case_id") == case_id
    )
    stats = table_record.metadata
    # A self-contained local webpage proves extraction without depending on external network access.
    tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZQmcAAAAASUVORK5CYII="
    html_path = EVALUATION_DIR / "multimodal_document_demo.html"
    html_path.write_text(
        f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>病例 {case_id} 多模态文档</title></head>
<body>
  <h1>病例 {case_id} 医学影像审查</h1>
  <p>该本地网页同时包含医学文本、影像和结构化统计表，用于验证多模态抽取能力。</p>
  <img src="data:image/png;base64,{tiny_png}" alt="病例 {case_id} 医学影像示意图">
  <table>
    <tr><th>case_id</th><th>shape</th><th>foreground_voxels</th><th>mask_ratio</th></tr>
    <tr><td>{case_id}</td><td>{stats['shape']}</td><td>{stats['mask_voxels']}</td><td>{stats['mask_ratio']}</td></tr>
  </table>
</body></html>
""",
        encoding="utf-8",
    )
    extracted = kb.ingest_html_document(html_path)
    counts = {
        modality: sum(record.modality == modality for record in extracted)
        for modality in ("text", "image", "table")
    }
    return {
        "source": html_path.relative_to(EVALUATION_DIR.parent).as_posix(),
        "extractor": "MultiModalKnowledgeBase.ingest_html_document",
        "counts": counts,
        "record_ids": [record.record_id for record in extracted],
        "passed": all(counts[modality] >= 1 for modality in ("text", "image", "table")),
    }


def evaluate_workflows(engine: WorkflowEngine, cases: list[str]) -> dict:
    sample_case = "036" if "036" in cases else cases[0]
    runs = [
        engine.run("submission_audit"),
        engine.run(
            "grounded_multimodal_qa",
            {"query": f"联合检索病例 {sample_case} 的影像、统计表和 U-Net 分割文献"},
        ),
        engine.run(
            "parallel_case_analysis",
            {"case_id": sample_case, "query": f"病例 {sample_case} 影像、统计表和 U-Net 文献"},
        ),
        engine.run(
            "conditional_case_review",
            {"case_id": sample_case, "mask_ratio_threshold": 0.05},
        ),
    ]
    return {
        "template_count": len(engine.list_workflows()),
        "supported_modes": list(engine.supported_modes),
        "runs": runs,
        "passed": sum(run["status"] == "success" for run in runs),
    }


def _run_cached(engine: WorkflowEngine, item: dict, cache: dict) -> dict:
    key = (item["workflow_id"], json.dumps(item.get("inputs", {}), sort_keys=True, ensure_ascii=False))
    if key not in cache:
        cache[key] = engine.run(item["workflow_id"], item.get("inputs", {}))
    return cache[key]


def evaluate_orchestration(engine: WorkflowEngine, flowcharts: dict) -> dict:
    items = json.loads((EVALUATION_DIR / "orchestration_benchmark.json").read_text(encoding="utf-8"))
    results = []
    cache = {}
    for item in items:
        assertion = item["assertion"]
        observed = None
        passed = False
        try:
            if assertion == "template_count_at_least_3":
                observed = len(engine.list_workflows())
                passed = observed >= 3
            elif assertion == "all_three_modes":
                observed = sorted(engine.supported_modes)
                passed = set(observed) == {"sequential", "parallel", "conditional"}
            elif assertion == "unknown_workflow_rejected":
                try:
                    engine.run("not-a-workflow")
                except KeyError as exc:
                    observed = str(exc)
                    passed = True
            elif assertion == "flowchart_generated":
                observed = flowcharts
                passed = bool(flowcharts["files"]) and set(flowcharts["supported_modes"]) == {
                    "sequential", "parallel", "conditional"
                }
            else:
                run = _run_cached(engine, item, cache)
                if assertion == "workflow_success":
                    observed = run["status"]
                    passed = observed == "success"
                elif assertion == "audit_data_transfer":
                    observed = sorted(run["result"])
                    passed = "submission_audit" in run["result"] and "audit_summary" in run["result"]
                elif assertion == "at_least_two_agents":
                    observed = sorted({entry["agent"] for entry in run["trace"] if entry["agent"] != "parallel-orchestrator"})
                    passed = len(observed) >= 2
                elif assertion == "at_least_three_parallel_agents":
                    observed = [entry["agent"] for entry in run["trace"] if entry["mode"] == "parallel" and entry["agent"] != "parallel-orchestrator"]
                    passed = run["status"] == "success" and len(set(observed)) >= 3
                elif assertion == "parallel_outputs_complete":
                    report = run["result"].get("case_report", {})
                    observed = sorted(report)
                    passed = run["status"] == "success" and report.get("parallel_outputs_complete") is True
                elif assertion == "selected_strategy":
                    observed = run["result"].get("review_result", {}).get("selected_strategy")
                    passed = run["status"] == "success" and observed == item["expected"]
                elif assertion == "missing_case_fails_safely":
                    observed = {
                        "status": run["status"],
                        "failed_steps": [entry["node_id"] for entry in run["trace"] if entry["status"] == "failed"],
                        "errors": [entry["output"].get("error") for entry in run["trace"] if entry["status"] == "failed"],
                    }
                    passed = run["status"] == "failed" and bool(observed["errors"])
        except Exception as exc:
            observed = {"unexpected_error": str(exc), "exception_type": type(exc).__name__}
            passed = False
        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "category": item["category"],
                "passed": passed,
                "observed": observed,
            }
        )
    passed = sum(item["passed"] for item in results)
    return {"total": len(results), "passed": passed, "pass_rate": passed / len(results), "results": results}


def evaluate_unit_tests() -> dict:
    stream = io.StringIO()
    suite = unittest.TestLoader().discover(str(PART_B_DIR / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    return {
        "total": result.testsRun,
        "passed": result.testsRun - failed - errors - skipped,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "successful": result.wasSuccessful(),
        "log": stream.getvalue().splitlines(),
    }


def main() -> int:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    cases = list_available_cases(DEFAULT_NPC_DATASET_DIR)
    if not cases:
        raise RuntimeError(f"未找到可用病例数据：{DEFAULT_NPC_DATASET_DIR}")

    kb = MultiModalKnowledgeBase(dataset_dir=DEFAULT_NPC_DATASET_DIR)
    kb.build(case_limit=len(cases))
    index_summary = kb.save(EVALUATION_DIR)
    multimodal = evaluate_multimodal(kb)
    dump(EVALUATION_DIR / "multimodal_demo_results.json", {"index": index_summary, **multimodal})

    sample_case = "036" if "036" in cases else cases[0]
    document_extraction = evaluate_document_extraction(kb, sample_case)
    dump(EVALUATION_DIR / "document_extraction_demo.json", document_extraction)
    engine = WorkflowEngine()
    workflows = evaluate_workflows(engine, cases)
    dump(EVALUATION_DIR / "workflow_demo_results.json", workflows)

    flowcharts = generate_flowcharts()
    orchestration = evaluate_orchestration(engine, flowcharts)
    dump(EVALUATION_DIR / "orchestration_benchmark_results.json", orchestration)
    unit_tests = evaluate_unit_tests()
    dump(EVALUATION_DIR / "unit_test_results.json", unit_tests)

    summary = {
        "runtime_mode": {
            "default": "local-only",
            "dashscope": "explicit-opt-in",
            "remote_html": "rejected",
        },
        "knowledge_records": index_summary["counts"],
        "multimodal_questions": multimodal["total"],
        "multimodal_passed": multimodal["passed"],
        "document_extraction": document_extraction["counts"],
        "document_extraction_passed": document_extraction["passed"],
        "workflow_templates": workflows["template_count"],
        "workflow_modes": workflows["supported_modes"],
        "workflow_demo_passed": workflows["passed"],
        "orchestration_questions": orchestration["total"],
        "orchestration_passed": orchestration["passed"],
        "flowchart_files": len(flowcharts["files"]),
        "unit_tests": unit_tests["total"],
        "unit_tests_passed": unit_tests["passed"],
    }
    dump(EVALUATION_DIR / "evaluation_summary.json", summary)
    try:
        from run_dynamic_orchestration_demo import run_dynamic_orchestration

        dynamic_output = run_dynamic_orchestration(refresh_rubric=False)
        summary = json.loads((EVALUATION_DIR / "evaluation_summary.json").read_text(encoding="utf-8"))
        summary["dynamic_orchestration_status"] = (
            f"{dynamic_output['passed']}/{dynamic_output['total']}"
        )
        dump(EVALUATION_DIR / "evaluation_summary.json", summary)
    except Exception as exc:
        summary["dynamic_orchestration_error"] = f"{type(exc).__name__}: {exc}"
        dump(EVALUATION_DIR / "evaluation_summary.json", summary)

    from evidence_builder import build_rubric_evidence

    build_rubric_evidence()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
