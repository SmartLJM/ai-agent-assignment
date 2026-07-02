from __future__ import annotations

import argparse
import json

from model_adapters import SegRap2023Adapter
from path_config import DEFAULT_NPC_DATASET_DIR, DEFAULT_SEGRAP2023_IO_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SegRap2023 task2 GTV adapter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="check local adapter dependencies")
    status.add_argument("--io-root", default=str(DEFAULT_SEGRAP2023_IO_DIR))

    prepare = subparsers.add_parser("prepare", help="export a case to SegRap2023 .mha input layout")
    prepare.add_argument("--case-id", required=True)
    prepare.add_argument("--dataset-dir", default=str(DEFAULT_NPC_DATASET_DIR))
    prepare.add_argument("--io-root", default=str(DEFAULT_SEGRAP2023_IO_DIR))
    prepare.add_argument("--contrast-ct", default="")
    prepare.add_argument("--require-contrast", action="store_true")

    importer = subparsers.add_parser("import-output", help="import SegRap2023 .mha output to prediction_segrap2023.npy")
    importer.add_argument("--case-id", required=True)
    importer.add_argument("--dataset-dir", default=str(DEFAULT_NPC_DATASET_DIR))
    importer.add_argument("--io-root", default=str(DEFAULT_SEGRAP2023_IO_DIR))
    importer.add_argument("--output-mha", default="")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    adapter = SegRap2023Adapter(io_root=args.io_root)

    if args.command == "status":
        ok, message = adapter.dependency_status()
        print(json.dumps({"ok": ok, "message": message}, ensure_ascii=False, indent=2))
        return

    if args.command == "prepare":
        result = adapter.prepare_case(
            case_id=args.case_id,
            dataset_dir=args.dataset_dir,
            io_root=args.io_root,
            contrast_ct_path=args.contrast_ct,
            duplicate_single_modality=not args.require_contrast,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "import-output":
        result = adapter.import_prediction(
            case_id=args.case_id,
            dataset_dir=args.dataset_dir,
            io_root=args.io_root,
            output_mha=args.output_mha,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
