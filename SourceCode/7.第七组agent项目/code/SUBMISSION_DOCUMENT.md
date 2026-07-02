# AI Agent 课程项目提交总说明

## 项目信息

- 课程项目：深度学习与生命科学 AI Agent 课程项目
- 研究方向：`medical-image-segmentation`
- 组员一：杨兴钊，`25210812000032`
- 组员二：赵帅，`25220854050036`

## 文件整理说明

本提交将以下三部分统一整理到本说明文档，并随完整项目一起打包：

1. 修改后的完整项目：`AI_AGENT_NEWL`
2. 评分文档：`SCORING_REPORT.md`
3. 修订摘要：`REVISION_SUMMARY.md`

其中 `SCORING_REPORT.md` 已保留在项目根目录；`REVISION_SUMMARY.md` 的核心内容已合并进本文档。

## 课程评分对齐结果

| 模块 | 满分 | 实现结果 | 建议得分 |
|---|---:|---|---:|
| 知识资产 | 35 | 75 个知识集，官方来源类型分层，三件套完整；51/51 篇论文有 DOI 或 arXiv DOI；3 条 web-resource 来源仍需人工替换为直达页 | 34/35 |
| 评测基准 | 35 | 81 道题，字段完整、ID 唯一、来源可追溯、主题为 `medical-image-segmentation` | 35/35 |
| 知识问答项目 | 30 | 选择两个 Lv.2 模块，难度和 4；编排和多模态评测全部通过 | 30/30 |
| **保守总分** | **100** | 扣除 1 分来源复核风险 | **99/100** |

如果将 3 条 `web-resource` 的题名检索回退页替换为 DOI、arXiv 或论文直达页，可主张 `100/100`。

## Part A：知识资产与评测基准

### 知识资产

- 总数：75 个知识集
- 结构：75/75 包含 `content/`、`keywords.json`、`source.json`
- 内容：75/75 `content.txt` 非空
- 关键词：75/75 通过 kebab-case 检查
- 来源类型分布：
  - `01-academic`：51
  - `02-textbook`：4
  - `03-course`：15
  - `06-knowledge-base`：5
- 来源质量：
  - 75/75 有 URL
  - 51/51 篇 `academic-paper` 有 DOI 或 arXiv DOI
  - 3 条 `web-resource` 仍为题名检索回退页，已在 `source.json` 中标记 `source_quality_note`

### 评测基准

- 题目数量：81 道
- Schema：81/81 字段完整
- ID：81/81 唯一
- 来源链：81/81 绑定本地知识资产
- 引用核验：81/81 引用原文可在知识资产中复核
- 主题：81/81 使用 `medical-image-segmentation`

## Part B：知识问答项目

本项目选择两个 Lv.2 自选模块，难度和为 `2 + 2 = 4`，满足课程要求。

### 模块一：进阶静态编排 Lv.2

- 4 个 JSON 工作流模板
- 支持串行、并行、条件分支
- 每个节点声明 Agent 角色、输入、输出和参数
- 每次执行保存节点轨迹、运行状态、耗时、输入键、输出和条件分支决策
- 编排评测：12/12 通过
- 流程图保存在 `PartB_智能体应用项目/evaluation/flowcharts/`

### 模块二：多模态知识库 Lv.2

- 文本记录：75
- 影像记录：277
- 表格记录：277
- 支持文本、影像、表格的模态过滤、确定性排序和本地证据 ID
- 本地 HTML 可抽取文本、图像引用和表格
- 多模态评测：20/20 通过

### 模型演示增强：SegRap2023 Task2 GTV 适配

- 新增 `SegRap2023Adapter`，用于鼻咽癌 GTV 分割模型的输入/输出适配。
- 可将本项目病例导出为官方要求的双目录 `.mha` 结构：`head-neck-ct/` 与 `head-neck-contrast-enhanced-ct/`。
- 可生成官方 Docker 构建与推理命令，便于在 NVIDIA Docker/GPU 环境中运行 `Astarakee/segrap2023` 的 `task2`。
- 可将官方输出 `gross-tumor-volume-segmentation/{case_id}.mha` 导回 `prediction_segrap2023.npy`，并在网页中查看 SegRap2023 3D 预测 mask 与 Dice/IoU。
- 当前演示数据只有单模态 CT；无增强 CT 时采用复制当前 CT 的演示兼容策略，真实精度需使用配准后的双模态 CT。

## 最新验证结果

| 验证项 | 结果 |
|---|---:|
| 知识资产结构检查 | 75/75 |
| 评测题 schema 与来源链 | 81/81 |
| 多模态评测 | 20/20 |
| 编排评测 | 12/12 |
| 单元测试 | 19/19 |
| 工作流模板 | 4 |
| 工作流模式 | sequential / parallel / conditional |
| 运行模式 | 默认本地离线，DashScope 显式启用才调用 |

## 关键证据文件

- `PartA_知识资产与评测基准/data/`
- `PartA_知识资产与评测基准/benchmark/qa_dataset.json`
- `PartA_知识资产与评测基准/validation_summary.json`
- `PartB_智能体应用项目/selected_modules.json`
- `PartB_智能体应用项目/workflows.json`
- `PartB_智能体应用项目/evaluation/evaluation_summary.json`
- `PartB_智能体应用项目/evaluation/rubric_evidence.json`
- `PartB_智能体应用项目/evaluation/orchestration_benchmark_results.json`
- `PartB_智能体应用项目/evaluation/multimodal_demo_results.json`
- `PartB_智能体应用项目/evaluation/flowcharts/`
- `SCORING_REPORT.md`

## 已完成的修改

- 将知识资产从扁平目录整理为官方来源类型分层。
- 为论文来源补充 DOI 或 arXiv DOI。
- 将无法确认论文 DOI 的条目标记为 `web-resource`。
- 修改 RAG、多模态索引、工作流审计和 PartA 验证脚本，使其兼容官方分层目录。
- 更新小组成员信息为：杨兴钊 `25210812000032`、赵帅 `25220854050036`。
- 刷新验证结果和评分证据文件。
- 接入 MedSAM 当前切片预测与 SegRap2023 Task2 GTV 格式/模态适配流程。

## 提交提醒

- PR 描述中说明选修模块为：进阶静态编排 Lv.2 + 多模态知识库 Lv.2，难度和 4。
- PR 中附上 `evaluation/evaluation_summary.json` 的关键结果。
- 演示截图或日志可引用 `PartB_智能体应用项目/evaluation/flowcharts/` 与各类评测 JSON。
- 提交前如有时间，建议人工替换 3 条 `web-resource` 回退来源。
