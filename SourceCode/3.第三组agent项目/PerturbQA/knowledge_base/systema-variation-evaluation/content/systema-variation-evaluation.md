# Systema: Evaluation Framework Beyond Systematic Variation

## Overview

Systema (Viñas Torné et al., Nature Biotechnology 2025) is an evaluation framework addressing a critical bias in how gene perturbation prediction models are assessed. The core problem is that standard benchmarks conflate two types of variation: **systematic variation** (technical and biological confounders shared across conditions) and **perturbation-specific variation** (the actual causal effect of each genetic perturbation). Models that simply learn to predict systematic variation — without actually learning perturbation-specific effects — can achieve deceptively high scores on standard metrics.

## The Systematic Variation Problem

In Perturb-seq experiments, observed gene expression differences between perturbed and control cells arise from:

1. **True perturbation effects**: The regulatory cascade triggered by knocking out gene g
2. **Systematic variation**: 
   - Batch effects (plate, lane, day-of-experiment)
   - Cell cycle state differences between perturbed and control populations
   - Library size variation
   - Ambient RNA contamination varying by condition

A model that learns only systematic variation can achieve:
- High R² on standard benchmarks
- But zero ability to discriminate between specific perturbations
- Incorrect causal inference about perturbation mechanisms

## Systema's Solution: Perturbed Centroid Reference

Systema introduces a new reference point for evaluation: the **perturbed centroid** — the mean expression across all perturbed cells (regardless of which gene was knocked out). By computing metrics relative to this centroid instead of the control centroid:

Δ_systematic = E[x_perturbed] - E[x_control]  (standard approach)
Δ_specific = x_perturbed_g - E[x_all_perturbed]   (Systema's approach)

The second formulation removes the shared systematic shift, focusing only on what makes perturbation g different from other perturbations.

## Framework Components

### Dataset Coverage
Systema evaluates across:
- **10 datasets**: Multiple Perturb-seq experiments from different labs and conditions
- **3 technologies**: Different scRNA-seq platforms with varying dropout rates and depth

### Metrics
- **Systematic variation score**: How much each model captures the shared perturbation-independent shift
- **Perturbation-specific score**: How much each model distinguishes individual perturbation effects
- **Calibrated R²**: R² computed on the Systema-corrected expression differences

### Reference Cell Construction
For each perturbation g, the reference is constructed from cells perturbed with other genes matched for:
- Similar cell cycle state
- Similar library size
- Same batch/plate conditions

This matching removes confounders before computing perturbation-specific scores.

## Benchmark Findings

Across 10 datasets and all tested models (GEARS, CPA, scGPT, etc.):
1. **All models capture systematic variation**: Models easily learn the shared shift but this doesn't predict perturbation-specific effects.
2. **Performance collapses after Systema correction**: Many models achieve near-zero performance on perturbation-specific scores, revealing that their seemingly high R² was driven by systematic variation.
3. **GEARS is relatively robust**: Among tested models, GEARS's graph-based inductive bias helps it capture some perturbation-specific signal.
4. **Simple baselines are competitive**: After removing systematic variation, simple per-gene effect models are again competitive with deep learning.

## Implications

1. **Re-evaluation of the field**: Prior results claiming strong performance may be dominated by systematic variation capture rather than perturbation-specific learning.
2. **Better experimental design**: Systema's framework suggests that Perturb-seq experiments should include negative controls (scrambled guides) in every batch for proper normalization.
3. **Metric recommendations**: Perturbation-specific metrics should be standard in benchmarks going forward.

## Relationship to Other Evaluation Work

| Work | Focus | Approach |
|------|-------|----------|
| Systema | Systematic variation bias | Perturbed centroid reference |
| AUPRC (Zhu et al.) | DEG identification | PR curve over ranked genes |
| Miller et al. | Effect size calibration | Dynamic Range Fraction |
| GGE (Rubbi et al.) | Metric standardization | Unified Python framework |
| Ahlmann-Eltze | Linear baseline parity | Cross-model benchmark |

## Citations

Viñas Torné R et al. (2025). Systema: a framework for evaluating genetic perturbation response prediction beyond systematic variation. *Nature Biotechnology*. doi:10.1038/s41587-025-02777-8.
