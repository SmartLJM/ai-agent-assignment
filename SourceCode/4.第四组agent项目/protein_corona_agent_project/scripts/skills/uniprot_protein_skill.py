from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import SKILL_CALL_LOG_PATH, UNIPROT_BASE_URL, UNIPROT_TIMEOUT  # noqa: E402


DEFAULT_ORGANISM_ID = 9606
DEFAULT_FIELDS = ",".join(
    [
        "accession",
        "id",
        "protein_name",
        "gene_names",
        "organism_name",
        "length",
        "cc_function",
        "cc_subcellular_location",
        "keyword",
    ]
)

GENE_ALIASES = {
    "OCT4": "POU5F1",
    "P53": "TP53",
    "C-MYC": "MYC",
}


@dataclass(frozen=True)
class ProteinSummary:
    accession: str
    entry_name: str
    protein_name: str
    genes: list[str]
    organism: str
    length: int | None
    function: str
    subcellular_location: str
    keywords: list[str]
    uniprot_url: str


def log_skill_call(tool: str, inputs: dict[str, Any], output: dict[str, Any]) -> None:
    SKILL_CALL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "skill": "UniProtProteinSkill",
        "tool": tool,
        "inputs": inputs,
        "output_preview": {
            key: value
            for key, value in output.items()
            if key in {"query", "accession", "protein_name", "result_count", "selected_accession"}
        },
    }
    with SKILL_CALL_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def request_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{UNIPROT_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    response = requests.get(url, params=params, timeout=UNIPROT_TIMEOUT)
    if not response.ok:
        raise RuntimeError(f"UniProt request failed: HTTP {response.status_code} {response.text[:500]}")
    return response.json()


def text_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        if isinstance(value.get("value"), str):
            return value["value"].strip()
        return " ".join(text_value(item) for item in value.values()).strip()
    if isinstance(value, list):
        return " ".join(text_value(item) for item in value).strip()
    return ""


def recommended_name(entry: dict[str, Any]) -> str:
    description = entry.get("proteinDescription") or {}
    recommended = description.get("recommendedName") or {}
    full_name = recommended.get("fullName") or {}
    name = text_value(full_name)
    if name:
        return name
    submission_names = description.get("submissionNames") or []
    if submission_names:
        return text_value(submission_names[0].get("fullName"))
    return str(entry.get("uniProtkbId") or entry.get("primaryAccession") or "")


def gene_names(entry: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for gene in entry.get("genes") or []:
        primary = gene.get("geneName") or {}
        name = text_value(primary)
        if name and name not in values:
            values.append(name)
        for synonym in gene.get("synonyms") or []:
            synonym_name = text_value(synonym)
            if synonym_name and synonym_name not in values:
                values.append(synonym_name)
    return values


def comment_text(entry: dict[str, Any], comment_type: str) -> str:
    parts: list[str] = []
    for comment in entry.get("comments") or []:
        if comment.get("commentType") != comment_type:
            continue
        for text in comment.get("texts") or []:
            value = text_value(text)
            if value:
                parts.append(value)
        for location in comment.get("subcellularLocations") or []:
            value = text_value(location)
            if value:
                parts.append(value)
    return " ".join(parts)


def keyword_names(entry: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for keyword in entry.get("keywords") or []:
        name = text_value(keyword.get("name") if isinstance(keyword, dict) else keyword)
        if name and name not in values:
            values.append(name)
    return values


def canonical_gene_query(query: str) -> str:
    normalized = query.strip()
    return GENE_ALIASES.get(normalized.upper(), normalized)


def parse_entry(entry: dict[str, Any]) -> ProteinSummary:
    accession = str(entry.get("primaryAccession") or "")
    return ProteinSummary(
        accession=accession,
        entry_name=str(entry.get("uniProtkbId") or ""),
        protein_name=recommended_name(entry),
        genes=gene_names(entry),
        organism=text_value((entry.get("organism") or {}).get("scientificName")),
        length=(entry.get("sequence") or {}).get("length"),
        function=comment_text(entry, "FUNCTION"),
        subcellular_location=comment_text(entry, "SUBCELLULAR LOCATION"),
        keywords=keyword_names(entry),
        uniprot_url=f"https://www.uniprot.org/uniprotkb/{accession}/entry" if accession else "",
    )


def summary_to_dict(summary: ProteinSummary) -> dict[str, Any]:
    return {
        "accession": summary.accession,
        "entry_name": summary.entry_name,
        "protein_name": summary.protein_name,
        "genes": summary.genes,
        "organism": summary.organism,
        "length": summary.length,
        "function": summary.function,
        "subcellular_location": summary.subcellular_location,
        "keywords": summary.keywords,
        "uniprot_url": summary.uniprot_url,
    }


def search_protein(
    query: str,
    *,
    organism_id: int = DEFAULT_ORGANISM_ID,
    size: int = 3,
    reviewed_only: bool = True,
) -> dict[str, Any]:
    query = query.strip()
    if not query:
        raise ValueError("Protein query is empty.")

    canonical_query = canonical_gene_query(query)
    base_clauses = [f"organism_id:{organism_id}"]
    if reviewed_only:
        base_clauses.append("reviewed:true")

    search_strategies = [
        f"gene_exact:{canonical_query} AND " + " AND ".join(base_clauses),
        f"gene:{canonical_query} AND " + " AND ".join(base_clauses),
        f"({query}) AND " + " AND ".join(base_clauses),
    ]

    payload: dict[str, Any] = {"results": []}
    used_query = search_strategies[-1]
    for search_query in search_strategies:
        payload = request_json(
            "/uniprotkb/search",
            {
                "query": search_query,
                "format": "json",
                "size": max(1, min(size, 10)),
                "fields": DEFAULT_FIELDS,
            },
        )
        used_query = search_query
        if payload.get("results"):
            break

    results = [summary_to_dict(parse_entry(entry)) for entry in payload.get("results") or []]
    output = {
        "query": query,
        "canonical_query": canonical_query,
        "uniprot_query": used_query,
        "organism_id": organism_id,
        "reviewed_only": reviewed_only,
        "result_count": len(results),
        "results": results,
    }
    log_skill_call("search_protein", {"query": query, "organism_id": organism_id, "size": size}, output)
    return output


def get_protein(accession: str) -> dict[str, Any]:
    accession = accession.strip()
    if not accession:
        raise ValueError("UniProt accession is empty.")
    payload = request_json(f"/uniprotkb/{accession}.json")
    output = summary_to_dict(parse_entry(payload))
    log_skill_call("get_protein", {"accession": accession}, output)
    return output


def explain_protein_for_context(
    query: str,
    context_question: str,
    *,
    organism_id: int = DEFAULT_ORGANISM_ID,
) -> dict[str, Any]:
    search = search_protein(query, organism_id=organism_id, size=1)
    if not search["results"]:
        output = {
            "query": query,
            "context_question": context_question,
            "selected_accession": "",
            "explanation": "No reviewed human UniProtKB entry was found for this query.",
            "protein": None,
        }
        log_skill_call(
            "explain_protein_for_context",
            {"query": query, "context_question": context_question, "organism_id": organism_id},
            output,
        )
        return output

    protein = search["results"][0]
    gene_text = ", ".join(protein["genes"][:4]) or "unknown gene"
    function = protein["function"] or "UniProt does not provide a concise function comment for this entry."
    explanation = (
        f"{query} maps to UniProt accession {protein['accession']} "
        f"({protein['protein_name']}; gene names: {gene_text}; organism: {protein['organism']}). "
        f"Function: {function}"
    )
    if protein.get("subcellular_location"):
        explanation += f" Subcellular location: {protein['subcellular_location']}"

    output = {
        "query": query,
        "context_question": context_question,
        "selected_accession": protein["accession"],
        "explanation": explanation,
        "protein": protein,
    }
    log_skill_call(
        "explain_protein_for_context",
        {"query": query, "context_question": context_question, "organism_id": organism_id},
        output,
    )
    return output


def main() -> None:
    result = explain_protein_for_context("OCT4", "OCT4 在细胞重编程中是什么角色？")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
