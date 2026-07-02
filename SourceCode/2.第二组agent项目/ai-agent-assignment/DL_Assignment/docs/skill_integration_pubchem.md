# PubChem SKILL Integration

The project integrates PubChem as a course-platform SKILL. It is used when the user asks for chemical properties such as molecular weight, formula, SMILES, InChIKey, or IUPAC name.

## Interfaces

```text
search_compound(name)
get_compound_properties(name)
get_synonyms(name)
```

## Example natural-language trigger

```text
What is the molecular weight of aspirin?
```

The orchestrator detects a chemical-property request and routes the query to `PubChemSkill.get_compound_properties("aspirin")`.

## Logs

Invocation logs are saved in:

```text
logs/skill_invocations.jsonl
```

Run:

```bash
python demo_skill.py
```
