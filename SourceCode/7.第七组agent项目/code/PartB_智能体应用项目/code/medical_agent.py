from __future__ import annotations

import json
import os
import re
from pathlib import Path

import nibabel as nib
import numpy as np
try:
    from dotenv import load_dotenv
except ImportError:  # optional: local mode does not require .env support
    def load_dotenv(*_args, **_kwargs):
        return False
from scipy.ndimage import zoom

from path_config import DEFAULT_NPC_DATASET_DIR, resolve_project_path


load_dotenv(Path(__file__).resolve().parent / ".env")


class MedicalDataMinerAgent:
    """Deterministic local NIfTI tool with explicitly enabled DashScope parsing."""

    def __init__(self):
        self.api_key = os.getenv("API_KEY", "").strip()
        self.dashscope_enabled = (
            os.getenv("ENABLE_DASHSCOPE", "0").strip().lower()
            in {"1", "true", "yes", "on"}
            and bool(self.api_key)
        )
        self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def preprocess_nifti(
        self,
        file_path: str | Path,
        target_shape: tuple[int, int, int] = (128, 128, 64),
        is_label: bool = False,
    ) -> dict:
        file_path = Path(file_path)
        image = nib.load(str(file_path))
        data = np.asarray(image.get_fdata(), dtype=np.float32)
        if data.ndim != 3:
            raise ValueError(f"仅支持 3D NIfTI，当前尺寸为 {data.shape}")

        factors = tuple(target / source for target, source in zip(target_shape, data.shape))
        resampled = zoom(data, factors, order=0 if is_label else 1)
        if is_label:
            rounded = np.rint(resampled)
            final = rounded.astype(np.uint8 if rounded.max(initial=0) <= 255 else np.int16)
        else:
            finite = np.isfinite(resampled)
            values = resampled[finite]
            mean = float(values.mean()) if values.size else 0.0
            std = float(values.std()) if values.size else 0.0
            final = np.zeros(resampled.shape, dtype=np.float32)
            if values.size:
                final[finite] = (resampled[finite] - mean) / (std + 1e-8)

        name = file_path.name
        stem = name[:-7] if name.endswith(".nii.gz") else file_path.stem
        output_path = file_path.with_name(f"{stem}_processed.npy")
        np.save(output_path, final)
        return {
            "input": str(file_path),
            "output": str(output_path),
            "is_label": is_label,
            "source_shape": list(data.shape),
            "target_shape": list(final.shape),
            "dtype": str(final.dtype),
        }

    def batch_process_dataset(self, dataset_dir: str | Path) -> dict:
        root = Path(resolve_project_path(dataset_dir))
        if not root.is_dir():
            raise FileNotFoundError(f"找不到数据集目录：{root}")
        results = []
        failures = []
        for case_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            for file_path in sorted(case_dir.iterdir()):
                lower = file_path.name.lower()
                if not (lower.endswith(".nii") or lower.endswith(".nii.gz")):
                    continue
                is_label = any(token in lower for token in ("label", "mask", "seg"))
                try:
                    results.append(self.preprocess_nifti(file_path, is_label=is_label))
                except Exception as exc:  # batch processing must continue per case
                    failures.append({"input": str(file_path), "error": str(exc)})
        return {
            "dataset_dir": str(root),
            "processed": len(results),
            "failed": len(failures),
            "results": results,
            "failures": failures,
        }

    @staticmethod
    def _path_from_instruction(instruction: str) -> str | None:
        quoted = re.findall(r"[\"']([^\"']+)[\"']", instruction)
        for candidate in quoted:
            if Path(resolve_project_path(candidate)).exists():
                return candidate
        for token in re.split(r"[，,。;；\s]+", instruction):
            if token and Path(resolve_project_path(token)).exists():
                return token
        return None

    def _llm_path(self, instruction: str) -> str | None:
        if not self.dashscope_enabled:
            return None
        try:
            import requests
        except ImportError:
            return None
        payload = {
            "model": "qwen-max",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "从用户指令提取 NIfTI 数据集目录，仅返回 JSON："
                        '{"dataset_path":"..."}。指令：' + instruction
                    ),
                }
            ],
            "temperature": 0,
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            return json.loads(match.group(0)).get("dataset_path") if match else None
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
            return None

    def chat_and_execute(self, user_instruction: str) -> dict:
        dataset_path = self._path_from_instruction(user_instruction) or self._llm_path(user_instruction)
        dataset_path = dataset_path or str(DEFAULT_NPC_DATASET_DIR)
        return self.batch_process_dataset(dataset_path)


if __name__ == "__main__":
    agent = MedicalDataMinerAgent()
    print(json.dumps(agent.batch_process_dataset(DEFAULT_NPC_DATASET_DIR), ensure_ascii=False, indent=2))
