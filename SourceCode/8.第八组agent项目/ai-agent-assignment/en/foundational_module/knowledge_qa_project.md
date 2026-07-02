# Knowledge Question-Answering Project

## Overview

This project is the third part of the basic module, requiring to build a simple knowledge question‑answering system. Tasks include:
1. Collect knowledge assets according to a chosen topic
2. Build a vector knowledge base that supports semantic retrieval
3. Implement an agent question‑answering system based on retrieval‑augmented generation (RAG)


## Framework Recommendations

### 1. Mature Python‑ecosystem frameworks

#### **LangChain / LangGraph**
- **Position**: The most popular agent engineering platform in the Python ecosystem
- **Features**: Mature ecosystem (100M+ monthly downloads), rich components, extremely flexible
- **Suitable for**: Scenarios requiring high customization and complex ecosystem integration
- **Learning curve**: Moderate (many concepts, steeper learning curve)
- **In a nutshell**: If you can only learn one framework, LangChain is the most general choice

#### **CrewAI**
- **Position**: Role‑driven collaborative agent framework
- **Features**: Intuitive design, models agents as company employees, concise code
- **Suitable for**: Scenarios requiring role‑based division of labor (multi‑agent), but can also be used for single‑agent RAG
- **Learning curve**: Low (a Hello World can be done in about 20 lines of code)
- **In a nutshell**: Suitable for quickly building role‑based agent workflows

### 2. Lightweight / emerging frameworks

#### **Agno**
- **Position**: Lightweight, concise AI application framework
- **Features**: Multi‑model support, clean API, suitable for rapid prototyping
- **Suitable for**: Teaching demonstrations, rapid prototype development
- **Learning curve**: Low
- **In a nutshell**: The lightest entry‑level choice

#### **PydanticAI**
- **Position**: SDK‑encapsulation paradigm based on Pydantic
- **Features**: Strong type validation, development experience similar to traditional web development
- **Suitable for**: Teams that value code quality and type safety
- **Learning curve**: Low (if you are familiar with Pydantic)
- **In a nutshell**: TypeScript‑style Python AI development

### 3. Platform‑level / enterprise frameworks

#### **AutoGen (Microsoft)**
- **Position**: Event‑driven multi‑agent system
- **Features**: Backed by Microsoft, good ecosystem support, complete functionality
- **Suitable for**: Complex multi‑agent collaboration, enterprise‑level applications
- **Learning curve**: Moderate
- **In a nutshell**: A reliable choice for enterprise‑grade multi‑agent collaboration

#### **Dify**
- **Position**: Low‑code AI application platform
- **Features**: Visual orchestration, out‑of‑the‑box usability, simple deployment
- **Suitable for**: Those not skilled in programming but wanting to build AI applications quickly
- **Learning curve**: Very low (but customisation capability is limited)
- **In a nutshell**: Build RAG applications rapidly through a visual interface

### 4. Other notable frameworks

| Framework        | Language | Features                                 | Suitable for                                      |
| ---------------- | -------- | ---------------------------------------- | ------------------------------------------------- |
| **MetaGPT**      | Python   | Simulates software‑company role division | Complex multi‑agent collaboration                 |
| **AgentScope**   | Python   | Event‑driven, Chinese‑friendly           | Chinese‑language multi‑agent scenarios            |
| **LlamaIndex**   | Python   | RAG expert, strong document parsing      | Scenarios requiring high‑quality document parsing |
| **Hermes Agent** | Python   | High performance, easy deployment        | Production‑environment deployment                 |
| **DeerFlow**     | Python   | Graph‑structured workflows               | Complex business‑process orchestration            |
