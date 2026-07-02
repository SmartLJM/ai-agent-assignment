from __future__ import annotations

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
PART_B_DIR = CODE_DIR.parent
PROJECT_ROOT = PART_B_DIR.parent
PART_A_DIR = PROJECT_ROOT / "PartA_知识资产与评测基准"
KNOWLEDGE_BASE_DIR = PART_A_DIR / "data"
BENCHMARK_FILE = PART_A_DIR / "benchmark" / "qa_dataset.json"
DEFAULT_NPC_DATASET_DIR = CODE_DIR / "npc_dataset_nii"
DEFAULT_SEGRAP2023_IO_DIR = PART_B_DIR / "segrap2023_io"
EVALUATION_DIR = PART_B_DIR / "evaluation"
WORKFLOW_FILE = PART_B_DIR / "workflows.json"

SOURCE_TYPE_DIRS = {
    "01-academic",
    "02-textbook",
    "03-course",
    "04-encyclopedia",
    "05-project",
    "06-knowledge-base",
    "07-blog",
    "08-forum",
}


def is_knowledge_asset_dir(path: str | Path) -> bool:
    path = Path(path)
    return (
        path.is_dir()
        and (path / "content").is_dir()
        and (path / "keywords.json").is_file()
        and (path / "source.json").is_file()
    )


def iter_knowledge_asset_dirs(root: str | Path = KNOWLEDGE_BASE_DIR) -> list[Path]:
    """Return knowledge-set directories in both flat and official nested layouts."""
    root = Path(root)
    if not root.exists():
        return []
    assets: dict[str, Path] = {}
    for source_path in sorted(root.rglob("source.json")):
        asset_dir = source_path.parent
        if is_knowledge_asset_dir(asset_dir):
            assets[asset_dir.name] = asset_dir
    return [assets[key] for key in sorted(assets)]


def resolve_project_path(value: str | Path) -> str:
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path)
    candidates = [CODE_DIR / path, PROJECT_ROOT / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return str((CODE_DIR / path).resolve())
