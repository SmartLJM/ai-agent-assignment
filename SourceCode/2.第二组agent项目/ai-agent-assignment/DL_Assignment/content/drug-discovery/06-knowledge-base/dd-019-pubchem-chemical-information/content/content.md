# PubChem and Chemical Information

**Knowledge set ID:** `dd-019-pubchem-chemical-information`  
**Theme:** `drug-discovery`  
**Source:** PubChem 2023 update  

## Curated Content

PubChem is an open chemistry database that provides information about chemical substances,
compounds, structures, identifiers, synonyms, computed properties, assays, bioactivity links,
patents, literature links, and safety annotations. It is useful for retrieving molecular formula,
molecular weight, canonical SMILES, InChIKey, and IUPAC names.  The PubChem PUG-REST service allows
software agents to query compound records through URLs. This makes PubChem suitable as a tool or
skill in an AI agent platform. For example, a user can ask for the molecular weight of aspirin, and
the agent can call PubChem rather than relying on memory.  A correct answer should distinguish
database lookup from medical recommendation. PubChem can provide chemical information, but it does
not by itself establish clinical efficacy, dosing, or patient-specific safety.

## Key Concepts

- `pubchem`
- `chemical-information`
- `compound-properties`
- `pug-rest`

## Retrieval Note

This self-contained knowledge set is used by the agent for grounded drug-discovery Q&A, benchmark citation, memory distillation, and dynamic orchestration evidence.
