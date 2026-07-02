import json
import re
from pathlib import Path

ROOT = Path(".")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

errors = []
assets = list((ROOT/"content"/"drug-discovery").rglob("source.json"))
if len(assets) < 20:
    errors.append(f"Expected at least 20 knowledge sets, found {len(assets)}")
for src in assets:
    folder = src.parent
    for needed in [folder/"content"/"content.md", folder/"keywords.json", folder/"source.json"]:
        if not needed.exists():
            errors.append(f"Missing {needed}")
    kw = json.loads((folder/"keywords.json").read_text(encoding="utf-8"))
    for theme, kws in kw.items():
        if not KEBAB.match(theme): errors.append(f"Non-kebab theme {theme} in {folder}")
        for k in kws:
            if not KEBAB.match(k): errors.append(f"Non-kebab keyword {k} in {folder}")
    source = json.loads(src.read_text(encoding="utf-8"))
    if not source.get("url"):
        errors.append(f"Missing URL in {src}")
bench = list((ROOT/"benchmark"/"drug-discovery").glob("Q*.json"))
if len(bench) < 20:
    errors.append(f"Expected at least 20 benchmark questions, found {len(bench)}")
required_q = {"id","question","type","difficulty","answer","sources","theme"}
for p in bench:
    q = json.loads(p.read_text(encoding="utf-8"))
    missing = required_q - set(q)
    if missing: errors.append(f"Missing {missing} in {p}")
    if not re.match(r"^Q\d{4}$", q.get("id", "")): errors.append(f"Bad id {q.get('id')} in {p}")
    if q.get("type") not in ["short-answer","true-false","single-choice","multiple-choice"]: errors.append(f"Bad type in {p}")
    if "type" not in q.get("answer", {}) or "content" not in q.get("answer", {}): errors.append(f"Bad answer object in {p}")
print(json.dumps({"knowledge_sets": len(assets), "benchmark_questions": len(bench), "errors": errors}, indent=2))
if errors:
    raise SystemExit(1)
