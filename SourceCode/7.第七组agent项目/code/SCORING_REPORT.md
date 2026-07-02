# AI Agent 课程项目评分文档

本文件依据课程仓库 `Yuplx-HU/ai-agent-assignment` 的 100 分评分标准整理，用于 PR 描述和教师审阅。项目研究方向为 `medical-image-segmentation`。


## 一、知识资产模块

| 评分点 | 满分 | 课程要求 | 本项目证据 | 自评 |
|---|---:|---|---|---:|
| 数量达标 | 7 | 至少 20 个有效知识集 | `validation_summary.json` 显示 75 个 | 7 |
| 文件完整 | 7 | 每个知识集包含 `content/`、`keywords.json`、`source.json` | 75/75 三件套完整 | 7 |
| 格式规范 | 7 | kebab-case 主题和关键词 | 75/75 关键词文件通过检查 | 7 |
| 领域内广度 | 5 | 覆盖不同来源/类型 | `01-academic` 51、`02-textbook` 4、`03-course` 15、`06-knowledge-base` 5 | 5 |
| 内容充实 | 5 | 内容非空、可检索 | 75/75 `content.txt` 非空，并被 RAG/多模态索引读取 | 5 |
| 来源可靠 | 4 | 论文有 DOI，网页有 URL | 51/51 篇论文有 DOI；75/75 有 URL；3 条 web-resource 仍为检索页 | 3 |

直接证据：

- `PartA_知识资产与评测基准/data/`
- `PartA_知识资产与评测基准/validation_summary.json`
- `PartB_智能体应用项目/evaluation/rubric_evidence.json`

## 二、评测基准模块

| 评分点 | 满分 | 课程要求 | 本项目证据 | 自评 |
|---|---:|---|---|---:|
| 问题数量 | 7 | 至少 20 个有效问题 | `qa_dataset.json` 共 81 道 | 7 |
| 答案准确 | 7 | 答案与本地证据一致 | 81/81 题带标准答案和原文片段 | 7 |
| 格式规范 | 7 | JSON 字段齐全 | 81/81 通过 schema 检查 | 7 |
| 问题质量 | 5 | 表述清晰、无明显歧义 | 覆盖模型机制、医学图像分割、训练策略、多模态证据 | 5 |
| 来源引用 | 5 | 每题有准确来源 | 81/81 来源绑定到本地知识资产，引用片段可复核 | 5 |
| 主题分类 | 4 | 使用预定义主题词 | 81/81 使用 `medical-image-segmentation` | 4 |

直接证据：

- `PartA_知识资产与评测基准/benchmark/qa_dataset.json`
- `PartA_知识资产与评测基准/validation_summary.json`

## 三、知识问答项目

已选择两个 Lv.2 模块，难度和 `2 + 2 = 4`，满足课程要求。

| 可选模块 | 难度 | 实现证据 | 模块自评 |
|---|---:|---|---:|
| 进阶静态编排 | Lv.2 | 4 个 JSON 工作流模板；支持串行、并行、条件分支；12/12 编排评测通过；流程图已生成 | 100/100 |
| 多模态知识库 | Lv.2 | 文本 75、影像 277、表格 277；20/20 多模态评测通过；本地 HTML 可抽取文本/图像/表格 | 100/100 |

加权计算：

```text
总难度和 = 2 + 2 = 4
模块权重 = 2/4, 2/4
加权总分 = 100 * 0.5 + 100 * 0.5 = 100
知识问答项目得分 = 100 * 0.3 = 30
```

直接证据：

- `PartB_智能体应用项目/selected_modules.json`
- `PartB_智能体应用项目/workflows.json`
- `PartB_智能体应用项目/code/workflow_engine.py`
- `PartB_智能体应用项目/code/multimodal_kb.py`
- `PartB_智能体应用项目/code/model_adapters/segrap2023_adapter.py`
- `PartB_智能体应用项目/evaluation/evaluation_summary.json`
- `PartB_智能体应用项目/evaluation/orchestration_benchmark_results.json`
- `PartB_智能体应用项目/evaluation/multimodal_demo_results.json`
- `PartB_智能体应用项目/evaluation/flowcharts/`

## 四、验证结果

已运行：

```text
python PartB_智能体应用项目/code/evaluation_runner.py
python -m unittest discover -s PartB_智能体应用项目/tests -v
```

最新结果：

| 验证项 | 结果 |
|---|---:|
| 多模态评测 | 20/20 |
| 编排评测 | 12/12 |
| 工作流模板 | 4 |
| 工作流模式 | sequential / parallel / conditional |
| 单元测试 | 19/19 |
| 运行模式 | 默认本地离线，DashScope 显式启用才调用 |

## 五、已完成的对齐修改

- 将知识资产从扁平目录整理为官方来源类型分层。
- 为论文来源补充 DOI 或 arXiv DOI，并将无法确认 DOI 的条目标记为 `web-resource`。
- 修改代码读取逻辑，使 RAG、多模态索引、工作流审计和证据构建都支持官方分层目录。
- 刷新 `validation_summary.json`、`evaluation_summary.json`、`rubric_evidence.json` 和测试日志。
- 新增本评分文档，便于 PR 中直接说明完成情况。
- 新增 SegRap2023 Task2 GTV 适配器，支持双模态 `.mha` 输入导出、Docker 命令生成、官方输出导入和网页可视化。

## 六、PR 提交清单

- 提交全部代码、数据、文档和评测结果。
- 在 PR 描述中说明选修模块：进阶静态编排 Lv.2 + 多模态知识库 Lv.2，难度和 4。
- 附上 `evaluation/evaluation_summary.json` 的关键结果。
- 附上流程图或演示日志路径：`PartB_智能体应用项目/evaluation/flowcharts/`。
- 提交前最好人工替换 3 条 `web-resource` 回退来源，位置可在 `validation_summary.json` 和 `rubric_evidence.json` 中定位。
