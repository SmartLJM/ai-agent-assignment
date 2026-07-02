from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dynamic_orchestrator import DynamicPlanner, DynamicWorkflowExecutor, save_json
from flowchart_generator import generate_dynamic_flowcharts
from path_config import EVALUATION_DIR, PART_B_DIR, WORKFLOW_FILE


BENCHMARK_PATH = EVALUATION_DIR / "dynamic_orchestration_benchmark.json"


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _observed_agents(result: dict) -> set[str]:
    plan_agents = {node["agent"] for node in result["plan"]["generated_nodes"]}
    trace_agents = {entry["agent"] for entry in result["trace"]}
    decision_agents = {
        str(decision.get("fallback_agent"))
        for decision in result["decision_trace"]
        if decision.get("fallback_agent")
    }
    output_agents = {
        str(entry.get("output", {}).get("fallback_agent"))
        for entry in result["trace"]
        if entry.get("output", {}).get("fallback_agent")
    }
    return plan_agents | trace_agents | decision_agents | output_agents


def _observed_features(result: dict) -> set[str]:
    decisions = result["decision_trace"]
    generated_modes = {node["mode"] for node in result["plan"]["generated_nodes"]}
    trace_modes = {entry["mode"] for entry in result["trace"]}
    agents = _observed_agents(result)
    features = set()

    if any(decision.get("decision_point") == "auto_plan_generation" for decision in decisions):
        features.add("auto_plan_generation")
    if decisions:
        features.add("decision_trace")
    if "parallel" in generated_modes or "parallel" in trace_modes:
        features.add("parallel_sub_agents")
    if "quality-validator" in agents or any(
        decision.get("decision_point") in {"quality_gate", "mask_quality_check"} for decision in decisions
    ):
        features.add("runtime_quality_gate")
    if result.get("runtime_adjustments") or any(decision.get("new_nodes_added") for decision in decisions):
        features.add("runtime_adjustment")
    if result.get("retry_count", 0) >= 1 or any(decision.get("retry_reason") for decision in decisions):
        features.add("retry_loop")
    if result.get("recovery_count", 0) >= 1 or any(
        decision.get("decision_point") == "error_recovery"
        and decision.get("decision") == "switch_to_fallback_agent"
        for decision in decisions
    ):
        features.add("error_recovery")
    return features


def _summarize_case(item: dict, result: dict) -> dict:
    agents = _observed_agents(result)
    features = _observed_features(result)
    expected_agents = set(item.get("expected_agents", []))
    expected_features = set(item.get("expected_dynamic_features", []))
    missing_agents = sorted(expected_agents - agents)
    missing_features = sorted(expected_features - features)
    passed = (
        result["status"] in {"success", "recovered"}
        and result["plan"]["intent"] == item.get("expected_intent")
        and not missing_agents
        and not missing_features
    )
    return {
        "id": item["id"],
        "question": item["question"],
        "passed": passed,
        "expected_intent": item.get("expected_intent"),
        "observed_intent": result["plan"]["intent"],
        "status": result["status"],
        "expected_agents": sorted(expected_agents),
        "observed_agents": sorted(agents),
        "missing_agents": missing_agents,
        "expected_dynamic_features": sorted(expected_features),
        "observed_dynamic_features": sorted(features),
        "missing_dynamic_features": missing_features,
        "retry_count": result.get("retry_count", 0),
        "recovery_count": result.get("recovery_count", 0),
        "runtime_adjustments": result.get("runtime_adjustments", []),
    }


def _trace_record(item: dict, result: dict) -> dict:
    return {
        "id": item["id"],
        "question": item["question"],
        "plan": result["plan"],
        "status": result["status"],
        "elapsed_ms": result["elapsed_ms"],
        "trace": result["trace"],
        "decision_trace": result["decision_trace"],
        "runtime_adjustments": result["runtime_adjustments"],
        "retry_count": result["retry_count"],
        "recovery_count": result["recovery_count"],
        "final_report": result["final_report"],
    }


def _plan_comparison(dynamic_records: list[dict]) -> dict:
    workflows = _read_json(WORKFLOW_FILE, {"workflows": []})
    static_workflow = next(
        (workflow for workflow in workflows.get("workflows", []) if workflow.get("id") == "parallel_case_analysis"),
        workflows.get("workflows", [{}])[0] if workflows.get("workflows") else {},
    )
    dynamic = next(
        (record for record in dynamic_records if record.get("runtime_adjustments")),
        next((record for record in dynamic_records if record["id"] == "dyn_005"), dynamic_records[0]),
    )
    generated_nodes = [
        {
            "node_id": node["node_id"],
            "agent": node["agent"],
            "mode": node["mode"],
            "reason": node["reason"],
        }
        for node in dynamic["plan"]["generated_nodes"]
    ]
    return {
        "comparison_target": "static template vs runtime generated plan",
        "static_baseline": {
            "workflow_id": static_workflow.get("id"),
            "source_file": "workflows.json",
            "selection_method": "predefined template",
            "supported_modes": workflows.get("supported_modes", []),
            "node_count": len(static_workflow.get("nodes", [])),
        },
        "dynamic_plan": {
            "benchmark_id": dynamic["id"],
            "source_file": "agent_registry.json + dynamic_orchestrator.py",
            "selection_method": "query intent + complexity + capability registry",
            "intent": dynamic["plan"]["intent"],
            "complexity_score": dynamic["plan"]["complexity_score"],
            "generated_node_count": len(generated_nodes),
            "generated_nodes": generated_nodes,
            "runtime_adjustments": dynamic["runtime_adjustments"],
        },
        "why_this_is_dynamic": [
            "The node list is generated at runtime from query signals.",
            "The quality gate can insert retry or review nodes after intermediate outputs are observed.",
            "The recovery manager can switch to fallback agents when a selected agent fails.",
            "Every decision records observation, reason, action, and affected nodes.",
        ],
    }


def _recovery_case(dynamic_records: list[dict]) -> dict:
    for record in dynamic_records:
        recovery_decisions = [
            decision
            for decision in record["decision_trace"]
            if decision.get("decision_point") == "error_recovery"
            and decision.get("decision") == "switch_to_fallback_agent"
        ]
        if not recovery_decisions:
            continue
        first = recovery_decisions[0]
        return {
            "benchmark_id": record["id"],
            "question": record["question"],
            "failed_agent": first.get("failed_agent"),
            "error_type": first.get("error_type"),
            "recovery_action": first.get("decision"),
            "fallback_agent": first.get("fallback_agent"),
            "new_nodes_added": first.get("new_nodes_added", []),
            "status": "recovered" if record["recovery_count"] else record["status"],
            "final_output_available": bool(record.get("final_report")),
            "decision_trace_excerpt": recovery_decisions,
        }
    return {
        "status": "not-triggered",
        "final_output_available": False,
        "message": "No recovery case was observed in the benchmark run.",
    }


def _update_evaluation_summary(summary: dict) -> dict:
    summary_path = EVALUATION_DIR / "evaluation_summary.json"
    existing = _read_json(summary_path, {})
    existing.update(
        {
            "dynamic_orchestration_questions": summary["total_questions"],
            "dynamic_orchestration_passed": summary["passed"],
            "dynamic_auto_generated_plans": summary["auto_generated_plans"],
            "dynamic_runtime_adjustment_plans": summary["plans_with_runtime_adjustment"],
            "dynamic_retry_plans": summary["plans_with_retry"],
            "dynamic_recovery_plans": summary["plans_with_error_recovery"],
            "dynamic_decision_trace_records": summary["decision_trace_records"],
        }
    )
    save_json(summary_path, existing)
    return existing


def run_dynamic_orchestration(refresh_rubric: bool = True) -> dict:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    benchmark = _read_json(BENCHMARK_PATH, [])
    if not benchmark:
        raise RuntimeError(f"未找到动态编排评测文件：{BENCHMARK_PATH}")

    planner = DynamicPlanner()
    executor = DynamicWorkflowExecutor()
    results = []
    trace_records = []

    for item in benchmark:
        context = dict(item.get("context", {}))
        plan = planner.plan(item["question"], context)
        result = executor.execute(plan, context)
        results.append(_summarize_case(item, result))
        trace_records.append(_trace_record(item, result))

    passed = sum(item["passed"] for item in results)
    flowcharts = generate_dynamic_flowcharts()
    summary = {
        "module": "advanced-dynamic-orchestration",
        "level": "Lv.3",
        "total_questions": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4),
        "auto_generated_plans": sum("auto_plan_generation" in item["observed_dynamic_features"] for item in results),
        "plans_with_runtime_adjustment": sum(bool(item["runtime_adjustments"]) for item in results),
        "plans_with_retry": sum(item["retry_count"] > 0 for item in results),
        "plans_with_error_recovery": sum(item["recovery_count"] > 0 for item in results),
        "decision_trace_records": len(trace_records),
        "flowcharts": flowcharts["files"],
        "results": results,
    }

    save_json(EVALUATION_DIR / "dynamic_orchestration_results.json", summary)
    save_json(EVALUATION_DIR / "dynamic_decision_traces.json", trace_records)
    save_json(EVALUATION_DIR / "dynamic_plan_comparison.json", _plan_comparison(trace_records))
    save_json(EVALUATION_DIR / "dynamic_recovery_case.json", _recovery_case(trace_records))
    updated_summary = _update_evaluation_summary(summary)

    if refresh_rubric:
        try:
            from evidence_builder import build_rubric_evidence

            build_rubric_evidence()
        except Exception as exc:
            print(f"rubric_evidence.json 未自动刷新：{type(exc).__name__}: {exc}")

    return {
        "summary": summary,
        "updated_evaluation_summary": updated_summary,
        "passed": passed,
        "total": len(results),
    }


def main() -> int:
    output = run_dynamic_orchestration(refresh_rubric=True)
    summary = output["summary"]
    updated_summary = output["updated_evaluation_summary"]

    print(
        json.dumps(
            {
                "dynamic_orchestration": {
                    "passed": f"{output['passed']}/{output['total']}",
                    "runtime_adjustment_plans": summary["plans_with_runtime_adjustment"],
                    "retry_plans": summary["plans_with_retry"],
                    "recovery_plans": summary["plans_with_error_recovery"],
                    "decision_trace_records": summary["decision_trace_records"],
                },
                "updated_evaluation_summary": {
                    "dynamic_orchestration_questions": updated_summary.get("dynamic_orchestration_questions"),
                    "dynamic_orchestration_passed": updated_summary.get("dynamic_orchestration_passed"),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
