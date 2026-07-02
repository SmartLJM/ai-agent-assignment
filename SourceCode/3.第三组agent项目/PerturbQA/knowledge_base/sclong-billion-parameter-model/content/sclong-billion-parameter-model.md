# scLong: Billion-Parameter Foundation Model Capturing Long-Range Gene Context

## Overview

scLong is a billion-parameter foundation model for single-cell transcriptomics that breaks two limitations of existing foundation models: (1) performing self-attention on only a small subset of highly expressed genes (typically 2,000-4,096), and (2) not integrating external gene-specific functional knowledge. Bai, Mo, Zhang et al. (Nature Communications 2026) pretrain scLong on 48 million cells to perform self-attention across the **entire set of 28,000 human genes**, capturing long-range dependencies between all genes including lowly expressed ones, and integrating Gene Ontology knowledge via a graph convolutional network.

## Problem Being Solved

Two fundamental limitations of current single-cell foundation models:

1. **Subset attention**: Models like Geneformer, scFoundation, and scGPT truncate inputs to 1,536-4,096 highly expressed genes to save compute. This excludes:
   - Lowly expressed regulatory genes (TFs, signaling molecules)
   - Rare transcripts with essential roles in specific cell states
   - Long-range gene interactions that cross expression-level boundaries

2. **No external knowledge**: Models rely purely on expression co-occurrence patterns. The Gene Ontology encodes rich hierarchical relationships between genes (biological processes, molecular functions, cellular components) that could enhance contextual understanding.

## Architecture: Dual Encoder Design

**Gene encoder (external knowledge integration)**:
- Constructs a gene graph from Gene Ontology: nodes = genes, edges weighted by Jaccard index of shared GO terms
- High-Jaccard pairs are connected, capturing functional similarity
- A Graph Convolutional Network (GCN) performs message passing to learn gene representation vectors
- Each gene gets a fixed representation reflecting its GO-annotated functional context

**Expression encoder**:
- A Multi-Layer Perceptron (MLP) converts each gene's scalar expression value to a representation vector
- Captures quantitative expression information independent of gene identity

**Element representation**:
- For each gene in a cell, combine gene representation (identity) + expression representation (quantity) into an element representation
- Result: 28,000 element representations per cell

**Contextual encoder (two-track Performer)**:
- Full self-attention across all ~28,000 genes is quadratic—too expensive
- **Performer** approximation: linearizes attention using random feature maps, reducing O(n²) to O(n)
- **Two-track design** for efficiency vs. quality balance:
  - **High-expression group** (top-ranked genes): Processed by a larger Performer encoder with more layers/parameters—capturing core regulatory interactions
  - **Low-expression group** (remaining genes): Processed by a smaller Performer encoder—efficiency-optimized for less critical signals
- Both track outputs are concatenated for a unified cell representation

## Why Include Low-Expression Genes?

The authors argue that low-expression genes (LEGs) are functionally important:
- Many transcription factors and signaling molecules are expressed at low levels even when active
- LEGs often act as regulatory switches in complex gene networks
- Excluding them creates incomplete representations that miss critical regulatory signals
- The two-track design handles them efficiently without sacrificing core performance

## Training

- **Scale**: 1 billion parameters, pretrained on 48 million cells
- **Pretraining task**: Masked gene expression prediction using Performer approximation
- **Gene Ontology integration**: GCN is pretrained separately on GO structure, then integrated with the contextual encoder

## Main Results

scLong surpasses both state-of-the-art foundation models (Geneformer, scFoundation, GeneCompass, UCE) and task-specific models across:

**Genetic perturbation prediction**: Substantially better prediction of transcriptional responses to CRISPR knockouts, especially for effects on lowly expressed genes that other models ignore.

**Chemical perturbation prediction**: Better generalization to novel drug-cell type combinations in the L1000/LINCS setting.

**Cancer drug response forecasting**: More accurate prediction of cancer cell line sensitivity to chemotherapy drugs (GDSC dataset).

**GRN inference**: Better reconstruction of known gene regulatory network interactions, benefiting from GO-informed gene representations.

**Cell type classification**: Competitive with or better than existing foundation models on standard cell type annotation benchmarks.

## Comparison to Other Large Models

| Model | Parameters | Attention | Full transcriptome | GO knowledge |
|-------|------------|-----------|-------------------|-------------|
| Geneformer | 40M | Dense Transformer | No (2,048 genes) | No |
| scFoundation | 100M | Asymmetric Transformer | No (subset) | No |
| GeneCompass | 100M | Transformer | No (2,048) | Partial (GRN) |
| UCE | 650M | Transformer | No | Protein LM |
| **scLong** | **1B** | **Performer (linear)** | **Yes (28,000)** | **Yes (GO GCN)** |

## Limitations

The Performer approximation introduces some error in attention computation compared to exact attention. The model requires substantial computational resources for training and inference. Full-transcriptome attention at 28,000 genes, even with Performer, is still more expensive than subset-attention models.

## Citation

Bai D, Mo S, Zhang R, Luo Y, Gao J, Yang JP, Wu Q, Rahmani H, Amariuta T, Grotjahn D, Zhong S, Lewis N, Wang W, Ideker T, Xie P, Xing E. "scLong: a billion-parameter foundation model for capturing long-range gene context in single-cell transcriptomics." Nature Communications 17, 2380 (2026). DOI: 10.1038/s41467-026-69102-y

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | scLong demonstrates substantially better prediction of transcriptional responses to CRISPR knockouts than competing foundation models, especially for effects on lowly expressed genes. |
| Cross cell-line (gene intersection) | Yes | scLong generalizes to novel drug-cell type combinations in the L1000/LINCS setting for chemical perturbation prediction with a full 28K-gene shared vocabulary. |
| Zero-shot unseen cell line (gene intersection) | Partial | The model's billion-parameter pretraining on 48M cells provides broad representations, but zero-shot prediction on completely unseen cell lines without any data is not explicitly demonstrated. |
| Cross perturbation technology (gene intersection) | Not evaluated | Genetic (CRISPR) and chemical perturbation prediction are evaluated separately; training on one technology and predicting another is not tested. |
| Zero-shot gene misalignment | No | scLong operates on the full 28,000 human gene vocabulary; completely disjoint gene vocabularies between train and test are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | scLong surpasses Geneformer, scFoundation, GeneCompass, and UCE on genetic perturbation, chemical perturbation, and cancer drug response forecasting tasks. |

**Overall capability tier**: Foundation
