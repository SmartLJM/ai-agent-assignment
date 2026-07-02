# Departures: Neural Schrodinger Bridge for Single-Cell Perturbation Prediction

## Overview

Departures (Distributional Transport for Single-Cell Perturbation Prediction with Neural Schrodinger Bridges) is a generative framework that addresses a fundamental challenge in single-cell perturbation modeling: RNA-seq is destructive, so the same cell cannot be observed both before and after perturbation, making the data inherently **unpaired**. Chi et al. (AAAI 2026) approximate the Schrodinger Bridge (SB) to directly align distributions of control and perturbed cells, achieving principled optimal transport without the computational burden of bidirectional inference.

## Problem Being Solved

The unpaired nature of single-cell perturbation data is a core challenge:
1. RNA sequencing requires cell lysis, preventing before/after measurements on the same cell
2. Existing VAE-based and regression-based methods often ignore the unpaired structure
3. Prior SB approximations require bidirectional model updates (forward and backward processes), which are computationally expensive and ill-defined in conditional settings
4. Some methods (e.g., the authors' prior work) align distributions indirectly through a shared prior space, deviating from energy-optimal transport trajectories

## Key Method: Schrodinger Bridge with Minibatch OT

The **Schrodinger Bridge (SB)** problem seeks the stochastic process that evolves between two marginal distributions (control and perturbed cell populations) while minimizing KL divergence from a reference diffusion process:

P* = argmin_{P∈P(C)} {KL(P|Q) : P₀=π₀, P_T=π_T}

This is an entropy-regularized optimal transport problem. The path distribution implicitly defines optimal pairings between control and perturbed cells.

**Departures' key innovations**:

1. **Minibatch OT pairing**: Instead of the standard alternating forward-backward IPF (Iterative Proportional Fitting) updates, Departures uses Minibatch Optimal Transport to directly compute source-target sample pairings during training. This pairing guides bridge matching, eliminating the need for bidirectional iterative updates.

2. **Bridge matching**: Given the minibatch OT pairings, Departures learns the Markovian projection (Gyongy 1986) that defines the optimal transition velocity field. This yields a tractable, scalable approximation to the SB.

3. **Dual SB models**: Two complementary Schrodinger Bridge models are trained jointly:
   - **Discrete SB**: Models gene activation states (binary on/off), capturing whether genes are expressed or silenced
   - **Continuous SB**: Models expression distributions (continuous values), capturing quantitative expression dynamics
   
   Joint training improves both biological fidelity and generative robustness.

## Main Results

Departures was evaluated on public genetic and chemical perturbation datasets:

**Genetic perturbations (Perturb-seq data)**:
- Achieves state-of-the-art Pearson correlation of predicted vs. observed post-perturbation expression
- Superior to CPA, GEARS, scGen, and the authors' own prior conditional diffusion model

**Drug perturbations (sciPlex, LINCS-like data)**:
- Outperforms baselines in distributional metrics (Wasserstein distance, energy distance)
- Better captures heterogeneous single-cell responses compared to population-level averaging

**Key advantages over prior work (Chi et al. 2025a)**:
- Direct distribution alignment avoids deviating from energy-optimal trajectories
- Eliminates the need for a separate mask regression model trained independently
- The minibatch OT pairing provides tighter coupling than latent space alignment

## Comparison to Related Methods

| Method | Handles unpaired data | Conditional (perturbation-specific) | Optimal transport | Bidirectional |
|--------|----------------------|-------------------------------------|-------------------|---------------|
| scGen | No | Yes (label shift) | No | No |
| CellOT | Yes | No (unconditional) | Yes | No |
| CPA | No | Yes | No | No |
| Chi et al. 2025a | Yes | Yes | Approximate | Yes |
| **Departures** | **Yes** | **Yes** | **Yes (SB)** | **No** |

## Limitations

As a generative distribution alignment model, Departures cannot predict outcomes for out-of-training perturbations that differ fundamentally from training data (unlike GEARS which uses graph priors). The minibatch OT approximation introduces some error relative to the true Schrodinger Bridge. Computational cost scales with the number of perturbation conditions.

## Citation

Chi C, Huang Y, Xia J, Zheng J, Liu Y, Zang Z, Li SZ. "Departures: Distributional Transport for Single-Cell Perturbation Prediction with Neural Schrodinger Bridges." AAAI Conference on Artificial Intelligence (AAAI-26), 2026.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | Departures is a distribution alignment model trained per perturbation condition; it explicitly cannot predict outcomes for out-of-training perturbations that differ fundamentally from training data. |
| Cross cell-line (gene intersection) | Partial | The framework can in principle be applied to new cell lines using shared gene features, but cross-cell-line generalization is not a primary focus of the evaluation. |
| Zero-shot unseen cell line (gene intersection) | No | Departures requires training data (control and perturbed distributions) for each target condition; zero-shot transfer to unseen cell lines is not demonstrated. |
| Cross perturbation technology (gene intersection) | Not evaluated | The paper evaluates both genetic and chemical perturbations separately but does not test training on one technology and predicting another. |
| Zero-shot gene misalignment | No | The Schrodinger Bridge operates on a fixed gene space; completely different gene vocabularies are not addressed. |
| Perturbation-specificity vs. simple baseline | Yes | Departures achieves state-of-the-art Pearson correlation on Perturb-seq data, outperforming CPA, GEARS, scGen, and prior conditional diffusion baselines. |

**Overall capability tier**: Specialist
