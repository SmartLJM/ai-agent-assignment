from pathlib import Path
from .utils import read_json, write_json, append_jsonl, tokenize, now_iso

DOMAIN_ENTITIES = [
    "target identification", "target validation", "molecular docking", "virtual screening", "adme",
    "pharmacokinetics", "pharmacodynamics", "pubchem", "chembl", "qsar", "drug repurposing",
    "clinical trial", "lead optimization", "toxicology", "knowledge graph", "ai", "machine learning",
    "aspirin", "caffeine", "ibuprofen", "acetaminophen"
]

class MemorySystem:
    """Multi-level persistent memory: working, episodic, semantic."""
    def __init__(self, memory_dir="memory", capacity=6):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.capacity = capacity
        self.working_path = self.memory_dir / "working_memory.json"
        self.episodic_path = self.memory_dir / "episodic_memory.jsonl"
        self.semantic_path = self.memory_dir / "semantic_memory.json"
        self._init_files()

    def _init_files(self):
        if not self.working_path.exists():
            write_json(self.working_path, {"layer":"working", "capacity": self.capacity, "turns": []})
        if not self.semantic_path.exists():
            write_json(self.semantic_path, {"layer":"semantic", "entities": [], "relations": []})
        self.episodic_path.touch(exist_ok=True)

    def read_working(self):
        return read_json(self.working_path, {"turns": []})

    def write_turn(self, question, answer, route):
        working = self.read_working()
        turn = {"time": now_iso(), "question": question, "answer": answer, "route": route}
        working.setdefault("turns", []).append(turn)
        working["turns"] = working["turns"][-self.capacity:]
        write_json(self.working_path, working)
        append_jsonl(self.episodic_path, {"layer":"episodic", "summary": f"User asked: {question} | Agent answered: {answer[:220]}", **turn})
        self._update_semantic(question, answer)

    def _update_semantic(self, question, answer):
        sem = read_json(self.semantic_path, {"entities": [], "relations": []})
        blob = (question + " " + answer).lower()
        existing = {e["id"]: e for e in sem.get("entities", [])}
        found = []
        for ent in DOMAIN_ENTITIES:
            if ent in blob:
                ent_id = ent.replace(" ", "-").lower()
                if ent_id not in existing:
                    existing[ent_id] = {"id": ent_id, "label": ent, "type": "drug-discovery-concept", "mentions": 0}
                existing[ent_id]["mentions"] += 1
                found.append(ent_id)
        sem["entities"] = list(existing.values())
        rels = sem.get("relations", [])
        for i in range(len(found)):
            for j in range(i+1, len(found)):
                rel = {"head": found[i], "relation": "co-mentioned-with", "tail": found[j]}
                if rel not in rels:
                    rels.append(rel)
        sem["relations"] = rels[-200:]
        write_json(self.semantic_path, sem)

    def _is_recall_question(self, text):
        """Detect meta-memory questions so they are not returned as remembered content."""
        t = (text or "").lower()
        return any(p in t for p in [
            "what did i ask", "what did i say", "earlier", "previous",
            "last question", "last time", "closest previous context"
        ])

    def retrieve(self, query, k=3):
        q = set(tokenize(query))
        results = []
        recall_query = self._is_recall_question(query)

        # Working memory retrieval. For recall questions, do not return earlier
        # recall/meta-memory questions, otherwise the demo can appear to
        # remember its own recall prompt instead of the user's substantive topic.
        for turn in self.read_working().get("turns", []):
            turn_question = turn.get("question", "")
            if recall_query and self._is_recall_question(turn_question):
                continue
            score = len(q.intersection(set(tokenize(turn_question + " " + turn.get("answer", "")))))
            if score:
                # Prefer actual user turns over semantic entities for conversation recall.
                results.append({"layer":"working", "score":score + (3 if recall_query else 0), "item":turn})

        # Episodic memory retrieval
        if self.episodic_path.exists():
            for line in self.episodic_path.read_text(encoding="utf-8").splitlines()[-100:]:
                if not line.strip():
                    continue
                import json
                item = json.loads(line)
                item_question = item.get("question", "")
                if recall_query and self._is_recall_question(item_question):
                    continue
                score = len(q.intersection(set(tokenize(item.get("summary", "")))))
                if score:
                    results.append({"layer":"episodic", "score":score + (2 if recall_query else 0), "item":item})

        # Semantic memory retrieval. Semantic entries are useful for concept recall,
        # but for conversational recall they should be a fallback only.
        if not recall_query:
            sem = read_json(self.semantic_path, {"entities": [], "relations": []})
            for ent in sem.get("entities", []):
                score = len(q.intersection(set(tokenize(ent.get("label", "") + " " + ent.get("id", "")))))
                if score:
                    related = [r for r in sem.get("relations", []) if r.get("head") == ent["id"] or r.get("tail") == ent["id"]]
                    results.append({"layer":"semantic", "score":score + ent.get("mentions", 0), "item":{"entity": ent, "relations": related[:5]}})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def storage_snapshot(self):
        sem = read_json(self.semantic_path, {"entities": [], "relations": []})
        return {
            "working_memory_file": str(self.working_path),
            "episodic_memory_file": str(self.episodic_path),
            "semantic_memory_file": str(self.semantic_path),
            "working_turns": len(self.read_working().get("turns", [])),
            "semantic_entities": len(sem.get("entities", [])),
            "semantic_relations": len(sem.get("relations", []))
        }
