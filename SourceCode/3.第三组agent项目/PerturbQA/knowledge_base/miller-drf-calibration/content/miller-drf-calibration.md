# Dynamic Range Fraction: Calibrated Evaluation for Perturbation Models

## Overview

Miller et al. (bioRxiv 2025) directly challenge the conclusion of Ahlmann-Eltze et al. (2025) that deep learning models do not outperform simple linear baselines. Using carefully calibrated evaluation metrics — specifically the Dynamic Range Fraction (DRF) — Miller et al. show that DL models DO outperform uninformative baselines on perturbations with sufficient effect size, when evaluated with metrics that account for the fundamental difficulty of low-effect perturbations.

## The Calibration Problem

### Effect Size Confounds Benchmarks
Perturbation experiments contain a mix of:
- **Large-effect knockouts**: Strong regulators where knockdown causes hundreds of genes to change significantly
- **Small-effect knockouts**: Genes with minimal regulatory role where expression changes are negligible

Standard benchmarks mix these categories, and simple baselines (e.g., predicting no change) perform well on small-effect perturbations. This artificially inflates the apparent performance of simple baselines relative to DL models that attempt to predict actual effects.

## Dynamic Range Fraction (DRF)

### Definition
DRF measures the fraction of the total dynamic range of expression change that is captured by the model:

DRF = (max_perturbation predicted effect) / (max_perturbation observed effect)

Or more precisely, for each perturbation g:
DRF_g = |ŷ_g - ŷ_control|_95th / |y_g - y_control|_95th

This normalizes predicted effect size against observed effect size, creating a scale-invariant metric.

### Why DRF Solves the Calibration Problem
- **Insensitive to near-zero perturbations**: Perturbations with negligible effects contribute minimal DRF values, preventing them from dominating average metrics.
- **Rewards effect recovery**: Models that correctly identify the direction and magnitude of large effects score high DRF.
- **Penalizes mean-collapse**: Models that predict near-zero change for all genes score low DRF on large-effect perturbations.

## Interpolated Duplicate Baseline

Miller et al. introduce a more appropriate baseline than simple additive linear models:

**Interpolated Duplicate**: For each perturbation g, the baseline prediction is constructed as:
ŷ_baseline = w × y_train_neighbor + (1-w) × ȳ_control

where y_train_neighbor is the expression profile of the nearest neighbor perturbation in training data (by embedding similarity), and w is a learned interpolation weight.

This baseline is stronger than a pure linear model because it exploits actual perturbation data from similar genes, providing a fair comparison against DL models that implicitly do the same thing.

## Benchmark Results

Across 14 datasets and 13 metrics:
- **DRF > 0.2 perturbations**: DL models (GEARS, CellFlow) outperform the interpolated duplicate baseline by 15-25%
- **DRF < 0.05 perturbations**: All models (including DL) perform similarly, confirming that small-effect knockouts are unpredictable
- **Large-effect perturbations**: CellFlow and scBIG show the largest gains over baselines

## Main Conclusions

1. **DL models do outperform** when evaluation is restricted to perturbations with sufficient effect size (DRF > 0.2)
2. **Effect size stratification is critical**: Reporting average performance across all perturbations misleads because low-effect knockouts dominate
3. **The field needs calibrated metrics**: DRF provides a principled way to separate informative from uninformative predictions
4. **Baselines must be appropriate**: The additive linear baseline used by Ahlmann-Eltze et al. is not a fair comparison for DL models

## Relationship to Other Evaluation Papers

| Paper | Main Claim | Metric Used |
|-------|-----------|-------------|
| Ahlmann-Eltze (2025) | DL doesn't outperform | R² on all genes |
| Miller et al. (2025) | DL does outperform (calibrated) | DRF + interpolated baseline |
| Systema | Systematic variation biases results | Perturbation-specific R² |
| AUPRC | Better metric for DEG identification | Precision-recall curve |

## Practical Implications

For researchers:
1. Report DRF stratified results separately for small/medium/large effect perturbations
2. Use interpolated duplicate baseline (not pure linear) for fair comparison
3. Prioritize high-DRF perturbations for model development and validation

## Citations

Miller M et al. (2025). Deep Learning-Based Genetic Perturbation Models Do Outperform Uninformative Baselines on Well-Calibrated Metrics. *bioRxiv:2025.10.20.683304*.
