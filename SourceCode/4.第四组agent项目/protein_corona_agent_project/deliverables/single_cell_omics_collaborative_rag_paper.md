# 面向单细胞与空间组学知识资产的协作式 RAG Agent 系统设计与实现

## 摘要

单细胞与空间组学文献具有方法密集、实体密集和证据链复杂的特点。传统的基于关键词或单次向量检索的问答系统虽然能够从文献中召回相关片段，但在面对比较型、综述型、跨文献综合型问题时，容易出现检索目标不明确、元数据约束失效、引用证据不平衡以及生物实体规范化不足等问题。本文设计并实现了一个面向单细胞与空间组学课程知识资产的协作式 RAG Agent 系统。系统以 PDF、EPUB、文本和结构化元数据为知识资产输入，构建了基于 bge-m3 的向量检索库和 SQLite 结构化知识库，并在基础 RAG 之上进一步集成 Agentic RAG、Hybrid RAG、多层持久记忆系统和 UniProtProteinSkill 外部工具。最终的协作问答模式将历史记忆、LLM 检索规划、结构化候选过滤、段落级向量检索和 UniProt 蛋白/基因注释融合到同一条回答链路中。当前系统包含 29 套知识资产元数据、4,696 个向量化文本块、28 条结构化论文/书籍记录和 20 题领域 benchmark。实验与系统测试表明，该设计能够使课程项目从单一检索演示扩展为可追溯、可消融、可评测的专业领域问答 Agent。

**关键词：** 单细胞组学；空间组学；检索增强生成；Agentic RAG；结构化知识库；UniProt；记忆系统

## 1 引言

近年来，单细胞 RNA 测序、空间转录组、多组学整合和基础模型方法快速发展，相关文献呈现出明显的高密度知识特征。一篇论文往往不仅包含方法名称和实验结论，还涉及输入数据类型、空间约束、模型目标、评价指标、适用场景和生物学实体。例如，Nicheformer 关注单细胞与空间组学之间的基础表示学习，CONCORD 关注跨单细胞数据集的一致细胞状态景观，CytoSignal 面向空间转录组中的配体-受体信号，REMAP 则试图从 scRNA-seq 推断多尺度组织空间结构。这类问题如果只依赖单次向量检索，容易把不同方法混淆，或者只检索到一个对象而无法完成比较。

本项目的目标不是训练一个新的大语言模型，而是让已有 LLM 能够可靠地检索、组织和使用课程知识资产。为此，系统围绕三个核心要求展开：第一，知识资产必须可追溯，回答中的关键事实应能回到具体文献片段；第二，检索过程必须可解释，尤其是复杂问题应显示其拆解和检索轨迹；第三，系统需要扩展出 Agent 能力，使其不仅能检索本地知识库，还能调用外部生物数据库并保存交互记忆。

围绕上述目标，本文实现了一个协作式 RAG Agent。该系统既保留基础 RAG、Agentic RAG、Hybrid RAG 和 UniProt Skill 的独立按钮作为消融实验入口，也提供“协作问答”作为最终集成模式。协作问答模式将多个可选模块串联为一个统一流程，从而避免各模块成为互不相关的演示功能。

## 2 知识资产构建

### 2.1 知识集格式

本项目采用统一的知识集目录结构来组织课程资料。每个知识集包含 `content/`、`source.json` 和 `keywords.json` 三类内容。其中，`content/` 存放 PDF、EPUB、TXT、Markdown 或 HTML 等原始资料；`source.json` 记录标题、作者、年份、期刊、DOI、URL 等来源信息；`keywords.json` 存放主题、关键词和方法实体等检索辅助信息。

这种结构的目的不是要求人工逐句标注文献，而是将资料分为“原文内容”和“可结构化元数据”两个层次。原文内容用于向量化检索，元数据用于精确过滤和知识库构建。例如，用户问题中出现“2026 年 Nature Biotechnology 的 foundation model 或 interpretability 论文”时，年份、期刊和主题词更适合由结构化数据库处理，而不是完全交给语义向量相似度。

### 2.2 文本切分与向量化

系统支持 PDF 和 EPUB 等常见出版物格式。构建向量库时，程序先从文件中提取文本，再按固定字符窗口切分为文本块，并保留一定 overlap，以降低语义边界被切断的风险。当前配置采用 bge-m3 作为本地 embedding 模型，通过 Ollama 服务生成 1,024 维向量。向量库运行时存储在 `storage/vector_store_bge_m3/` 中，包括 `chunks.jsonl`、`vectors.npy` 和 `manifest.json`。

截至当前版本，向量库包含 4,696 个文本块，向量矩阵形状为 `4696 x 1024`。这种 NumPy 向量库实现比完整 Chroma 依赖更轻量，也更适合当前 Windows + PyCharm 的课程开发环境。系统仍保留 Chroma 相关代码作为兼容实验路径，但主运行时以轻量向量库为准。

### 2.3 结构化知识库

除向量库外，系统还从 `source.json` 和 `keywords.json` 构建 SQLite 结构化知识库。数据库包含 `papers`、`authors`、`themes`、`keywords`、`methods` 及其多对多关系表。当前结构化库包含 28 条论文/书籍记录、316 个作者条目、111 个关键词、24 个主题和 14 个方法实体。

结构化知识库承担“精确条件”的处理任务。向量检索擅长寻找语义相关段落，但不擅长稳定处理年份、期刊、方法名、主题标签等离散约束。Hybrid RAG 因此先用 SQLite 找到候选知识集，再在候选集合内部进行向量检索，从而减少无关文献干扰。

## 3 基础 RAG 问答流程

基础 RAG 是系统的最小闭环。用户问题首先通过同一个 embedding 模型转为查询向量，随后在本地向量库中计算相似度，取 top-k 文本块作为上下文。系统将问题、检索片段和来源元数据共同构造成最终 LLM 请求，并要求模型用中文回答，同时在关键事实后使用 `[1]`、`[2]` 等编号引用来源。

基础 RAG 的优点是流程清晰、成本较低、便于调试。它适合回答单篇论文解释型问题，例如“Nicheformer 主要解决了什么问题”。但当问题要求比较多个方法、检索多个主题或判断证据不足时，单次检索往往不够稳健。因此，基础 RAG 在本项目中被定位为基线，而不是最终形态。

## 4 Agentic RAG：检索规划与多步检索

Agentic RAG 在基础 RAG 之前加入一个 LLM planner。planner 不直接回答问题，而是输出严格 JSON 格式的检索计划，包括 `need_retrieval`、`question_type`、`reasoning` 和 `steps`。每个 step 包含检索 query、检索目的和 top-k 数量。Python 程序负责解析计划并执行每一步检索，然后去重证据并交给最终回答模型。

这种设计的核心价值在于将复杂问题显式拆解。例如，面对“比较 Nicheformer 和 CONCORD 在单细胞组学中的作用差异”时，planner 可以分别生成针对 Nicheformer 和 CONCORD 的检索步骤，再增加综合比较步骤。这样可以避免系统只召回其中一篇论文，从而提高比较题的来源平衡性。

系统还实现了 planner cache 和 fallback 机制。当外部 LLM API 暂时不稳定时，程序会复用缓存计划或退回原问题检索，保证检索链路不会直接崩溃。这一点对课程演示尤其重要，因为评审时系统的可运行性比单次最优回答更关键。

## 5 Hybrid RAG：结构化过滤与向量检索协作

Hybrid RAG 的动机是弥补向量检索对精确元数据约束的不稳定性。系统首先调用结构化知识库，根据用户问题中的年份、期刊、主题、关键词或方法实体筛选候选知识集。如果存在候选集合，则向量检索只在候选知识集内部执行；如果没有候选集合，则退回普通向量检索。

例如，当用户询问“哪些 2026 年 Nature Biotechnology 论文涉及 foundation model 或 interpretability”时，系统可以先由结构化 KB 处理 `2026`、`Nature Biotechnology`、`foundation-model` 和 `interpretability` 等条件，再在候选论文中检索原文片段作为证据。这样既利用了 SQL 的精确性，又保留了向量检索对自然语言问题的适应性。

Hybrid RAG 的返回结果中包含结构化候选、匹配原因和最终证据片段。Web 页面中的 trace 面板会显示诸如 `year:2026`、`journal:Nature Biotechnology`、`keyword:foundation-model`、`theme:interpretability` 等匹配依据，使检索决策过程可解释。

## 6 多层持久记忆系统

记忆系统为 RAG 增加了跨轮次和跨会话的信息延续能力。本项目实现了三层 SQLite 记忆结构：working memory、episodic memory 和 semantic memory。Working memory 保存当前 session 的近期对话；episodic memory 保存跨会话问答经验、答案摘要和来源 ID；semantic memory 从交互中抽取保守的实体关系三元组，例如方法-主题关系、论文-DOI 关系或论文-关键词关系。

当前记忆库文件为 `storage/memory.sqlite3`。运行时 health endpoint 显示，系统已有 working memory、episodic memory 和 semantic memory 三类记录。协作问答和 Hybrid RAG 会在回答前检索相关记忆，在回答后将本次交互写回记忆库。这样，系统可以在后续追问中利用历史偏好和已知上下文，但记忆内容不会替代文献证据。

本项目采用关键词匹配而非向量记忆，主要是出于可解释性和开发稳定性考虑。后续可进一步为 memory 建立单独 embedding 索引，并加入过期、压缩和可信度策略。

## 7 UniProtProteinSkill：外部生物数据库工具

在生物医学问答中，很多问题同时涉及文献证据和标准生物实体。例如，用户询问“OCT4 在细胞重编程中是什么角色”时，本地知识库可能提供细胞重编程语境，但蛋白/基因的标准名称、accession、别名和功能注释更适合从 UniProt 获取。因此，本项目实现了 UniProtProteinSkill，将 UniProt REST API 封装为本地可调用工具。

该 Skill 提供三个函数：`search_protein` 用于按基因/蛋白名搜索 reviewed human UniProtKB 条目；`get_protein` 用于按 accession 获取条目；`explain_protein_for_context` 用于结合用户问题返回简洁功能解释。UniProt 是公开数据库，不需要申请 API key。测试结果显示，`OCT4` 可映射到 `Q01860`，对应 `POU domain, class 5, transcription factor 1`；`TP53/P53` 可映射到 `P04637`，对应 `Cellular tumor antigen p53`。

为了避免把方法名误识别成蛋白名，系统采用保守的规则和正则触发策略。它会识别已知基因别名、UniProt accession 和明显带数字的基因符号，同时过滤 `REMAP`、`CONCORD`、`Nicheformer` 等方法名。更完整的升级方向是接入 HGNC 或 UniProt 候选校验，将本地抽取出的候选词逐个验证为 approved gene symbol 或 reviewed protein entry。

## 8 协作式 Agentic Hybrid RAG

最终系统的核心不是多个孤立按钮，而是“协作问答”模式。该模式将记忆检索、Agentic planner、结构化知识库、向量检索和 UniProt Skill 集成到同一条链路中。其执行流程如下：

1. 用户提出自然语言问题。
2. 系统检索相关历史记忆，形成 memory context。
3. LLM planner 生成多步检索计划。
4. 每个检索步骤先查询结构化 KB；若有候选知识集，则执行过滤向量检索；否则执行普通向量检索。
5. 系统去重所有证据片段。
6. 系统检测问题中的蛋白/基因实体，必要时调用 UniProtProteinSkill。
7. 最终 LLM 同时接收原始问题、记忆上下文、planner JSON、结构化候选、检索轨迹、文献证据和 UniProt 结果。
8. 答案生成后写回 working、episodic 和 semantic memory。

这一设计使各个可选模块不再只是独立功能，而是在最终模式中形成协作关系。独立的“问答”“Agentic 问答”“Hybrid 问答”和“UniProt Skill”按钮仍保留在 Web App 中，用于消融实验和课堂展示；真正的最终系统则通过“协作问答”按钮体现。

## 9 Benchmark 设计

为了评估不同 RAG 变体，本项目设计了 20 题单细胞/空间组学 benchmark。题型覆盖单篇论文解释、方法比较、多文献综合、质量控制、benchmark reasoning、生物学解释和证据不足判断。每题包含问题类型、难度、主题、必需知识集 ID、预期回答要点、禁止声称内容和检索期望。

评分维度包括五项：检索相关性 30 分、答案正确性 35 分、引用忠实度 20 分、推理与综合 10 分、格式与清晰度 5 分。这样的评分设计强调 RAG 系统不应只追求回答流畅，而应同时检验是否召回了正确来源、是否依据证据回答、是否在比较题中平衡多个来源、以及是否能在证据不足时拒绝过度推断。

Benchmark 中包含多个高风险问题。例如，“是否可以得出一个通用 foundation model 已经可以替代所有专用空间组学方法”的问题要求系统明确不能从当前知识库得出这种结论，并同时引用 Nicheformer、CytoSignal、3D-OT 和 SpatialGlue 等不同任务来源。这类问题用于测试系统的幻觉控制能力。

## 10 系统实现与运行界面

系统以 Python 脚本为主实现，面向 PyCharm 运行环境进行了适配。用户无需在控制台传参，而是可以直接修改脚本顶部常量运行。核心模块包括 `build_vector_store.py`、`build_structured_kb.py`、`rag_core.py`、`agentic_rag.py`、`hybrid_rag.py`、`agentic_hybrid_rag.py`、`memory_system.py` 和 `scripts/skills/`。

本地 Web App 由 `rag_web.py` 提供，默认运行在 `http://127.0.0.1:8000`。界面包含六个操作入口：只检索、问答、协作问答、UniProt Skill、Agentic 问答和 Hybrid 问答。Health endpoint 会显示 embedding 模型、LLM 模型、向量库目录、chunk 数量、向量矩阵形状和记忆库统计。当前运行配置使用 Ollama `bge-m3` 作为 embedding 模型，外部 OpenAI-compatible API 中的 `deepseek-ai/DeepSeek-V4-Flash` 作为生成模型。

## 11 局限性与改进方向

当前系统已经完成课程项目所需的核心链路，但仍存在若干局限。首先，文本切分采用字符窗口和 overlap，虽然简单稳定，但仍可能切断复杂语义结构。后续可引入基于标题、段落、图表说明和参考文献边界的结构化切分策略。其次，Skill 触发目前依赖保守规则和手写别名表，能够减少误调用，但会漏掉部分纯字母的新基因符号。更正式的方案是引入 HGNC gene symbol / alias 校验，再将规范化后的 symbol 交给 UniProt 查询。

第三，记忆系统目前采用关键词匹配，优点是可解释、低成本，缺点是不能充分处理语义相似的历史问题。后续可构建独立 memory embedding index，并加入时间衰减、置信度和用户偏好分层。第四，当前 benchmark 已经设计完成，但仍需要系统性跑分，以量化 Basic RAG、Agentic RAG、Hybrid RAG 和协作问答之间的实际差异。

最后，系统调用外部 LLM 和 UniProt API，因此在网络不稳定时仍可能出现延迟或失败。当前系统通过 planner cache、fallback answer 和错误返回降低演示风险，但若部署为正式服务，还需要更完整的重试、限流、缓存和日志监控。

## 12 结论

本文设计并实现了一个面向单细胞与空间组学知识资产的协作式 RAG Agent 系统。系统从知识资产组织出发，将 PDF、EPUB 和结构化元数据转化为向量库与 SQLite 知识库，并在基础 RAG 之上集成 Agentic planner、Hybrid RAG、多层持久记忆和 UniProtProteinSkill。最终的协作问答模式能够同时使用历史上下文、检索计划、结构化候选、段落证据和外部蛋白注释，形成可追溯、可解释、可消融的问答链路。

该项目的核心贡献在于：第一，将课程知识资产构建为可持久化、可检索、可结构化的本地知识库；第二，将多个可选模块整合到一个实际协作流程中，而不是停留在独立演示；第三，设计了 20 题 benchmark，用于从检索、答案、引用、推理和格式五个维度评估系统表现。整体来看，该系统证明了在不训练新 LLM 的前提下，通过合理的知识资产工程、检索编排和工具调用，也可以构建面向专业文献的实用型领域 Agent。

## 参考文献

[1] Nicheformer: a foundation model for single-cell and spatial omics. 项目知识集：`nicheformer-foundation-model-single-cell-spatial-omics-2025`。

[2] Revealing a coherent cell-state landscape across single-cell datasets with CONCORD. 项目知识集：`concord-cell-state-landscape-single-cell-atlases-2026`。

[3] Reconstructing multi-scale tissue spatial architecture from single-cell RNA-seq with REMAP. 项目知识集：`reconstructing-multiscale-tissue-spatial-architecture-remap-2026`。

[4] CytoSignal detects locations and dynamics of ligand-receptor signaling at cellular resolution from spatial transcriptomic data. 项目知识集：`cytosignal-ligand-receptor-spatial-transcriptomics-2026`。

[5] UniProt Consortium. UniProt: the Universal Protein Knowledgebase. 系统使用 UniProt REST API：`https://rest.uniprot.org`。

[6] 项目源码与运行文档：`README.md`、`docs/AGENTIC_RAG.md`、`docs/STRUCTURED_KB.md`、`docs/MEMORY_SYSTEM.md`、`docs/SKILL_SYSTEM.md`、`docs/AGENTIC_HYBRID_RAG.md`。
