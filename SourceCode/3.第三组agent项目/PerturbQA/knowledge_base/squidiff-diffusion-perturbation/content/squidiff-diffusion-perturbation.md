# Squidiff: Diffusion Model for Predicting Cellular Development and Perturbation Responses

## Overview

Squidiff (Single-cell Quantitative Inference of Stimulus responses by a Diffusion model) is a conditional diffusion model framework that predicts transcriptomic changes across diverse cell types in response to environmental changes—including cell differentiation, gene perturbations, and drug treatments. He, Zhu, Tavakol et al. (Nature Methods 2025) from Columbia University and Stanford present Squidiff as a versatile framework that captures transient cell states during development and provides high-resolution transcriptomic landscapes over time and across conditions.

## Problem Being Solved

Mapping transcriptomic changes in diverse cell types requires expensive, large-scale single-cell sequencing screens. Current prediction models face limitations:
- VAE-based models (scGen, scVIDR) fail to predict high-resolution dynamic transcriptional responses
- Optimal transport approaches (CellOT) don't interpolate cell states
- Most models are task-specific rather than applicable to differentiation, genetic perturbation, AND drug response
- Models that require both unperturbed and perturbed data as inputs limit generalization
- None capture transient intermediate cell states during organ development

## Architecture: Conditional DDIM

Squidiff is a **conditional denoising diffusion implicit model (DDIM)** with two components:

**Semantic encoder**:
- Maps single-cell transcriptomic data into a unified semantic latent space Z_sem
- Captures biologically meaningful variation in gene expression associated with specific cell states
- Separates biological signal from stochastic transcriptional noise

**Diffusion model**:
- Generates target cell transcriptomes by denoising a Gaussian noise x_T conditioned on Z_sem
- Standard denoising process: learns to reverse noise addition
- DDIM-style inference enables fewer sampling steps than standard DDPM, improving efficiency

**Two latent manipulation strategies**:

1. **Addition (perturbation direction Δz_sem)**:
   - Learn a perturbation vector in semantic space from training examples
   - Add this vector to the reference cell's Z_sem
   - Decode to generate the perturbed transcriptome
   - Used for drug perturbation and gene knockout prediction

2. **Interpolation**:
   - Linear interpolation between start and end state Z_sem vectors
   - Decode each interpolated point to recover intermediate transcriptomes
   - Used for developmental trajectory reconstruction and transient state modeling

## Key Applications

**Cell differentiation prediction**:
- Predicts transcriptomic profiles during iPSC differentiation into three germ layers
- Captures transient intermediate states (mesoderm progenitors, etc.) that other methods miss
- Guided by stimulus vectors encoding specific growth factor combinations

**Gene perturbation prediction**:
- Handles non-additive genetic perturbation effects (interactions between multiple gene knockouts)
- Predicts cell type-specific responses (glioblastoma vs. melanoma cells respond differently to the same perturbation)

**Drug response in complex cell systems**:
- Predicts responses to new drug combinations by combining perturbation vectors
- Tested on glioblastoma and melanoma with clinically relevant drug combinations

**Blood vessel organoid (BVO) application**:
- Applied to model neovascularization and vasculopathy in blood vessel organoids exposed to high linear energy transfer (LET) neutron radiation
- Predicts transcriptomes of endothelial cells, fibroblasts, and mural cells throughout differentiation
- Identifies mural-to-endothelial developmental pathway consistent with recent time-series studies
- Predicts radiation damage mechanisms and suggests granulocyte colony-stimulating factor (G-CSF) as radioprotective—predicting protective effect on vascular specification

## Main Results

Evaluated across three biomedical scenarios (differentiation, genetic perturbations, drug response):

- **Differentiation**: Correctly predicts germ layer-specific transcriptomes; uniquely captures transient progenitor states
- **Genetic perturbations**: Achieves state-of-the-art in predicting non-additive epistatic effects; better cell-type specificity than GEARS and scGen
- **Drug response**: Competitive with best single-task models while handling multiple drug combinations

**BVO study**: Experimental single-cell sequencing validation confirms Squidiff's predictions of radiation-induced transcriptomic changes and G-CSF protective effects—demonstrating real-world translational value.

## Comparison to Related Models

| Model | Differentiation | Gene perturbation | Drug response | Transient states |
|-------|----------------|-------------------|---------------|-----------------|
| scGen | No | Yes | Partial | No |
| GEARS | No | Yes | No | No |
| CellOT | Limited | No | No | No |
| scVAEDer | Yes | Yes | No | Partial |
| **Squidiff** | **Yes** | **Yes** | **Yes** | **Yes** |

## Limitations

Squidiff requires biological knowledge of the starting state and stimulus vectors to guide interpolation/addition—it cannot generate arbitrary novel cellular states without specified conditions. Training requires paired or time-series data for differentiation trajectories. The model may not capture highly heterogeneous single-cell responses where individual cells diverge dramatically.

## Citation

He S, Zhu Y, Tavakol DN, Ye H, Lao YH, Zhu Z, Xu C, Chauhan S, Garty G, Tomer R, Vunjak-Novakovic G, Zou J, Azizi E, Leong KW. "Squidiff: predicting cellular development and responses to perturbations using a diffusion model." Nature Methods (2025). DOI: 10.1038/s41592-025-02877-y

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Partial | Squidiff predicts responses to unseen drug combinations by composing perturbation vectors, but requires training examples of constituent perturbations to define the direction in semantic space. |
| Cross cell-line (gene intersection) | Yes | The model demonstrates cell-type-specific perturbation prediction across glioblastoma and melanoma cell types using shared gene representations. |
| Zero-shot unseen cell line (gene intersection) | No | Squidiff requires training data from the target cell type to learn perturbation direction vectors; it is not demonstrated in a zero-shot unseen cell line setting. |
| Cross perturbation technology (gene intersection) | Partial | Squidiff handles genetic knockouts and drug treatments within one model, but cross-technology generalization (e.g., train on CRISPRi, predict CRISPR-KO) is not explicitly evaluated. |
| Zero-shot gene misalignment | No | The model operates on a fixed semantic latent space trained on the same gene vocabulary; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | Squidiff achieves state-of-the-art performance on non-additive epistatic effect prediction and outperforms GEARS and scGen on cell-type-specific perturbation tasks. |

**Overall capability tier**: Specialist
