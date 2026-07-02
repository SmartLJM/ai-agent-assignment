# Lv. 1 Basic Static Orchestration

**Task Objective**: Implement a fixed multi-agent collaborative workflow to complete knowledge Q&A tasks.

**Case Reference**:
- **Planner**: Analyze user questions, formulate retrieval and response plans;
- **Retriever**: Retrieve relevant content from the knowledge base according to the plan;
- **Generator**: Integrate retrieval results and generate responses;
- **Validator**: Check the accuracy and completeness of responses.

**Task Requirements**:
- Implement at least four agents in a fixed collaborative workflow;
- Each agent has clear input and output interfaces;
- Draw a complete workflow diagram showing data flow between agents;
- Show intermediate results (output of each agent).

**Deliverables**:
- Workflow Diagram: Show the complete collaborative process of all agents;
- Intermediate Results: Input and output examples for each agent.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (60 points)

| Check Item | Points | Grading Rules |
| ------ | --- | ------------------------------------------- |
| Number of Agents | 15 | ≥4 agents = 15 points; 3 = 3 points; 2 = 1 point; 1 = 0 points |
| Collaborative Workflow Implementation | 25 | Smooth collaboration and clear data flow = 25 points; partial collaboration = 5 points; basically runnable = 3 points |
| Task Completion | 20 | Can complete knowledge Q&A tasks = 20 points; partially complete = 10 points |

**II. Code and Documentation** (40 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 20 | Runs without errors = 20 points; minor fixable issues = 10 points; cannot run = 0 points |
| Workflow Diagram | 12 | Contains all agents + data flow = 12 points; partial workflow = 6 points |
| Intermediate Results | 8 | Clear display of each agent's input and output = 8 points; partial display = 4 points |


# Lv. 1 Basic Dynamic Orchestration

**Task Objective**: Implement a dynamic orchestration system where agents autonomously determine subsequent workflows.

**Case Example**:
- After receiving a task, the agent autonomously analyzes task complexity;
- Decides whether to create sub-agents for parallel execution;
- Dynamically adjusts execution strategies.

**Task Requirements**:
- Implement an agent autonomous decision-making mechanism to determine subsequent workflows;
- Support dynamic creation of sub-agents for parallel execution;
- Draw a dynamic orchestration workflow diagram;
- Show intermediate results and decision-making processes.

**Deliverables**:
- Workflow Diagram: Show dynamic decision-making and sub-agent creation processes;
- Intermediate Results: Results at each decision point and execution step;
- Additional Evaluation Benchmark: No fewer than 10 questions to test dynamic orchestration capabilities.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (50 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Autonomous Decision Mechanism | 20 | Can analyze tasks and determine subsequent workflows = 20 points; partially implemented = 10 points |
| Sub-agent Creation | 15 | Can dynamically create parallel sub-agents = 15 points; partially implemented = 8 points |
| Workflow Adjustment Capability | 15 | Can adjust workflow based on intermediate results = 15 points; partially implemented = 8 points |

**II. Question Set Quality** (25 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Number of Questions | 10 | ≥10 = 10 points; ≥8 = 6 points; <8 = 3 points |
| Question Effectiveness | 15 | Questions can test dynamic orchestration capabilities = 15 points; basically reasonable = 8 points |

**III. Code and Documentation** (25 points)

| Check Item | Points | Grading Rules |
|---|---|---|
| Runnability | 10 | Runs without errors = 10 points; minor fixable issues = 5 points; cannot run = 0 points |
| Workflow Diagram | 8 | Contains dynamic decision-making + sub-agent creation process = 8 points; partial display = 4 points |
| Intermediate Results | 7 | Clear display of decision-making process and execution results = 7 points; partial display = 4 points |


# Lv. 2 Advanced Static Orchestration

**References**:
- Sarker AK, et al. AAFLOW: Scalable Patterns for Agentic AI Workflows. ArXiv. 2026;abs/2505.02362.
- Athrey K, et al. From Intent to Execution: Composing Agentic Workflows with Agent Recommendation. ArXiv. 2026.

**Task Objective**: Implement a predefined multi-agent static workflow orchestration system capable of:
- Selecting predefined agent execution chains based on task type;
- Calling multiple agents in a fixed sequence to complete composite tasks;
- Supporting three basic orchestration modes: serial, parallel, and conditional branching.

**Task Requirements**:
- Define at least 3 preset workflow templates (e.g., Literature Retrieval → Summary Generation → Comparative Analysis);
- Implement a workflow engine supporting sequential execution, parallel execution, and conditional branching;
- Each workflow node corresponds to an agent role with clear data transfer between nodes;
- Provide workflow definition files (JSON/YAML format) with configurable node parameters.

**Deliverables**:
- Show execution processes and results of at least 2 different workflows;
- Provide workflow definition examples and runtime screenshots.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (60 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Workflow Template Quantity | 15 | ≥3 templates = 15 points; 2 = 10 points; 1 = 5 points |
| Orchestration Mode Support | 20 | Supports serial + parallel + conditional = 20 points; supports 2 = 12 points; only 1 = 5 points |
| Agent Node Implementation | 15 | Each node has clear role and input/output = 15 points; some nodes unclear = 8 points |
| Data Transfer | 10 | Correct and complete data transfer between nodes = 10 points; partial loss = 5 points |

**II. Code and Documentation** (40 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Runnability | 15 | Runs without errors = 15 points; minor fixable issues = 8 points; cannot run = 0 points |
| Workflow Definition File | 15 | Provides clear configurable JSON/YAML = 15 points; definition present but unclear = 8 points |
| Execution Display | 10 | Shows 2+ workflow execution processes = 10 points; only 1 = 5 points |


# Lv. 3 Advanced Dynamic Orchestration

**References**:
- Wang X, et al. On Time, Within Budget: Constraint-Driven Online Resource Allocation for Agentic Workflows. ArXiv. 2026.
- Gao Y, et al. DecisionBench: A Benchmark for Emergent Delegation in Long-Horizon Agentic Workflows. ArXiv. 2026.

**Task Objective**: Implement an adaptive dynamic workflow orchestration system capable of:
- Automatically reasoning and generating optimal agent execution chains based on task input;
- Dynamically adjusting subsequent steps during execution based on intermediate results;
- Supporting loop iteration and error recovery mechanisms.

**Task Requirements**:
- Implement a dynamic planning module that can automatically generate workflows based on task descriptions (not predefined templates);
- Support dynamic adjustment during execution: determine next actions based on previous agent outputs;
- Implement loop mechanism: automatically retry or switch strategies for unsatisfactory intermediate results;
- Implement error handling: when an agent fails, degrade or switch to alternative solutions;
- Provide execution trace records showing dynamic decision-making processes.

**Deliverables**:
- Show comparison between dynamically generated execution chains and predefined chains;
- Show at least 1 actual case containing loop iteration or error recovery;
- Provide execution trace logs explaining the rationale for each decision point.


**Grading Criteria** (Total 100 points)

**I. Functional Completeness** (60 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Dynamic Planning Capability | 20 | Can automatically generate workflow based on input = 20 points; requires partial manual intervention = 10 points |
| Execution Adjustment | 15 | Can dynamically adjust based on intermediate results = 15 points; only supports preset branches = 7 points |
| Loop and Retry | 15 | Supports automatic retry and strategy switching = 15 points; only manual retry = 7 points |
| Error Recovery | 10 | Can degrade or switch solutions on failure = 10 points; only stops with error = 3 points |

**II. Trace and Explainability** (25 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Execution Trace Recording | 15 | Complete records of each decision point and rationale = 15 points; records present but incomplete = 8 points |
| Dynamic Decision Display | 10 | Clearly shows dynamic adjustment process = 10 points; display present but unclear = 5 points |

**III. Code and Documentation** (15 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Runnability | 8 | Runs without errors = 8 points; minor fixable issues = 4 points |
| Documentation Completeness | 7 | Contains architecture description and usage examples = 7 points; basic documentation = 3 points |
