# Biolord: Disentangling Single-Cell Data for Perturbation and Multi-Omic Analysis

## Overview

Biolord is a deep generative framework for learning disentangled representations in single-cell multi-omic data. Published in Nature Biotechnology (2024), Piran et al. present a method that separates single-cell measurements into known biological attributes (cell type, drug treatment, time point, spatial location) and unknown residual attributes (batch effects, biological noise, unclassified variation). By virtually shifting cells across conditions in this disentangled space, biolord enables prediction of experimentally inaccessible states and outperforms state-of-the-art methods in predicting responses to unseen drugs and genetic perturbations.

## Problem Being Solved

Single-cell gene expression profiles simultaneously encode multiple overlapping biological attributes: cell type, tissue of origin, differentiation stage, treatment, time, and technical batch effects. Existing methods either:
1. Disentangle for specific tasks (perturbation response, group-specific attributes) but not general multi-attribute scenarios
2. Rely on linearity/independence assumptions that fail in complex biological settings
3. Cannot integrate multiple types of information or provide generic reconstruction

Biolord provides a general-purpose disentanglement framework applicable across modalities and attribute types.

## Architecture: Decomposed Latent Space

**Input**: Single-cell measurements with partial supervision—each cell has labels for some known attributes (e.g., cell type, perturbation, time point) but not others.

**Encoding**:
- Each known attribute has a dedicated encoder that produces a representation Z_y for that attribute (separate latent spaces for cell type, drug, time, etc.)
- An additional unknown attribute encoder Z_u captures remaining variation

**Decomposed latent space**: Z = {Z_y1, Z_y2, ..., Z_yk, Z_u}

**Generator (decoder)**: G_θ maps the decomposed representations back to single-cell measurements. The generator is shared and must reconstruct any combination of known and unknown attribute representations.

**Optimization**: The loss function balances:
- **Completeness**: Maximize reconstruction accuracy (using all latent codes)
- **Compactness**: Minimize information in Z_u (limiting its capacity to encode known-attribute variation)
- **Attribute classification**: Auxiliary losses ensuring Z_y codes genuinely capture their respective attributes

**Counterfactual generation**: To predict a cell's gene expression in an unobserved state, replace the known attribute code (e.g., drug treatment) while keeping Z_u fixed. This generates a "virtual" cell that retains the unknown residual characteristics of the original cell but has the biological context of the target state.

## Key Applications

**Drug response prediction (out-of-sample)**:
- Biolord is tested on predicting transcriptional responses to drugs not seen during training (novel drug generalization)
- Achieves E(r²) = 0.76 ± 0.0005 vs. chemCPA-pretrained at 0.51 ± 0.0062 and chemCPA at 0.40 ± 0.0067 on standard drug response benchmarks
- **Dramatically outperforms** state-of-the-art models on out-of-sample drug prediction

**Genetic perturbation prediction**: Similarly strong generalization to unseen genetic perturbations by disentangling the perturbation effect from cell-type-specific background

**Spatial-temporal analysis**: Biolord handles continuous attributes (time, spatial coordinates) as ordered attribute spaces, enabling interpolation of intermediate time points or spatial positions

**Multi-omic integration**: Applied to paired RNA + protein (CITE-seq) or RNA + ATAC data, disentangling shared and modality-specific variation

**Batch correction**: Z_u captures batch effects as part of the unknown attributes, enabling cleaner biological signal extraction

## Main Results

- Outperforms chemCPA, CPA, scGen, and biolord predecessors on drug response prediction benchmarks
- Consistently better at generalizing to novel perturbations across multiple datasets
- Successfully disentangles known attributes in diverse biological systems (embryogenesis, COVID-19 infection, drug treatment)
- Identifies driver genes of specific cell states through attribution of high-weight unknown attributes

## Limitations

Biolord requires labeled attributes for supervised disentanglement—purely unsupervised discovery of latent factors is limited. Performance degrades when labeled attributes are highly correlated or when the unknown attributes carry substantial biological variation of interest.

## Citation

Piran Z, Cohen N, Hoshen Y, Nitzan M. "Disentanglement of single-cell data with biolord." Nature Biotechnology 42, 1678–1683 (2024). DOI: 10.1038/s41587-023-02079-x

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | Biolord achieves E(r²) = 0.76 on out-of-sample drug prediction, dramatically outperforming chemCPA (0.51) and CPA (0.40) on unseen drug generalization benchmarks. |
| Cross cell-line (gene intersection) | Yes | Biolord's disentangled latent space separates cell type attributes from perturbation effects, enabling transfer of perturbation predictions to new cell types using shared gene features. |
| Zero-shot unseen cell line (gene intersection) | Partial | By replacing known attribute codes (cell type, drug) while keeping unknown residual codes fixed, biolord can generate counterfactuals for new conditions, but requires labeled attribute annotations. |
| Cross perturbation technology (gene intersection) | Not evaluated | Biolord evaluates both drug response and genetic perturbation prediction separately but does not test cross-technology generalization. |
| Zero-shot gene misalignment | No | Biolord operates on a fixed gene vocabulary during training and inference; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | Biolord consistently outperforms chemCPA, CPA, scGen, and predecessor methods on drug response and genetic perturbation prediction benchmarks. |

**Overall capability tier**: Specialist
