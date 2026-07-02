# CellFlow: Generative Single-Cell Phenotype Modeling with Flow Matching

## Overview

CellFlow (Klein et al., bioRxiv 2025) is a generative model for single-cell perturbation prediction that uses flow matching with optimal transport (OT) pairing. Unlike most perturbation prediction methods that focus on CRISPR gene knockouts in a single cell line, CellFlow is designed as a general framework applicable across multiple perturbation modalities: cytokines, small molecule drugs, and CRISPR gene knockouts, tested at massive scale (~10 million PBMCs and zebrafish cells).

## Core Technology: Flow Matching with Optimal Transport

### Flow Matching
CellFlow builds on continuous normalizing flows (CNF), specifically using flow matching — a simulation-free approach to learning mappings between probability distributions. Given:
- Source distribution P₀: unperturbed cell population
- Target distribution P₁: perturbed cell population

Flow matching learns a vector field v(t, x) that continuously transforms samples from P₀ to P₁ along time t ∈ [0,1].

### Optimal Transport Pairing
A key challenge in single-cell perturbation data is that cells cannot be measured twice (RNA-seq destroys the cell), creating an **unpaired** setting. CellFlow addresses this using minimax Optimal Transport (OT) to create soft pairings between control and perturbed cells:

π = OT(P₀, P₁)

This pairing identifies which control cells are most likely "ancestors" of which perturbed cells, creating training signal for the flow. OT pairing is better than random pairing because it minimizes transport cost, creating biologically plausible trajectories.

## Architecture

### Encoder
- A neural network encoder maps gene expression profiles to a low-dimensional latent space
- The encoder is shared across all perturbation conditions

### Conditional Flow Network
- A neural ODE (ordinary differential equation) network parameterized by a small MLP
- Conditioned on the perturbation embedding (perturbation identity + cell type)
- Learns to transport cells from control to perturbed state

### Perturbation Embedding
- Gene knockouts: Embedded using sequence-derived or pre-trained gene representations
- Small molecules: Embedded using molecular fingerprints or SMILES-based encoders
- Cytokines: Protein sequence or pre-trained protein language model embeddings

## Scale of Application

CellFlow is tested at unprecedented scale:

### PBMC Dataset
- ~10 million peripheral blood mononuclear cells
- Multiple cytokine perturbations (IFN-γ, IL-2, etc.) across multiple cell types
- Demonstrates that CellFlow can handle high-dimensional, complex immune responses

### Zebrafish Dataset
- Developmental single-cell atlas of zebrafish embryo
- Tests whether flow matching can model developmental trajectories (differentiation)
- Shows generalization to non-perturbation (differentiation) settings

### Combinatorial Generalization
- CellFlow is tested on predicting cytokine combination effects from single cytokine training data
- Demonstrates compositionality in the latent flow space

## Comparison with Other Generative Methods

| Method | Core Technology | Pairing | Scale |
|--------|----------------|---------|-------|
| CellFlow | Flow matching + OT | OT-based soft pairing | ~10M cells |
| PerturbDiff | Functional diffusion (RKHS) | None (unconditional gen.) | 61M pre-train |
| Unlasting | DDIB (dual diffusion) | Implicit Gaussian prior | ~100k cells |
| CPA | Compositional VAE | No pairing needed | ~1M cells |
| GEARS | GNN regression | No generation | N/A |

## Results

- **Distribution matching**: Lower Wasserstein distance than CPA and GEARS on multiple benchmarks
- **Heterogeneity**: Generated cells show appropriate single-cell variance
- **Compositionality**: Cytokine combination effects predicted with reasonable accuracy from single-cytokine training
- **Multi-modality**: Single framework handles genetic, chemical, and protein perturbations

## Key Limitations

1. **OT pairing approximation**: The OT pairing is computationally expensive and may be imperfect for very heterogeneous populations
2. **Mean-collapse partially addressed**: While better than VAE methods, CellFlow can still underestimate rare cell subpopulations
3. **No mechanistic interpretability**: The flow vector field does not directly correspond to biological regulatory processes

## Citations

Klein O et al. (2025). CellFlow enables generative single-cell phenotype modeling with flow matching. *bioRxiv:2025.04.11.648220*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | CellFlow is tested on predicting cytokine combination effects from single-cytokine training data and generalizes to unseen perturbation combinations through compositional flow matching. |
| Cross cell-line (gene intersection) | Yes | CellFlow is tested across multiple cell types in the ~10M PBMC dataset, demonstrating cross-cell-line generalization with lower Wasserstein distance than CPA and GEARS. |
| Zero-shot unseen cell line (gene intersection) | No | While CellFlow handles multiple cell types, zero-shot prediction to completely unseen cell lines with no training data is not explicitly evaluated. |
| Cross perturbation technology (gene intersection) | Yes | CellFlow handles cytokines, small molecule drugs, and CRISPR gene knockouts within a single framework using modality-specific perturbation embeddings. |
| Zero-shot gene misalignment | No | CellFlow operates on a shared gene expression space; predictions into completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | CellFlow achieves lower Wasserstein distance than CPA and GEARS on multiple benchmarks and shows compositionality for cytokine combinations, demonstrating perturbation-specific signal beyond baselines. |

**Overall capability tier**: Foundation
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
