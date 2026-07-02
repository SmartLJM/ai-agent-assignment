from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from model_adapters import MedSAMAdapter
from multimodal_kb import MultiModalKnowledgeBase
from path_config import DEFAULT_NPC_DATASET_DIR, EVALUATION_DIR, PART_B_DIR
from segmentation_visualizer import list_available_cases, load_case, render_case


@dataclass
class DynamicNode:
    node_id: str
    agent: str
    mode: str
    reason: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class DynamicPlan:
    plan_id: str
    query: str
    intent: str
    complexity_score: int
    complexity_level: str
    case_id: str | None
    generated_nodes: list[DynamicNode]
    generation_decisions: list[dict[str, Any]]
    expected_dynamic_features: list[str]


@dataclass
class NodeTrace:
    node_id: str
    agent: str
    mode: str
    status: str
    elapsed_ms: float
    input_keys: list[str]
    output: dict[str, Any]
    decision: dict[str, Any] | None = None


def _load_registry(path: str | Path | None = None) -> dict[str, dict]:
    registry_path = Path(path or (PART_B_DIR / "agent_registry.json"))
    return json.loads(registry_path.read_text(encoding="utf-8"))


def _case_id_from_query(query: str) -> str | None:
    match = re.search(r"(?:npc|case|病例)?[\s_-]*(\d{3})", query, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _mask_statistics(case_id: str, dataset_dir: str | Path = DEFAULT_NPC_DATASET_DIR) -> dict:
    image, mask = load_case(case_id, dataset_dir)
    foreground = mask > 0
    coords = np.argwhere(foreground)
    bbox = [*coords.min(axis=0).tolist(), *coords.max(axis=0).tolist()] if coords.size else []
    finite = image[np.isfinite(image)]
    return {
        "case_id": case_id,
        "shape": list(mask.shape),
        "labels": [int(value) for value in np.unique(mask)],
        "foreground_voxels": int(foreground.sum()),
        "foreground_ratio": round(float(foreground.mean()), 6),
        "bbox": bbox,
        "image_mean": round(float(finite.mean()), 6),
        "image_std": round(float(finite.std()), 6),
    }


class DynamicPlanner:
    """Generate a runtime workflow from query signals instead of selecting a template."""

    def __init__(self, registry_path: str | Path | None = None):
        self.registry = _load_registry(registry_path)
        self._counter = 0

    @staticmethod
    def _contains(query: str, values: tuple[str, ...]) -> bool:
        lowered = query.lower()
        return any(value in lowered for value in values)

    def analyze_intent(self, query: str) -> str:
        if self._contains(query, ("medsam", "predict", "prediction", "model")):
            return "segmentation_prediction_demo"
        if self._contains(query, ("compare", "difference", "evaluate", "比较", "评估")):
            return "comparative_analysis"
        if self._contains(query, ("case", "npc", "mask", "overlay", "bbox", "病例", "切片")):
            return "case_segmentation_analysis"
        if self._contains(query, ("evidence", "source", "paper", "citation", "local evidence", "文献", "证据", "来源")):
            return "grounded_qa"
        return "simple_qa"

    def estimate_complexity(self, query: str, case_id: str | None) -> tuple[int, str, list[dict]]:
        score = 0
        decisions = []

        def add(points: int, signal: str, reason: str) -> None:
            nonlocal score
            score += points
            decisions.append({"signal": signal, "points": points, "reason": reason})

        if self._contains(query, ("what is", "explain", "define", "什么", "解释")):
            add(1, "concept_explanation", "The query asks for a concept explanation.")
        if self._contains(query, ("evidence", "source", "paper", "citation", "local evidence", "文献", "证据", "来源")):
            add(2, "needs_local_evidence", "The query asks for grounded evidence.")
        if case_id:
            add(2, "case_id_detected", f"The query mentions case {case_id}.")
        if self._contains(query, ("image", "mask", "slice", "volume", "影像", "图像", "切片", "体素")):
            add(2, "image_or_mask_required", "The query needs image or mask processing.")
        if self._contains(query, ("overlay", "visual", "show", "显示", "可视化")):
            add(2, "visualization_required", "The query asks for overlay or visualization.")
        if self._contains(query, ("medsam", "predict", "prediction", "model")):
            add(2, "model_prediction_required", "The query asks for model prediction.")
        if self._contains(query, ("compare", "difference", "evaluate", "比较", "评估")):
            add(2, "comparison_required", "The query asks for comparison or evaluation.")
        if self._contains(query, ("invalid", "unavailable", "fallback", "recover", "不存在", "失败")):
            add(2, "recovery_likely", "The query likely needs recovery or fallback.")

        level = "simple" if score <= 2 else "medium" if score <= 5 else "complex"
        return score, level, decisions

    def _node(self, agent: str, mode: str, reason: str, suffix: str = "", **params: Any) -> DynamicNode:
        info = self.registry[agent]
        capability = info["capability"].replace("_", "-")
        node_id = f"{capability}{('-' + suffix) if suffix else ''}"
        return DynamicNode(
            node_id=node_id,
            agent=agent,
            mode=mode,
            reason=reason,
            inputs=list(info.get("inputs", [])),
            outputs=list(info.get("outputs", [])),
            params=params,
        )

    def plan(self, query: str, context: dict | None = None) -> DynamicPlan:
        context = dict(context or {})
        self._counter += 1
        case_id = context.get("case_id") or _case_id_from_query(query)
        intent = self.analyze_intent(query)
        complexity_score, complexity_level, decisions = self.estimate_complexity(query, case_id)
        nodes: list[DynamicNode] = []
        features = ["auto_plan_generation", "decision_trace"]

        if intent == "simple_qa":
            nodes.append(self._node("text-retriever", "sequential", "A concept query needs text evidence."))
            nodes.append(self._node("report-agent", "final", "Merge retrieved evidence into an answer."))
        elif intent == "grounded_qa":
            nodes.append(self._node("text-retriever", "sequential", "Grounded QA requires local text evidence."))
            nodes.append(self._node("quality-validator", "conditional", "Evidence must pass the quality gate."))
            nodes.append(self._node("report-agent", "final", "Generate a grounded final answer."))
            features.append("runtime_quality_gate")
        elif intent == "case_segmentation_analysis":
            nodes.extend(
                [
                    self._node("text-retriever", "parallel", "Case analysis needs literature evidence."),
                    self._node("image-agent", "parallel", "The query mentions a case image."),
                    self._node("mask-agent", "parallel", "The query needs segmentation mask statistics."),
                ]
            )
            if self._contains(query, ("overlay", "show", "visual", "显示", "可视化")):
                nodes.append(self._node("overlay-visualizer", "after_parallel", "The query asks for mask overlay."))
            nodes.append(self._node("quality-validator", "conditional", "Intermediate case outputs must be checked."))
            nodes.append(self._node("report-agent", "final", "Generate the final case report."))
            features.extend(["parallel_sub_agents", "runtime_quality_gate"])
        elif intent == "comparative_analysis":
            nodes.extend(
                [
                    self._node("text-retriever", "parallel", "Comparison needs method evidence."),
                    self._node("table-statistics-agent", "parallel", "Comparison needs structured mask statistics."),
                    self._node("multi-case-retriever", "parallel", "The query compares more than one case or evidence source."),
                    self._node("quality-validator", "conditional", "Comparative outputs must be validated."),
                    self._node("report-agent", "final", "Merge comparison evidence into a report."),
                ]
            )
            features.extend(["parallel_sub_agents", "runtime_quality_gate"])
        else:
            nodes.append(self._node("image-agent", "sequential", "Prediction demo needs the case image."))
            nodes.append(self._node("medsam-agent", "sequential", "The query asks for MedSAM/model prediction."))
            nodes.append(self._node("quality-validator", "conditional", "Prediction output or fallback must be validated."))
            nodes.append(self._node("report-agent", "final", "Report prediction status and fallback evidence."))
            features.extend(["runtime_quality_gate", "error_recovery"])

        plan_id = f"dynamic_plan_{self._counter:03d}"
        decisions.insert(
            0,
            {
                "decision_point": "auto_plan_generation",
                "decision": "generate_runtime_workflow",
                "reason": "The system builds nodes from query signals and the agent registry, not from workflows.json.",
                "intent": intent,
                "case_id": case_id,
                "generated_nodes": [asdict(node) for node in nodes],
            },
        )
        return DynamicPlan(
            plan_id=plan_id,
            query=query,
            intent=intent,
            complexity_score=complexity_score,
            complexity_level=complexity_level,
            case_id=case_id,
            generated_nodes=nodes,
            generation_decisions=decisions,
            expected_dynamic_features=list(dict.fromkeys(features)),
        )


class RecoveryManager:
    """Convert failures into fallback nodes instead of terminating the workflow."""

    def __init__(self, registry: dict[str, dict]):
        self.registry = registry

    def recover(self, node: DynamicNode, error: dict, context: dict) -> tuple[DynamicNode | None, dict]:
        fallback_agent = self.registry.get(node.agent, {}).get("fallback")
        error_text = str(error.get("error", ""))
        if "找不到病例" in error_text or "case" in error_text.lower() or "病例" in error_text:
            fallback_agent = "case-metadata-agent"
        if node.agent == "medsam-agent":
            fallback_agent = "ground-truth-overlay-agent"
        if not fallback_agent:
            return None, {
                "decision_point": "error_recovery",
                "failed_agent": node.agent,
                "decision": "no_fallback_available",
                "reason": "The agent registry does not define a fallback.",
                "observed_result": error,
            }
        fallback = DynamicNode(
            node_id=f"fallback-{fallback_agent}",
            agent=fallback_agent,
            mode="recovery",
            reason=f"Recover from {node.agent} failure using {fallback_agent}.",
            inputs=list(self.registry.get(fallback_agent, {}).get("inputs", [])),
            outputs=list(self.registry.get(fallback_agent, {}).get("outputs", [])),
        )
        decision = {
            "decision_point": "error_recovery",
            "failed_agent": node.agent,
            "error_type": error.get("exception_type", "RuntimeError"),
            "decision": "switch_to_fallback_agent",
            "reason": f"{node.agent} failed, so RecoveryManager selected {fallback_agent}.",
            "fallback_agent": fallback_agent,
            "observed_result": error,
            "new_nodes_added": [fallback.node_id],
        }
        return fallback, decision


class QualityGate:
    """Inspect intermediate context and add retry/review nodes when needed."""

    def inspect(self, context: dict) -> tuple[dict, list[DynamicNode], dict | None]:
        text_evidence = context.get("text_evidence", [])
        mask_statistics = context.get("mask_statistics") or {}
        retry_count = int(context.get("retry_count", 0))
        added: list[DynamicNode] = []
        report = {
            "text_evidence_count": len(text_evidence),
            "retry_count": retry_count,
            "mask_foreground_ratio": mask_statistics.get("foreground_ratio"),
            "prediction_status": context.get("prediction_status"),
        }

        if context.get("requires_grounded_evidence") and len(text_evidence) < 2 and retry_count < 1:
            added = [
                DynamicNode(
                    node_id="rewrite-query-for-retry",
                    agent="query-rewriter",
                    mode="retry",
                    reason="Only one evidence item was retrieved; rewrite the query and retry.",
                    inputs=["query", "quality_report"],
                    outputs=["query", "rewrite_reason"],
                ),
                DynamicNode(
                    node_id="retrieve-text-evidence-retry",
                    agent="text-retriever",
                    mode="retry",
                    reason="Run text retrieval again with the rewritten query.",
                    inputs=["query"],
                    outputs=["text_evidence"],
                    params={"retry": True},
                ),
                DynamicNode(
                    node_id="validate-quality-after-retry",
                    agent="quality-validator",
                    mode="conditional",
                    reason="Validate evidence after retry.",
                    inputs=["context"],
                    outputs=["quality_report"],
                ),
            ]
            decision = {
                "decision_point": "quality_gate",
                "observed_result": report,
                "decision": "add_retry_nodes",
                "reason": "Fewer than two text evidence items were retrieved for grounded QA.",
                "new_nodes_added": [node.node_id for node in added],
                "retry_count": retry_count + 1,
                "retry_reason": "insufficient_evidence",
                "strategy_switch": "query_rewrite",
            }
            return report | {"passed": False}, added, decision

        ratio = mask_statistics.get("foreground_ratio")
        if isinstance(ratio, (int, float)) and not context.get("target_review"):
            if ratio < 0.005:
                added = [
                    DynamicNode(
                        node_id="small-target-review",
                        agent="small-target-review-agent",
                        mode="conditional",
                        reason="The mask foreground ratio is very small.",
                        inputs=["mask_statistics"],
                        outputs=["target_review"],
                    )
                ]
                decision = {
                    "decision_point": "mask_quality_check",
                    "observed_result": {"foreground_ratio": ratio},
                    "decision": "add_small_target_review_agent",
                    "reason": "Small foreground masks need visibility and label checks.",
                    "new_nodes_added": [node.node_id for node in added],
                }
                return report | {"passed": False}, added, decision
            if ratio > 0.05:
                added = [
                    DynamicNode(
                        node_id="large-region-review",
                        agent="large-region-review-agent",
                        mode="conditional",
                        reason="The mask foreground ratio is large.",
                        inputs=["mask_statistics"],
                        outputs=["target_review"],
                    )
                ]
                decision = {
                    "decision_point": "mask_quality_check",
                    "observed_result": {"foreground_ratio": ratio},
                    "decision": "add_large_region_review_agent",
                    "reason": "Large foreground masks need multi-view and bbox review.",
                    "new_nodes_added": [node.node_id for node in added],
                }
                return report | {"passed": False}, added, decision

        return report | {"passed": True}, [], {
            "decision_point": "quality_gate",
            "observed_result": report,
            "decision": "pass",
            "reason": "Intermediate outputs satisfy the current quality rules.",
            "new_nodes_added": [],
        }


class DynamicWorkflowExecutor:
    """Execute generated nodes, dynamically inserting retry/review/fallback nodes."""

    def __init__(self, registry_path: str | Path | None = None, dataset_dir: str | Path = DEFAULT_NPC_DATASET_DIR):
        self.registry = _load_registry(registry_path)
        self.dataset_dir = Path(dataset_dir)
        self.recovery = RecoveryManager(self.registry)
        self.quality_gate = QualityGate()

    def execute(self, plan: DynamicPlan, context: dict | None = None) -> dict:
        context = dict(context or {})
        context.update({
            "query": plan.query,
            "original_query": plan.query,
            "intent": plan.intent,
            "case_id": context.get("case_id") or plan.case_id,
            "dataset_dir": str(context.get("dataset_dir") or self.dataset_dir),
            "requires_grounded_evidence": plan.intent in {"grounded_qa", "case_segmentation_analysis", "comparative_analysis"},
        })
        trace: list[dict] = []
        decisions: list[dict] = list(plan.generation_decisions)
        runtime_adjustments: list[dict] = []
        nodes = list(plan.generated_nodes)
        started = time.perf_counter()
        index = 0
        status = "success"

        while index < len(nodes):
            node = nodes[index]
            if node.mode == "parallel":
                group = []
                while index < len(nodes) and nodes[index].mode == "parallel":
                    group.append(nodes[index])
                    index += 1
                group_results = self._execute_parallel(group, context)
                trace.extend(group_results["trace"])
                decisions.extend(group_results["decisions"])
                runtime_adjustments.extend(group_results["runtime_adjustments"])
                if group_results["status"] == "failed":
                    status = "failed"
                    break
                continue

            result = self._execute_node(node, context)
            trace.append(result["trace"])
            decisions.extend(result["decisions"])
            runtime_adjustments.extend(result["runtime_adjustments"])
            if result["status"] == "failed":
                status = "failed"
                break
            if result["new_nodes"]:
                nodes[index + 1:index + 1] = result["new_nodes"]
            index += 1

        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        retry_count = int(context.get("retry_count", 0))
        recovery_count = sum(1 for item in decisions if item.get("decision_point") == "error_recovery" and item.get("decision") == "switch_to_fallback_agent")
        if status == "failed" and recovery_count:
            status = "recovered"
        return {
            "plan": {
                **asdict(plan),
                "generated_nodes": [asdict(node) for node in nodes],
            },
            "status": status,
            "elapsed_ms": elapsed_ms,
            "trace": trace,
            "decision_trace": decisions,
            "runtime_adjustments": runtime_adjustments,
            "retry_count": retry_count,
            "recovery_count": recovery_count,
            "final_report": context.get("final_report"),
            "context_keys": sorted(context),
        }

    def _execute_parallel(self, nodes: list[DynamicNode], context: dict) -> dict:
        with ThreadPoolExecutor(max_workers=len(nodes), thread_name_prefix="dynamic-agent") as pool:
            futures = [pool.submit(self._execute_node, node, dict(context)) for node in nodes]
            results = [future.result() for future in futures]
        merged = {}
        trace = []
        decisions = []
        runtime_adjustments = []
        status = "success"
        for result in results:
            trace.append(result["trace"])
            decisions.extend(result["decisions"])
            runtime_adjustments.extend(result["runtime_adjustments"])
            if result["status"] == "failed":
                status = "failed"
            merged.update(result["output"])
        context.update(merged)
        return {
            "status": status,
            "trace": trace,
            "decisions": decisions,
            "runtime_adjustments": runtime_adjustments,
        }

    def _execute_node(self, node: DynamicNode, context: dict) -> dict:
        started = time.perf_counter()
        decisions = []
        runtime_adjustments = []
        new_nodes: list[DynamicNode] = []
        try:
            output = self._run_agent(node, context)
            status = "success"
        except Exception as exc:
            output = {"error": str(exc), "exception_type": type(exc).__name__}
            fallback, decision = self.recovery.recover(node, output, context)
            decisions.append(decision)
            if fallback:
                fallback_result = self._execute_node(fallback, context)
                decisions.extend(fallback_result["decisions"])
                runtime_adjustments.append({"source_node": node.node_id, "new_nodes_added": [fallback.node_id]})
                fallback_output = fallback_result["output"]
                output = {
                    **fallback_output,
                    "failed_agent": node.agent,
                    "error": output,
                    "fallback_agent": fallback.agent,
                    "fallback_output": fallback_output,
                    "recovered": fallback_result["status"] in {"success", "recovered"},
                }
                status = "success" if output["recovered"] else "failed"
            else:
                status = "failed"

        context.update(output if status == "success" else {})
        decision_for_trace = decisions[-1] if decisions else None
        trace = asdict(
            NodeTrace(
                node_id=node.node_id,
                agent=node.agent,
                mode=node.mode,
                status=status,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
                input_keys=sorted(context),
                output=output,
                decision=decision_for_trace,
            )
        )
        if status == "success" and node.agent == "quality-validator":
            quality_report = output.get("quality_report", {})
            quality_nodes = output.get("_new_nodes", [])
            quality_decision = output.get("_decision")
            if quality_decision:
                decisions.append(quality_decision)
            if quality_nodes:
                new_nodes = quality_nodes
                runtime_adjustments.append({"source_node": node.node_id, "new_nodes_added": [item.node_id for item in new_nodes]})
            trace["decision"] = quality_decision
            context["quality_report"] = quality_report
        return {
            "status": status,
            "trace": trace,
            "decisions": decisions,
            "runtime_adjustments": runtime_adjustments,
            "new_nodes": new_nodes,
            "output": output,
        }

    def _run_agent(self, node: DynamicNode, context: dict) -> dict:
        agent = node.agent
        if agent in {"text-retriever", "keyword-retriever"}:
            return self._retrieve_text(context, retry=bool(node.params.get("retry")), keyword_only=agent == "keyword-retriever")
        if agent == "query-rewriter":
            return self._rewrite_query(context)
        if agent == "image-agent":
            return self._image_summary(context)
        if agent == "case-metadata-agent":
            return self._case_metadata(context)
        if agent == "mask-agent":
            return self._mask_summary(context)
        if agent == "table-statistics-agent":
            return self._table_statistics(context)
        if agent == "multi-case-retriever":
            return self._multi_case_statistics(context)
        if agent == "overlay-visualizer":
            return self._overlay(context, "真实 mask")
        if agent == "ground-truth-overlay-agent":
            return self._overlay(context, "真实 mask") | {"prediction_status": "fallback_ground_truth_overlay"}
        if agent == "medsam-agent":
            return self._medsam_prediction(context)
        if agent == "quality-validator":
            report, added, decision = self.quality_gate.inspect(context)
            return {"quality_report": report, "_new_nodes": added, "_decision": decision}
        if agent == "small-target-review-agent":
            return {"target_review": {"strategy": "small-target-review", "checks": ["visibility", "label consistency", "slice-level review"]}}
        if agent == "large-region-review-agent":
            return {"target_review": {"strategy": "large-region-review", "checks": ["3-view review", "bbox sanity check", "volume ratio review"]}}
        if agent == "report-agent":
            return self._report(context)
        raise KeyError(f"Unknown dynamic agent: {agent}")

    def _kb(self) -> MultiModalKnowledgeBase:
        kb = MultiModalKnowledgeBase(dataset_dir=self.dataset_dir)
        kb.build(case_limit=len(list_available_cases(self.dataset_dir)))
        return kb

    def _retrieve_text(self, context: dict, retry: bool = False, keyword_only: bool = False) -> dict:
        query = context.get("query") or context.get("original_query", "")
        kb = self._kb()
        top_k = 3 if retry or keyword_only else 1 if context.get("force_insufficient_first_pass") else 3
        hits = kb.search(str(query), top_k=top_k, modalities=["text"])
        if keyword_only and not hits:
            hits = kb.search("medical image segmentation U-Net Dice", top_k=3, modalities=["text"])
        retry_count = int(context.get("retry_count", 0)) + (1 if retry else 0)
        return {
            "text_evidence": hits,
            "text_evidence_ids": [item["record_id"] for item in hits],
            "retry_count": retry_count,
            "retrieval_strategy": "query_rewrite_retry" if retry else "initial_keyword_scoring",
        }

    @staticmethod
    def _rewrite_query(context: dict) -> dict:
        query = str(context.get("original_query") or context.get("query") or "")
        rewritten = (
            f"{query} Dice score limitation small object segmentation "
            "Hausdorff distance boundary error medical image segmentation evaluation"
        )
        return {
            "query": rewritten,
            "rewrite_reason": "insufficient_evidence",
            "strategy_switch": "query_rewrite",
        }

    def _image_summary(self, context: dict) -> dict:
        case_id = self._require_case(context)
        image, _ = load_case(case_id, context.get("dataset_dir") or self.dataset_dir)
        finite = image[np.isfinite(image)]
        return {
            "image_summary": {
                "case_id": case_id,
                "shape": list(image.shape),
                "mean": round(float(finite.mean()), 6),
                "std": round(float(finite.std()), 6),
                "min": round(float(finite.min()), 6),
                "max": round(float(finite.max()), 6),
            }
        }

    def _mask_summary(self, context: dict) -> dict:
        case_id = self._require_case(context)
        stats = _mask_statistics(case_id, context.get("dataset_dir") or self.dataset_dir)
        return {"mask_statistics": stats}

    def _table_statistics(self, context: dict) -> dict:
        case_id = context.get("case_id")
        if case_id and case_id in list_available_cases(context.get("dataset_dir") or self.dataset_dir):
            return {"table_statistics": _mask_statistics(str(case_id), context.get("dataset_dir") or self.dataset_dir)}
        kb = self._kb()
        hits = kb.search(str(context.get("query") or "case statistics mask ratio"), top_k=2, modalities=["table"])
        return {"table_statistics": {"retrieved_tables": hits, "count": len(hits)}}

    def _multi_case_statistics(self, context: dict) -> dict:
        query = str(context.get("query") or "")
        case_ids = re.findall(r"\d{3}", query)
        if len(case_ids) < 2:
            case_ids = list_available_cases(context.get("dataset_dir") or self.dataset_dir)[:2]
        stats = []
        for case_id in case_ids[:3]:
            if case_id in list_available_cases(context.get("dataset_dir") or self.dataset_dir):
                stats.append(_mask_statistics(case_id, context.get("dataset_dir") or self.dataset_dir))
        return {"multi_case_statistics": stats}

    def _overlay(self, context: dict, mask_type: str) -> dict:
        case_id = self._require_case(context)
        rendered = render_case(
            case_id,
            axis=str(context.get("axis") or "axial"),
            index=context.get("slice_index", 31),
            mask_type=mask_type,
            dataset_dir=context.get("dataset_dir") or self.dataset_dir,
        )
        return {
            "overlay_result": {
                "case_id": case_id,
                "axis": "axial",
                "slice_index": rendered["index"],
                "overlay_available": True,
                "mask_statistics": rendered["mask_statistics"],
            },
            "mask_statistics": rendered["mask_statistics"],
        }

    def _medsam_prediction(self, context: dict) -> dict:
        if context.get("force_model_unavailable"):
            raise RuntimeError("model_unavailable: forced demo path for recovery benchmark")
        adapter = MedSAMAdapter()
        if not adapter.available():
            raise RuntimeError(f"model_unavailable: {adapter.last_error}")
        # The dynamic demo only validates orchestration; full prediction is exposed in web_ui.py.
        return {"prediction_status": "medsam_available", "prediction_mask": "ready_for_web_ui_slice_prediction"}

    def _case_metadata(self, context: dict) -> dict:
        requested_case_id = context.get("case_id")
        available = list_available_cases(context.get("dataset_dir") or self.dataset_dir)
        selected = available[0] if available else None
        if selected:
            context["case_id"] = selected
        return {
            "case_recovery": {
                "requested_case_id": requested_case_id,
                "available_cases": available[:10],
                "selected_fallback_case": selected,
            },
            "case_id": selected,
        }

    @staticmethod
    def _report(context: dict) -> dict:
        evidence = context.get("text_evidence", [])
        report = {
            "query": context.get("original_query"),
            "intent": context.get("intent"),
            "case_id": context.get("case_id"),
            "text_evidence_count": len(evidence),
            "text_evidence_ids": [item.get("record_id") for item in evidence],
            "has_image_summary": bool(context.get("image_summary")),
            "has_mask_statistics": bool(context.get("mask_statistics")),
            "has_overlay": bool(context.get("overlay_result")),
            "target_review": context.get("target_review"),
            "prediction_status": context.get("prediction_status"),
            "recovery": context.get("case_recovery"),
        }
        return {"final_report": report}

    @staticmethod
    def _require_case(context: dict) -> str:
        case_id = str(context.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("Dynamic workflow requires case_id for this agent.")
        return case_id


def save_json(path: str | Path, value: Any) -> None:
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_single_dynamic_query(query: str, context: dict | None = None) -> dict:
    planner = DynamicPlanner()
    plan = planner.plan(query, context)
    result = DynamicWorkflowExecutor().execute(plan, context)
    return result
