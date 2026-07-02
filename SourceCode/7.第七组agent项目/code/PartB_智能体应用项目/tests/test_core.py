from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from flowchart_generator import generate_flowcharts  # noqa: E402
from expert_qa_agent import MedicalExpertAgent  # noqa: E402
from multimodal_kb import MultiModalKnowledgeBase  # noqa: E402
from path_config import (  # noqa: E402
    BENCHMARK_FILE,
    DEFAULT_NPC_DATASET_DIR,
    KNOWLEDGE_BASE_DIR,
    iter_knowledge_asset_dirs,
)
from segmentation_visualizer import (  # noqa: E402
    clamp_slice_index,
    dice_score,
    iou_score,
    list_available_cases,
    normalize_axis,
)
from workflow_engine import WorkflowEngine  # noqa: E402


class SubmissionTests(unittest.TestCase):
    def test_official_asset_layout(self):
        assets = iter_knowledge_asset_dirs(KNOWLEDGE_BASE_DIR)
        self.assertGreaterEqual(len(assets), 20)
        for asset in assets:
            self.assertTrue((asset / "content").is_dir(), asset.name)
            self.assertTrue((asset / "keywords.json").is_file(), asset.name)
            self.assertTrue((asset / "source.json").is_file(), asset.name)

    def test_official_source_type_folders_exist(self):
        expected = {"01-academic", "02-textbook", "03-course"}
        observed = {path.name for path in KNOWLEDGE_BASE_DIR.iterdir() if path.is_dir()}
        self.assertTrue(expected <= observed)

    def test_official_benchmark_schema(self):
        questions = json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
        required = {"id", "question", "type", "difficulty", "answer", "sources", "theme"}
        self.assertGreaterEqual(len(questions), 20)
        self.assertEqual(len({item["id"] for item in questions}), len(questions))
        for item in questions:
            self.assertTrue(required <= set(item))

    def test_metrics(self):
        gt = np.array([[0, 1], [1, 0]], dtype=np.uint8)
        pred = np.array([[0, 1], [0, 0]], dtype=np.uint8)
        self.assertAlmostEqual(dice_score(pred, gt), 2 / 3)
        self.assertAlmostEqual(iou_score(pred, gt), 1 / 2)

    def test_empty_masks_are_a_perfect_match(self):
        empty = np.zeros((4, 4), dtype=np.uint8)
        self.assertEqual(dice_score(empty, empty), 1.0)
        self.assertEqual(iou_score(empty, empty), 1.0)

    def test_invalid_axis_and_slice_are_clamped(self):
        self.assertEqual(normalize_axis("not-an-axis"), "axial")
        self.assertEqual(clamp_slice_index((10, 12, 8), "axial", 99), 7)
        self.assertEqual(clamp_slice_index((10, 12, 8), "axial", -5), 0)

    def test_multimodal_index_counts(self):
        kb = MultiModalKnowledgeBase(dataset_dir=DEFAULT_NPC_DATASET_DIR)
        kb.build(case_limit=10)
        counts = {modality: sum(item.modality == modality for item in kb.records) for modality in ("text", "image", "table")}
        self.assertGreaterEqual(counts["text"], 10)
        self.assertGreaterEqual(counts["image"], 10)
        self.assertGreaterEqual(counts["table"], 10)

    def test_multimodal_empty_query_returns_no_evidence(self):
        kb = MultiModalKnowledgeBase(dataset_dir=DEFAULT_NPC_DATASET_DIR)
        result = kb.answer("")
        self.assertEqual(result["evidence"], [])

    def test_html_document_extracts_three_modalities(self):
        with tempfile.TemporaryDirectory() as directory:
            html_path = Path(directory) / "case.html"
            html_path.write_text(
                "<html><body><p>medical image text</p>"
                "<img src='case.png' alt='case image'>"
                "<table><tr><th>case</th><th>ratio</th></tr><tr><td>036</td><td>0.1</td></tr></table>"
                "</body></html>",
                encoding="utf-8",
            )
            kb = MultiModalKnowledgeBase(dataset_dir=DEFAULT_NPC_DATASET_DIR)
            records = kb.ingest_html_document(html_path)
            self.assertEqual({record.modality for record in records}, {"text", "image", "table"})

    def test_remote_html_document_is_rejected(self):
        kb = MultiModalKnowledgeBase(dataset_dir=DEFAULT_NPC_DATASET_DIR)
        with self.assertRaisesRegex(ValueError, "完全本地模式"):
            kb.ingest_html_document("https://example.com/remote.html")

    def test_dashscope_is_disabled_by_default_even_with_api_key(self):
        environment = {"ENABLE_DASHSCOPE": "0", "API_KEY": "test-key"}
        with patch.dict(os.environ, environment, clear=False):
            qa_agent = MedicalExpertAgent(KNOWLEDGE_BASE_DIR)
            self.assertFalse(qa_agent.dashscope_enabled)
            with patch.object(qa_agent, "_dashscope_answer") as cloud_answer:
                answer = qa_agent.answer_question("U-Net 医学图像分割")
                cloud_answer.assert_not_called()
            self.assertIn("本地证据", answer)

    def test_workflow_modes_and_templates(self):
        engine = WorkflowEngine()
        self.assertGreaterEqual(len(engine.list_workflows()), 3)
        self.assertEqual(set(engine.supported_modes), {"sequential", "parallel", "conditional"})

    def test_sequential_workflow_data_transfer(self):
        engine = WorkflowEngine()
        result = engine.run("submission_audit")
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["result"]["submission_audit"]["passed"])
        self.assertIn("audit_summary", result["result"])
        agents = [item["agent"] for item in result["trace"]]
        self.assertEqual(agents, ["compliance-agent", "evidence-agent"])

    def test_parallel_workflow_runs_three_agents_and_merges(self):
        result = WorkflowEngine().run(
            "parallel_case_analysis",
            {"case_id": "036", "query": "病例036影像、统计表和U-Net文献"},
        )
        self.assertEqual(result["status"], "success")
        parallel_agents = {
            item["agent"] for item in result["trace"]
            if item["mode"] == "parallel" and item["agent"] != "parallel-orchestrator"
        }
        self.assertEqual(parallel_agents, {"image-agent", "mask-agent", "case-retriever"})
        self.assertTrue(result["result"]["case_report"]["parallel_outputs_complete"])

    def test_conditional_workflow_selects_both_branches(self):
        engine = WorkflowEngine()
        large = engine.run("conditional_case_review", {"case_id": "036", "mask_ratio_threshold": 0.0})
        small = engine.run("conditional_case_review", {"case_id": "036", "mask_ratio_threshold": 1.0})
        self.assertEqual(large["result"]["review_result"]["selected_strategy"], "large-foreground-review")
        self.assertEqual(small["result"]["review_result"]["selected_strategy"], "small-foreground-review")
        self.assertTrue(any(item["mode"] == "conditional" for item in large["trace"]))

    def test_workflow_missing_required_input_returns_failed_trace(self):
        result = WorkflowEngine().run("parallel_case_analysis", {})
        self.assertEqual(result["status"], "failed")
        failures = [item for item in result["trace"] if item["status"] == "failed"]
        self.assertGreaterEqual(len(failures), 1)
        self.assertTrue(all("error" in item["output"] for item in failures if item["agent"] != "parallel-orchestrator"))

    def test_unknown_workflow_is_rejected(self):
        with self.assertRaises(KeyError):
            WorkflowEngine().run("unknown-workflow")

    def test_flowchart_evidence_is_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = generate_flowcharts(directory)
            self.assertEqual(set(manifest["supported_modes"]), {"sequential", "parallel", "conditional"})
            self.assertTrue((Path(directory) / "workflow_modes.svg").is_file())
            self.assertGreaterEqual(len(list(Path(directory).glob("*.mmd"))), 3)

    def test_demo_cases(self):
        self.assertGreaterEqual(len(list_available_cases(DEFAULT_NPC_DATASET_DIR)), 10)


if __name__ == "__main__":
    unittest.main()
