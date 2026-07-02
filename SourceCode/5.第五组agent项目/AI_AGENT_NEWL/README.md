# AI_AGENT_NEWL

本提交对应《深度学习与生命科学》AI Agent 课程项目。作业内容全部来自 new 版本；old 版本不作为代码或数据来源。

## 提交结构

- `PartA_知识资产与评测基准/data/`：75 个 `content/ + keywords.json + source.json` 知识资产，已按官方来源类型整理到 `01-academic/`、`02-textbook/`、`03-course/`、`06-knowledge-base/`。
- `PartA_知识资产与评测基准/benchmark/qa_dataset.json`：81 道字段完整、ID 唯一、带来源的 QA。
- `PartA_知识资产与评测基准/validation_summary.json`：Part A 自动检查结果。
- `SCORING_REPORT.md`：对照课程 100 分评分标准的自评说明和证据索引。
- `PartB_智能体应用项目/code/`：本地问答、NIfTI 处理、真实标注可视化、多模态检索、静态工作流基线和 Lv.3 动态编排执行器。
- `PartB_智能体应用项目/agent_registry.json`：动态编排使用的 Agent 能力注册表，包含输入、输出、并行能力和 fallback 关系。
- `PartB_智能体应用项目/workflows.json`：4 个预定义工作流及 Agent 角色、输入、输出和参数，作为动态编排的静态基线对照。
- `PartB_智能体应用项目/evaluation/`：评测问题、执行轨迹、自动评分结果和流程图。
- `PartB_智能体应用项目/tests/test_core.py`：核心功能与边界情况测试。

## 本地运行边界

- 知识检索、问答回退、NIfTI处理、工作流和全部评测默认完全离线运行。
- 系统只从提交包内知识资产、病例数据和本地 HTML 读取内容，不抓取在线网页。
- DashScope 仅作为可选回答增强保留；默认 `ENABLE_DASHSCOPE=0`。只有显式设置为 `1` 且提供 `API_KEY` 才会调用云端，未启用时不影响任何核心功能与评测。
- `source.json` 中的网页地址只是来源引用元数据，本地检索不会访问这些地址。

## 自选模块（难度和 = 5）

### 1. 进阶动态编排 Lv.3（难度 3）

- `DynamicPlanner` 根据问题实时判断 intent、复杂度、病例需求、模型预测需求和证据需求，并从 `agent_registry.json` 生成工作流节点。
- `DynamicWorkflowExecutor` 支持顺序、并行、条件检查、运行时插入节点、retry 和 fallback recovery。
- `QualityGate` 会根据中间结果动态插入小目标复核、大区域复核或 query rewrite retry 节点。
- `RecoveryManager` 会在 MedSAM 不可用、病例缺失等场景中切换到注册表内的 fallback agent。
- 12 道动态编排评测已生成 `dynamic_orchestration_results.json`、`dynamic_decision_traces.json`、`dynamic_plan_comparison.json` 和 `dynamic_recovery_case.json`。
- 原 Lv.2 静态工作流保留为 baseline：`workflows.json`、`workflow_engine.py`、`workflow_modes.svg`。

### 2. 多模态知识库 Lv.2（难度 2）

- 75 条文本、277 条影像、277 条表格记录；提交包保留完整 NPC 病例数据集。
- `ingest_html_document()` 仅从提交包内的本地 HTML 抽取文本、图像引用和表格；不访问互联网。本地演示结果见 `evaluation/document_extraction_demo.json`。
- 20 道单模态和多模态联合问题。
- 支持文本、影像、表格的模态过滤、确定性排序、无命中返回和证据 ID。
- 构建流程与检索流程图保存在 `evaluation/flowcharts/`。

## 运行

```powershell
pip install -r requirements.txt
python PartB_智能体应用项目/code/evaluation_runner.py
python PartB_智能体应用项目/code/run_dynamic_orchestration_demo.py
python -m unittest discover -s PartB_智能体应用项目/tests -v
python PartB_智能体应用项目/code/web_ui.py
```

如需启用“开始预测”中的 MedSAM 2D 当前切片功能，额外安装：

```powershell
pip install -r requirements-medsam.txt
pip install "numpy>=1.26,<2" --force-reinstall
```

项目已包含 `PartB_智能体应用项目/model_weights/medsam/medsam_vit_b.pth` 权重。MedSAM 当前只做 2D 切片预测演示，预测会保存为当前病例目录下的 `prediction_medsam_slice.npy`。

如需启用 SegRap2023 Task2 GTV 分割适配，额外安装本地 `.mha` 读写依赖：

```powershell
pip install -r requirements-segrap2023.txt
```

SegRap2023 官方推理通过 Docker/nnU-Net 运行，适配流程如下：

1. 在网页“分割可视化与评测”中选择病例，点击“生成 SegRap2023 输入与命令”。
2. 系统会在 `PartB_智能体应用项目/segrap2023_io/input/` 下生成官方需要的 `head-neck-ct/` 与 `head-neck-contrast-enhanced-ct/` 两个 `.mha` 目录，并生成 Docker 构建/运行命令。
3. 在安装 NVIDIA Docker 的 GPU 环境中构建并运行官方 `Astarakee/segrap2023` 的 `task2` 镜像。
4. 推理完成后，将输出目录挂回本项目，点击“导入 SegRap2023 3D 输出”，系统会把 `gross-tumor-volume-segmentation/{case_id}.mha` 转为病例目录下的 `prediction_segrap2023.npy`，可直接选择“SegRap2023 3D 预测”查看 Dice/IoU。

同一流程也可用命令行复现：

```powershell
python PartB_智能体应用项目/code/segrap2023_cli.py prepare --case-id 036
python PartB_智能体应用项目/code/segrap2023_cli.py import-output --case-id 036
```

当前内置 NPC 演示数据只有单模态 CT；若没有额外增强 CT，适配器会复制原 CT 作为演示兼容输入。该策略用于展示格式与流程适配，真实模型精度仍应以配准后的非增强 CT + 增强 CT 双模态输入为准。

如果本机没有官方 SegRap2023 Docker 输出，网页“开始预测”会生成 `prediction_segrap2023.npy` 本地演示 mask，用于保证可视化与指标流程可展示；该结果会在界面状态中标注为演示结果，不等同于官方权重推理。

如需主动启用可选 DashScope 增强，可复制 `code/.env.example` 为 `code/.env`，将
`ENABLE_DASHSCOPE` 改为 `1` 并填写 `API_KEY`。课程提交和离线演示不需要执行此步骤。

## 评分证据入口

| 评分点 | 直接证据 |
|---|---|
| 知识资产数量与三件套 | `PartA_知识资产与评测基准/validation_summary.json` |
| 官方来源类型目录 | `PartA_知识资产与评测基准/data/01-academic/`、`02-textbook/`、`03-course/`、`06-knowledge-base/` |
| 论文 DOI / 来源 URL | 51/51 篇 `academic-paper` 有 DOI；75/75 有 URL；3 条 `web-resource` 已标注待人工复核 |
| QA 数量、格式和唯一 ID | `PartA_知识资产与评测基准/benchmark/qa_dataset.json` |
| Part A 与来源链检查 | 工作流 `submission_audit` 的轨迹 |
| Lv.3 动态编排能力注册表 | `PartB_智能体应用项目/agent_registry.json` |
| 运行时计划生成与执行器 | `PartB_智能体应用项目/code/dynamic_orchestrator.py` |
| 12 道动态编排评测 | `evaluation/dynamic_orchestration_results.json` |
| 决策轨迹、重试与恢复证据 | `evaluation/dynamic_decision_traces.json`、`dynamic_recovery_case.json` |
| 静态工作流基线 | `PartB_智能体应用项目/workflows.json`、`evaluation/orchestration_benchmark_results.json` |
| 3 模态规模与20题结果 | `evaluation/multimodal_demo_results.json` |
| 默认离线及远程HTML拒绝 | `PartB_智能体应用项目/tests/test_core.py` 与 `evaluation/unit_test_results.json` |
| 可视化流程图 | `evaluation/flowcharts/advanced_dynamic_orchestration.svg`、`dynamic_recovery_loop.svg`、`workflow_modes.svg` |
| 总体结果 | `evaluation/evaluation_summary.json` 与 `evaluation/rubric_evidence.json` |
| 对照评分文档 | `SCORING_REPORT.md` |

## 诚实边界

- 分割页面用于查看真实标注、MedSAM 2D 切片预测及 SegRap2023 3D 预测；真实标注不与自身计算 Dice/IoU。
- MedSAM 适配器与 `model_weights/medsam/medsam_vit_b.pth` 权重保留；MedSAM 预测为可选切片演示，真实 mask 可视化和全部评分证据不依赖云端服务。
- SegRap2023 Task2 适配已接入输入导出、Docker 命令生成和输出导入；官方推理需要 NVIDIA Docker/GPU 环境，且真实高精度结果依赖双模态 CT。
- 75 个来源都有 URL；51 篇 `academic-paper` 已补 DOI 或 arXiv DOI。
- 3 个 `web-resource` 仍为题名检索回退页，已在 `source.json` 中保留 `source_quality_note`，建议提交 PR 前人工替换为论文直达页。
