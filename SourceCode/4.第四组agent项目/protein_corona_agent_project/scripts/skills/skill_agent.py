from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import SKILL_CALL_LOG_PATH  # noqa: E402
from skills.uniprot_protein_skill import (  # noqa: E402
    explain_protein_for_context,
    get_protein,
    search_protein,
)


# PyCharm can run this file directly. Edit USER_REQUEST for a one-shot demo.
USER_REQUEST = "OCT4 在细胞重编程中是什么角色？请查 UniProt。"


ACCESSION_PATTERN = re.compile(r"\b[A-NR-Z][0-9][A-Z0-9]{3}[0-9]\b|\b[A-Z][0-9][A-Z0-9]{3}[0-9]-[0-9]+\b")
KNOWN_ALIASES = {
    "OCT4": "OCT4",
    "POU5F1": "POU5F1",
    "SOX2": "SOX2",
    "KLF4": "KLF4",
    "MYC": "MYC",
    "C-MYC": "MYC",
    "TP53": "TP53",
    "P53": "TP53",
    "RNF20": "RNF20",
    "NANOG": "NANOG",
    "H2B": "H2B",
    "EGFR": "EGFR",
}


def extract_protein_query(text: str) -> str:
    upper_text = text.upper()
    for alias, normalized in KNOWN_ALIASES.items():
        if re.search(rf"(?<![A-Z0-9]){re.escape(alias)}(?![A-Z0-9])", upper_text):
            return normalized

    candidates = re.findall(r"\b[A-Z0-9]{2,10}\b", upper_text)
    blocked = {"API", "RAG", "LLM", "DNA", "RNA", "JSON", "HTTP", "HTTPS", "UNIPROT"}
    for candidate in candidates:
        if candidate not in blocked and any(char.isdigit() for char in candidate):
            return candidate
    for candidate in candidates:
        if candidate not in blocked:
            return candidate
    raise ValueError("No protein or gene symbol was detected in the user request.")


def route_skill(user_request: str) -> dict[str, Any]:
    accession_match = ACCESSION_PATTERN.search(user_request)
    lower = user_request.lower()

    if accession_match and ("详细" in user_request or "accession" in lower or "条目" in user_request):
        accession = accession_match.group(0)
        return {
            "skill": "UniProtProteinSkill",
            "tool": "get_protein",
            "args": {"accession": accession},
            "reason": "The request contains a UniProt-like accession and asks for an entry lookup.",
        }

    protein_query = extract_protein_query(user_request)
    if any(word in lower for word in ["explain", "role", "function"]) or any(
        word in user_request for word in ["作用", "角色", "功能", "是什么", "解释"]
    ):
        return {
            "skill": "UniProtProteinSkill",
            "tool": "explain_protein_for_context",
            "args": {"query": protein_query, "context_question": user_request},
            "reason": "The request asks for a biological role or function, so a contextual explanation is appropriate.",
        }

    return {
        "skill": "UniProtProteinSkill",
        "tool": "search_protein",
        "args": {"query": protein_query, "size": 3},
        "reason": "The request asks for protein information, so a UniProt search is appropriate.",
    }


def execute_plan(plan: dict[str, Any]) -> dict[str, Any]:
    tool = plan["tool"]
    args = plan["args"]
    if tool == "search_protein":
        return search_protein(**args)
    if tool == "get_protein":
        return get_protein(**args)
    if tool == "explain_protein_for_context":
        return explain_protein_for_context(**args)
    raise ValueError(f"Unsupported skill tool: {tool}")


def run_skill_agent(user_request: str) -> dict[str, Any]:
    plan = route_skill(user_request)
    result = execute_plan(plan)
    return {
        "user_request": user_request,
        "selected_skill": plan["skill"],
        "selected_tool": plan["tool"],
        "selection_reason": plan["reason"],
        "tool_args": plan["args"],
        "result": result,
        "call_log_path": str(SKILL_CALL_LOG_PATH),
    }


def main() -> None:
    output = run_skill_agent(USER_REQUEST)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
