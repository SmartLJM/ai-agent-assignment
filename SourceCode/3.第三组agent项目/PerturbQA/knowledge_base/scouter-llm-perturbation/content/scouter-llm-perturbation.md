# Scouter: LLM Embeddings for Perturbation Prediction

## Overview

Scouter (Zhu & Li, bioRxiv 2024) proposes a fundamentally different approach to perturbation prediction by replacing graph neural networks (used by GEARS) or explicit molecular structure (used by CPA) with large language model (LLM) embeddings. The key idea is that the biological semantics of gene function are richly encoded in pre-trained LLM text embeddings (specifically from OpenAI's ChatGPT text-embedding-ada-002 / GenePT), providing a powerful inductive bias without requiring manually constructed biological graphs.

## Core Innovation: LLM Gene Embeddings

### GenePT Embeddings
Scouter uses GenePT (Chen & Zou, 2023), which embeds gene function descriptions from NCBI into a 1536-dimensional vector using ChatGPT's text-embedding-ada-002 model. These embeddings capture:
- Gene function annotations (GO terms, pathways)
- Disease associations
- Protein interactions (described in text)
- Evolutionary conservation patterns
- Regulatory relationships (as described in literature)

Unlike graph-based methods that require explicit edge construction, GenePT implicitly encodes this knowledge in a continuous semantic space.

### Compressor-Generator Architecture
Scouter introduces a two-stage architecture:

**1. Compressor**: Maps the 1536-dim GenePT embedding to a compact latent code representing the perturbation semantics. This removes noise and irrelevant information from the LLM embedding.

**2. Generator**: Takes the compressed perturbation representation and the basal cell state to predict the post-perturbation expression profile.

The compressor is trained to distill only the perturbation-relevant information from the full LLM embedding, while the generator learns to apply this signal to the cell-specific context.

## Experimental Results

Scouter is evaluated on 5 benchmark datasets including Norman et al. and Adamson et al.:

### Performance Metrics
- **MSE**: Mean squared error on all genes
- **1-PCC**: 1 minus Pearson correlation coefficient on differentially expressed genes

### Comparison with GEARS
Scouter achieves approximately **half the MSE and 1-PCC** of GEARS on average across the 5 datasets. This is a dramatic improvement suggesting that semantic LLM embeddings provide a richer perturbation signal than graph-based biological networks.

### Why LLM Embeddings Outperform Graphs
1. **Coverage**: GO graphs and co-expression networks miss many gene relationships; text embeddings capture all published biology.
2. **Semantic richness**: LLM embeddings encode functional context, not just topology.
3. **No manual curation**: No need to maintain biological databases or choose graph construction parameters.
4. **Noise robustness**: The compressor filters LLM embedding noise, retaining only perturbation-relevant information.

## Key Limitations

1. **Interpretability**: Unlike GEARS's explicit graph, it is difficult to understand which aspects of the LLM embedding drive predictions.
2. **Proprietary embeddings**: Dependence on OpenAI API (text-embedding-ada-002) creates reproducibility concerns; GenePT embeddings need to be pre-computed.
3. **Static knowledge**: LLM embeddings reflect published biology up to the training cutoff; novel gene functions are not captured.
4. **No combinatorial mechanism**: Scouter does not have an explicit mechanism for combinatorial perturbation prediction (gene pairs are simply embedded independently).

## Relationship to Other Approaches

| Method | Gene Representation | Source of Biological Knowledge |
|--------|--------------------|---------------------------------|
| Scouter | LLM embedding (1536-dim) | Text (literature, annotations) |
| GEARS | Graph node embedding | Gene Ontology + co-expression |
| TxPert | Multi-graph (STRING+GO+PxMap) | Protein interactions + pathways |
| scGPT | Learned from expression | Single-cell data patterns |
| CPA | Learned perturbation embedding | None (data-driven) |

## Impact

Scouter demonstrates that the field of perturbation prediction has underexplored the potential of large language models as gene representation tools. Its success suggests that text-based biological knowledge (accumulated in papers, databases, annotations) may be more informative than curated network databases for predicting perturbation outcomes.

## Citations

Zhu J, Li B (2024). Scouter: Predicting Transcriptional Responses to Genetic Perturbations with LLM embeddings. *bioRxiv:2024.12.06.627290*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | Scouter achieves approximately half the MSE and 1-PCC of GEARS on average across 5 benchmark datasets by using LLM semantic embeddings to generalize to unseen genetic perturbations. |
| Cross cell-line (gene intersection) | No | No explicit cross-cell-line transfer evaluation is reported; Scouter is evaluated on Norman and Adamson datasets within single cell-line contexts. |
| Zero-shot unseen cell line (gene intersection) | No | The paper does not evaluate zero-shot transfer to completely unseen cell lines without any fine-tuning. |
| Cross perturbation technology (gene intersection) | No | Scouter is evaluated only on CRISPR genetic perturbations; no cross-technology transfer evaluation is reported. |
| Zero-shot gene misalignment | No | Scouter predicts into the fixed training gene expression space; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | Scouter achieves approximately half the MSE of GEARS (which itself beats mean baselines), demonstrating strong perturbation-specific signal capture via LLM embeddings. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
