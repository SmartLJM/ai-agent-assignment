# PrePR-CT: Graph Attention Networks for Cell-Type-Specific Drug Response Prediction in the Small-Data Regime

## Overview

Predicting how drugs affect diverse cell types phenotypically requires models that can generalize to unseen cell types even with limited training data. Alsulami et al. (Nature Machine Intelligence 2026) introduce **PrePR-CT** (Prediction of Perturbation Response for Cell Types), a graph-based deep learning approach that uses **cell-type-specific co-expression networks as inductive priors** (inductive bias) to predict transcriptional responses to chemical perturbations. The key insight is that leveraging cell-type-specific gene interaction structure—rather than pooling all cells together—enables generalization to new cell types with minimal data.

## Problem Being Solved

Current generative models (scGen, biolord, CPA, chemCPA) for predicting drug responses suffer from:
1. Requiring substantial amounts of single-cell data to learn distribution parameters
2. Poor generalization to out-of-distribution cell types not represented in training
3. Inability to incorporate cell-type-specific gene interaction structure as a structural prior
4. Limited interpretability regarding which gene-gene interactions drive response predictions

## Key Architecture

**PrePR-CT Pipeline**:

1. **Cell-type-specific co-expression graph construction**: For each cell type in the training set, compute a cell-type-specific gene co-expression network (adjacency matrix) from single-cell expression data. This graph encodes the regulatory context of that cell type.

2. **Graph Attention Network (GAT) encoding**: For a given batch of training samples containing cells from different cell types:
   - Retrieve the graph for each cell type
   - Apply GAT layers to process each graph, learning node (gene) embeddings
   - Apply graph pooling (max pooling across nodes) to generate a fixed-size cell-type feature vector H_c
   - These vectors capture cell-type-specific gene interaction patterns

3. **Feature integration and prediction**:
   - Stack cell-type feature vectors based on cell type labels in the batch
   - Concatenate with perturbation embeddings P (from pre-defined compound descriptors)
   - Pass through MLP regression layers to predict the perturbation response (post-perturbation expression for DEGs)

**Perturbation embeddings**: Pre-defined chemical descriptors (Morgan fingerprints or similar) represent each compound, enabling generalization to unseen perturbations.

## Main Results

**Benchmark evaluation** across five single-cell RNA-seq datasets (human blood cells, multiple cancer lines) and one bulk transcriptomics dataset:

- PrePR-CT achieves higher accuracy for **expression variability prediction** compared to generative baselines (scGen, chemCPA) when predicting unseen cell types in limited-data settings
- Particularly strong in cross-cell-type generalization: when the test cell type has no training examples, PrePR-CT's co-expression prior enables meaningful predictions

**Attribution analysis**: The GAT attention values provide gene-level interpretability, identifying "high-attention genes" that complement traditional differential expression analysis. These high-attention genes highlight pathway-specific mechanisms of drug response, including:
- Drug-specific transcription factor network activation
- Pathway-selective gene interaction rewiring

**Large-scale chemical screen**: PrePR-CT scales effectively to large-scale screening experiments, demonstrating computational efficiency advantages over generative models that require per-condition training.

## Why Inductive Priors Help in Small Data

The theoretical motivation is that co-expression networks encode cell-type-specific regulatory structure that constrains the hypothesis space. When data is limited, this structural prior prevents overfitting and guides the model to biologically meaningful solutions. In contrast, generative models try to learn the structure purely from data, requiring far more examples.

## Limitations

PrePR-CT requires co-expression network construction for training cell types, adding a preprocessing step. The approach predicts mean expression changes for DEGs rather than the full single-cell distribution. Performance on highly novel compound classes not represented in training compound sets may be limited.

## Citation

Alsulami R, Lehmann R, Khan SA, Lagani V, Maillo A, Gomez-Cabrero D, Kiani NA, Tegner J. "Predicting and interpreting cell-type-specific drug responses in the small-data regime using inductive priors." Nature Machine Intelligence 8, 461–473 (2026). DOI: 10.1038/s42256-026-01202-2

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | PrePR-CT uses pre-defined chemical descriptors (Morgan fingerprints) enabling generalization to unseen compounds without requiring biological annotation. |
| Cross cell-line (gene intersection) | Yes | The model is specifically designed and evaluated for cross-cell-type generalization using cell-type-specific co-expression graphs over shared gene vocabularies. |
| Zero-shot unseen cell line (gene intersection) | Yes | When the test cell type has no training examples, PrePR-CT's co-expression prior enables meaningful predictions by leveraging structural gene interaction priors. |
| Cross perturbation technology (gene intersection) | Not evaluated | The paper focuses on chemical perturbations only; cross-technology generalization between genetic and chemical perturbation types is not evaluated. |
| Zero-shot gene misalignment | No | PrePR-CT constructs cell-type-specific co-expression graphs over a shared gene vocabulary; completely disjoint gene vocabularies are not addressed. |
| Perturbation-specificity vs. simple baseline | Yes | PrePR-CT achieves higher accuracy than generative baselines (scGen, chemCPA) for expression variability prediction in limited-data cross-cell-type settings. |

**Overall capability tier**: Specialist
