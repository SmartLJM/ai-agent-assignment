# GPerturb: Gaussian Process Modeling of Single-Cell Perturbation Data

## Overview

GPerturb is a Gaussian process-based sparse perturbation regression model for estimating gene-level perturbation effects from single-cell CRISPR screening data. Xing and Yau (Nature Communications 2025) present GPerturb as an alternative to black-box deep learning approaches, offering a principled Bayesian framework with explicit uncertainty quantification, interpretable sparse perturbation effects, and competitive predictive performance. The model handles both discrete (binary on/off) and continuous perturbation responses without requiring latent embeddings or external biological databases.

## Problem Being Solved

Single-cell CRISPR screening generates high-dimensional, sparse measurements where the goal is to identify which genes are affected by each perturbation and by how much. Key challenges:
1. **High dimensionality**: Thousands of genes measured per cell, most unaffected by any given perturbation
2. **Practical issues**: Different methods make incompatible assumptions about input data types (CPA: categorical cell info + continuous expression; SAMS-VAE: count-based only; GEARS: discrete perturbations only with knowledge graph)
3. **Interpretability**: Deep learning models lack transparency in identifying which perturbations affect which genes
4. **Uncertainty**: Point estimates without confidence intervals are inadequate for biological decision-making

## Model Formulation

**GPerturb** is a generative Bayesian model:

For each cell with gene expression X:
- **Basal expression component**: Determined by cell-specific parameters (cell type, batch)
- **Perturbation effect component**: A feature-specific additive effect from the applied perturbation, controlled by a **binary on/off switch** per feature
- **Distribution model**: 
  - GPerturb-Gaussian: Normal distribution for continuous transformed expression (e.g., log-normalized)
  - GPerturb-ZIP: Zero-inflated Poisson for raw count data

**Gaussian processes** model the expression functions:
- The basal expression is a nonlinear function of cell-type parameters, modeled by a GP
- The perturbation effect for each gene is a nonlinear function of the perturbation type, modeled by a separate GP

**Sparsity**: Binary spike-and-slab priors (on/off switches) enforce that most genes are unaffected by any given perturbation. This mirrors biological reality and improves generalization by regularizing the model.

**Inference**: Variational Bayes inference approximates the posterior distributions over perturbation effects and which genes are affected.

## Key Advantages Over Deep Learning Methods

| Feature | CPA | SAMS-VAE | GEARS | GPerturb |
|---------|-----|---------|-------|---------|
| Continuous expressions | Yes | No | Yes | Yes (Gaussian) |
| Count data | No | Yes | No | Yes (ZIP) |
| Cell type info | Yes | No | Yes | Yes |
| Continuous dosage | Yes | No | No | Yes |
| External gene graphs | No | No | Yes | No |
| Uncertainty estimates | No | Partial | No | Yes |
| Interpretable sparsity | No | Yes | No | Yes |

## Main Results

**Single-gene perturbation analysis** on genome-wide CRISPRi Perturb-seq dataset:
- GPerturb-Gaussian achieves competitive Pearson correlation with CPA and GEARS despite using no external knowledge graphs
- GPerturb-ZIP achieves competitive performance with SAMS-VAE on count data

The additive sparse structure despite not using latent embeddings or external information reveals that **much of the perturbation prediction task can be solved by simple, interpretable models**.

**Gene-perturbation interaction discovery**: The binary on/off switches identify which genes are specifically affected by each perturbation, producing interpretable gene×perturbation interaction matrices consistent with known biology.

**Combinatorial perturbation analysis**: GPerturb handles combination perturbation effects through additive GP components, enabling principled uncertainty estimation for combinatorial effects.

**Uncertainty quantification**: Unlike deep learning models that produce point predictions, GPerturb provides calibrated posterior distributions over perturbation effects—crucial for prioritizing follow-up experiments.

## Limitations

GPerturb's GP kernel assumes relatively smooth perturbation response functions, which may not capture highly nonlinear effects. Computational cost scales quadratically with the number of unique perturbations, limiting applicability to very large screens (thousands of perturbations). The model does not leverage biological prior knowledge (gene networks) that GEARS uses effectively.

## Citation

Xing H, Yau C. "GPerturb: Gaussian process modelling of single-cell perturbation data." Nature Communications 16, 5423 (2025). DOI: 10.1038/s41467-025-61165-7

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | GPerturb predicts gene-level perturbation effects for held-out perturbations in genome-wide CRISPRi Perturb-seq data, achieving competitive Pearson correlation with CPA and GEARS without using external knowledge graphs. |
| Cross cell-line (gene intersection) | No | GPerturb is evaluated within single cell-line contexts; no explicit cross-cell-line transfer evaluation is reported. |
| Zero-shot unseen cell line (gene intersection) | No | The Gaussian process models are fit to data from a single experimental context; zero-shot transfer to completely unseen cell lines is not evaluated. |
| Cross perturbation technology (gene intersection) | No | GPerturb supports both discrete and continuous perturbation inputs but is validated only on CRISPR screens; no cross-technology transfer evaluation is reported. |
| Zero-shot gene misalignment | No | GPerturb models perturbation effects in the fixed gene space of the training dataset; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | GPerturb's binary on/off gene-perturbation interaction matrices recover known biology, outperforming simple linear models, and the paper notes that much of the perturbation prediction task can be solved by interpretable sparse models. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
