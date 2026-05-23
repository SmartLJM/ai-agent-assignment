# Lv. 1 Expand Knowledge Assets and Evaluation Benchmark

**Task Objective**: Expand course knowledge assets and evaluation benchmarks to provide richer data support for the knowledge Q&A system.

**Task Requirements**:
- Expand knowledge assets: Increase the number of knowledge sets in the selected domain to improve domain breadth;
- Expand evaluation benchmarks: Increase the number of questions to improve question quality and coverage;
- Draw knowledge asset classification diagrams and evaluation benchmark coverage diagrams.

**Deliverables**:
- Show the expanded knowledge asset classification structure;
- Show the expanded evaluation benchmark coverage analysis.


**Grading Criteria** (Total 100 points)

**I. Knowledge Asset Expansion** (50 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Number of Knowledge Sets | 20 | New ≥30 = 20 points; new 20-29 = 15 points; new 10-19 = 10 points; <10 = 5 points |
| Domain Breadth | 15 | Covers ≥5 types = 15 points; covers 3-4 types = 10 points; covers 1-2 types = 5 points |
| Content Quality | 15 | Substantial content, reliable sources = 15 points; basically qualified = 10 points; uneven quality = 5 points |

**II. Evaluation Benchmark Expansion** (35 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Number of Questions | 15 | New ≥30 = 15 points; new 20-29 = 10 points; new 10-19 = 6 points; <10 = 3 points |
| Question Quality | 10 | Clear questions, definite answers = 10 points; basically reasonable = 6 points; partially vague = 3 points |
| Coverage | 10 | Covers multiple question types and difficulties = 10 points; partial coverage = 6 points; single type = 3 points |

**III. Documentation and Presentation** (15 points)

| Check Item | Points | Grading Rules |
| -------- | --- | -------------------------- |
| Knowledge Asset Classification Diagram | 8 | Clearly shows classification structure = 8 points; basically readable = 5 points |
| Evaluation Benchmark Coverage Diagram | 7 | Clearly shows question type and difficulty distribution = 7 points; basically readable = 4 points |


# Lv. 1 Structured Knowledge Base

**References**:
- Edge D, Trinh H, Cheng N, Bradley J, Chao A, Mody AN, et al. From Local to Global: A Graph RAG Approach to Query-Focused Summarization. ArXiv. 2024;abs/2404.16130.
- Zhuang L, Chen S, Xiao Y, Zhou H, Zhang Y, Chen H, et al. LinearRAG: Linear Graph Retrieval Augmented Generation on Large-scale Corpora. ArXiv. 2025;abs/2510.10114.

**Task Objective**: Extract entities and relationships from unstructured text to build a structured knowledge base supporting basic queries.

**Task Requirements**:
- Extract entities and relationships from text corpora to build a knowledge base;
- Support basic entity attribute queries;
- Draw knowledge base construction flowcharts and entity relationship diagrams.

**Deliverables**: Show the entity relationship diagram of the knowledge base.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (60 points)

| Check Item | Points | Grading Rules |
| ------- | --- | ------------------------------------------ |
| Entity and Relationship Extraction | 25 | Can extract and classify entities, can extract relationships = 25 points; partially correct = 15 points; basically runnable = 5 points |
| Attribute Completeness | 20 | Each entity contains ≥2 attributes = 20 points; some have attributes = 10 points |
| Query Function | 15 | Can retrieve entity attributes based on questions = 15 points; partially runnable = 5 points |

**II. Code and Documentation** (40 points)

| Check Item | Points | Grading Rules |
| ----- | --- | ------------------------------------- |
| Runnability | 20 | Runs without errors = 20 points; minor fixable issues = 10 points; cannot run = 0 points |
| Flowchart | 10 | Contains complete knowledge base construction process = 10 points; partial process = 5 points |
| Entity Relationship Diagram | 10 | Clearly shows entities and relationships = 10 points; basically readable = 5 points; missing = 0 points |


# Lv. 1 Agentic RAG

**References**:
- Singh A, Ehtesham A, Kumar S, Khoei TT. Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG. ArXiv. 2025;abs/2501.09136.

**Task Objective**: Implement an adaptive retrieval-augmented generation system capable of:
- Decomposing composite problems into sub-tasks, retrieving separately, and integrating results;
- Self-checking and correcting answer quality.

**Task Requirements**:
- Implement task decomposition and result integration for composite problems;
- Implement answer quality self-checking and correction mechanisms;
- Draw system flowcharts.

**Deliverables**:
- Composite task problems: Need to be decomposed into multiple sub-tasks, no fewer than 8;
- Show the system's decision-making process for each problem in the following format:

| Problem | Sub-task Decomposition | Generated Answer | Self-check Result |
|---|---|---|---|
| {Problem content} | {List of decomposed sub-tasks} | {Final generated answer} | {Pass/Fail + Reason} |


**Grading Criteria** (Total 100 points)

**I. Question Set Quality** (25 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Number of Composite Tasks | 15 | ≥12 = 15 points; 8-11 = 10 points; <8 = 5 points |
| Question Effectiveness | 10 | Clear problems, require decomposition, definite answers = 10 points; basically reasonable = 5 points; vague problems = 2 points |

**II. Functional Completeness** (50 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Task Decomposition and Integration | 30 | Can correctly decompose composite tasks and integrate results = 30 points; partially correct = 15 points; basically runnable = 5 points |
| Self-check Correction Mechanism | 20 | Can self-check and correct answers = 20 points; only self-check without correction = 10 points; no self-check = 0 points |

**III. Code and Documentation** (15 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 10 | Runs without errors = 10 points; minor fixable issues = 5 points; cannot run = 0 points |
| Flowchart | 5 | Contains complete system processing flow = 5 points; partial flow = 3 points |

**IV. Results Presentation** (10 points)

| Check Item | Points | Grading Rules |
| ------ | --- | -------------------------------------- |
| Decision Process Display | 5 | Complete decomposition + self-check results for each problem = 5 points; partial display = 3 points |
| Answer Quality | 5 | Accurate and complete answers = 5 points; basically correct but incomplete = 3 points; obvious errors = 1 point |


# Lv. 1 Multi-level Persistent Memory System

**References**:
- Huang W-C, Zhang W, Liang Y, Bei Y, Chen Y, Feng T, et al. Rethinking Memory Mechanisms of Foundation Agents in the Second Half: A Survey. ArXiv. 2026;abs/2602.06052.

**Task Objective**: Implement a multi-level persistent memory system that divides agent memory into three layers:
- **Working Memory**: Context information for the current session with capacity constraints;
- **Episodic Memory**: Specific experience records across sessions;
- **Semantic Memory**: Structured knowledge distilled from experiences.

**Additional Notes**:
- Working memory is responsible for saving the current session's online workspace;
- Episodic memory is responsible for recording cross-session historical session summaries;
- Semantic memory is responsible for storing entities and relationships extracted from sessions.

**Task Requirements**:
- Implement persistent storage for the three-layer memory;
- Implement write mechanisms for the three-layer memory;
- Implement retrieval mechanisms for the three-layer memory;
- Draw the architecture diagram of the multi-level memory system.

**Deliverables**:
- Show the storage structure and example content of the three-layer memory;
- Show retrieval examples of the three-layer memory.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (50 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Working Memory | 15 | Implements current session context storage and retrieval = 15 points; partially implemented = 8 points; basically runnable = 3 points |
| Episodic Memory | 20 | Implements cross-session historical summary storage and retrieval = 20 points; partially implemented = 10 points; basically runnable = 5 points |
| Semantic Memory | 15 | Implements entity and relationship storage and retrieval = 15 points; partially implemented = 8 points; basically runnable = 3 points |

**II. Code and Documentation** (30 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 15 | Runs without errors = 15 points; minor fixable issues = 8 points; cannot run = 0 points |
| Architecture Diagram | 10 | Contains complete architecture and data flow of three-layer memory = 10 points; partial display = 5 points |
| Code Structure | 5 | Three-layer memory clearly separated with comments = 5 points; basically reasonable = 3 points; messy structure = 1 point |

**III. Results Presentation** (20 points)

| Check Item | Points | Grading Rules |
| ------ | --- | -------------------------------- |
| Memory Operation Display | 10 | Provides read/write examples for each layer with clear logic = 10 points; partially provided = 5 points |
| Storage Structure Display | 10 | Clearly shows actual storage methods of three-layer memory = 10 points; partial display = 5 points |


# Lv. 2 Knowledge Base Multi-hop Reasoning

**References**:
- Luu H, Nguyen L, Pham T, Pham H, Quan T. HiGraAgent: Dual-Agent Adaptive Reasoning over Hierarchical Knowledge Graph for Open Domain Multi-hop Question Answering. 2026. 1193–217 p.
- Zhuang L, Chen S, Xiao Y, Zhou H, Zhang Y, Chen H, et al. LinearRAG: Linear Graph Retrieval Augmented Generation on Large-scale Corpora. ArXiv. 2025;abs/2510.10114.

**Task Objective**: Implement a knowledge base-based multi-hop reasoning Q&A system capable of:
- Performing multi-step retrieval for implicit indirect questions, gradually deriving answers from multiple sources;
- Verifying the logical completeness and answer consistency of multi-hop reasoning.

**Task Requirements**:
- Implement retrieval function: Retrieve relevant content from the knowledge base based on questions;
- Implement reasoning function: Integrate retrieval results, perform multi-step reasoning, and generate answers;
- Implement verification function: Check answer logical completeness, multi-hop coverage, and source consistency;
- Draw system flowcharts showing data flow and verification logic.

**Verification Loop Logic**:
- Verification passed → Process ends;
- Verification failed → Return to re-retrieve, maximum 3 iterations.

**Deliverables**:
- Question set requirement: No fewer than 10 indirect questions (requiring multi-step reasoning);
- Show the complete trajectory of the system answering questions.

**Indirect Reasoning Question Examples**:

**Q1**: What type of housing is most suitable for office workers?  
**Reasoning**: office workers → stable but limited income + busy schedule → key needs: short commute and convenient amenities → suitable housing: small units in urban areas with good infrastructure.

**Q2**: Why do some people prefer working in coffee shops?  
**Reasoning**: coffee shop environment → relatively quiet + caffeine available → work needs → requires concentration without interruption → personal preference → needs ambiance and occasional social interaction.

**Q3**: What kind of gift is appropriate for a newly-hired colleague?  
**Reasoning**: newly hired → new environment, unfamiliar with everyone → gift purpose → show friendliness, should not be too expensive → selection criteria → practical, recognizable, moderately priced.

**Q4**: Why do houses in the same neighborhood vary in price?  
**Reasoning**: housing price factors → layout, floor, orientation, noise → in the same neighborhood → differences come from building position, natural lighting, proximity to streets → comprehensive judgment logic.


**Grading Criteria** (Total 100 points)

**I. Question Set Quality** (35 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Number of Questions | 15 | ≥15 = 15 points; 10-14 = 10 points; <10 = 5 points |
| Question Effectiveness | 20 | Indirect questions requiring multi-step reasoning = 20 points; some questions too direct = 12 points; most questions don't require reasoning = 5 points |

**II. Functional Completeness** (35 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Retrieval Capability | 12 | Can retrieve relevant content based on questions = 12 points; partial retrieval effective = 6 points |
| Reasoning Capability | 12 | Can perform multi-step reasoning to generate answers = 12 points; only single-step reasoning = 6 points |
| Verification Capability | 11 | Can verify logical completeness and provide feedback = 11 points; can verify but no feedback = 6 points; no verification = 0 points |

**III. Trajectory Completeness** (20 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Trajectory Recording | 10 | Each question has complete retrieval-reasoning-verification trajectory = 10 points; partial trajectory missing = 5 points |
| Iteration Process | 10 | Complete iteration process when verification fails = 10 points; verification but no iteration = 5 points |

**IV. Code and Documentation** (10 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 5 | Runs without errors = 5 points; minor fixable issues = 3 points; cannot run = 0 points |
| Flowchart | 3 | Contains system flow + data flow + verification logic = 3 points; basic flow = 2 points |
| Code Structure | 2 | Clear functional module separation = 2 points; basically reasonable = 1 point |


# Lv. 2 Multi-modal Knowledge Base

**References**:
- Guo Z, Ren X, Xu L, Zhang J, Huang C. RAG-Anything: All-in-One RAG Framework. ArXiv. 2025;abs/2510.12323.

**Task Objective**: Implement a knowledge base system supporting multi-modal content, capable of:
- Processing and storing various unstructured data including text, images, and tables;
- Performing knowledge retrieval and Q&A based on multi-modal content.

**Task Requirements**:
- Extract and store knowledge from multi-modal documents (PDFs or web pages containing text, images, and tables);
- Support retrieval for at least two modalities (text retrieval, image retrieval, or table retrieval);
- Retrieve relevant modal content based on user questions and generate answers;
- Draw multi-modal knowledge base construction flowcharts and retrieval flowcharts.

**Deliverables**:
- Multi-modal knowledge base scale: At least 3 modal types (text, image, table), each with no fewer than 10 records;
- Question set requirement: No fewer than 15 questions, covering single-modal queries and multi-modal joint queries;
- Show the content structure and retrieval examples of the multi-modal knowledge base.


**Grading Criteria** (Total 100 points)

**I. Question Set Quality** (35 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Number of Questions | 15 | ≥20 = 15 points; 15-19 = 10 points; <15 = 5 points |
| Question Effectiveness | 10 | Clear questions, covering single-modal and multi-modal queries = 10 points; basically reasonable = 5 points |
| Multi-modal Coverage | 10 | Covers 3 modal queries = 10 points; covers 2 = 6 points; only 1 = 2 points |

**II. Functional Completeness** (40 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Multi-modal Extraction | 15 | Can extract text, images, tables from documents = 15 points; partially correct = 8 points |
| Multi-modal Retrieval | 15 | Can retrieve corresponding modal content based on questions = 15 points; partially runnable = 8 points |
| Answer Generation | 10 | Can generate answers based on multi-modal content = 10 points; partially correct = 5 points |

**III. Code and Documentation** (25 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 10 | Runs without errors = 10 points; minor fixable issues = 5 points; cannot run = 0 points |
| Knowledge Base Construction Flowchart | 8 | Contains complete multi-modal processing flow = 8 points; partial flow = 4 points |
| Retrieval Flowchart | 7 | Contains multi-modal retrieval and answer generation flow = 7 points; basically readable = 4 points |


# Lv. 3 Self-evolving Memory Base

**References**:
- Pan W, Liu S, Zhou X, Zhang S, Shi W, Xu M, et al., editors. MSTAR: Every Task Deserves Its Own Memory Harness. 2026.

**Task Objective**: Implement a memory base system that can automatically evolve based on historical experience, capable of:
- Extracting experience units from users' historical Q&A records and task execution logs;
- Automatically evaluating the effectiveness of current memory base structure, discovering and fixing deficiencies;
- Gradually discovering optimal memory base structures for specific tasks.

**Additional Notes**: The memory base consists of two core parts:
- **Knowledge Base**: Structured domain knowledge storage (such as knowledge graphs, entity relationships, etc.);
- **Working Context**: Current task's session state, temporary variables, and intermediate reasoning results.

**Task Requirements**:
- Extract experience units from historical Q&A and task execution logs and store them;
- Establish evaluation mechanisms to automatically detect memory base deficiencies and score them;
- Implement optimization modules that can adjust memory base structure based on evaluation feedback;
- Support discovering the advantages and disadvantages of different memory base structures;
- Draw the overall flowchart of the self-evolving memory base.

**Deliverables**:
- Experience unit library: At least 20 valid experience units;
- Show the evolution process of the memory base, including initial structure, optimized structure, and final structure;
- Show the trend of evaluation score changes.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (40 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Experience Extraction | 12 | Can extract experience units from historical records = 12 points; partially correct = 6 points |
| Evaluation Mechanism | 14 | Can automatically detect memory base deficiencies and score = 14 points; can evaluate but no scores = 7 points; no evaluation = 0 points |
| Optimization Module | 14 | Can adjust memory base structure based on feedback = 14 points; can adjust but effect not obvious = 7 points; no optimization = 0 points |

**II. Results Presentation** (35 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Experience Unit Library | 10 | ≥20 valid experience units = 10 points; ≥15 = 7 points; ≥10 = 4 points |
| Evolution Process Display | 15 | Clearly shows complete evolution from initial → optimized → final = 15 points; partial display = 8 points; only results without process = 3 points |
| Evaluation Score Trend | 10 | Shows evaluation score change curve with reasonable trend = 10 points; only final score = 5 points; no evaluation results = 0 points |

**III. Code and Documentation** (25 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 10 | Runs without errors = 10 points; minor fixable issues = 5 points; cannot run = 0 points |
| Flowchart | 8 | Contains complete self-evolution flow (evaluation + optimization + iteration) = 8 points; partial flow = 4 points |
| Code Structure | 7 | Clear modularization with comments = 7 points; basically reasonable = 4 points; messy structure = 1 point |
