# Deep Learning vs Linear Baselines for Perturbation Prediction

## Overview

Ahlmann-Eltze & Huber (Nature Methods 2025) conducted a systematic benchmark study evaluating whether state-of-the-art deep learning models for gene perturbation prediction genuinely outperform simple linear baselines. Their surprising conclusion: on standard benchmarks (Norman and Replogle datasets), models including scGPT, GEARS, CPA, scBERT, Geneformer, and UCE do **not** significantly outperform a simple additive linear model when evaluated on held-out perturbations.

## Benchmark Setup

### Models Evaluated
- **Deep learning**: scGPT, GEARS, CPA, scBERT, Geneformer, UCE
- **Linear baseline**: Simple additive linear model predicting expression as sum of single-gene effects

### Datasets
- **Norman et al. (2019)**: K562 cells, ~287 combinatorial perturbation conditions
- **Replogle et al. (2022)**: Genome-scale Perturb-seq, 1,832 perturbations in K562 and RPE1

### Evaluation Protocol
- Held-out perturbations (genes never seen during training)
- R² metric comparing predicted vs. observed mean expression profiles
- Comparison across all genes and top differentially expressed genes

## Key Findings

### 1. Linear Model Competitive Performance
The simple additive linear model, which predicts:
y_combo = y_gene1 + y_gene2 - y_control

achieves performance comparable to or better than deep learning approaches on combinatorial perturbation prediction tasks on the Norman dataset.

### 2. Deep Learning Does Not Extrapolate
Deep learning models trained on single-gene perturbations do not reliably generalize to:
- **New cell lines** not seen during training
- **Combinatorial perturbations** for gene pairs not observed together
- **Very different perturbation magnitudes** (e.g., large-effect knockouts)

### 3. R² as Metric Issues
The R² metric computed on all genes is dominated by non-responding genes (the vast majority), inflating all model scores. Even a model predicting zero change achieves R² ~ 0.5 on many perturbations.

## Why Deep Learning Fails to Outperform

1. **Data scarcity**: Training data typically contains hundreds of single-gene perturbations — insufficient for neural networks to learn complex regulatory patterns.
2. **Sparse effects**: Only ~2-5% of genes change significantly for any perturbation, making it easy to achieve high R² by predicting near-zero changes everywhere.
3. **Mean collapse**: Models converge to predicting the global average expression, which achieves high overall correlation but misses true perturbation-specific signals.
4. **Benchmark contamination**: Some datasets used for evaluation overlap with pre-training data for foundation models (scGPT, Geneformer), inflating their apparent performance.

## Implications for the Field

This work raises important questions about:
- **Metric choice**: R² on all genes is not informative; DEG-specific metrics (AUPRC, top-k precision) are more appropriate.
- **Evaluation rigor**: Strict OOD evaluation with genes completely held out is necessary.
- **Model claims**: Many papers in this area may overstate performance due to improper baselines.

## Counter-Evidence

Miller et al. (2025) showed that deep learning models DO outperform when:
1. Using calibrated metrics like Dynamic Range Fraction (DRF)
2. Excluding perturbations with negligible effect (< DRF threshold)
3. Using an interpolated duplicate baseline instead of simple additive linear

This suggests the debate is partly about metric choices rather than model capability.

## Relationship to Other Papers

- **Systema** (Viñas Torné et al.): Addresses systematic variation bias that confounds evaluation
- **AUPRC** (Zhu et al.): Proposes area under precision-recall curve as better metric
- **Miller et al.**: Shows DL does outperform with calibrated metrics
- **PerturbedVAE** (Jiang et al.): Explains mechanistically why FMs fail via perturbation suppression hypothesis

## Citations

Ahlmann-Eltze C, Huber W (2025). Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. *Nature Methods*. doi:10.1038/s41592-025-02772-6.
