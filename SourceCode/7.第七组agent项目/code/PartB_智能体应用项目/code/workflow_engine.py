from __future__ import annotations

import json
import operator
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from multimodal_kb import MultiModalKnowledgeBase
from path_config import DEFAULT_NPC_DATASET_DIR, PROJECT_ROOT, WORKFLOW_FILE, iter_knowledge_asset_dirs
from segmentation_visualizer import load_case


StepFunction = Callable[[dict], dict]


@dataclass
class StepTrace:
    node_id: str
    agent: str
    mode: str
    status: str
    elapsed_ms: float
    input_keys: list[str]
    output: dict
    decision: dict | None = None


class WorkflowEngine:
    """JSON-configured static workflow engine supporting three orchestration modes."""

    STEP_TYPES = {"step", "parallel", "condition"}
    OPERATORS = {
        "eq": operator.eq,
        "ne": operator.ne,
        "gt": operator.gt,
        "gte": operator.ge,
        "lt": operator.lt,
        "lte": operator.le,
    }

    def __init__(self, workflow_file: str | Path = WORKFLOW_FILE):
        self.workflow_file = Path(workflow_file)
        self.config = json.loads(self.workflow_file.read_text(encoding="utf-8"))
        self.agent_roles = self.config.get("agent_roles", {})
        self.supported_modes = tuple(self.config.get("supported_modes", []))
        workflows = self.config.get("workflows", [])
        self.workflows = {item["id"]: item for item in workflows}
        self.registry: dict[str, StepFunction] = {
            "validate_submission": self._validate_submission,
            "summarize_audit": self._summarize_audit,
            "retrieve_multimodal": self._retrieve_multimodal,
            "analyze_retrieval": self._analyze_retrieval,
            "analyze_image": self._analyze_image,
            "analyze_mask": self._analyze_mask,
            "retrieve_case_evidence": self._retrieve_case_evidence,
            "compose_case_report": self._compose_case_report,
            "inspect_case_statistics": self._inspect_case_statistics,
            "review_large_foreground": self._review_large_foreground,
            "review_small_foreground": self._review_small_foreground,
        }
        self.validate_config()

    def validate_config(self) -> None:
        if len(self.workflows) < 3:
            raise ValueError("进阶静态编排至少需要 3 个工作流模板。")
        required_modes = {"sequential", "parallel", "conditional"}
        if not required_modes <= set(self.supported_modes):
            raise ValueError(f"缺少编排模式：{sorted(required_modes - set(self.supported_modes))}")
        for workflow in self.workflows.values():
            if workflow.get("mode") not in required_modes:
                raise ValueError(f"工作流 {workflow['id']} 的 mode 无效。")
            nodes = workflow.get("nodes")
            if not isinstance(nodes, list) or not nodes:
                raise ValueError(f"工作流 {workflow['id']} 没有可执行节点。")
            self._validate_nodes(nodes, workflow["id"])

    def _validate_nodes(self, nodes: list[dict], workflow_id: str) -> None:
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            if not node_id or node_type not in self.STEP_TYPES:
                raise ValueError(f"工作流 {workflow_id} 包含无效节点：{node}")
            if node_type == "step":
                action = node.get("action")
                agent = node.get("agent")
                if action not in self.registry:
                    raise ValueError(f"节点 {node_id} 包含未知 action：{action}")
                if agent not in self.agent_roles:
                    raise ValueError(f"节点 {node_id} 包含未知 Agent 角色：{agent}")
                if not isinstance(node.get("inputs", []), list) or not isinstance(node.get("outputs", []), list):
                    raise ValueError(f"节点 {node_id} 的 inputs/outputs 必须是数组。")
            elif node_type == "parallel":
                branches = node.get("branches")
                if not isinstance(branches, list) or len(branches) < 2:
                    raise ValueError(f"并行节点 {node_id} 至少需要两个分支。")
                self._validate_nodes(branches, workflow_id)
            else:
                condition = node.get("condition", {})
                if not condition.get("field") or condition.get("operator") not in self.OPERATORS:
                    raise ValueError(f"条件节点 {node_id} 缺少有效条件。")
                for branch_name in ("if_true", "if_false"):
                    branch = node.get(branch_name)
                    if not isinstance(branch, list) or not branch:
                        raise ValueError(f"条件节点 {node_id} 缺少 {branch_name} 分支。")
                    self._validate_nodes(branch, workflow_id)

    def list_workflows(self) -> list[dict]:
        return list(self.workflows.values())

    def describe_capabilities(self) -> dict:
        return {
            "template_count": len(self.workflows),
            "supported_modes": list(self.supported_modes),
            "agent_role_count": len(self.agent_roles),
            "agent_roles": self.agent_roles,
        }

    def run(self, workflow_id: str, inputs: dict | None = None) -> dict:
        if workflow_id not in self.workflows:
            raise KeyError(f"未知工作流：{workflow_id}")
        workflow = self.workflows[workflow_id]
        context = dict(inputs or {})
        trace: list[dict] = []
        started = time.perf_counter()
        success = self._execute_nodes(workflow["nodes"], context, trace)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "declared_mode": workflow["mode"],
            "status": "success" if success else "failed",
            "elapsed_ms": elapsed_ms,
            "trace": trace,
            "modes_used": sorted({item["mode"] for item in trace}),
            "result": context,
        }

    def _execute_nodes(self, nodes: list[dict], context: dict, trace: list[dict]) -> bool:
        for node in nodes:
            node_type = node["type"]
            if node_type == "step":
                success = self._execute_step(node, context, trace, mode="sequential")
            elif node_type == "parallel":
                success = self._execute_parallel(node, context, trace)
            else:
                success = self._execute_condition(node, context, trace)
            if not success:
                return False
        return True

    def _capture_step(self, node: dict, context: dict, mode: str) -> tuple[dict, dict, bool]:
        local_context = dict(context)
        local_context.update(node.get("params", {}))
        started = time.perf_counter()
        try:
            output = self.registry[node["action"]](local_context)
            if not isinstance(output, dict):
                raise TypeError(f"节点 {node['id']} 必须返回 dict。")
            status = "success"
            success = True
        except Exception as exc:
            output = {"error": str(exc), "exception_type": type(exc).__name__}
            status = "failed"
            success = False
        trace = asdict(
            StepTrace(
                node_id=node["id"],
                agent=node["agent"],
                mode=mode,
                status=status,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
                input_keys=sorted(local_context),
                output=output,
            )
        )
        return trace, output, success

    def _execute_step(self, node: dict, context: dict, trace: list[dict], mode: str) -> bool:
        item, output, success = self._capture_step(node, context, mode)
        trace.append(item)
        if success:
            context.update(output)
        return success

    def _execute_parallel(self, node: dict, context: dict, trace: list[dict]) -> bool:
        branches = node["branches"]
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=len(branches), thread_name_prefix="workflow-agent") as pool:
            futures = [pool.submit(self._capture_step, branch, dict(context), "parallel") for branch in branches]
            results = [future.result() for future in futures]

        branch_status = {}
        merged_output: dict = {}
        output_conflicts: list[str] = []
        all_success = True
        branch_traces = []
        for branch, (item, output, success) in zip(branches, results):
            branch_status[branch["id"]] = item["status"]
            branch_traces.append(item)
            all_success = all_success and success
            if success:
                duplicate = set(merged_output) & set(output)
                if duplicate:
                    output_conflicts.extend(sorted(duplicate))
                    all_success = False
                else:
                    merged_output.update(output)

        group_trace = asdict(
            StepTrace(
                node_id=node["id"],
                agent="parallel-orchestrator",
                mode="parallel",
                status="success" if all_success else "failed",
                elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
                input_keys=sorted(context),
                output={
                    "branches": branch_status,
                    "merged_keys": sorted(merged_output),
                    "output_conflicts": sorted(set(output_conflicts)),
                },
            )
        )
        trace.append(group_trace)
        trace.extend(branch_traces)
        context.update(merged_output)
        return all_success

    def _execute_condition(self, node: dict, context: dict, trace: list[dict]) -> bool:
        condition = node["condition"]
        actual = self._resolve_field(context, condition["field"])
        expected = context.get(
            condition.get("value_from", ""),
            condition.get("value", condition.get("default")),
        )
        decision = bool(self.OPERATORS[condition["operator"]](actual, expected))
        branch_name = "if_true" if decision else "if_false"
        trace.append(
            asdict(
                StepTrace(
                    node_id=node["id"],
                    agent="conditional-orchestrator",
                    mode="conditional",
                    status="success",
                    elapsed_ms=0.0,
                    input_keys=sorted(context),
                    output={"selected_branch": branch_name},
                    decision={
                        "field": condition["field"],
                        "operator": condition["operator"],
                        "actual": actual,
                        "expected": expected,
                        "result": decision,
                    },
                )
            )
        )
        return self._execute_nodes(node[branch_name], context, trace)

    @staticmethod
    def _resolve_field(context: dict, dotted_path: str):
        value = context
        for part in dotted_path.split("."):
            if not isinstance(value, dict) or part not in value:
                raise KeyError(f"条件字段不存在：{dotted_path}")
            value = value[part]
        return value

    @staticmethod
    def _dataset_dir(context: dict) -> str:
        return str(context.get("dataset_dir") or DEFAULT_NPC_DATASET_DIR)

    @staticmethod
    def _require_case_id(context: dict) -> str:
        case_id = str(context.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("该工作流需要 case_id。")
        return case_id

    def _retrieve_multimodal(self, context: dict) -> dict:
        query = str(context.get("query") or "医学图像分割的影像、统计表和文献证据")
        kb = MultiModalKnowledgeBase(dataset_dir=self._dataset_dir(context))
        kb.build()
        answer = kb.answer(query)
        counts = {
            modality: sum(record.modality == modality for record in kb.records)
            for modality in ("text", "image", "table")
        }
        return {"multimodal_answer": answer, "index_counts": counts}

    @staticmethod
    def _analyze_retrieval(context: dict) -> dict:
        answer = context.get("multimodal_answer") or {}
        evidence = answer.get("evidence", [])
        return {
            "retrieval_analysis": {
                "evidence_count": len(evidence),
                "modalities": sorted({item.get("modality") for item in evidence if item.get("modality")}),
                "has_local_evidence": bool(evidence),
                "evidence_ids": [item.get("record_id") for item in evidence],
            }
        }

    def _analyze_image(self, context: dict) -> dict:
        case_id = self._require_case_id(context)
        image, _ = load_case(case_id, self._dataset_dir(context))
        finite = image[np.isfinite(image)]
        return {
            "image_analysis": {
                "case_id": case_id,
                "shape": list(image.shape),
                "dtype": str(image.dtype),
                "mean": round(float(finite.mean()), 6),
                "std": round(float(finite.std()), 6),
                "min": round(float(finite.min()), 6),
                "max": round(float(finite.max()), 6),
            }
        }

    def _analyze_mask(self, context: dict) -> dict:
        case_id = self._require_case_id(context)
        _, mask = load_case(case_id, self._dataset_dir(context))
        foreground = mask > 0
        coords = np.argwhere(foreground)
        bbox = [*coords.min(axis=0).tolist(), *coords.max(axis=0).tolist()] if coords.size else []
        return {
            "mask_analysis": {
                "case_id": case_id,
                "shape": list(mask.shape),
                "labels": [int(value) for value in np.unique(mask)],
                "foreground_voxels": int(foreground.sum()),
                "mask_ratio": round(float(foreground.mean()), 6),
                "bbox": bbox,
            }
        }

    def _retrieve_case_evidence(self, context: dict) -> dict:
        case_id = self._require_case_id(context)
        query = str(context.get("query") or f"病例 {case_id} 的影像、统计表和 U-Net 分割文献")
        kb = MultiModalKnowledgeBase(dataset_dir=self._dataset_dir(context))
        kb.build()
        evidence = []
        for modality in ("image", "table", "text"):
            evidence.extend(kb.search(query, top_k=2, modalities=[modality]))
        return {
            "case_evidence": {
                "query": query,
                "evidence_count": len(evidence),
                "modalities": sorted({item["modality"] for item in evidence}),
                "evidence_ids": [item["record_id"] for item in evidence],
            }
        }

    @staticmethod
    def _compose_case_report(context: dict) -> dict:
        required = ("image_analysis", "mask_analysis", "case_evidence")
        missing = [key for key in required if key not in context]
        if missing:
            raise ValueError(f"并行结果缺失：{missing}")
        return {
            "case_report": {
                "case_id": context["image_analysis"]["case_id"],
                "image": context["image_analysis"],
                "ground_truth_mask": context["mask_analysis"],
                "evidence": context["case_evidence"],
                "parallel_outputs_complete": True,
            }
        }

    def _inspect_case_statistics(self, context: dict) -> dict:
        return {"case_statistics": self._analyze_mask(context)["mask_analysis"]}

    @staticmethod
    def _review_large_foreground(context: dict) -> dict:
        stats = context["case_statistics"]
        return {
            "review_result": {
                "selected_strategy": "large-foreground-review",
                "reason": f"mask_ratio={stats['mask_ratio']} 高于阈值，执行完整三视图与边界审查。",
                "checks": ["axial", "coronal", "sagittal", "bbox"],
            }
        }

    @staticmethod
    def _review_small_foreground(context: dict) -> dict:
        stats = context["case_statistics"]
        return {
            "review_result": {
                "selected_strategy": "small-foreground-review",
                "reason": f"mask_ratio={stats['mask_ratio']} 未超过阈值，优先检查小目标可见性。",
                "checks": ["foreground-slice", "bbox", "label-presence"],
            }
        }

    @staticmethod
    def _validate_submission(context: dict) -> dict:
        root = Path(context.get("project_root") or PROJECT_ROOT)
        data_dir = root / "PartA_知识资产与评测基准" / "data"
        benchmark_path = root / "PartA_知识资产与评测基准" / "benchmark" / "qa_dataset.json"
        assets = iter_knowledge_asset_dirs(data_dir)
        valid_assets = []
        direct_sources = 0
        fallback_sources = 0
        fallback_source_titles = []
        content_by_id = {}
        for path in assets:
            content_path = path / "content" / "content.txt"
            keywords_path = path / "keywords.json"
            source_path = path / "source.json"
            if content_path.is_file() and keywords_path.is_file() and source_path.is_file():
                valid_assets.append(path)
                content_by_id[path.name] = content_path.read_text(encoding="utf-8", errors="ignore")
                source = json.loads(source_path.read_text(encoding="utf-8"))
                if source.get("url_kind") == "title-search-fallback":
                    fallback_sources += 1
                    fallback_source_titles.append(source.get("title", path.name))
                elif str(source.get("url", "")).startswith(("http://", "https://")):
                    direct_sources += 1

        questions = json.loads(benchmark_path.read_text(encoding="utf-8"))
        required = {"id", "question", "type", "difficulty", "answer", "sources", "theme"}
        valid_questions = [item for item in questions if isinstance(item, dict) and required <= set(item)]
        linked_questions = 0
        for item in valid_questions:
            sources = item.get("sources") or []
            if sources and all(source.get("knowledge_set_id") in content_by_id for source in sources):
                linked_questions += 1

        audit = {
            "asset_count": len(assets),
            "valid_asset_count": len(valid_assets),
            "direct_source_count": direct_sources,
            "fallback_source_count": fallback_sources,
            "fallback_source_titles": fallback_source_titles,
            "question_count": len(questions),
            "valid_question_count": len(valid_questions),
            "linked_question_count": linked_questions,
            "passed": (
                len(valid_assets) >= 20
                and len(valid_questions) >= 20
                and linked_questions == len(valid_questions)
            ),
        }
        return {"submission_audit": audit}

    @staticmethod
    def _summarize_audit(context: dict) -> dict:
        audit = context.get("submission_audit")
        if not audit:
            raise ValueError("缺少 submission_audit 输入。")
        return {
            "audit_summary": {
                "passed": audit["passed"],
                "score_evidence": {
                    "knowledge_assets": f"{audit['valid_asset_count']}/{audit['asset_count']}",
                    "benchmark_schema": f"{audit['valid_question_count']}/{audit['question_count']}",
                    "benchmark_links": f"{audit['linked_question_count']}/{audit['question_count']}",
                },
                "quality_warning": (
                    f"结构合规已通过；{audit['fallback_source_count']} 条 web-resource 来源仍为题名检索回退页，"
                    f"已标记为待人工复核：{audit.get('fallback_source_titles', [])}。"
                    if audit["fallback_source_count"]
                    else "所有来源均为直达 URL，无来源回退警告。"
                ),
            }
        }


if __name__ == "__main__":
    engine = WorkflowEngine()
    print(json.dumps(engine.run("submission_audit"), ensure_ascii=False, indent=2))
