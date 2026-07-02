from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from path_config import DEFAULT_NPC_DATASET_DIR, DEFAULT_SEGRAP2023_IO_DIR, PROJECT_ROOT, resolve_project_path

from .base import BaseSegmenter


@dataclass
class SegRap2023Paths:
    io_root: Path
    input_dir: Path
    output_dir: Path
    ct_dir: Path
    enhanced_ct_dir: Path
    output_mask_dir: Path


class SegRap2023Adapter(BaseSegmenter):
    """Adapter for SegRap2023 task2 gross tumor volume segmentation.

    SegRap2023 expects two registered CT modalities in MetaImage format:
    head-neck-ct and head-neck-contrast-enhanced-ct. The bundled NPC demo data
    contains one raw NIfTI image per case, so the adapter can duplicate that
    image as a demo compatibility fallback when no enhanced CT is provided.
    """

    name = "segrap2023_task2_gtv"
    docker_image = "segrap2023_gtv_segmentationcontainer"

    def __init__(self, io_root: str | Path | None = None):
        self.io_root = Path(resolve_project_path(io_root)) if io_root else DEFAULT_SEGRAP2023_IO_DIR
        self._last_error = ""

    @staticmethod
    def _require_sitk():
        try:
            import SimpleITK as sitk
        except Exception as exc:
            raise RuntimeError(
                "缺少 SimpleITK，无法导出/读取 SegRap2023 的 .mha 文件。"
                "请先安装：python -m pip install -r requirements-segrap2023.txt"
            ) from exc
        return sitk

    @staticmethod
    def _case_dir(case_id: str, dataset_dir: str | Path | None = None) -> Path:
        root = Path(resolve_project_path(dataset_dir or DEFAULT_NPC_DATASET_DIR)).resolve()
        case_dir = root / str(case_id)
        if not case_dir.exists():
            raise FileNotFoundError(f"找不到病例目录：{case_dir}")
        return case_dir

    def paths(self, io_root: str | Path | None = None) -> SegRap2023Paths:
        root = Path(resolve_project_path(io_root)) if io_root else self.io_root
        input_dir = root / "input"
        output_dir = root / "output"
        return SegRap2023Paths(
            io_root=root,
            input_dir=input_dir,
            output_dir=output_dir,
            ct_dir=input_dir / "head-neck-ct",
            enhanced_ct_dir=input_dir / "head-neck-contrast-enhanced-ct",
            output_mask_dir=output_dir / "gross-tumor-volume-segmentation",
        )

    def dependency_status(self) -> tuple[bool, str]:
        try:
            self._require_sitk()
        except RuntimeError as exc:
            return False, str(exc)
        docker_ready = shutil.which("docker") is not None
        docker_note = "Docker 已安装" if docker_ready else "未检测到 Docker，仍可生成输入目录与运行命令"
        return True, f"SegRap2023 格式适配依赖已就绪；{docker_note}。"

    def available(self) -> bool:
        ok, message = self.dependency_status()
        self._last_error = "" if ok else message
        return ok

    @property
    def last_error(self) -> str:
        if self._last_error:
            return self._last_error
        ok, message = self.dependency_status()
        return "" if ok else message

    @staticmethod
    def _write_mha(source_path: Path, destination_path: Path) -> dict[str, object]:
        sitk = SegRap2023Adapter._require_sitk()
        image = sitk.ReadImage(str(source_path))
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        warning_display = sitk.ProcessObject_GetGlobalWarningDisplay()
        sitk.ProcessObject_SetGlobalWarningDisplay(False)
        try:
            sitk.WriteImage(image, str(destination_path), True)
        finally:
            sitk.ProcessObject_SetGlobalWarningDisplay(warning_display)
        return {
            "source": str(source_path),
            "destination": str(destination_path),
            "size_xyz": list(image.GetSize()),
            "spacing_xyz": [float(value) for value in image.GetSpacing()],
            "origin_xyz": [float(value) for value in image.GetOrigin()],
        }

    def prepare_case(
        self,
        case_id: str,
        dataset_dir: str | Path | None = None,
        io_root: str | Path | None = None,
        contrast_ct_path: str | Path | None = None,
        duplicate_single_modality: bool = True,
    ) -> dict[str, object]:
        """Export a case into the SegRap2023 task2 input folder layout."""
        case_dir = self._case_dir(case_id, dataset_dir)
        ct_source = case_dir / "image.nii.gz"
        if not ct_source.exists():
            raise FileNotFoundError(f"病例 {case_id} 缺少原始 CT：{ct_source}")

        if contrast_ct_path and str(contrast_ct_path).strip():
            enhanced_source = Path(resolve_project_path(contrast_ct_path)).resolve()
            modality_policy = "external_contrast_ct"
        elif duplicate_single_modality:
            enhanced_source = ct_source
            modality_policy = "single_modality_duplicated_for_demo"
        else:
            raise FileNotFoundError("未提供增强 CT，且未启用单模态复制策略。")

        if not enhanced_source.exists():
            raise FileNotFoundError(f"找不到增强 CT 文件：{enhanced_source}")

        paths = self.paths(io_root)
        ct_target = paths.ct_dir / f"{case_id}.mha"
        enhanced_target = paths.enhanced_ct_dir / f"{case_id}.mha"
        ct_meta = self._write_mha(ct_source, ct_target)
        enhanced_meta = self._write_mha(enhanced_source, enhanced_target)
        paths.output_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "adapter": self.name,
            "case_id": str(case_id),
            "input_dir": str(paths.input_dir),
            "output_dir": str(paths.output_dir),
            "modality_policy": modality_policy,
            "ct": ct_meta,
            "contrast_enhanced_ct": enhanced_meta,
            "docker_build_command": self.build_command(),
            "docker_run_command": self.run_command(paths.input_dir, paths.output_dir),
            "notes": [
                "SegRap2023 task2 原生需要非增强 CT 与增强 CT 两个已配准模态。",
                "当前演示数据只有单模态 CT；复制单模态只用于流程适配演示，不能等同于真实双模态推理质量。",
            ],
        }
        manifest_path = paths.io_root / "adapter_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest | {"manifest_path": str(manifest_path)}

    def build_command(self, repo_task2_dir: str | Path | None = None) -> str:
        repo = self.resolve_task2_repo(repo_task2_dir) or Path("path/to/segrap2023/task2")
        return f'cd "{repo}" && docker build . -t {self.docker_image}'

    @staticmethod
    def resolve_task2_repo(repo_task2_dir: str | Path | None = None) -> Path | None:
        if repo_task2_dir:
            candidate = Path(resolve_project_path(repo_task2_dir)).resolve()
            return candidate if candidate.exists() else candidate
        env_value = os.getenv("SEGRAP2023_TASK2_DIR", "").strip()
        if env_value:
            candidate = Path(resolve_project_path(env_value)).resolve()
            return candidate if candidate.exists() else candidate
        candidates = [
            PROJECT_ROOT / "external" / "segrap2023" / "task2",
            PROJECT_ROOT.parent / "external" / "segrap2023" / "task2",
            PROJECT_ROOT.parent.parent / "external" / "segrap2023" / "task2",
            Path.cwd() / "work" / "external" / "segrap2023" / "task2",
        ]
        return next((path.resolve() for path in candidates if path.exists()), None)

    def run_command(
        self,
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        gpu: str = "all",
    ) -> str:
        paths = self.paths()
        input_path = Path(input_dir) if input_dir else paths.input_dir
        output_path = Path(output_dir) if output_dir else paths.output_dir
        return (
            f'docker run --rm --gpus {gpu} '
            f'-v "{input_path.resolve()}:/input/images" '
            f'-v "{output_path.resolve()}:/output/images" '
            f'--shm-size 2g {self.docker_image}'
        )

    def import_prediction(
        self,
        case_id: str,
        dataset_dir: str | Path | None = None,
        io_root: str | Path | None = None,
        output_mha: str | Path | None = None,
    ) -> dict[str, object]:
        """Import SegRap2023 4D .mha output as prediction_segrap2023.npy."""
        sitk = self._require_sitk()
        case_dir = self._case_dir(case_id, dataset_dir)
        paths = self.paths(io_root)
        source = Path(output_mha) if output_mha else paths.output_mask_dir / f"{case_id}.mha"
        if not source.is_absolute():
            source = Path(resolve_project_path(source)).resolve()
        if not source.exists():
            raise FileNotFoundError(f"未找到 SegRap2023 输出：{source}")

        image = sitk.ReadImage(str(source))
        array = sitk.GetArrayFromImage(image)
        label = self._to_label_volume(array)

        target_shape = tuple(np.load(case_dir / "mask_processed.npy").shape)
        if label.shape != target_shape:
            label = self._resize_to_shape(label, target_shape)

        output_path = case_dir / "prediction_segrap2023.npy"
        np.save(output_path, label.astype(np.uint8))
        return {
            "case_id": str(case_id),
            "source": str(source),
            "output": str(output_path),
            "source_shape": list(array.shape),
            "saved_shape": list(label.shape),
            "labels": [int(value) for value in np.unique(label)],
        }

    def create_demo_prediction(
        self,
        case_id: str,
        dataset_dir: str | Path | None = None,
    ) -> dict[str, object]:
        """Create a local visualization fallback when official Docker output is absent.

        This is intentionally labeled as a demo result. It keeps the UI usable on
        machines without NVIDIA Docker/GPU, but it is not an official SegRap2023
        model inference result.
        """
        case_dir = self._case_dir(case_id, dataset_dir)
        image_path = case_dir / "image_processed.npy"
        mask_path = case_dir / "mask_processed.npy"
        if not image_path.exists() or not mask_path.exists():
            raise FileNotFoundError(f"病例 {case_id} 缺少 image_processed.npy 或 mask_processed.npy。")

        image = np.load(image_path)
        reference_mask = np.load(mask_path) > 0
        if reference_mask.any():
            try:
                from scipy.ndimage import binary_dilation
            except Exception as exc:
                raise RuntimeError("需要 scipy 才能生成 SegRap2023 本地演示 mask。") from exc
            prediction = binary_dilation(reference_mask, iterations=1).astype(np.uint8)
            method = "ground_truth_dilated_demo"
        else:
            finite = image[np.isfinite(image)]
            if finite.size == 0:
                prediction = np.zeros_like(image, dtype=np.uint8)
            else:
                threshold = float(np.percentile(finite, 99.5))
                prediction = (image >= threshold).astype(np.uint8)
            method = "intensity_percentile_demo"

        output_path = case_dir / "prediction_segrap2023.npy"
        np.save(output_path, prediction.astype(np.uint8))
        return {
            "case_id": str(case_id),
            "output": str(output_path),
            "method": method,
            "saved_shape": list(prediction.shape),
            "labels": [int(value) for value in np.unique(prediction)],
            "foreground_voxels": int((prediction > 0).sum()),
            "is_official_inference": False,
        }

    @staticmethod
    def _to_label_volume(array: np.ndarray) -> np.ndarray:
        arr = np.asarray(array)
        if arr.ndim == 4:
            label = np.zeros(arr.shape[1:], dtype=np.uint8)
            for channel in range(arr.shape[0]):
                label[arr[channel] > 0] = channel + 1
        elif arr.ndim == 3:
            label = np.rint(arr).astype(np.uint8)
        else:
            raise ValueError(f"SegRap2023 输出应为 3D 或 4D 体数据，当前为 {arr.shape}")
        return np.transpose(label, (2, 1, 0))

    @staticmethod
    def _resize_to_shape(volume: np.ndarray, target_shape: tuple[int, int, int]) -> np.ndarray:
        try:
            from scipy.ndimage import zoom
        except Exception as exc:
            raise RuntimeError("需要 scipy 才能把 SegRap2023 输出重采样回项目预处理尺寸。") from exc
        factors = tuple(target / source for target, source in zip(target_shape, volume.shape))
        return zoom(volume, factors, order=0).astype(np.uint8)

    def predict(self, image_volume: np.ndarray, prompt=None) -> np.ndarray:
        raise NotImplementedError("SegRap2023 通过 Docker/nnU-Net 处理完整 3D 双模态输入，请使用 prepare_case/import_prediction。")

    @staticmethod
    def docker_image_exists(image_name: str | None = None) -> bool:
        if shutil.which("docker") is None:
            return False
        target = image_name or SegRap2023Adapter.docker_image
        result = subprocess.run(
            ["docker", "image", "inspect", target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
