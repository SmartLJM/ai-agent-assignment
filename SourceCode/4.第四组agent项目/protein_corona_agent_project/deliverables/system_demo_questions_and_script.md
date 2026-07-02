# 系统演示问题与现场文稿

## 演示准备

启动方式：

```text
在 PyCharm 运行 scripts/rag_web.py
浏览器打开 http://127.0.0.1:8000
```

演示顺序建议：

```text
1. 健康检查
2. 普通问答
3. 只检索
4. Hybrid 问答
5. Agentic 问答
6. 记忆系统
7. UniProt Skill
8. 协作问答
9. Benchmark 报告
```

---

## 1. 健康检查：证明系统真的加载了

操作：

```text
打开 http://127.0.0.1:8000/health
```

展示重点：

```text
chunk_count
embedding_model
llm_model
structured_kb
memory
```

现场文稿：

```text
我先展示系统的健康检查页面。这里不是问答结果，而是后端状态。
可以看到系统已经加载了向量索引、embedding 模型、结构化知识库和记忆数据库。
这一步的作用是证明后面的回答不是静态文本，而是由当前项目的 RAG 系统实时检索和生成的。
```

---

## 2. 普通问答：展示基础 RAG

问题：

```text
Nicheformer 这篇论文主要解决了单细胞和空间组学中的什么问题？它为什么需要同时利用解离单细胞数据和空间转录组数据？
```

点击按钮：

```text
问答
```

展示重点：

```text
右侧证据片段
回答中的来源引用
是否命中 Nicheformer 论文
```

现场文稿：

```text
这个问题用于展示最基础的 RAG 流程。
系统会先把问题向量化，然后在本地向量库中检索相关 chunk，最后把检索到的证据交给 LLM 生成回答。
这里重点看右侧证据片段。只要能看到 Nicheformer 相关来源，就说明系统不是单纯依赖 LLM 自己的记忆，而是先找到了本地知识库中的论文证据。
```

---

## 3. 只检索：展示检索质量

问题：

```text
Nicheformer 如何利用空间上下文来改进单细胞表示学习？
```

点击按钮：

```text
只检索
```

展示重点：

```text
只显示证据，不生成答案
检索结果是否来自 Nicheformer
chunk 的 title、page、similarity
```

现场文稿：

```text
这一项不让 LLM 生成回答，只看检索结果。
这样可以把“检索能力”和“语言生成能力”拆开观察。
如果只检索已经能命中正确论文和相关片段，说明向量索引和 embedding 检索是有效的。
这个按钮也可以作为消融实验入口：先确认资料找得准，再讨论生成答案是否准确。
```

---

## 4. Hybrid 问答：结构化检索 + 向量检索

问题：

```text
请找出 2026 年左右与单细胞或空间组学 foundation model 相关的研究，并说明它们关注的问题。
```

点击按钮：

```text
Hybrid 问答
```

展示重点：

```text
Structured candidates
matched_by
year / keyword / theme
右侧证据片段
```

现场文稿：

```text
这个问题用于展示 Hybrid RAG。
普通向量检索擅长找语义相似内容，但不擅长处理年份、主题、方法类型这种硬条件。
所以 Hybrid RAG 会先用结构化知识库筛出候选资料，比如年份接近 2026、主题包含 foundation model、关键词和单细胞或空间组学相关。
然后系统只在这些候选资料对应的 chunk 中做向量检索。
也就是说，结构化检索决定“在哪些资料里找”，向量检索决定“这些资料里的哪些段落最相关”。
```

---

## 5. Agentic 问答：多步检索规划

问题：

```text
比较 Nicheformer 和 CONCORD：它们分别解决什么问题，核心思路有什么不同？
```

点击按钮：

```text
Agentic 问答
```

展示重点：

```text
question_type
reasoning
Step 1 / Step 2
每个 step 的 query 和 results
最终回答是否同时覆盖两篇论文
```

现场文稿：

```text
这个问题用于展示 Agentic RAG。
如果只做一次普通向量检索，系统可能只检索到 Nicheformer，或者只检索到 CONCORD，导致比较不平衡。
Agentic RAG 的做法是先让 LLM 作为 planner，把复杂问题拆成多个检索步骤。
例如第一步检索 Nicheformer，第二步检索 CONCORD，最后再综合二者的任务、数据和核心思路。
程序按这些 step 分别检索，再把多路证据合并交给 LLM 回答。
所以它适合比较题、多对象题和复杂综述题。
```

---

## 6. 记忆系统：多轮上下文

第一轮问题：

```text
我后面主要关注空间转录组质量控制和平台偏差问题，请记住这个偏好。
```

点击按钮：

```text
协作问答
```

第二轮问题：

```text
根据我刚才的偏好，我应该优先阅读哪些资料，为什么？
```

点击按钮：

```text
协作问答
```

展示重点：

```text
第二轮回答是否提到空间转录组质量控制和平台偏差
是否推荐 Spatial Touchstone 或 Xenium 相关资料
trace / memory_context / memory stats
```

现场文稿：

```text
这个演示用于证明系统不是每一轮都从零开始。
第一轮我给系统一个研究偏好：关注空间转录组质量控制和平台偏差。
第二轮我只问“根据刚才的偏好应该看哪些资料”，这个问题本身是不完整的。
如果系统能推荐 Spatial Touchstone 和 Xenium sensitivity、specificity、signal contamination 相关资料，就说明它读取了上一轮记忆。
记忆系统的作用不是替代 RAG，而是补充用户历史上下文；RAG 仍然负责提供文献证据。
```

---

## 7. UniProt Skill：外部工具调用

问题：

```text
OCT4 在细胞重编程中是什么角色？请查 UniProt。
```

点击按钮：

```text
UniProt Skill
```

备用问题：

```text
TP53/P53 的标准人类蛋白条目是什么？
```

展示重点：

```text
selected_skill
selected_tool
selected_accession
OCT4 -> Q01860
TP53/P53 -> P04637
```

现场文稿：

```text
这个功能展示的是 Skill，也就是程序允许 LLM 或系统调用外部工具。
在生物医学问答里，OCT4、TP53、P53 这类名称可能是基因名、蛋白名或别名。
如果只靠 LLM 生成，可能会出现实体混淆。
所以这里调用 UniProt 公共数据库，把自然语言中的实体规范化到标准蛋白条目。
比如 OCT4 对应 Q01860，TP53 或 P53 对应 P04637。
这让回答不仅有本地文献语境，也有权威数据库中的标准实体信息。
```

---

## 8. 协作问答：最终完整链路

问题：

```text
请结合本地资料和 UniProt，说明 OCT4 在细胞重编程中的作用，并指出回答依据来自哪里。
```

点击按钮：

```text
协作问答
```

展示重点：

```text
memory
plan
structured candidates
retrieval results
UniProt Skill calls
本地证据和 UniProt 结果是否被区分
```

现场文稿：

```text
这是最终集成模式，也是最重要的演示。
前面的按钮分别展示了普通 RAG、Hybrid RAG、Agentic RAG、记忆系统和 UniProt Skill。
协作问答会把这些模块放到同一条链路里。
系统先读取记忆，再进行检索规划；如果问题中有结构化约束，就使用结构化知识库过滤候选资料；之后进行向量检索；如果识别到 OCT4 这样的蛋白或基因实体，就调用 UniProt Skill；最后 LLM 根据本地证据和工具结果生成回答。
所以其他按钮更像消融实验入口，而协作问答是最终系统入口。
```

---

## 9. Benchmark 报告：证明不是只挑成功样例

操作：

```text
打开 outputs/benchmark_runs/run_20260622_135029/report.md
```

展示重点：

```text
30 questions evaluated
Overall score
sc-rag-026 / sc-rag-027 / sc-rag-028 / sc-rag-029
sc-rag-030 暴露的问题
```

现场文稿：

```text
最后展示自动 benchmark 报告。
这个项目不是只设计了几个演示问题，而是有 30 个 benchmark item。
自动测试会检查 required source 是否命中、相关 chunk 数量是否足够、Agentic trace 是否生成、Structured candidates 是否存在、Memory context 是否读取、UniProt Skill 是否返回预期 accession。
例如 OCT4 相关题需要检测 Q01860，TP53/P53 题需要检测 P04637，多轮记忆题需要检测上一轮偏好是否进入 memory context。
报告里也保留了失败或不足项，例如综合题 sc-rag-030 的检索覆盖不完整。
这说明 benchmark 不是装饰，而是能暴露系统当前弱点，用于后续改进。
```

---

## 推荐正式演示顺序压缩版

如果时间只有 8 到 10 分钟，建议只演示这 5 个：

```text
1. /health
2. Nicheformer 普通问答
3. Nicheformer vs CONCORD Agentic 问答
4. OCT4 UniProt Skill
5. OCT4 协作问答
6. benchmark report
```

如果时间有 15 分钟以上，再加入：

```text
Hybrid 问答
记忆系统两轮问答
只检索
```

