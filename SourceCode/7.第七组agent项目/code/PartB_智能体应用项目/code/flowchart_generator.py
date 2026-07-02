from __future__ import annotations

import html
import json
import re
from pathlib import Path

from path_config import EVALUATION_DIR, WORKFLOW_FILE


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", value)


def _manifest_path(path: Path) -> str:
    try:
        return path.relative_to(EVALUATION_DIR.parent).as_posix()
    except ValueError:
        return str(path)


def _node_label(node: dict) -> str:
    if node["type"] == "step":
        return f"{node['agent']}<br/>{node['action']}"
    if node["type"] == "parallel":
        return "Parallel fork / merge"
    condition = node["condition"]
    return f"{condition['field']} {condition['operator']} threshold?"


def workflow_to_mermaid(workflow: dict) -> str:
    lines = ["flowchart TD", f"  START([Input: {workflow['name']}])"]
    counter = 0

    def walk(nodes: list[dict], predecessors: list[str]) -> list[str]:
        nonlocal counter
        current = predecessors
        for node in nodes:
            counter += 1
            node_id = f"N{counter}_{_safe_id(node['id'])}"
            if node["type"] == "step":
                lines.append(f'  {node_id}["{_node_label(node)}"]')
                for previous in current:
                    lines.append(f"  {previous} --> {node_id}")
                current = [node_id]
            elif node["type"] == "parallel":
                lines.append(f'  {node_id}{{"Parallel fork"}}')
                for previous in current:
                    lines.append(f"  {previous} --> {node_id}")
                branch_ends = []
                for branch in node["branches"]:
                    branch_ends.extend(walk([branch], [node_id]))
                counter += 1
                merge_id = f"N{counter}_{_safe_id(node['id'])}_merge"
                lines.append(f'  {merge_id}{{"Merge outputs"}}')
                for branch_end in branch_ends:
                    lines.append(f"  {branch_end} --> {merge_id}")
                current = [merge_id]
            else:
                lines.append(f'  {node_id}{{"{_node_label(node)}"}}')
                for previous in current:
                    lines.append(f"  {previous} --> {node_id}")
                true_ends = walk(node["if_true"], [node_id])
                false_ends = walk(node["if_false"], [node_id])
                first_true = true_ends[0] if true_ends else node_id
                first_false = false_ends[0] if false_ends else node_id
                lines.append(f"  {node_id} -. true .-> {first_true}")
                lines.append(f"  {node_id} -. false .-> {first_false}")
                current = true_ends + false_ends
        return current

    ends = walk(workflow["nodes"], ["START"])
    lines.append("  END([Trace + result])")
    for end in ends:
        lines.append(f"  {end} --> END")
    return "\n".join(lines) + "\n"


def _svg_text(x: int, y: int, text: str, size: int = 18, weight: int = 400, color: str = "#e5e7eb") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Segoe UI, Arial" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="middle">{html.escape(text)}</text>'
    )


def _svg_box(x: int, y: int, width: int, height: int, title: str, subtitle: str, color: str) -> str:
    return "".join(
        [
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="#111827" stroke="{color}" stroke-width="2"/>',
            _svg_text(x + width // 2, y + 34, title, 18, 700, color),
            _svg_text(x + width // 2, y + 62, subtitle, 14, 400, "#cbd5e1"),
        ]
    )


def _arrow(x1: int, y1: int, x2: int, y2: int, label: str = "") -> str:
    parts = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)"/>']
    if label:
        parts.append(_svg_text((x1 + x2) // 2, (y1 + y2) // 2 - 8, label, 13, 600, "#fbbf24"))
    return "".join(parts)


def build_modes_svg() -> str:
    width, height = 1400, 940
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#020617"/>',
        _svg_text(700, 48, "Advanced Static Orchestration Lv.2 — Three Executable Modes", 28, 700, "#f8fafc"),
        _svg_text(700, 78, "Every node has an Agent role, explicit inputs/outputs, and an auditable trace", 16, 400, "#94a3b8"),
    ]

    parts.extend([
        _svg_text(90, 145, "SEQUENTIAL", 18, 700, "#22d3ee"),
        _svg_box(130, 175, 235, 82, "Compliance Agent", "validate_submission", "#22d3ee"),
        _arrow(365, 216, 485, 216),
        _svg_box(485, 175, 235, 82, "Evidence Agent", "summarize_audit", "#22d3ee"),
        _arrow(720, 216, 840, 216),
        _svg_box(840, 175, 320, 82, "Trace + Evidence", "status / elapsed / output", "#22d3ee"),
    ])

    parts.extend([
        _svg_text(75, 365, "PARALLEL", 18, 700, "#34d399"),
        _svg_box(80, 400, 210, 82, "Case Input", "case_id + query", "#34d399"),
        _arrow(290, 441, 390, 441, "fork"),
        _svg_box(410, 330, 235, 76, "Image Agent", "image_analysis", "#34d399"),
        _svg_box(410, 425, 235, 76, "Mask Agent", "mask_analysis", "#34d399"),
        _svg_box(410, 520, 235, 76, "Retrieval Agent", "case_evidence", "#34d399"),
        _arrow(645, 368, 780, 441),
        _arrow(645, 463, 780, 441),
        _arrow(645, 558, 780, 441),
        _svg_box(800, 400, 220, 82, "Merge", "deterministic outputs", "#34d399"),
        _arrow(1020, 441, 1110, 441),
        _svg_box(1110, 400, 235, 82, "Report Agent", "case_report", "#34d399"),
    ])

    parts.extend([
        _svg_text(88, 705, "CONDITIONAL", 18, 700, "#a78bfa"),
        _svg_box(90, 740, 230, 82, "Case Inspector", "mask_ratio", "#a78bfa"),
        _arrow(320, 781, 470, 781),
        '<polygon points="560,720 650,781 560,842 470,781" fill="#111827" stroke="#a78bfa" stroke-width="2"/>',
        _svg_text(560, 775, "ratio >", 16, 700, "#a78bfa"),
        _svg_text(560, 798, "threshold?", 14, 400, "#cbd5e1"),
        _arrow(650, 756, 820, 710, "true"),
        _arrow(650, 806, 820, 855, "false"),
        _svg_box(840, 665, 300, 82, "Large-region Review", "3 views + bbox", "#fbbf24"),
        _svg_box(840, 815, 300, 82, "Small-target Review", "visibility + label check", "#fbbf24"),
        _arrow(1140, 706, 1280, 781),
        _arrow(1140, 856, 1280, 781),
        _svg_box(1220, 740, 150, 82, "Decision", "recorded", "#a78bfa"),
    ])
    parts.append("</svg>")
    return "".join(parts)


def _simple_flow_svg(title: str, steps: list[tuple[str, str, str]]) -> str:
    width, height = 1400, 360
    box_width = 230
    gap = 35
    start_x = 60
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#020617"/>',
        _svg_text(700, 55, title, 28, 700, "#f8fafc"),
    ]
    for index, (name, detail, color) in enumerate(steps):
        x = start_x + index * (box_width + gap)
        parts.append(_svg_box(x, 135, box_width, 100, name, detail, color))
        if index:
            previous_x = start_x + (index - 1) * (box_width + gap) + box_width
            parts.append(_arrow(previous_x, 185, x, 185))
    parts.append("</svg>")
    return "".join(parts)


def build_multimodal_construction_svg() -> str:
    return _simple_flow_svg(
        "Multimodal Knowledge Base Construction",
        [
            ("Text assets", "75 content records", "#22d3ee"),
            ("3D images", "10 image statistics", "#34d399"),
            ("Mask tables", "10 structured rows", "#a78bfa"),
            ("Unified index", "text / image / table", "#fbbf24"),
            ("Evidence files", "JSON index + CSV", "#fb7185"),
        ],
    )


def build_multimodal_retrieval_svg() -> str:
    return _simple_flow_svg(
        "Multimodal Retrieval and Grounded Answer",
        [
            ("User question", "single or joint modality", "#22d3ee"),
            ("Query analysis", "terms + modality hints", "#34d399"),
            ("Filtered scoring", "text / image / table", "#a78bfa"),
            ("Ranked evidence", "record IDs + sources", "#fbbf24"),
            ("Grounded answer", "or explicit no-hit", "#fb7185"),
        ],
    )


def generate_flowcharts(output_dir: str | Path | None = None) -> dict:
    config = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
    output_dir = Path(output_dir or (EVALUATION_DIR / "flowcharts"))
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for workflow in config["workflows"]:
        path = output_dir / f"{workflow['id']}.mmd"
        path.write_text(workflow_to_mermaid(workflow), encoding="utf-8")
        files.append(_manifest_path(path))
    svg_path = output_dir / "workflow_modes.svg"
    svg_path.write_text(build_modes_svg(), encoding="utf-8")
    files.append(_manifest_path(svg_path))
    construction_svg = output_dir / "multimodal_construction.svg"
    construction_svg.write_text(build_multimodal_construction_svg(), encoding="utf-8")
    files.append(_manifest_path(construction_svg))
    retrieval_svg = output_dir / "multimodal_retrieval.svg"
    retrieval_svg.write_text(build_multimodal_retrieval_svg(), encoding="utf-8")
    files.append(_manifest_path(retrieval_svg))
    construction_mmd = output_dir / "multimodal_construction.mmd"
    construction_mmd.write_text(
        "flowchart LR\n  A[75 text assets] --> D[Unified index]\n  B[10 image records] --> D\n  C[10 table records] --> D\n  D --> E[JSON index + CSV]\n",
        encoding="utf-8",
    )
    files.append(_manifest_path(construction_mmd))
    retrieval_mmd = output_dir / "multimodal_retrieval.mmd"
    retrieval_mmd.write_text(
        "flowchart LR\n  Q[Question] --> A[Terms + modality hints]\n  A --> S[Filtered scoring]\n  S --> E[Ranked evidence IDs]\n  E --> R[Grounded answer or no-hit]\n",
        encoding="utf-8",
    )
    files.append(_manifest_path(retrieval_mmd))
    manifest = {
        "workflow_count": len(config["workflows"]),
        "supported_modes": config["supported_modes"],
        "files": files,
    }
    (output_dir / "flowchart_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate_flowcharts(), ensure_ascii=False, indent=2))
