# CRADLE-VAE: Counterfactual Artifact Disentanglement for Perturbation Modeling

## Overview

CRADLE-VAE (Baek et al., 2024) is a variational autoencoder designed to improve single-cell gene perturbation prediction by explicitly disentangling three types of latent variation: the **basal cell state**, the **perturbation effect**, and **experimental artifacts**. The key insight is that standard VAEs conflate technical noise and batch effects with true biological perturbation signals, leading to poor generalization to unseen perturbations.

## Problem: Artifact Contamination in Perturbation Modeling

When modeling Perturb-seq data:
- **Technical artifacts**: Library size variation, batch effects, ambient RNA contamination
- **Biological invariants**: Background cell state not affected by perturbation
- **True perturbation signal**: The actual regulatory response of interest

Most methods (GEARS, CPA, scGPT) do not explicitly model artifacts, causing:
1. Perturbation embeddings to absorb artifact variation
2. Poor calibration of perturbation-specific predictions
3. Reduced generalization to new experimental conditions

## Architecture: Three-Subspace Latent Model

CRADLE-VAE decomposes the latent space into three components:

### 1. Basal Subspace (z_b)
Captures the cell-type-specific baseline expression independent of perturbation. Shared across perturbed and control cells of the same type.

### 2. Perturbation Subspace (z_p)
Captures only the perturbation-induced changes. Encoded from the difference signal between perturbed and control cells.

### 3. Artifact Subspace (z_a)
Captures technical variation: batch effects, library size, dropout patterns. This is treated as nuisance variation to be removed from the other subspaces.

## Training Objectives

### Primary ELBO
Standard VAE evidence lower bound with reconstruction loss (negative binomial) and KL divergence regularization on all three subspaces.

### KL Auxiliary Loss
An additional KL loss encourages the artifact subspace (z_a) to be independent of perturbation identity:
KL[q(z_a | x, p) || q(z_a | x, control)] ≈ 0

This forces the artifact encoder to produce similar distributions regardless of whether the cell is perturbed, preventing artifact information from leaking into z_a based on perturbation identity.

### Counterfactual Consistency
Predictions for the same cell under different perturbations should differ only in the perturbation subspace, not the artifact subspace. This counterfactual constraint encourages artifact independence.

## Experimental Results

Evaluated on Norman et al. (2019) and Replogle et al. (2022):
- **Better DEG recovery**: CRADLE-VAE recovers differentially expressed genes more accurately than CPA and standard VAE baselines
- **Improved OOD**: Better generalization to held-out perturbation conditions
- **Reduced batch confounding**: Artifact disentanglement reduces correlation between z_p and known technical covariates

## Relationship to GPO-VAE

CRADLE-VAE serves as the base model for GPO-VAE (Baek et al., 2025), which adds gene regulatory network (GRN) alignment on top of the counterfactual artifact framework. GPO-VAE's main innovation is using GRN structure to constrain which parameters are updated during perturbation conditioning, providing biological interpretability and improved DEG identification.

## Key Limitations

1. **Artifact definition**: The boundary between biological and technical variation is fuzzy; artifacts in one context (e.g., stress response) may be signals in another.
2. **Requires control cells**: The artifact subspace training relies on paired perturbed and control cells from the same experiment.
3. **Computational cost**: Three separate encoders increase model size and training time.

## Citations

Baek M, Oh S, Kim WJ (2024). CRADLE-VAE: Enhancing Single-Cell Gene Perturbation Modeling with Counterfactual Reasoning-based Artifact Disentanglement. *arXiv:2409.05484*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | CRADLE-VAE predicts responses to held-out perturbation conditions on Norman et al. and Replogle et al. datasets, outperforming CPA and standard VAE baselines on OOD perturbations. |
| Cross cell-line (gene intersection) | No | The paper evaluates on Norman and Replogle datasets within single cell-line contexts; no explicit cross-cell-line transfer evaluation is reported. |
| Zero-shot unseen cell line (gene intersection) | No | CRADLE-VAE requires paired perturbed and control cells from the same experiment for artifact subspace training; zero-shot transfer to unseen cell lines is not evaluated. |
| Cross perturbation technology (gene intersection) | No | CRADLE-VAE focuses on CRISPR genetic perturbations; no cross-technology transfer evaluation is reported. |
| Zero-shot gene misalignment | No | The model operates on a fixed gene vocabulary consistent across training and evaluation; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | CRADLE-VAE recovers differentially expressed genes more accurately than CPA and standard VAE baselines, demonstrating perturbation-specific signal capture beyond mean prediction. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
