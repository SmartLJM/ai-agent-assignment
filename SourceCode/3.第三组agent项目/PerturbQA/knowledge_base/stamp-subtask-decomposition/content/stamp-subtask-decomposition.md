# STAMP: Subtask Decomposition Modeling for Genetic Perturbation Prediction

## Overview

STAMP (Subtask Decomposition Modeling for Genetic Perturbation Prediction) is an AI framework that reformulates the challenging genetic perturbation prediction problem into three progressive, tractable subtasks. Gao et al. (Nature Computational Science 2024) demonstrate that this decomposition strategy substantially improves performance over existing methods for single-gene perturbations, multi-gene perturbations, and cross-cell-line generalization.

## Problem Being Solved

Predicting transcriptional outcomes of genetic perturbations is fundamental to understanding gene function, yet existing methods face three main challenges:

1. **Single-gene perturbation prediction**: Predicting which genes are differentially expressed and by how much when a single gene is knocked out
2. **Combinatorial perturbation prediction**: The space of possible multi-gene combinations grows exponentially, making brute-force experimentation infeasible
3. **Cross-cell-line generalization**: Models trained on one cell line often fail when applied to novel cell lines due to cell-type-specific regulatory contexts

Existing approaches (CPA, GEARS, scBERT, Geneformer, scGPT) treat prediction as a monolithic end-to-end task, but the inherent logical structure of the problem suggests a hierarchical decomposition.

## Key Innovation: Subtask Decomposition

Inspired by human cognitive strategies for complex problems, STAMP decomposes the high-dimensional genetic perturbation prediction into three progressive subtasks:

**Subtask 1: Identify DEGs**
- Binary classification: For each gene in the genome, predict whether it will be differentially expressed after the perturbation
- This is a dimension reduction step—only a sparse subset of genes are typically affected
- Maps gene embeddings of perturbed genes to a DEG indicator vector
- The sparsity of the postperturbation space improves signal-to-noise ratio

**Subtask 2: Determine expression change directions**
- Given the predicted DEGs from Subtask 1, classify whether each DEG will be upregulated or downregulated
- Binary classification on the subset of predicted DEGs
- Subtask 2's predictions serve as intermediate supervisory signals for Subtask 3

**Subtask 3: Estimate expression change magnitudes**
- Regression: Given predicted DEGs and their directions, estimate the continuous magnitude of expression change
- Subtask 2 outcomes serve as intermediate supervision for Subtask 3 (hierarchical intermediate supervision)
- This avoids the "prediction of zero" failure mode—only predicted DEGs need magnitude prediction

**Joint training**: All three subtasks are trained jointly using multitask learning and intermediate supervised learning via gradient descent, enabling the subtasks to mutually reinforce each other.

## Plug-in Compatibility

STAMP is designed as a flexible plug-in framework compatible with:
- Pretrained gene embeddings from scBERT, Geneformer, or scGPT (leveraging these as input representations)
- Dynamically learnable gene embedding matrices
This makes STAMP applicable with or without foundation model pretraining.

## Main Results

Evaluated on four benchmark datasets (RPE1_essential, K562_essential, TFatlas, K562_GW from Norman et al.):

**Single-gene perturbation**: STAMP substantially outperforms CPA, GEARS, and foundation-model-based baselines on all three subtask metrics (DEG precision/recall, direction accuracy, magnitude correlation).

**Multi-gene perturbation**: STAMP correctly identifies synergistic and antagonistic genetic interactions with higher precision than GEARS, which relies on knowledge graphs of gene-gene relationships.

**Cross-cell-line generalization**: STAMP applied to new cell lines shows robust performance, rapidly identifying key regulatory genes and pathways with small amounts of adaptation data.

**Genetic interaction subtype detection**: The subtask decomposition enables finer-grained analysis of genetic interaction types (additive, synergistic, suppressive), with STAMP achieving more accurate subtype classification.

## Limitations

STAMP requires gene embeddings as input (from pretrained models or learned); the quality of these embeddings affects prediction accuracy. The method is currently validated for genetic perturbations (CRISPR knockout) and may not directly transfer to chemical perturbations. Cross-cell-line generalization, while improved, remains the hardest challenge.

## Citation

Gao Y, Wei Z, Dong K, Chen K, Yang J, Chuai G, Liu Q. "Toward subtask-decomposition-based learning and benchmarking for predicting genetic perturbation outcomes and beyond." Nature Computational Science (2024). DOI: 10.1038/s43588-024-00698-1

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | STAMP is evaluated on held-out single-gene and multi-gene perturbations not seen during training, substantially outperforming CPA and GEARS. |
| Cross cell-line (gene intersection) | Yes | STAMP explicitly demonstrates cross-cell-line generalization, applying trained models to novel cell lines and identifying key regulatory genes with small adaptation data. |
| Zero-shot unseen cell line (gene intersection) | Partial | Cross-cell-line results are shown but require at least small amounts of adaptation data; truly zero-shot performance is not separately characterized. |
| Cross perturbation technology (gene intersection) | No | STAMP is validated only for genetic perturbations (CRISPR knockout); chemical perturbation generalization is not addressed. |
| Zero-shot gene misalignment | No | STAMP relies on gene embeddings from pretrained foundation models operating on a shared gene vocabulary; completely different gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | STAMP substantially outperforms CPA, GEARS, and foundation-model baselines on DEG precision/recall, direction accuracy, and magnitude correlation across all four benchmark datasets. |

**Overall capability tier**: Specialist
