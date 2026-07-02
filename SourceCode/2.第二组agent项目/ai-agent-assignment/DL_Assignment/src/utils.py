import json
import re
from datetime import datetime
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)?")

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def append_jsonl(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def tokenize(text):
    return [t.lower() for t in TOKEN_RE.findall(text or "")]

def clean_text(text):
    text = (text or "").strip()
    for marker in ["<|endoftext|>", "[student]", "[assistant]", "\nStudent:", "\nNew Question:"]:
        idx = text.find(marker)
        if idx >= 0:
            text = text[:idx]
    return re.sub(r"\s+", " ", text).strip()

def first_sentences(text, n=3):
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join([p.strip() for p in parts if p.strip()][:n])
