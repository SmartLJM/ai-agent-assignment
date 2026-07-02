# Agentic Retrieval-Augmented Generation for Drug Discovery Q&A

**Knowledge set ID:** `dd-020-agentic-rag`  
**Theme:** `drug-discovery`  
**Source:** Course project implementation: drug discovery agentic RAG  

## Curated Content

Agentic retrieval-augmented generation combines retrieval, planning, tool use, memory, and answer
validation. In a drug-discovery Q&A system, the agent should decide whether a question needs
internal knowledge retrieval, a chemical database skill, memory retrieval, multi-hop comparison, or
a fallback strategy.  A static RAG system always follows the same sequence. An agentic RAG system
can generate a workflow from the question, run the appropriate agents, inspect intermediate results,
and adjust if evidence is insufficient. For example, if PubChem lookup fails, the system can fall
back to internal chemical knowledge and explain the limitation. If retrieval confidence is low, it
can broaden the query and retry.  The main advantage is traceability. Execution traces record why
the agent chose retrieval, skill invocation, memory, validation, or retry. This is especially
important in scientific Q&A because answers should be supported by sources, not just fluent
generation.

## Key Concepts

- `agentic-rag`
- `retrieval-augmented-generation`
- `tool-use`
- `verification`

## Retrieval Note

This self-contained knowledge set is used by the agent for grounded drug-discovery Q&A, benchmark citation, memory distillation, and dynamic orchestration evidence.
