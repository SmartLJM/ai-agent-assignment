# LPM: Large Perturbation Model for In Silico Biological Discovery

## Overview

Most existing computational models for perturbation biology focus narrowly on predicting gene expression changes from a specific perturbation type (CRISPR genetic knockouts OR chemical compounds) using a single readout modality (transcriptomics). Miladinovic et al. (Nature Computational Science 2025) present the **Large Perturbation Model (LPM)**, a deep learning model that integrates multiple, heterogeneous perturbation experiments across diverse perturbation types (CRISPR, chemical), readout modalities (transcriptomics, viability), and biological contexts (single-cell, bulk, multiple cell lines) into a single unified model.

## Problem Being Solved

Perturbation experiments vary in protocols, readouts, and model systems—making it extremely difficult to extract generalizable biological insights that transfer across experiments. Existing models like GEARS (genetic perturbations, knowledge graphs) and CPA (chemical perturbations, autoencoders) are context-specific. Foundation models like Geneformer and scGPT are limited to transcriptomics and face challenges with the low signal-to-noise ratio in high-throughput screens. No prior model can seamlessly handle the full diversity of perturbation data types.

## Key Architecture: PRC-Disentangled Design

LPM introduces a **decoder-only architecture** that represents each perturbation experiment as a disentangled tuple of three dimensions:

- **P (Perturbation)**: The identity and type of the perturbation (e.g., STAT1 CRISPRi, compound X)
- **R (Readout)**: The measured output type (e.g., gene expression of gene Y, cell viability)
- **C (Context)**: The biological context (e.g., cell line A549, LINCS protocol)

Each dimension is represented as a separate conditioning variable. The model learns to predict the outcome of the P-R-C combination.

**Key advantages of this architecture**:

1. **Seamless heterogeneous integration**: By representing experiments as P-R-C tuples, LPM handles diverse data types without loss of generality, regardless of dataset shape or format
2. **No encoder constraints**: Unlike encoder-based foundation models that extract context from noisy observations, LPM learns perturbation-response rules disentangled from context-specific measurement variability
3. **Enhanced accuracy**: The decoder-only design with PRC conditioning consistently achieves state-of-the-art performance across experimental settings

## Main Results

**Perturbation effect prediction**: LPM consistently and significantly outperforms state-of-the-art baselines (CPA, GEARS, Catboost+STRING/Reactome, Geneformer, scGPT, GenePT) on:
- Multiple experimental contexts (cell lines, treatment protocols)
- Different perturbation types (CRISPR genetic and chemical)
- Varying preprocessing strategies

**Molecular mechanism identification**: LPM's perturbation embeddings capture meaningful drug-target interaction information. In a unified latent space, chemical perturbations can be associated with their genetic counterparts based on shared mechanisms of action.

**Gene interaction network inference**: LPM enables causal gene-to-gene interaction network inference by analyzing how perturbations in one gene influence predicted expression of others.

**Data scaling benefit**: LPM's advantage grows as more diverse perturbation data are included in training—significantly outperforming baselines especially when trained on pooled multi-experiment data.

**Therapeutic discovery case study**: LPM was used to identify potential therapeutics for autosomal dominant polycystic kidney disease (ADPKD) by predicting which compounds would produce expression profiles similar to disease reversal.

## Comparison to Foundation Models

LPM explicitly addresses two limitations of encoder-based foundation models (scGPT, Geneformer):
1. Low signal-to-noise in high-throughput screens impairs encoder representations
2. Encoder models are inherently transcriptomics-only

The decoder-only approach sidesteps these limitations but sacrifices the ability to predict for out-of-vocabulary (unseen) contexts.

## Citation

Miladinovic D, Hoppe T, Chevalley M, Georgiou A, Stuart L, Mehrjou A, Bantscheff M, Scholkopf B, Schwab P. "In silico biological discovery with large perturbation models." Nature Computational Science (2025). DOI: 10.1038/s43588-025-00870-1

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | LPM's PRC-disentangled decoder-only design enables prediction for perturbations not seen during training by conditioning on perturbation identity tokens. |
| Cross cell-line (gene intersection) | Yes | LPM integrates heterogeneous perturbation experiments across multiple cell lines and biological contexts within a single model, with context (C) as a disentangled conditioning variable. |
| Zero-shot unseen cell line (gene intersection) | No | LPM explicitly sacrifices out-of-vocabulary context prediction—the decoder-only approach cannot generalize to unseen contexts not represented during training. |
| Cross perturbation technology (gene intersection) | Yes | LPM integrates both CRISPR genetic and chemical perturbation data across diverse readout modalities, enabling cross-technology perturbation predictions. |
| Zero-shot gene misalignment | No | LPM operates on a fixed gene/readout vocabulary defined during training; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | LPM consistently and significantly outperforms CPA, GEARS, Catboost, Geneformer, scGPT, and GenePT across multiple perturbation types and experimental contexts. |

**Overall capability tier**: Foundation
