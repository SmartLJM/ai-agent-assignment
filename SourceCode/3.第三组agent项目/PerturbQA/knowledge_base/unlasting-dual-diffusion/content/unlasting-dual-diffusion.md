# Unlasting: Unpaired Single-Cell Perturbation via Dual Diffusion Implicit Bridges

## Overview

Unlasting (Chi et al., 2025) addresses a fundamental challenge in single-cell perturbation modeling: the inherently **unpaired** nature of the data. Because RNA-seq requires cell lysis, the same cell cannot be measured before and after perturbation. Unlasting proposes a framework based on Dual Diffusion Implicit Bridges (DDIB) that learns the mapping between unperturbed and perturbed cell distributions without requiring explicit pairing of individual cells.

## The Unpaired Problem in Single-Cell Biology

Single-cell perturbation experiments produce two separate populations:
- **Control cells**: Unperturbed, but sequenced and therefore destroyed
- **Perturbed cells**: Treated with CRISPR knockout or drug, separately sequenced

These populations cannot be paired at the individual cell level. Most existing methods handle this by:
1. **Forced pairing**: Randomly matching control and perturbed cells (introduces noise)
2. **Distribution matching**: Ignoring pairing entirely (loses cell-specific trajectory information)
3. **OT pairing** (CellFlow): Computationally expensive soft assignment

Both approaches have limitations. Unlasting proposes learning separate distributions for control and perturbed cells, then bridging them through a shared Gaussian latent space.

## Dual Diffusion Implicit Bridges (DDIB)

### Core Mechanism
DDIB leverages the DDIM (Denoising Diffusion Implicit Models) inversion technique to create implicit bridges between two data distributions:

**Source model**: Learns the distribution of unperturbed (control) cells P₀
**Target model**: Learns the distribution of perturbed cells P₁ conditioned on perturbation P

Both models share a **common prior space**: a shared Gaussian distribution. This shared prior creates an implicit bridge: any control cell x can be inverted to Gaussian noise via DDIM, then denoised into a perturbed cell with different conditioning.

**Mathematically**:
x^l = DDIMInverse(SourceModel, x^c, 0 → 1)  [map to shared prior]
x^t = DDIMDenoise(TargetModel, x^l, P, 1 → 0)  [map to perturbed distribution]

This framework is interpreted as data augmentation: DDIB continuously augments target domain samples with an infinite set of source domain samples, overcoming the limitations of discrete random pairing.

## Architecture Components

### GRN Block
Unlasting integrates gene regulatory network (GRN) information:
- **GRN adjacency matrix A**: Learned from pre-trained foundation models (e.g., SCENIC+) + co-expression correlation
- **GAT layers**: Graph Attention Network aggregates information across GRN edges
- **Perturbation propagation**: Perturbation signals are propagated through GRN in the target model

### Mask Model for Silent Genes
Gene expression data is sparse; many genes are completely silenced in specific conditions. Unlasting trains a dedicated **mask model** (trained independently from the main model) to predict which genes will be silent (zero expression) under each perturbation condition. This mask is applied to final predictions:
x̂₀ = (M̂_{c,P} ⊙ x^t) × x_max

where M̂_{c,P} is the predicted sparsity mask.

## New Evaluation Metric for Heterogeneous Responses

Unlasting introduces distribution-aware metrics to address the observation that many genes show **bimodal expression** under the same perturbation condition:
- **E-distance**: Energy distance captures both inter-group and intra-group distributional differences
- **Earth Mover's Distance (EMD)**: Quantifies gene-level distributional shifts

These metrics are evaluated on all genes, top-20 DE genes, and top-40 DE genes separately.

## Experimental Results

Benchmarked on Adamson et al. (2016, CRISPR) and sci-Plex3 (drug perturbations):

### Genetic Perturbations (Adamson)
- Unlasting achieves the lowest E-distance and EMD across all and DE gene subsets
- Outperforms GEARS, GraphVCI, and scGPT on E-distance for DE genes

### Chemical Perturbations (sci-Plex3)
- Best performance among compared methods on OOD drug conditions
- Particularly strong on top-40 DE genes where distribution fidelity matters most

### Double Gene Perturbation
- Successfully handles combinatorial gene knockouts
- Outperforms GEARS on E-distance for double perturbations

## Key Advantages Over Alternatives

1. **No explicit pairing needed**: DDIB naturally handles unpaired data through shared prior
2. **Handles bimodality**: Distribution-to-distribution mapping preserves multimodal responses
3. **GRN guidance**: Biological regulatory structure improves perturbation propagation
4. **Mask model**: Explicitly predicts gene silence, improving prediction quality for sparse genes

## Citations

Chi C et al. (2025). Unlasting: Unpaired Single-Cell Multi-Perturbation Estimation by Dual Conditional Diffusion Implicit Bridges. *arXiv:2506.21107*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | Unlasting achieves the lowest E-distance and EMD on OOD drug conditions in sci-Plex3 and outperforms GEARS on E-distance for held-out genetic perturbations in Adamson et al. |
| Cross cell-line (gene intersection) | No | Unlasting is evaluated on Adamson and sci-Plex3 datasets within fixed cell-line contexts; no explicit cross-cell-line transfer evaluation is reported. |
| Zero-shot unseen cell line (gene intersection) | No | The DDIB framework requires learning source and target distributions from the training cell line; zero-shot transfer to unseen cell lines is not evaluated. |
| Cross perturbation technology (gene intersection) | Partial | Unlasting is evaluated on both CRISPR genetic perturbations (Adamson) and drug perturbations (sci-Plex3), demonstrating some cross-technology applicability. |
| Zero-shot gene misalignment | No | Both source and target diffusion models operate on the same fixed gene vocabulary; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | Unlasting outperforms GEARS, GraphVCI, and scGPT on E-distance for DE genes, with particularly strong performance on top-40 DE genes where distribution fidelity matters most. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
