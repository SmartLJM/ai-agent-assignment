# PerturbDiff: Functional Diffusion for Single-Cell Perturbation Modeling

## Overview

PerturbDiff (Yuan et al., 2026) represents a paradigm shift in perturbation prediction by formulating the problem as functional diffusion in a Reproducing Kernel Hilbert Space (RKHS) rather than diffusion in raw gene expression space. The key innovation is treating each cell's gene expression profile as a function (from genes to expression values) and diffusing over the space of such functions using kernel mean embeddings, enabling distribution-level predictions that naturally capture single-cell heterogeneity.

## Motivation: Distribution-Level Prediction

Standard perturbation models predict the mean post-perturbation expression profile. However, single-cell data exhibits substantial heterogeneity: different cells respond differently to the same perturbation due to:
- Cell cycle state
- Stochastic gene expression
- Subclonal variation
- Epigenetic heterogeneity

Predicting only the mean loses this distributional information, which is critical for understanding how heterogeneous tumor populations respond to drug treatment, or how stem cell differentiation trajectories vary across cells.

## Functional Diffusion Framework

### RKHS Representation
PerturbDiff represents each cell's expression profile as a point in a Reproducing Kernel Hilbert Space (RKHS) H using the kernel mean embedding:
μ_P = E_{x~P}[φ(x)] ∈ H

where φ(x) is the feature map associated with a kernel k (e.g., Gaussian RBF kernel on gene expression vectors).

The diffusion process operates in this functional space, enabling:
1. Distribution-to-distribution mappings (not just point predictions)
2. Principled uncertainty quantification
3. Preservation of correlation structure between genes

### MM-DiT Architecture
PerturbDiff uses a Multi-Modal Diffusion Transformer (MM-DiT) architecture:
- **Cell expression tokens**: Each cell's gene expression vector is tokenized
- **Perturbation tokens**: The perturbation identity (gene knockout) is embedded as tokens
- **Cross-modal attention**: Perturbation tokens attend to cell tokens to condition the diffusion

This architecture is adapted from image generation models (Stable Diffusion 3) to the single-cell domain.

### Marginal Pre-training
A critical contribution is **marginal pre-training** on 61 million single cells (without perturbation labels). This pre-training step:
1. Teaches the model the manifold of biologically valid cell states
2. Provides strong initialization for fine-tuning on perturbation data
3. Enables the model to generate diverse but biologically realistic cells

## Key Technical Contributions

### 1. Distributional Metrics
PerturbDiff is evaluated using distribution-level metrics:
- **Wasserstein distance**: Measures distributional alignment between predicted and true cell populations
- **MMD (Maximum Mean Discrepancy)**: Kernel-based distributional distance
- These are more informative than MSE on mean expression

### 2. Conditional Generation
At inference time, given:
- A set of unperturbed control cells
- The identity of the knocked-out gene

PerturbDiff generates a set of synthetic perturbed cells that collectively form the predicted distribution.

### 3. Scalability
Pre-training on 61M cells provides broad coverage of cell types and states, making fine-tuning on specific perturbation datasets more data-efficient.

## Results

On Norman et al. and Replogle et al. benchmarks:
- **Distribution recovery**: PerturbDiff achieves significantly lower Wasserstein distance than CPA, GEARS, and CellFlow
- **Heterogeneity preservation**: Generated cells show appropriate variance in DEG expression matching the true single-cell spread
- **Rare subpopulation modeling**: Unlike mean-prediction models, PerturbDiff can capture bimodal response distributions

## Comparison with CellFlow

| Aspect | PerturbDiff | CellFlow |
|--------|-------------|----------|
| Methodology | Functional diffusion (RKHS) | Flow matching (OT) |
| Pre-training | 61M cells | Not specified |
| Architecture | MM-DiT transformer | CNF (Neural ODE) |
| Key metric | Wasserstein distance | Wasserstein + Pearson |
| Distribution modeling | Yes (RKHS) | Yes (OT pairing) |

## Limitations

1. **Computational cost**: Diffusion models require many forward passes at inference (typically 50-100 steps)
2. **RKHS abstraction**: The kernel choice significantly affects results; default RBF kernel may not optimally represent gene expression geometry
3. **Pre-training data**: The 61M cell pre-training corpus may introduce biases toward common cell types

## Citations

Yuan X et al. (2026). PerturbDiff: Functional Diffusion for Single-Cell Perturbation Modeling. *arXiv:2602.19685*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | PerturbDiff is evaluated on held-out perturbation conditions from Norman et al. and Replogle et al., achieving significantly lower Wasserstein distance than CPA, GEARS, and CellFlow. |
| Cross cell-line (gene intersection) | Partial | Marginal pre-training on 61M cells provides broad cell-state coverage that partially supports cross-cell-line generalization, though no explicit cross-cell-line transfer protocol is described. |
| Zero-shot unseen cell line (gene intersection) | No | The paper does not report zero-shot evaluation on completely unseen cell lines without fine-tuning. |
| Cross perturbation technology (gene intersection) | No | PerturbDiff focuses on CRISPR genetic knockouts; no cross-technology evaluation is reported. |
| Zero-shot gene misalignment | No | The RKHS functional diffusion operates in the training gene expression space; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | PerturbDiff captures bimodal and heterogeneous single-cell response distributions, substantially outperforming mean-prediction baselines on Wasserstein and MMD distributional metrics. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
