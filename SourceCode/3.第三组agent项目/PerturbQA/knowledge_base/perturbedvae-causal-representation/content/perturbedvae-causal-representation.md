# PerturbedVAE: Causal Representation Learning for Perturbation Prediction

## Overview

PerturbedVAE (Jiang et al., ICML 2026) addresses a fundamental challenge in single-cell perturbation modeling that the authors call the **Perturbation Suppression Hypothesis**: perturbation-invariant information (background cellular programs) dominates gene expression data, while perturbation-specific signals are intrinsically sparse. Most existing methods — from VAEs to foundation models — fail to effectively separate these two types of variation, leading to poor generalization on perturbation-specific tasks.

## The Perturbation Suppression Hypothesis

### Core Observation
In Perturb-seq data:
- **Background cellular programs** (cell cycle, housekeeping, metabolic state) account for the vast majority of gene expression variation
- **Perturbation-specific signals** occupy only a small fraction of the expression space (~2-5% of genes change per perturbation)

When a model is trained to reconstruct gene expression profiles, it naturally prioritizes modeling the dominant background variation. As a result:
1. Foundation models (scGPT, UCE, Geneformer): Representations encode background programs well but suppress perturbation-specific signals
2. Causal VAEs (CRADLE-VAE, CPA): Without explicit separation, invariant information leaks into perturbation representations

### Empirical Evidence
A linear probing experiment is conducted: perturbation labels are predicted from frozen representations of several foundation models (scFoundation, UCE, Geneformer) using linear classifiers. These achieve lower accuracy than a simple PCA baseline applied directly to gene expression — demonstrating that perturbation information is more accessible in raw expression space than in FM representations.

## PerturbedVAE Framework

### Latent Space Decomposition
PerturbedVAE decomposes the latent space into two components:

**z_i** (perturbation-invariant): Captures background cellular programs shared across conditions
- Distribution: i.i.d. Gaussian
- Constrained to be consistent across perturbed and unperturbed cells of the same type

**z_ν** (perturbation-responsive): Captures perturbation-induced effects
- Distribution: Structured, conditioned on perturbation label u
- Assumed to follow a directed acyclic graph (DAG) causal structure

### Variational Inference
The posterior factorizes as:
q(z_ν, z_i | x, u) = q(z_ν | x, u) × q(z_i | x)

This forces z_i to be inferred without access to perturbation identity, ensuring it captures only perturbation-invariant information.

### Contrastive Alignment
The key innovation is a **contrastive alignment objective** to enforce perturbation-invariant representations:

For each perturbed cell (x, u), a matched control cell x^(u₀) is sampled. The invariant representations are encouraged to agree:

L_contrast = ||z_i - z_i^(u₀)||²₂

This ensures z_i remains stable across perturbation conditions, freeing z_ν to capture the perturbation-specific residual.

### Total Objective
L = -L_ELBO + α × L_contrast

where α controls the strength of contrastive alignment.

## Identifiability Analysis

PerturbedVAE provides theoretical guarantees under four conditions:
1. **Invertibility**: The decoder g is smooth and invertible
2. **Environmental Sufficiency**: Sufficient diversity of perturbation conditions
3. **Optimal Alignment**: Contrastive alignment reaches global minimum
4. **Intervention Sufficiency**: DAG structure satisfies technical conditions

Under these conditions:
- z_ν is identified up to permutation and scaling
- z_i is identified up to a linear block transformation

This is stronger than most existing identifiability results for causal representation learning.

## Test-Time Prediction

At test time, for out-of-distribution prediction (new perturbation u'):
1. Encode a control cell: z_i ~ q_φ(z_i | x^(u₀))
2. Generate the perturbation-responsive component: z_ν ~ p_θ(z_ν | z_i, u')
3. Decode: x̂ = g(z_i, z_ν)

For double-gene OOD: the two-hot perturbation vector is fed into the same learned u-conditioned mechanism, without any retraining.

## Experimental Results

### Double-Gene Perturbation (Norman 2019)
Compared against foundation models (scFoundation, UCE, Geneformer, STATE):
- PerturbedVAE achieves best RMSE (0.4474 vs 0.4931 for best FM baseline)
- Best R² on double-gene perturbation (0.9865 vs 0.9800 for best FM)

### Comparison with Causal Methods
Outperforms SENA-discrepancy-VAE, sVAE+, SAMS-VAE, and Discrepancy-VAE (existing causal methods), validating the contrastive alignment component.

### Interpretability
Learned causal graph among z_ν components recovers known regulatory interactions:
- TGFBR2 → SNAI1 (EMT regulation)
- TP73 → CDKN1A (tumor suppressor pathway)
- JUN inhibition by DUSP9 in MAPK signaling

## Citations

Jiang W et al. (2026). What Makes a Representation Good for Single-Cell Perturbation Prediction? *Proceedings of ICML 2026*. arXiv:2605.19343.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | PerturbedVAE predicts double-gene OOD perturbations on Norman 2019 with best RMSE (0.4474) and R² (0.9865), outperforming all foundation model baselines. |
| Cross cell-line (gene intersection) | No | The paper focuses on the Norman 2019 dataset within K562 cells; no explicit cross-cell-line transfer evaluation is reported. |
| Zero-shot unseen cell line (gene intersection) | No | PerturbedVAE requires control cells from the same experiment for contrastive alignment training; zero-shot unseen cell line prediction is not evaluated. |
| Cross perturbation technology (gene intersection) | No | The model is evaluated only on CRISPR genetic perturbations; no cross-technology transfer evaluation is reported. |
| Zero-shot gene misalignment | No | The decoder operates on a fixed gene vocabulary from the training dataset; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | PerturbedVAE achieves the best RMSE and R² on double-gene OOD perturbations, substantially outperforming foundation models (scFoundation, UCE, Geneformer) and causal baselines that exhibit perturbation suppression. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
