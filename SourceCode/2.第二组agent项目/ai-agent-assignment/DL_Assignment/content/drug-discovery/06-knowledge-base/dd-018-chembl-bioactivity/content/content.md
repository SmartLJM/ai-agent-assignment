# ChEMBL and Bioactivity Data

**Knowledge set ID:** `dd-018-chembl-bioactivity`  
**Theme:** `drug-discovery`  
**Source:** The ChEMBL database in 2017  

## Curated Content

ChEMBL is a curated database of bioactive molecules with drug-like properties. It links compounds,
targets, assays, activities, mechanisms, documents, and drug information. ChEMBL is widely used to
train and evaluate computational models for bioactivity prediction, target association, QSAR, and
chemical biology analysis.  Bioactivity data need careful interpretation because assay formats,
units, target constructs, species, endpoints, and confidence levels vary. IC50, Ki, EC50, inhibition
percentage, and phenotypic readouts are not always directly comparable. Data curation and filtering
are essential before using ChEMBL for machine learning.  In agentic systems, ChEMBL is a knowledge-
base resource. The agent should mention assay context and confidence instead of treating every
activity value as equivalent proof of drug efficacy.

## Key Concepts

- `chembl`
- `bioactivity`
- `compound-target-assay`
- `database`

## Retrieval Note

This self-contained knowledge set is used by the agent for grounded drug-discovery Q&A, benchmark citation, memory distillation, and dynamic orchestration evidence.
