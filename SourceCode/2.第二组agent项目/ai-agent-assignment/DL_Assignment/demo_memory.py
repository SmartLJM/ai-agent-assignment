import json
import shutil
from pathlib import Path
from src.orchestrator import DynamicOrchestrator

# Use a clean demo memory/log folder so the evidence is deterministic and
# previous UI tests cannot pollute the recall result.
demo_memory_dir = Path("reports/demo_memory_store")
demo_log_dir = Path("reports/demo_memory_logs")
for p in [demo_memory_dir, demo_log_dir]:
    if p.exists():
        shutil.rmtree(p)

orchestrator = DynamicOrchestrator(memory_dir=str(demo_memory_dir), log_dir=str(demo_log_dir))

print(orchestrator.answer("Remember that my project focuses on ADME and pharmacokinetics."))
print(orchestrator.answer("Why is a docking score not enough to approve a drug?"))
answer, trace = orchestrator.answer("What did I ask earlier about ADME?", return_trace=True)
print(answer)
print(json.dumps(orchestrator.memory.storage_snapshot(), indent=2))
