# GGE: Generated Genetic Expression Evaluator — Standardized Evaluation Framework

## Overview

GGE (Rubbi et al., ICLR 2026 Gen² Workshop) is an open-source Python framework for standardized evaluation of generative models for single-cell gene expression data. The paper identifies a critical problem: the lack of standardized evaluation practices in the single-cell generative modeling literature makes cross-paper comparison virtually impossible, and documents that the same method can appear to produce 5-10× different metric values depending solely on implementation choices.

## The Standardization Crisis

### Evidence of Inconsistency
A survey of 12 influential single-cell generative modeling papers finds:
- **No two papers** use identical evaluation protocols
- **Metric names are shared but implementations differ**: "Wasserstein distance" can mean per-gene 1D average W₁, multivariate Sinkhorn approximation, or exact W₂ — differing by 5-10×
- **Computation space varies**: Raw gene space, PCA-30, PCA-50, PCA-100, HVG subset
- **DEG thresholds unreported**: Critical hyperparameters (log-fold change cutoff, significance threshold) often unspecified
- **Biological context missing**: Some methods evaluate on all genes, others only on top-20 or top-100 DEGs

### Quantitative Impact
Table 2 in the paper shows the same data computed under different configurations:
- W₂ in raw (G=2000): 104.3 ± 0.3
- W₂ in PCA-100: 53.8 ± 0.1
- W₂ in PCA-50: 33.6 ± 0.1
- W₂ in PCA-25: 17.2 ± 0.1

A 6× range in reported W₂ values from identical predictions — purely due to implementation choices.

## GGE Framework Design

### Core Design Principles

**1. Explicit Configuration**
Every implementation choice is an explicit parameter:
- `space`: "raw", "pca", or "deg"
- `n_components`: Dimensionality for PCA space
- `deg_lfc`, `deg_pval`: Log-fold change and p-value thresholds for DEG selection
- `n_top_degs`: Top-N DEG selection (mimicking scGen top-100 or GEARS top-20)
- `blur`: Sinkhorn regularization strength for OT metrics

**2. Universal Space Support**
All metrics — distributional (Wasserstein, MMD, Energy), correlation, and reconstruction — compute in all three spaces:
- **Raw gene space**: Gene-level interpretability preserved
- **PCA space**: Statistical tractability, denoising
- **DEG space**: Biologically targeted evaluation

**3. Condition-Aware Design**
Metrics are computed per condition (cell type × perturbation), then aggregated. This enables stratified analysis and surfaces heterogeneity that aggregate metrics would obscure.

## Supported Metrics

### Distributional Metrics
- **Wasserstein distance (W₁, W₂)**: OT-based geometric discrepancy between distributions
- **MMD (Maximum Mean Discrepancy)**: Kernel-based two-sample statistic
- **Energy Distance**: Non-parametric distance without parametric density assumptions

### Correlation and Reconstruction Metrics
- **Pearson correlation**: On mean expression profiles
- **R²**: Reconstruction accuracy
- **MSE**: Mean squared error on expression values

### DEG-Specific Metrics
- **Perturbation-effect correlation (ρ_effect)**: Correlation on perturbation deltas (perturbed minus control), not raw expression
- **DES@K**: Differential Expression Score at K

## Perturbation-Effect Correlation

A subtle but critical innovation: standard correlation on raw expression means is dominated by highly-expressed genes shared across conditions. GGE computes:

ρ_effect = corr(μ_real - μ_ctrl, μ_gen - μ_ctrl)

This measures whether the model captures the *direction and magnitude of perturbation effects* — the biologically relevant signal — rather than merely reconstructing background expression.

## Comparison with cell-eval

GGE is compared with cell-eval (the evaluation framework from Arc Institute's STATE model):
- cell-eval: Comprehensive pipeline optimized for STATE ecosystem, less flexible
- GGE: Lightweight, model-agnostic, emphasizes explicit configuration and reproducibility

## Recommendations for the Field

Based on the theoretical analysis and experimental demonstration, GGE recommends:
1. **PCA-50 as primary space** for distributional metrics (statistical robustness + computational tractability)
2. **DEG-restricted space** for biologically targeted evaluation
3. **Raw gene space** only when gene-level interpretability is required
4. **Multi-space evaluation**: Report all three spaces simultaneously for completeness
5. **Always specify**: n_components, DEG thresholds, Sinkhorn regularization

## DEG Threshold Effects

Table 3 shows sensitivity of correlation metrics to DEG selection strategy:
- Top-20 like GEARS: Average DEGs=20, Pearson=0.614 ± 0.066
- Top-100 like scGen: Average DEGs=100, Pearson=0.594 ± 0.024
- Strict threshold (lfc>1, p<0.01): Average DEGs=15.3, Pearson=0.506 ± 0.217
- Relaxed threshold (lfc>0.25, p<0.1): Average DEGs=71.7, Pearson=0.622 ± 0.079

Top-N selection provides more consistent gene counts across conditions; threshold-based selection adapts to perturbation strength.

## Code Availability

GGE is available as an open-source Python package installable via pip (`gge-eval`) with full documentation and source code.

## Citations

Rubbi A et al. (2026). A Standardized Framework For Evaluating Gene Expression Generative Models. *ICLR 2026 Gen² Workshop*. arXiv:2603.11244.
