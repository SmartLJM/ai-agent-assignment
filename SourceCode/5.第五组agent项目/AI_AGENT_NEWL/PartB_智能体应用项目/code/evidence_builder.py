from __future__ import annotations

import json
import re
from pathlib import Path

from path_config import (
    BENCHMARK_FILE,
    EVALUATION_DIR,
    KNOWLEDGE_BASE_DIR,
    PART_B_DIR,
    PROJECT_ROOT,
    iter_knowledge_asset_dirs,
)


KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_QA_FIELDS = {"id", "question", "type", "difficulty", "answer", "sources", "theme"}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized(text: str) -> str:
    return re.sub(r"\s+", "", str(text)).lower()


def audit_assets() -> dict:
    assets = iter_knowledge_asset_dirs(KNOWLEDGE_BASE_DIR)
    valid_structure = 0
    nonempty_content = 0
    valid_keywords = 0
    urls = 0
    direct_urls = 0
    fallback_urls = 0
    academic_papers = 0
    academic_with_doi = 0
    source_kinds = {}
    content_by_id = {}
    issues = []
    for asset in assets:
        content_path = asset / "content" / "content.txt"
        keywords_path = asset / "keywords.json"
        source_path = asset / "source.json"
        if content_path.is_file() and keywords_path.is_file() and source_path.is_file():
            valid_structure += 1
        else:
            issues.append({"asset": asset.name, "issue": "missing-required-file"})
            continue

        content = content_path.read_text(encoding="utf-8", errors="ignore").strip()
        content_by_id[asset.name] = content
        nonempty_content += bool(content)
        keywords = _read_json(keywords_path)
        keyword_values = [keyword for values in keywords.values() for keyword in values] if isinstance(keywords, dict) else []
        if keyword_values and all(KEBAB_CASE.fullmatch(keyword) for keyword in keyword_values):
            valid_keywords += 1
        else:
            issues.append({"asset": asset.name, "issue": "invalid-keywords"})

        source = _read_json(source_path)
        source_type = source.get("type", "missing")
        source_kinds[source_type] = source_kinds.get(source_type, 0) + 1
        url = str(source.get("url", ""))
        urls += url.startswith(("http://", "https://"))
        if source.get("url_kind") == "title-search-fallback":
            fallback_urls += 1
        elif url.startswith(("http://", "https://")):
            direct_urls += 1
        if source_type == "academic-paper":
            academic_papers += 1
            academic_with_doi += bool(source.get("doi"))

    return {
        "asset_count": len(assets),
        "valid_structure": valid_structure,
        "nonempty_content": nonempty_content,
        "valid_keywords": valid_keywords,
        "url_count": urls,
        "direct_url_count": direct_urls,
        "fallback_url_count": fallback_urls,
        "academic_paper_count": academic_papers,
        "academic_papers_with_doi": academic_with_doi,
        "source_types": source_kinds,
        "issues": issues,
        "content_by_id": content_by_id,
    }


def audit_benchmark(content_by_id: dict[str, str]) -> dict:
    questions = _read_json(BENCHMARK_FILE)
    valid_schema = 0
    linked_sources = 0
    quoted_evidence_matches = 0
    valid_theme = 0
    all_ids = []
    issues = []
    for item in questions:
        question_id = item.get("id", "missing") if isinstance(item, dict) else "invalid"
        if not isinstance(item, dict) or not REQUIRED_QA_FIELDS <= set(item):
            issues.append({"id": question_id, "issue": "missing-required-field"})
            continue
        valid_schema += 1
        all_ids.append(item["id"])
        theme = item.get("theme")
        theme_is_valid = theme == "medical-image-segmentation"
        if isinstance(theme, list):
            theme_is_valid = any(
                isinstance(entry, dict) and "medical-image-segmentation" in entry
                for entry in theme
            )
        valid_theme += theme_is_valid
        sources = item.get("sources") or []
        source_ids = [source.get("knowledge_set_id") for source in sources]
        if sources and all(source_id in content_by_id for source_id in source_ids):
            linked_sources += 1
        else:
            issues.append({"id": item["id"], "issue": "unlinked-source"})
        matches = True
        for source in sources:
            source_id = source.get("knowledge_set_id")
            quote = source.get("original_text", "")
            if not source_id or source_id not in content_by_id or not quote:
                matches = False
                break
            if _normalized(quote) not in _normalized(content_by_id[source_id]):
                matches = False
                break
        if matches and sources:
            quoted_evidence_matches += 1
        else:
            issues.append({"id": item["id"], "issue": "quoted-evidence-not-found"})

    return {
        "question_count": len(questions),
        "valid_schema": valid_schema,
        "unique_id_count": len(set(all_ids)),
        "linked_source_count": linked_sources,
        "quoted_evidence_match_count": quoted_evidence_matches,
        "valid_theme_count": valid_theme,
        "issues": issues,
    }


def build_rubric_evidence(output_path: str | Path | None = None) -> dict:
    assets = audit_assets()
    content_by_id = assets.pop("content_by_id")
    benchmark = audit_benchmark(content_by_id)
    selected = _read_json(PART_B_DIR / "selected_modules.json")
    summary_path = EVALUATION_DIR / "evaluation_summary.json"
    summary = _read_json(summary_path) if summary_path.is_file() else {}
    remaining_risks = [
        "自动检查能证明格式、链接和引用原文存在，不能替代教师对答案学术准确性的人工判断。",
    ]
    if assets["fallback_url_count"]:
        remaining_risks.insert(
            0,
            f"{assets['fallback_url_count']} 个 web-resource 来源仍为题名检索回退页，已在 source.json 中标记 source_quality_note，建议提交前人工替换为直达论文页。",
        )

    evidence = {
        "official_rubric": {
            "total": 100,
            "knowledge_assets": 35,
            "benchmark": 35,
            "optional_modules": 30,
        },
        "knowledge_assets": {
            "observed": assets,
            "status": "pass" if (
                assets["valid_structure"] >= 20
                and assets["fallback_url_count"] == 0
                and assets["academic_papers_with_doi"] == assets["academic_paper_count"]
            ) else ("pass-with-source-quality-risk" if assets["valid_structure"] >= 20 else "fail"),
            "evidence_files": [
                "PartA_知识资产与评测基准/data/",
                "PartA_知识资产与评测基准/validation_summary.json",
            ],
            "presentation_evidence": [
                f"{assets['valid_structure']}/{assets['asset_count']} 个资产三件套完整",
                f"{assets['valid_keywords']}/{assets['asset_count']} 个关键词文件符合 kebab-case",
                f"{assets['direct_url_count']} 个直达来源；{assets['fallback_url_count']} 个题名检索回退页",
                f"{assets['academic_papers_with_doi']}/{assets['academic_paper_count']} 个 academic-paper 来源含 DOI",
            ],
        },
        "benchmark": {
            "observed": benchmark,
            "status": "pass" if (
                benchmark["question_count"] >= 20
                and benchmark["valid_schema"] == benchmark["question_count"]
                and benchmark["unique_id_count"] == benchmark["question_count"]
                and benchmark["linked_source_count"] == benchmark["question_count"]
                and benchmark["quoted_evidence_match_count"] == benchmark["question_count"]
            ) else "partial",
            "evidence_files": [
                "PartA_知识资产与评测基准/benchmark/qa_dataset.json",
                "PartA_知识资产与评测基准/validation_summary.json",
            ],
            "presentation_evidence": [
                f"{benchmark['question_count']} 道问题",
                f"{benchmark['valid_schema']}/{benchmark['question_count']} 字段完整",
                f"{benchmark['unique_id_count']}/{benchmark['question_count']} ID 唯一",
                f"{benchmark['linked_source_count']}/{benchmark['question_count']} 来源绑定到本地资产",
                f"{benchmark['quoted_evidence_match_count']}/{benchmark['question_count']} 引用原文可在资产中复核",
            ],
        },
        "optional_modules": {
            "selected": selected,
            "observed": summary,
            "status": "pass" if (
                selected.get("difficulty_sum", 0) >= 4
                and summary.get("dynamic_orchestration_passed") == summary.get("dynamic_orchestration_questions")
                and summary.get("multimodal_passed") == summary.get("multimodal_questions")
                and summary.get("document_extraction_passed") is True
            ) else "partial",
            "evidence_files": [
                "PartB_智能体应用项目/agent_registry.json",
                "PartB_智能体应用项目/code/dynamic_orchestrator.py",
                "PartB_智能体应用项目/code/run_dynamic_orchestration_demo.py",
                "PartB_智能体应用项目/evaluation/dynamic_orchestration_benchmark.json",
                "PartB_智能体应用项目/evaluation/dynamic_orchestration_results.json",
                "PartB_智能体应用项目/evaluation/dynamic_decision_traces.json",
                "PartB_智能体应用项目/evaluation/dynamic_plan_comparison.json",
                "PartB_智能体应用项目/evaluation/dynamic_recovery_case.json",
                "PartB_智能体应用项目/evaluation/flowcharts/advanced_dynamic_orchestration.svg",
                "PartB_智能体应用项目/evaluation/flowcharts/dynamic_recovery_loop.svg",
                "PartB_智能体应用项目/workflows.json",
                "PartB_智能体应用项目/evaluation/workflow_demo_results.json",
                "PartB_智能体应用项目/evaluation/orchestration_benchmark_results.json",
                "PartB_智能体应用项目/evaluation/multimodal_demo_results.json",
                "PartB_智能体应用项目/evaluation/document_extraction_demo.json",
                "PartB_智能体应用项目/evaluation/flowcharts/workflow_modes.svg",
                "PartB_智能体应用项目/evaluation/flowcharts/multimodal_construction.svg",
                "PartB_智能体应用项目/evaluation/flowcharts/multimodal_retrieval.svg",
            ],
            "presentation_evidence": [
                f"难度和 {selected.get('difficulty_sum')}",
                f"动态编排评测：{summary.get('dynamic_orchestration_passed', 0)}/{summary.get('dynamic_orchestration_questions', 0)}",
                f"自动生成计划：{summary.get('dynamic_auto_generated_plans', 0)}",
                f"运行时调整：{summary.get('dynamic_runtime_adjustment_plans', 0)}",
                f"重试计划：{summary.get('dynamic_retry_plans', 0)}",
                f"恢复计划：{summary.get('dynamic_recovery_plans', 0)}",
                f"决策轨迹记录：{summary.get('dynamic_decision_trace_records', 0)}",
                f"静态工作流基线：{summary.get('workflow_templates', 0)} 个模板，模式 {summary.get('workflow_modes', [])}",
                f"多模态规模：{summary.get('knowledge_records', {})}",
                f"多模态评测：{summary.get('multimodal_passed', 0)}/{summary.get('multimodal_questions', 0)}",
                f"本地 HTML 三模态抽取：{summary.get('document_extraction', {})}",
                f"运行模式：{summary.get('runtime_mode', {})}",
                f"单元测试：{summary.get('unit_tests_passed', 0)}/{summary.get('unit_tests', 0)}",
            ],
        },
        "evidence_chain_complete": benchmark["linked_source_count"] == benchmark["question_count"],
        "remaining_risks": remaining_risks,
    }
    output_path = Path(output_path or (EVALUATION_DIR / "rubric_evidence.json"))
    output_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence


if __name__ == "__main__":
    print(json.dumps(build_rubric_evidence(), ensure_ascii=False, indent=2))
