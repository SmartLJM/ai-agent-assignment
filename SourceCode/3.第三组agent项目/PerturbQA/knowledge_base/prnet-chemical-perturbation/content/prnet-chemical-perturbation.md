# PRnet: Deep Generative Model for Predicting Transcriptional Responses to Novel Chemical Perturbations

## Overview

PRnet (Perturbation Response network) is a flexible and scalable perturbation-conditioned deep generative model that predicts transcriptional responses to chemical perturbations that were never experimentally tested—at both bulk and single-cell resolution. Developed by Qi, Zhao, Tian et al. (Nature Communications 2024), PRnet addresses the fundamental bottleneck in drug discovery: the infeasibility of experimentally screening all possible disease-compound combinations.

## Problem Being Solved

Understanding transcriptional responses to chemical perturbations is central to drug discovery, yet exhaustive experimental screening is impossible given the vast chemical space. Existing methods have major limitations:
- CPA, scGen, biolord predict cell-type transfer but not novel compound effects
- chemCPA incorporates compound structure but lacks broad generalization
- GEARS uses gene knowledge graphs but targets genetic perturbations
- Linear regression methods fail to capture nonlinear chemical effects across diverse cell types

PRnet uniquely focuses on predicting responses to **novel compounds** (never experimentally tested), not just unseen cell types.

## Architecture: Three-Component Design

PRnet is a VAE-based encoder-decoder model with three components:

**1. Perturb-adapter**
- Takes compound structure encoded as SMILES strings as input
- Uses RDKit to generate Functional-Class Fingerprints (FCFPs) capturing molecular topology
- Adapts novel compounds into the perturbation space without requiring prior biological annotation
- Enables generalization to truly unseen compounds

**2. Perturb-encoder**
- Encodes the unperturbed transcriptional profile (bulk or single-cell) as a latent representation
- Incorporates perturbation information from the Perturb-adapter as a conditioning signal
- Learns a latent space that captures both cellular state and compound effects

**3. Perturb-decoder**
- Decodes the combined latent representation back to a perturbed transcriptional profile
- Models the distribution of gene expression responses, enabling uncertainty quantification
- Trained with near 100 million bulk HTS observations (175,549 compounds) and tens of millions of single-cell observations (188 compounds)

The learnable latent space facilitates gene-level response interpretation by enabling attribution of expression changes to specific pathway programs.

## Main Results

**Benchmark performance**: PRnet outperforms alternative approaches (CPA, chemCPA, scGen, biolord, scVIDR) in predicting transcriptional responses to:
- Novel compounds (never seen during training)
- Novel pathways (compound classes not represented in training)
- Novel cell lines (cross-cell-line generalization)

**Drug discovery validation**:
1. **Small cell lung cancer (SCLC)**: PRnet identified novel bioactive compounds against SCLC. Experimental validation confirmed activity within the predicted concentration ranges.
2. **Colorectal cancer (CRC)**: Novel natural compounds predicted by PRnet showed validated anti-CRC activity.

**Large-scale atlas**: PRnet generated a virtual perturbation atlas covering 88 cell lines, 52 tissues, and multiple compound libraries (935 FDA-approved drugs, 4,158 active compounds, 30,456 natural compounds, 29,670 drug-like compounds).

**Disease candidate recommendation**: Using gene signature matching (GSEA-based scoring), PRnet recommended drug candidates for 233 different diseases from 577 studies. Three metabolic disorders (NASH, PCOS, IBD) had predictions supported by existing clinical/animal literature.

## Technical Details

- Training data: ~100 million bulk HTS profiles (LINCS L1000), tens of millions of single-cell profiles (sciPlex, etc.)
- Compound encoding: SMILES → RDKit FCFPs (functional-class fingerprints capturing pharmacophore topology)
- Loss function: ELBO (evidence lower bound) from VAE + reconstruction loss
- Supports both bulk and single-cell prediction modes

## Limitations

PRnet predicts aggregate or population-level responses and may not capture single-cell heterogeneity as faithfully as specialized single-cell generative models. Novel compound predictions rely on the quality of SMILES encoding and fingerprint representation—highly structurally novel compounds may extrapolate poorly.

## Citation

Qi X, Zhao L, Tian C, Li Y, Chen ZL, Huo P, Chen R, Liu X, Wan B, Yang S, Zhao Y. "Predicting transcriptional responses to novel chemical perturbations using deep generative model for drug discovery." Nature Communications 15, 9256 (2024). DOI: 10.1038/s41467-024-53457-1

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | PRnet is uniquely focused on predicting responses to novel compounds never experimentally tested, encoding compounds via SMILES fingerprints without requiring prior biological annotation. |
| Cross cell-line (gene intersection) | Yes | PRnet demonstrates cross-cell-line generalization, outperforming alternatives on novel cell lines and generating a virtual perturbation atlas across 88 cell lines. |
| Zero-shot unseen cell line (gene intersection) | Partial | PRnet generalizes to novel cell lines but the perturb-encoder requires an unperturbed transcriptional profile of the target cell, so fully zero-shot (no data at all) is not demonstrated. |
| Cross perturbation technology (gene intersection) | No | PRnet focuses exclusively on chemical perturbations; genetic perturbation generalization is not a design goal. |
| Zero-shot gene misalignment | No | PRnet requires a shared gene vocabulary (e.g., L1000 landmark genes) between training and inference; completely different gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | PRnet outperforms CPA, chemCPA, scGen, biolord, and scVIDR on predicting responses to novel compounds, novel pathways, and novel cell lines, with experimental drug discovery validations. |

**Overall capability tier**: Specialist
