import json
from pathlib import Path
from app import answer_question
from src.utils import tokenize

BENCH_DIR = Path("benchmark/drug-discovery")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

def score_answer(pred, q):
    ans = q["answer"]
    qtype = q["type"]
    if qtype in ["true-false", "single-choice", "multiple-choice"]:
        gold = ans["content"]
        pred_low = pred.lower()
        if isinstance(gold, list):
            return 1.0 if all(str(x).lower() in pred_low for x in gold) else 0.0
        return 1.0 if str(gold).lower() in pred_low else 0.0
    keypoints = ans.get("keypoints", [])
    if not keypoints:
        return 0.0
    pred_tokens = set(tokenize(pred))
    hits = 0
    for kp in keypoints:
        kp_tokens = set(tokenize(kp["point"]))
        # Give credit for partial keypoint coverage.
        if kp_tokens and len(pred_tokens.intersection(kp_tokens)) / len(kp_tokens) >= 0.34:
            hits += 1
    return hits / len(keypoints)

def main():
    rows = []
    for path in sorted(BENCH_DIR.glob("Q*.json")):
        q = json.loads(path.read_text(encoding="utf-8"))
        pred = answer_question(q["question"], show_trace=False)
        score = score_answer(pred, q)
        rows.append({"id": q["id"], "question": q["question"], "score": round(score, 3), "prediction": pred, "gold": q["answer"]["content"], "sources": q["sources"]})
    avg = sum(r["score"] for r in rows) / max(1, len(rows))
    report = {"question_count": len(rows), "average_score": round(avg, 3), "passed_at_0_34": sum(r["score"] >= 0.34 for r in rows), "results": rows}
    (REPORT_DIR/"benchmark_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["question_count", "average_score", "passed_at_0_34"]}, indent=2))

if __name__ == "__main__":
    main()
