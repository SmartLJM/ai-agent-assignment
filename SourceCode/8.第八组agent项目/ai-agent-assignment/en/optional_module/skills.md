# Lv.1 Deploy or Integrate MCP Tool / SKILL

**Task Objective**: Successfully integrate at least one MCP (Model Context Protocol) tool or SKILL into the course platform, enabling the platform agent to directly invoke the tool to complete specific tasks.

**Task Requirements**:
- Select at least one publicly available MCP tool or SKILL (from official repositories, community, or open-source projects);
- Complete deployment or integration configuration to ensure the tool runs properly in the platform environment;
- Write simple invocation examples showing how the agent triggers the tool through natural language instructions;
- Provide integration documentation explaining tool functionality, configuration steps, and usage examples.

**Deliverables**:
- Show complete conversation or logs of the agent invoking the tool;
- Explain any issues encountered during integration and their solutions (if applicable).

**Grading Criteria** (Total 100 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Tool Runnability | 40 | Agent successfully invokes and returns results = 40 points; invocation fails but configuration correct = 20 points |
| Integration Documentation | 30 | Contains functionality description, configuration steps, usage examples = 30 points; incomplete documentation = 15 points |
| Invocation Examples | 30 | Shows ≥1 complete invocation scenario = 30 points; simple example = 15 points |


# Lv.2 Build MCP / SKILL for Domain-Renowned Projects

**Task Objective**: Build MCP interfaces or encapsulate as SKILL for at least one renowned open-source project/database/tool in life sciences or course-related domains, enabling agents to invoke its functionality in a standardized way.

**Task Requirements**:
- Select an influential project in the domain (e.g., UniProt, PDB, BLAST, AlphaFold API, KEGG, PubChem, etc.);
- Read the project's official API documentation or source code to understand its core functionality;
- Build MCP server or SKILL encapsulation, exposing at least 3 core functional interfaces;
- Write test cases to verify interface correctness;
- Provide complete documentation including project introduction, interface description, and usage examples.

**Deliverables**:
- Show the complete process of the agent invoking the project through MCP/SKILL;
- Provide interface test reports or screenshots.

**Grading Criteria** (Total 100 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Project Selection | 15 | Selects renowned domain project = 15 points; average project influence = 8 points |
| Function Coverage | 25 | Exposes ≥3 core interfaces = 25 points; 2 = 15 points; 1 = 8 points |
| Interface Correctness | 25 | All test cases pass = 25 points; partially pass = 12 points |
| Documentation Completeness | 20 | Contains project introduction, interface description, usage examples = 20 points; basic documentation = 10 points |
| Runnability | 15 | Runs without errors = 15 points; requires minor fixes = 8 points |


# Lv.2 Large-scale Skill Routing System

**References**:
- Zheng Y, Zhang Z, Ma C, Yu Y, Zhu J, Wu Y, et al., editors. SkillRouter: Skill Routing for LLM Agents at Scale. 2026.

**Task Objective**: Implement a SKILL Router that, when the agent faces user requests, can quickly and accurately select and invoke the most appropriate skill from a large-scale skill library (≥2000 SKILLS).

**Task Requirements**:
- Build or integrate at least 2000 SKILLS (can use simulated data, open-source skill libraries, or automatically generated skill descriptions);
- Implement the core skill routing module: retrieve and rank candidate skills from the skill library based on user request semantics;
- Support multi-skill combination invocation: when a single skill cannot complete the task, plan the execution order of multiple skills;
- Implement routing decision explainability: record and show why specific skills are selected (e.g., semantic similarity, historical success rate, user feedback, etc.);
- Provide performance evaluation: evaluate routing accuracy, latency, and other metrics on test sets.

**Deliverables**:
- Show routing effects on ≥2000 skill library (e.g., Top-1 accuracy, Top-5 recall);
- Show at least 1 complex case of multi-skill combination invocation;
- Provide routing decision logs explaining selection rationale.

**Grading Criteria** (Total 100 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Skill Library Scale | 20 | ≥2000 SKILLS = 20 points; 1000-1999 = 12 points; 500-999 = 6 points |
| Routing Accuracy | 25 | Top-1 accuracy ≥80% = 25 points; 60-79% = 15 points; <60% = 8 points |
| Multi-skill Combination | 20 | Supports and shows multi-skill combination = 20 points; single skill only = 10 points |
| Explainability | 15 | Clearly shows routing decision rationale = 15 points; logs present but unclear = 8 points |
| Performance Evaluation | 10 | Provides quantitative metrics such as accuracy, latency = 10 points; qualitative description only = 5 points |
| Code and Documentation | 10 | Code runs, documentation complete = 10 points; basically runnable = 5 points |


# Lv.2 Self-Evolving Skill System

**References**:
- Shi Y, Chen Y, Lu Z, Miao Y, Liu S, Qi G, et al., editors. Skill1: Unified Evolution of Skill-Augmented Agents via Reinforcement Learning2026.

**Task Objective**: Build a self-evolving skill system that enables the agent to extract experiences from skill usage history, discover new skill patterns, and automatically crystallize them into reusable SKILLS, while managing the skill lifecycle (creation, update, retirement).

**Task Requirements**:
- **Experience Extraction**: Analyze agent historical conversations or task execution logs, extracting at least 20 valid experience units (e.g., successful problem-solving patterns, frequently used tool combinations, effective prompt strategies, etc.);
- **Skill Generation**: Automatically transform extracted experiences into standardized SKILL descriptions (including name, functional description, input/output specifications, applicable scenarios), generating at least 10 new SKILLS;
- **Skill Validation**: Design validation mechanisms to assess the effectiveness of newly generated SKILLS (e.g., validation success rate on test sets, deduplication comparison with existing skills);
- **Skill Management**: Implement skill lifecycle management—new skill onboarding, merging or deduplication with existing skills, retirement of low-usage skills (e.g., skills with <5 invocations in 30 days are marked as pending retirement);
- **Evolution Demonstration**: Show the evolution process of the skill library, including statistics such as number of new skills added, number of retired skills, and usage rate trends.

**Deliverables**:
- Show the complete pipeline from raw logs to experience extraction to SKILL generation;
- Show detailed descriptions and validation results for at least 3 newly generated SKILLS;
- Show specific operations of skill lifecycle management (e.g., skill deduplication, retirement decision process);
- Provide statistical charts or logs of the skill library evolution process.

**Grading Criteria** (Total 100 points)

| Check Item | Points | Grading Rules |
|--------|------|----------|
| Experience Extraction Quality | 20 | Extracts ≥20 valid experience units = 20 points; 10-19 = 12 points; <10 = 6 points |
| Skill Generation Quantity | 20 | Generates ≥10 new SKILLS = 20 points; 5-9 = 12 points; <5 = 6 points |
| Skill Validation Mechanism | 20 | Complete validation process with test pass rate ≥70% = 20 points; validation present but pass rate 50-69% = 12 points; incomplete validation = 6 points |
| Lifecycle Management | 20 | Implements full onboarding/deduplication/retirement workflow = 20 points; implements partial workflow = 12 points; conceptual description only = 6 points |
| Evolution Process Demonstration | 10 | Shows evolution process with statistical charts or logs = 10 points; text description only = 5 points |
| Code and Documentation | 10 | Code runs, documentation complete = 10 points; basically runnable = 5 points |
