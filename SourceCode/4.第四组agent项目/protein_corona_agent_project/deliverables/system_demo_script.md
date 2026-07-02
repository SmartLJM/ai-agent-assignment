# 系统演示文稿（中英双语）

## Q0 健康检查

操作：

```text
打开 http://127.0.0.1:8000/health
```

展示：

```text
chunk_count、embedding_model、llm_model、structured_kb、memory
```

中文口播：

```text
我先展示系统的健康检查页面。这里不是问答结果，而是后端运行状态。
可以看到系统已经加载了向量索引、embedding 模型、结构化知识库和记忆数据库。
这一步的作用是证明后面的回答不是静态文本，而是由当前项目的 RAG 系统实时检索和生成的。
```

English script:

```text
First, I will show the health endpoint of the system. This page is not a generated answer; it shows the backend status.
Here we can see that the vector index, the embedding model, the structured knowledge base, and the memory database have been loaded.
This step proves that the following answers are not static demo text. They are produced by the running RAG system through real retrieval and generation.
```

## Q1 普通问答：基础 RAG

操作：

```text
输入问题：
Nicheformer 这篇论文主要解决了单细胞和空间组学中的什么问题？它为什么需要同时利用解离单细胞数据和空间转录组数据？

点击按钮：
问答
```

展示：

```text
右侧证据片段、回答中的引用、是否命中 Nicheformer 来源。
```

中文口播：

```text
这个问题用于展示最基础的 RAG 流程。
系统会先把问题向量化，然后在本地向量库中检索相关 chunk，最后把检索到的证据交给 LLM 生成回答。
这里重点看右侧证据片段。只要能看到 Nicheformer 相关来源，就说明系统不是单纯依赖 LLM 自己的记忆，而是先找到了本地知识库中的论文证据。
```

English script:

```text
This question demonstrates the basic RAG workflow.
The system first embeds the user question, retrieves relevant chunks from the local vector store, and then sends the retrieved evidence to the LLM for answer generation.
The key point is the evidence panel on the right. If the retrieved evidence comes from the Nicheformer source, then the answer is not only based on the LLM's internal memory. It is grounded in the local knowledge base.
```

## Q2 只检索：观察检索结果

操作：

```text
输入问题：
Nicheformer 如何利用空间上下文来改进单细胞表示学习？

点击按钮：
只检索
```

展示：

```text
检索结果列表、title、page、similarity、Nicheformer 相关 chunk。
```

中文口播：

```text
这一项不让 LLM 生成回答，只看检索结果。
这样可以把检索能力和语言生成能力拆开观察。
如果只检索已经能命中正确论文和相关片段，说明向量索引和 embedding 检索是有效的。
这个按钮也可以作为消融实验入口：先确认资料找得准，再讨论生成答案是否准确。
```

English script:

```text
This mode does not ask the LLM to generate an answer. It only shows the retrieved evidence.
This allows us to separate retrieval quality from language generation quality.
If retrieve-only mode already finds the correct paper and relevant chunks, then the vector index and embedding search are working properly.
This button is also useful for ablation, because we can first check whether the system finds the right evidence before judging the final answer.
```

## Q3 Hybrid RAG：结构化检索 + 向量检索

操作：

```text
输入问题：
请找出 2026 年左右与单细胞或空间组学 foundation model 相关的研究，并说明它们关注的问题。

点击按钮：
Hybrid 问答
```

展示：

```text
Structured candidates、matched_by、year、keyword、theme、右侧证据片段。
```

中文口播：

```text
这个问题用于展示 Hybrid RAG。
普通向量检索擅长找语义相似内容，但不擅长处理年份、主题、方法类型这种硬条件。
所以 Hybrid RAG 会先用结构化知识库筛出候选资料，比如年份接近 2026、主题包含 foundation model、关键词和单细胞或空间组学相关。
然后系统只在这些候选资料对应的 chunk 中做向量检索。
也就是说，结构化检索决定在哪些资料里找，向量检索决定这些资料里的哪些段落最相关。
```

English script:

```text
This question demonstrates Hybrid RAG.
Pure vector retrieval is good at semantic similarity, but it is not naturally reliable for hard constraints such as year, topic, or method type.
So Hybrid RAG first uses the structured knowledge base to select candidate sources. For example, it can look for sources around 2026, related to foundation models, and connected to single-cell or spatial omics.
After that, the system performs vector retrieval only inside the chunks that belong to those candidate sources.
In short, structured retrieval decides where to search, and vector retrieval decides which passages inside those sources are most relevant.
```

## Q4 Agentic RAG：多步检索规划

操作：

```text
输入问题：
比较 Nicheformer 和 CONCORD：它们分别解决什么问题，核心思路有什么不同？

点击按钮：
Agentic 问答
```

展示：

```text
question_type、reasoning、Step 1 / Step 2、每个 step 的 query 和 results、最终回答是否同时覆盖两篇论文。
```

中文口播：

```text
这个问题用于展示 Agentic RAG。
如果只做一次普通向量检索，系统可能只检索到 Nicheformer，或者只检索到 CONCORD，导致比较不平衡。
Agentic RAG 的做法是先让 LLM 作为 planner，把复杂问题拆成多个检索步骤。
例如第一步检索 Nicheformer，第二步检索 CONCORD，最后再综合二者的任务、数据和核心思路。
程序按这些 step 分别检索，再把多路证据合并交给 LLM 回答。
所以它适合比较题、多对象题和复杂综述题。
```

English script:

```text
This question demonstrates Agentic RAG.
If we use only one ordinary vector search, the system may retrieve mostly Nicheformer evidence or mostly CONCORD evidence, which makes the comparison unbalanced.
Agentic RAG uses the LLM first as a planner. The planner decomposes a complex question into several retrieval steps.
For example, one step can retrieve Nicheformer evidence, another step can retrieve CONCORD evidence, and the final answer can compare their tasks, data, and core ideas.
The program executes these steps, merges the retrieved evidence, and then asks the LLM to answer based on the collected evidence.
This is useful for comparison questions, multi-object questions, and complex survey questions.
```

## Q5 记忆系统：第一轮

操作：

```text
输入问题：
我后面主要关注空间转录组质量控制和平台偏差问题，请记住这个偏好。

点击按钮：
协作问答
```

展示：

```text
系统是否确认记住偏好，或 trace / memory 相关内容。
```

中文口播：

```text
下面演示记忆系统。
第一轮我不给具体文献问题，而是告诉系统一个用户偏好：后续主要关注空间转录组质量控制和平台偏差。
这一轮的重点不是检索效果，而是让系统把用户偏好写入记忆数据库。
```

English script:

```text
Next, I will demonstrate the memory system.
In the first turn, I do not ask a specific literature question. Instead, I give the system a user preference: I want to focus on spatial transcriptomics quality control and platform bias.
The purpose of this turn is not retrieval performance. The purpose is to let the system write this preference into the persistent memory database.
```

## Q6 记忆系统：第二轮

操作：

```text
输入问题：
根据我刚才的偏好，我应该优先阅读哪些资料，为什么？

点击按钮：
协作问答
```

展示：

```text
回答是否提到空间转录组质量控制和平台偏差；是否推荐 Spatial Touchstone 或 Xenium 相关资料；是否出现 memory_context。
```

中文口播：

```text
第二轮我只问“根据刚才的偏好应该看哪些资料”，这个问题本身是不完整的。
如果系统能推荐 Spatial Touchstone 和 Xenium sensitivity、specificity、signal contamination 相关资料，就说明它读取了上一轮记忆。
记忆系统的作用不是替代 RAG，而是补充用户历史上下文；RAG 仍然负责提供文献证据。
```

English script:

```text
In the second turn, I only ask which materials I should read based on my previous preference. This question is incomplete by itself.
If the system recommends Spatial Touchstone and the Xenium paper about sensitivity, specificity, and signal contamination, then it means the previous preference has been retrieved from memory.
The memory system does not replace RAG. It provides user-history context, while RAG still provides evidence from the knowledge base.
```

## Q7 UniProt Skill：外部工具调用

操作：

```text
输入问题：
OCT4 在细胞重编程中是什么角色？请查 UniProt。

点击按钮：
UniProt Skill
```

备用操作：

```text
输入问题：
TP53/P53 的标准人类蛋白条目是什么？

点击按钮：
UniProt Skill
```

展示：

```text
selected_skill、selected_tool、selected_accession。
OCT4 预期 Q01860；TP53/P53 预期 P04637。
```

中文口播：

```text
这个功能展示的是 Skill，也就是程序允许系统调用外部工具。
在生物医学问答里，OCT4、TP53、P53 这类名称可能是基因名、蛋白名或别名。
如果只靠 LLM 生成，可能会出现实体混淆。
所以这里调用 UniProt 公共数据库，把自然语言中的实体规范化到标准蛋白条目。
比如 OCT4 对应 Q01860，TP53 或 P53 对应 P04637。
这让回答不仅有本地文献语境，也有权威数据库中的标准实体信息。
```

English script:

```text
This function demonstrates a skill, which means the system can call an external tool instead of only generating text.
In biomedical QA, names such as OCT4, TP53, and P53 may refer to gene symbols, protein names, or aliases.
If we rely only on the LLM, entity confusion may occur.
Here the system calls the public UniProt database and normalizes the entity to a standard protein entry.
For example, OCT4 should map to Q01860, and TP53 or P53 should map to P04637.
This gives the answer both local literature context and authoritative external database information.
```

## Q8 协作问答：最终完整链路

操作：

```text
输入问题：
请结合本地资料和 UniProt，说明 OCT4 在细胞重编程中的作用，并指出回答依据来自哪里。

点击按钮：
协作问答
```

展示：

```text
memory、plan、structured candidates、retrieval results、UniProt Skill calls、本地证据和 UniProt 结果是否被区分。
```

中文口播：

```text
这是最终集成模式，也是最重要的演示。
前面的按钮分别展示了普通 RAG、Hybrid RAG、Agentic RAG、记忆系统和 UniProt Skill。
协作问答会把这些模块放到同一条链路里。
系统先读取记忆，再进行检索规划；如果问题中有结构化约束，就使用结构化知识库过滤候选资料；之后进行向量检索；如果识别到 OCT4 这样的蛋白或基因实体，就调用 UniProt Skill；最后 LLM 根据本地证据和工具结果生成回答。
所以其他按钮更像消融实验入口，而协作问答是最终系统入口。
```

English script:

```text
This is the final integrated mode and the most important demonstration.
The previous buttons show basic RAG, Hybrid RAG, Agentic RAG, memory, and UniProt Skill separately.
Collaborative QA connects these modules into one workflow.
The system first reads memory, then plans retrieval. If the question contains structured constraints, the structured knowledge base filters candidate sources. Then vector retrieval collects evidence. If the system detects a protein or gene entity such as OCT4, it calls the UniProt Skill. Finally, the LLM generates an answer based on local evidence and tool results.
So the other buttons are mainly ablation entries, while Collaborative QA is the final system entry.
```

## Q9 Benchmark 报告

操作：

```text
打开 outputs/benchmark_runs/run_20260622_135029/report.md
```

展示：

```text
30 questions evaluated、Overall score、sc-rag-026、sc-rag-027、sc-rag-028、sc-rag-029、sc-rag-030。
```

中文口播：

```text
最后展示自动 benchmark 报告。
这个项目不是只设计了几个演示问题，而是有 30 个 benchmark item。
自动测试会检查 required source 是否命中、相关 chunk 数量是否足够、Agentic trace 是否生成、Structured candidates 是否存在、Memory context 是否读取、UniProt Skill 是否返回预期 accession。
例如 OCT4 相关题需要检测 Q01860，TP53/P53 题需要检测 P04637，多轮记忆题需要检测上一轮偏好是否进入 memory context。
报告里也保留了失败或不足项，例如综合题 sc-rag-030 的检索覆盖不完整。
这说明 benchmark 不是装饰，而是能暴露系统当前弱点，用于后续改进。
```

English script:

```text
Finally, I will show the automatic benchmark report.
This project does not only contain several hand-picked demo questions. It contains a 30-item benchmark.
The automatic test checks whether required sources are retrieved, whether enough relevant chunks are found, whether the Agentic trace is generated, whether structured candidates exist, whether memory context is retrieved, and whether UniProt Skill returns the expected accession.
For example, OCT4-related questions should detect Q01860, TP53/P53 questions should detect P04637, and memory questions should verify whether the previous preference appears in memory context.
The report also keeps failure or weakness cases, such as incomplete retrieval coverage in sc-rag-030.
This shows that the benchmark is not decorative. It can expose current system weaknesses and guide future improvement.
```

