# Advanced Dynamic Orchestration Architecture

```mermaid
flowchart TD
    Q[User question] --> P[Planner: analyze task]
    P --> D{Dynamic decision}
    D -->|memory cues| M[Memory retriever]
    D -->|chemical property| S[PubChem SKILL]
    D -->|comparison / complex| R2[Parallel / multi-hop retriever]
    D -->|standard| R1[Knowledge retriever]
    M --> G[Synthesizer]
    S --> G
    R1 --> G
    R2 --> G
    G --> V[Validator]
    V -->|pass| A[Final answer]
    V -->|fail| L[Loop: broaden query / retry]
    L --> R1
    S -->|tool error| F[Fallback retrieval]
    F --> G
```

## Dynamic vs predefined chain

Predefined baseline:

```text
planner -> knowledge-retriever -> synthesizer -> validator
```

Dynamic chain examples:

```text
planner -> skill-router -> knowledge-retriever -> synthesizer -> validator
planner -> memory-retriever -> parallel-retriever -> synthesizer -> validator
planner -> skill-router -> error-recovery -> fallback-retriever -> synthesizer -> validator
```

The dynamic chain is generated from task features such as chemical-property requests, memory references, comparison terms, and complexity indicators.
