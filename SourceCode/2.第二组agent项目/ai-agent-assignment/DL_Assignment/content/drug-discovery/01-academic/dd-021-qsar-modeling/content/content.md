# QSAR Modeling

**Knowledge set ID:** `dd-021-qsar-modeling`  
**Theme:** `drug-discovery`  
**Source:** QSAR modeling: where have you been? where are you going to?  

## Curated Content

Quantitative structure-activity relationship modeling links molecular structure to measured
biological activity. Traditional QSAR uses molecular descriptors and statistical models, while
modern QSAR may use fingerprints, graph neural networks, transformers, or ensemble machine learning.
QSAR can prioritize compounds and guide medicinal chemistry decisions.  Reliable QSAR requires
curated data, consistent endpoints, appropriate train-test splitting, external validation, and clear
applicability domain. Random splits can overestimate performance when similar compounds appear in
both training and test sets. Scaffold splits and prospective validation provide stronger evidence
for generalization.  A correct answer should avoid treating QSAR predictions as guaranteed activity.
QSAR generates hypotheses and rankings that must be tested experimentally, especially for new
scaffolds outside the model’s training domain.

## Key Concepts

- `qsar`
- `molecular-descriptors`
- `bioactivity-prediction`
- `applicability-domain`

## Retrieval Note

This self-contained knowledge set is used by the agent for grounded drug-discovery Q&A, benchmark citation, memory distillation, and dynamic orchestration evidence.
