from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import math
import json
from .utils import tokenize, first_sentences

def curated_body(markdown):
    text = markdown or ""
    if "## Curated Content" in text:
        text = text.split("## Curated Content", 1)[1]
    if "## Key Concepts" in text:
        text = text.split("## Key Concepts", 1)[0]
    return text.replace("**", "").replace("`", "").strip()

def relevant_excerpt(query, markdown, n=4):
    body = curated_body(markdown)
    sentences = [x.strip() for x in __import__("re").split(r"(?<=[.!?])\s+", body) if x.strip()]
    q = set(tokenize(query))
    scored = []
    for idx, sent in enumerate(sentences):
        toks = set(tokenize(sent))
        score = len(q.intersection(toks))
        # Boost exact phrases and important scientific cues.
        lower = sent.lower()
        for term in ["target validation", "applicability domain", "orthogonal assays", "potency", "retrieval confidence", "docking scores", "generated molecule"]:
            if term in (query or "").lower() and term in lower:
                score += 5
        if score > 0:
            scored.append((score, idx, sent))
    if scored:
        chosen = sorted(sorted(scored, key=lambda x: x[0], reverse=True)[:n], key=lambda x: x[1])
        return " ".join(x[2] for x in chosen)
    return first_sentences(body, n)


@dataclass
class KnowledgeAsset:
    id: str
    title: str
    content: str
    keywords: list
    theme: str
    source: dict
    path: str

class KnowledgeBase:
    """Rubric-aligned knowledge asset loader with deterministic lexical retrieval.

    The project can optionally be extended to Chroma/SentenceTransformers, but this
    backend is intentionally dependency-light so the submission is runnable even on
    restricted university machines.
    """
    def __init__(self, content_root="content/drug-discovery"):
        self.content_root = Path(content_root)
        self.assets = self._load_assets()
        self._doc_tokens = {a.id: tokenize(a.title + " " + a.content + " " + " ".join(a.keywords)) for a in self.assets}
        self._df = Counter()
        for toks in self._doc_tokens.values():
            for t in set(toks):
                self._df[t] += 1
        self._n = max(1, len(self.assets))

    def _load_assets(self):
        assets = []
        for source_file in sorted(self.content_root.rglob("source.json")):
            folder = source_file.parent
            kw_file = folder / "keywords.json"
            content_file = folder / "content" / "content.md"
            if not kw_file.exists() or not content_file.exists():
                continue
            source = json.loads(source_file.read_text(encoding="utf-8"))
            keywords_obj = json.loads(kw_file.read_text(encoding="utf-8"))
            theme = list(keywords_obj.keys())[0]
            keywords = keywords_obj.get(theme, [])
            content = content_file.read_text(encoding="utf-8")
            title = content.splitlines()[0].replace("#", "").strip() if content.splitlines() else source.get("title", "")
            assets.append(KnowledgeAsset(
                id=source.get("knowledge_set_id", folder.name), title=title, content=content,
                keywords=keywords, theme=theme, source=source, path=str(folder)
            ))
        if not assets:
            raise RuntimeError(f"No valid knowledge assets found under {self.content_root}")
        return assets

    def search(self, query, k=4, required_keywords=None):
        q_tokens = tokenize(query)
        required_keywords = set(required_keywords or [])
        results = []
        for asset in self.assets:
            toks = self._doc_tokens[asset.id]
            tf = Counter(toks)
            score = 0.0
            for q in q_tokens:
                if q in tf:
                    idf = math.log((self._n + 1) / (self._df[q] + 1)) + 1
                    score += (1 + math.log(tf[q])) * idf
            # Strong boost for exact title/keyword matches.
            lower_blob = (asset.title + " " + " ".join(asset.keywords)).lower()
            for q in q_tokens:
                if q in lower_blob:
                    score += 2.0
            if required_keywords and required_keywords.intersection(set(asset.keywords)):
                score += 5.0
            if score > 0:
                results.append({
                    "id": asset.id, "title": asset.title, "score": round(score, 4),
                    "content": asset.content, "excerpt": relevant_excerpt(query, asset.content, 4),
                    "keywords": asset.keywords, "source": asset.source
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def get(self, asset_id):
        for a in self.assets:
            if a.id == asset_id:
                return a
        return None

    def coverage(self):
        themes = Counter()
        kw = Counter()
        source_types = Counter()
        for a in self.assets:
            themes[a.theme] += 1
            source_types[a.source.get("source_type", "unknown")] += 1
            for k in a.keywords:
                kw[k] += 1
        return {"asset_count": len(self.assets), "themes": dict(themes), "source_types": dict(source_types), "top_keywords": dict(kw.most_common(20))}
