import json
from pathlib import Path
from app import orchestrator

cases = [
    "What is the molecular weight of aspirin?",
    "Compare pharmacokinetics and pharmacodynamics.",
    "What should the agent do if PubChem fails for an unknown compound xyzznotreal?",
    "Why is a docking score not enough to approve a drug?"
]
traces = []
for q in cases:
    answer, trace = orchestrator.answer(q, return_trace=True)
    traces.append({"question": q, "answer": answer, "trace": trace})
Path("reports/orchestration_demo_traces.json").write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved reports/orchestration_demo_traces.json")
