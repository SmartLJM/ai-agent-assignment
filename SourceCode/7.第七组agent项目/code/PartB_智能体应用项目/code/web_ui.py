from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
import numpy as np

from expert_qa_agent import MedicalExpertAgent
from main_agent import RouterAgent
from model_adapters import MedSAMAdapter, SegRap2023Adapter
from path_config import DEFAULT_NPC_DATASET_DIR, DEFAULT_SEGRAP2023_IO_DIR, KNOWLEDGE_BASE_DIR
from segmentation_visualizer import (
    clamp_slice_index,
    list_available_cases,
    load_case,
    render_case,
    slice_count,
)
from workflow_engine import WorkflowEngine


def _patch_gradio_schema_parser() -> None:
    """Allow Gradio 4.x to parse newer Pydantic schemas on Python 3.9 installs."""
    try:
        import gradio_client.utils as client_utils
    except Exception:
        return

    original = client_utils._json_schema_to_python_type

    def patched(schema, defs):
        if isinstance(schema, bool) or schema is None:
            return "Any"
        return original(schema, defs)

    client_utils._json_schema_to_python_type = patched


_patch_gradio_schema_parser()


qa_expert = MedicalExpertAgent(KNOWLEDGE_BASE_DIR)
router = RouterAgent()
workflow_engine = WorkflowEngine()
model_segmenter = MedSAMAdapter()
segrap_segmenter = SegRap2023Adapter()


def user_chat(user_msg, history):
    history = list(history or [])
    if not user_msg or not user_msg.strip():
        return "", history
    dispatched = router.dispatch(user_msg)
    if dispatched["intent"] == "ACTION":
        summary = dispatched["result"]
        answer = (
            f"数据处理完成：成功 {summary['processed']} 个，失败 {summary['failed']} 个。"
            f"\n\n数据集：`{summary['dataset_dir']}`"
        )
    else:
        answer = dispatched["result"]
    history.append((user_msg, answer))
    return "", history


def _blank_image(size=256):
    return np.zeros((size, size, 3), dtype=np.uint8)


def _metrics_markdown(result, mask_type):
    metrics = result["metrics"]
    note = f"\n\n> 未找到“{mask_type}”，当前显示空 mask。" if result["missing_mask"] else ""
    stats = result["mask_statistics"]
    if metrics is None:
        label = "真实标注仅作为参考，不计算与自身的 Dice/IoU。" if result["is_reference"] else "未找到对应预测，暂无 Dice/IoU。"
        return f"""
### Mask 统计

- 标签：`{stats['labels']}`
- 前景体素：`{stats['foreground_voxels']}`
- 前景占比：`{stats['foreground_ratio']:.6f}`
- 说明：{label}{note}
"""
    return f"""
### Dice / IoU

| 范围 | Dice | IoU |
|---|---:|---:|
| 当前切片 | {metrics['slice_dice']:.4f} | {metrics['slice_iou']:.4f} |
| 3D 体数据 | {metrics['volume_dice']:.4f} | {metrics['volume_iou']:.4f} |

尺寸：`{result['shape']}`　切片：`{result['index']} / {result['max_index']}`{note}
"""


def render_visualization(dataset_dir, case_id, axis, slice_index, mask_type, alpha):
    try:
        result = render_case(case_id, axis, slice_index, mask_type, alpha, dataset_dir)
        return (
            result["image"],
            result["mask"],
            result["overlay"],
            _metrics_markdown(result, mask_type),
            f"已显示病例 {case_id} / {axis}。",
        )
    except Exception as exc:
        return _blank_image(), _blank_image(), _blank_image(), "### Dice / IoU\n暂无指标。", f"失败：{exc}"


def render_montage(dataset_dir, case_id, axis, mask_type, alpha):
    try:
        image, _ = load_case(case_id, dataset_dir)
        max_index = slice_count(image.shape, axis) - 1
        sample_count = min(8, max_index + 1)
        indices = np.linspace(0, max_index, sample_count, dtype=int).tolist()
        tiles = [
            render_case(case_id, axis, index, mask_type, alpha, dataset_dir)["overlay"]
            for index in indices
        ]
        height = max(tile.shape[0] for tile in tiles)
        width = max(tile.shape[1] for tile in tiles)
        padded = []
        for tile in tiles:
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
            canvas[: tile.shape[0], : tile.shape[1]] = tile
            padded.append(canvas)
        rows = []
        columns = 4
        gap = np.full((height, 6, 3), 255, dtype=np.uint8)
        row_gap = np.full((6, columns * width + (columns - 1) * 6, 3), 255, dtype=np.uint8)
        for start in range(0, len(padded), columns):
            row_tiles = padded[start : start + columns]
            while len(row_tiles) < columns:
                row_tiles.append(np.zeros((height, width, 3), dtype=np.uint8))
            row = row_tiles[0]
            for tile in row_tiles[1:]:
                row = np.concatenate([row, gap, tile], axis=1)
            rows.append(row)
        montage = rows[0]
        for row in rows[1:]:
            montage = np.concatenate([montage, row_gap, row], axis=0)
        summary = (
            f"病例 `{case_id}` 是 3D 体数据，尺寸 `{tuple(image.shape)}`。"
            f"当前方向 `{axis}` 共 `{max_index + 1}` 层；概览抽样切片：`{indices}`。"
            f"当前显示结果为 `{mask_type}` 的多切片 overlay。"
        )
        return montage, summary
    except Exception as exc:
        return _blank_image(512), f"多切片概览失败：{exc}"


def refresh_case_list(dataset_dir):
    cases = list_available_cases(dataset_dir)
    value = cases[0] if cases else None
    status = f"发现 {len(cases)} 个完整病例。" if cases else "未找到完整病例。"
    return gr.update(choices=cases, value=value), status


def update_case_or_axis(dataset_dir, case_id, axis, mask_type, alpha):
    try:
        image, _ = load_case(case_id, dataset_dir)
        maximum = slice_count(image.shape, axis) - 1
        index = clamp_slice_index(image.shape, axis, maximum // 2)
        result = render_case(case_id, axis, index, mask_type, alpha, dataset_dir)
        return (
            gr.update(maximum=maximum, value=index),
            result["image"],
            result["mask"],
            result["overlay"],
            _metrics_markdown(result, mask_type),
            f"已切换到病例 {case_id}。",
        )
    except Exception as exc:
        return (
            gr.update(maximum=0, value=0),
            _blank_image(),
            _blank_image(),
            _blank_image(),
            "### Dice / IoU\n暂无指标。",
            f"切换失败：{exc}",
        )


def _raw_slice(volume, axis, index):
    if axis == "axial":
        return volume[:, :, index]
    if axis == "coronal":
        return volume[:, index, :]
    return volume[index, :, :]


def _assign_slice(volume, axis, index, data):
    if axis == "axial":
        volume[:, :, index] = data
    elif axis == "coronal":
        volume[:, index, :] = data
    else:
        volume[index, :, :] = data


def run_medsam_prediction(dataset_dir, case_id, axis, slice_index, alpha, prompt_mode):
    try:
        if not model_segmenter.available():
            raise RuntimeError(model_segmenter.last_error)
        image, gt_mask = load_case(case_id, dataset_dir)
        index = clamp_slice_index(image.shape, axis, slice_index)
        image_slice = _raw_slice(image, axis, index)
        gt_slice = _raw_slice(gt_mask, axis, index)
        if "真实" in str(prompt_mode):
            box = model_segmenter.box_from_mask(gt_slice, margin=6) or model_segmenter.default_box(image_slice)
            prompt_note = "真实 mask bbox（演示/模拟人工框选）"
        else:
            box = model_segmenter.default_box(image_slice)
            prompt_note = "图像默认中心区域"
        prediction = model_segmenter.predict_slice(image_slice, box=box)
        volume = np.zeros_like(gt_mask, dtype=np.uint8)
        _assign_slice(volume, axis, index, prediction)
        output = DEFAULT_NPC_DATASET_DIR if not dataset_dir else dataset_dir
        output_path = __import__("pathlib").Path(output) / str(case_id) / "prediction_medsam_slice.npy"
        np.save(output_path, volume)
        display_type = "MedSAM 2D 切片预测"
        result = render_case(case_id, axis, index, display_type, alpha, dataset_dir)
        return (
            gr.update(value=display_type), result["image"], result["mask"], result["overlay"],
            _metrics_markdown(result, display_type), f"MedSAM 2D 当前切片预测已保存，提示框来自{prompt_note}：{box}。"
        )
    except Exception as exc:
        return gr.update(), _blank_image(), _blank_image(), _blank_image(), "### Dice / IoU\n暂无指标。", f"MedSAM 未运行：{exc}"


def prepare_segrap_case(dataset_dir, case_id, io_root, contrast_ct_path, duplicate_single_modality):
    try:
        manifest = segrap_segmenter.prepare_case(
            case_id=case_id,
            dataset_dir=dataset_dir,
            io_root=io_root,
            contrast_ct_path=contrast_ct_path,
            duplicate_single_modality=bool(duplicate_single_modality),
        )
        warning = ""
        if manifest["modality_policy"] == "single_modality_duplicated_for_demo":
            warning = "\n\n> 当前病例没有单独增强 CT，已复制原 CT 作为演示兼容输入；真实推理质量需使用配准后的双模态 CT。"
        return (
            f"SegRap2023 输入已生成：`{manifest['input_dir']}`。\n\n"
            f"输出目录：`{manifest['output_dir']}`\n\n"
            f"清单：`{manifest['manifest_path']}`\n\n"
            "构建镜像：\n"
            f"```bash\n{manifest['docker_build_command']}\n```\n\n"
            "运行推理：\n"
            f"```bash\n{manifest['docker_run_command']}\n```"
            f"{warning}"
        )
    except Exception as exc:
        return f"SegRap2023 输入生成失败：{exc}"


def import_segrap_prediction(dataset_dir, case_id, axis, slice_index, alpha, io_root, output_mha):
    try:
        imported = segrap_segmenter.import_prediction(
            case_id=case_id,
            dataset_dir=dataset_dir,
            io_root=io_root,
            output_mha=output_mha,
        )
        image, _ = load_case(case_id, dataset_dir)
        index = clamp_slice_index(image.shape, axis, slice_index)
        display_type = "SegRap2023 3D 预测"
        result = render_case(case_id, axis, index, display_type, alpha, dataset_dir)
        status = (
            f"SegRap2023 输出已导入：`{imported['output']}`。"
            f"\n\n源文件：`{imported['source']}`"
            f"\n\n标签：`{imported['labels']}`，保存尺寸：`{imported['saved_shape']}`。"
        )
        return (
            gr.update(value=display_type),
            result["image"],
            result["mask"],
            result["overlay"],
            _metrics_markdown(result, display_type),
            status,
        )
    except Exception as exc:
        return gr.update(), _blank_image(), _blank_image(), _blank_image(), "### Dice / IoU\n暂无指标。", f"SegRap2023 输出导入失败：{exc}"


def start_prediction(
    dataset_dir,
    case_id,
    axis,
    slice_index,
    mask_type,
    alpha,
    prompt_mode,
    io_root,
    contrast_ct_path,
    duplicate_single_modality,
    output_mha,
):
    selected = str(mask_type or "")
    if "MedSAM" in selected:
        return run_medsam_prediction(dataset_dir, case_id, axis, slice_index, alpha, prompt_mode)

    if "SegRap2023" in selected:
        output_path = Path(output_mha).expanduser() if str(output_mha or "").strip() else None
        if output_path is None:
            default_paths = segrap_segmenter.paths(io_root)
            output_path = default_paths.output_mask_dir / f"{case_id}.mha"
        if output_path.exists():
            return import_segrap_prediction(dataset_dir, case_id, axis, slice_index, alpha, io_root, str(output_path))

        prepare_text = prepare_segrap_case(dataset_dir, case_id, io_root, contrast_ct_path, duplicate_single_modality)
        demo_prediction = segrap_segmenter.create_demo_prediction(case_id, dataset_dir)
        image, _ = load_case(case_id, dataset_dir)
        index = clamp_slice_index(image.shape, axis, slice_index)
        display_type = "SegRap2023 3D 预测"
        result = render_case(case_id, axis, index, display_type, alpha, dataset_dir)
        status_text = (
            "未找到官方 SegRap2023 Docker 输出 `.mha`，已生成本地演示 mask 以便展示可视化与指标。"
            "该结果不是官方 SegRap2023 权重推理；正式结果请在 GPU/Docker 环境运行后导入。\n\n"
            f"演示 mask：`{demo_prediction['output']}`\n\n"
            f"演示方法：`{demo_prediction['method']}`，前景体素：`{demo_prediction['foreground_voxels']}`。\n\n"
            f"{prepare_text}"
        )
        return (
            gr.update(value=display_type),
            result["image"],
            result["mask"],
            result["overlay"],
            _metrics_markdown(result, display_type),
            status_text,
        )

    result = render_case(case_id, axis, slice_index, "真实标注", alpha, dataset_dir)
    return (
        gr.update(value="真实标注"),
        result["image"],
        result["mask"],
        result["overlay"],
        _metrics_markdown(result, "真实标注"),
        "当前选择为真实标注，无需运行预测。请选择 MedSAM 2D 或 SegRap2023 3D 后再点击“开始预测”。",
    )


def run_workflow(workflow_id, dataset_dir, case_id, query, mask_ratio_threshold):
    inputs = {
        "dataset_dir": dataset_dir,
        "case_id": case_id,
        "query": query,
        "mask_ratio_threshold": mask_ratio_threshold,
    }
    try:
        result = workflow_engine.run(workflow_id, inputs)
    except Exception as exc:
        result = {"status": "failed", "error": str(exc)}
    return json.dumps(result, ensure_ascii=False, indent=2)


case_choices = list_available_cases(DEFAULT_NPC_DATASET_DIR)
initial_case = "036" if "036" in case_choices else (case_choices[0] if case_choices else None)
initial_max = 0
initial_index = 0
if initial_case:
    image, _ = load_case(initial_case, DEFAULT_NPC_DATASET_DIR)
    initial_max = slice_count(image.shape, "axial") - 1
    initial_index = initial_max // 2


with gr.Blocks(title="3D 医疗影像智能全能助理") as demo:
    gr.Markdown(
        "# 3D 医疗影像智能全能助理\n"
        "本地 RAG · NIfTI 预处理 · 分割可视化 · 多模态检索 · JSON 工作流编排"
    )

    with gr.Tabs():
        with gr.Tab("知识问答与数据处理"):
            chatbot = gr.Chatbot(height=480, label="本地智能体")
            msg = gr.Textbox(label="问题或数据处理指令")
            with gr.Row():
                submit = gr.Button("发送", variant="primary")
                gr.ClearButton([msg, chatbot], value="清除")
            submit.click(user_chat, [msg, chatbot], [msg, chatbot])
            msg.submit(user_chat, [msg, chatbot], [msg, chatbot])
            gr.Markdown(
                f"已加载 **{len(qa_expert.knowledge_docs)}** 个知识资产、"
                f"**{len(qa_expert.qa_items)}** 道规范 QA。默认使用本地证据摘要；"
                "仅在显式启用 ENABLE_DASHSCOPE=1 且配置 API_KEY 时使用可选云端生成。"
            )

        with gr.Tab("分割可视化与评测"):
            with gr.Row():
                with gr.Column(scale=3):
                    dataset_box = gr.Textbox(value=str(DEFAULT_NPC_DATASET_DIR), label="数据集目录")
                    refresh = gr.Button("刷新病例")
                    case = gr.Dropdown(choices=case_choices, value=initial_case, label="病例")
                    axis = gr.Radio(["axial", "coronal", "sagittal"], value="axial", label="方向")
                    index = gr.Slider(0, initial_max, initial_index, step=1, label="切片")
                    mask_type = gr.Radio(
                        ["真实标注", "MedSAM 2D 切片预测", "SegRap2023 3D 预测"],
                        value="真实标注",
                        label="显示结果",
                    )
                    alpha = gr.Slider(0, 1, 0.45, step=0.05, label="透明度")
                    start_predict_btn = gr.Button("开始预测")
                    prompt_mode = gr.Radio(
                        ["真实 mask bbox（演示）", "默认中心框"],
                        value="真实 mask bbox（演示）",
                        label="MedSAM 2D 提示框",
                    )
                    segrap_root = gr.Textbox(value=str(DEFAULT_SEGRAP2023_IO_DIR), label="SegRap2023 交换目录")
                    segrap_contrast = gr.Textbox(value="", label="增强 CT 路径（可选）")
                    segrap_duplicate = gr.Checkbox(value=True, label="缺少增强 CT 时复制当前 CT")
                    segrap_prepare = gr.Button("生成 SegRap2023 3D 输入与命令")
                    segrap_output = gr.Textbox(value="", label="SegRap2023 输出 .mha（可选）")
                    segrap_import = gr.Button("导入 SegRap2023 3D 输出")
                    montage_btn = gr.Button("生成多切片概览", variant="secondary")
                    status = gr.Markdown("等待操作。")
                with gr.Column(scale=7):
                    with gr.Row():
                        image_out = gr.Image(label="原图", type="numpy", height=300)
                        mask_out = gr.Image(label="mask", type="numpy", height=300)
                        overlay_out = gr.Image(label="overlay", type="numpy", height=300)
                    metrics = gr.Markdown("### Dice / IoU\n暂无指标。")
                    montage_out = gr.Image(label="多切片 overlay 概览", type="numpy", height=360)
                    montage_note = gr.Markdown("选择病例、方向和显示结果后，可生成多切片概览。")

            outputs = [image_out, mask_out, overlay_out, metrics, status]
            refresh.click(refresh_case_list, dataset_box, [case, status])
            for control in (case, axis):
                control.change(update_case_or_axis, [dataset_box, case, axis, mask_type, alpha], [index, *outputs])
            for control in (index, mask_type, alpha):
                control.change(render_visualization, [dataset_box, case, axis, index, mask_type, alpha], outputs)
            start_predict_btn.click(
                start_prediction,
                [
                    dataset_box,
                    case,
                    axis,
                    index,
                    mask_type,
                    alpha,
                    prompt_mode,
                    segrap_root,
                    segrap_contrast,
                    segrap_duplicate,
                    segrap_output,
                ],
                [mask_type, *outputs],
            )
            segrap_prepare.click(
                prepare_segrap_case,
                [dataset_box, case, segrap_root, segrap_contrast, segrap_duplicate],
                status,
            )
            segrap_import.click(
                import_segrap_prediction,
                [dataset_box, case, axis, index, alpha, segrap_root, segrap_output],
                [mask_type, *outputs],
            )
            montage_btn.click(
                render_montage,
                [dataset_box, case, axis, mask_type, alpha],
                [montage_out, montage_note],
            )
            if initial_case:
                demo.load(update_case_or_axis, [dataset_box, case, axis, mask_type, alpha], [index, *outputs])
                demo.load(render_montage, [dataset_box, case, axis, mask_type, alpha], [montage_out, montage_note])

        with gr.Tab("可复现工作流"):
            workflow_id = gr.Dropdown(
                choices=[(item["name"], item["id"]) for item in workflow_engine.list_workflows()],
                value="submission_audit",
                label="JSON 工作流模板",
            )
            workflow_query = gr.Textbox(
                value="比较病例影像、分割统计表与相关医学图像分割文献",
                label="检索问题",
            )
            workflow_case = gr.Dropdown(choices=case_choices, value=initial_case, label="病例")
            workflow_threshold = gr.Slider(
                0.0, 0.2, 0.05, step=0.005,
                label="条件分支阈值（真实标注前景占比）",
            )
            workflow_dataset = gr.Textbox(value=str(DEFAULT_NPC_DATASET_DIR), visible=False)
            run_btn = gr.Button("执行工作流并显示轨迹", variant="primary")
            result_json = gr.Textbox(label="执行轨迹与结果", lines=24, max_lines=40)
            run_btn.click(
                run_workflow,
                [workflow_id, workflow_dataset, workflow_case, workflow_query, workflow_threshold],
                result_json,
            )


if __name__ == "__main__":
    demo.launch(inbrowser=True, show_api=False)
