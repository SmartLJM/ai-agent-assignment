# scDist: Robust Identification of Perturbed Cell Types in scRNA-seq Data

## Overview

Single-cell transcriptomics enables researchers to identify how different cell types respond to diseases, infections, or treatments by comparing gene expression across conditions. However, existing methods for "differential state analysis"—detecting cell types with altered transcriptional profiles between conditions—suffer from a critical flaw: they do not account for individual-to-individual variability, leading to false positive discoveries. This paper introduces scDist, a statistically rigorous approach based on linear mixed-effects models that correctly identifies perturbed cell types while controlling for individual and technical variability.

## Problem Being Solved

The predominant tool Augur uses machine learning classifiers to rank cell types by transcriptional separation between conditions. However, Augur and similar methods do not account for inter-individual variability. The authors demonstrate this fatal flaw: when six healthy controls are randomly split into two groups and analyzed as if they represent different "conditions," Augur falsely identifies multiple cell types as perturbed in 93% of AUC measurements, and classifies red blood cells as perturbed in all 20 repeated trials. Standard batch correction (Harmony) as preprocessing does not resolve this issue. The root cause is that individual-to-individual variation is incorrectly interpreted as condition-level difference.

## Key Method

**scDist** models the vector of normalized gene expression counts for each cell type using a linear mixed-effects model:

z_ij = α + x_j β + ω_j + ε_ij

where:
- α is the baseline expression vector
- x_j is a binary condition indicator
- β is the condition-level effect (the parameter of interest)
- ω_j is a random effect capturing inter-individual variability (ω_j ~ N(0, τ²I))
- ε_ij is cell-level noise (ε_ij ~ N(0, σ²I))

The key metric is the **estimated transcriptomic distance** between condition means (||β||₂), computed in a low-dimensional PCA embedding for computational efficiency. This distance is interpretable as the magnitude of the condition-level transcriptional shift, independent of sample sizes and significance thresholds.

**Input**: Pearson residuals from scTransform normalization (or other normalization methods) are recommended. The model estimates the random effects jointly across genes, enabling proper variance partitioning.

**Computational efficiency**: By operating on PCA embeddings, scDist is substantially faster than Augur—achieving speedups of 10-100x depending on dataset size—making it practical for large cohort studies.

## Main Results

**Negative control validation**: On the 6-sample healthy blood dataset split into random groups, scDist correctly identifies no significantly perturbed cell types, while Augur has extensive false positives.

**COVID-19 dataset**: scDist identifies transcriptomic perturbations in dendritic cells (DCs), plasmacytoid dendritic cells (pDCs), and FCER1G+ NK cells—findings not recoverable by Augur due to its inability to control for individual variability.

**Multi-cohort immunotherapy analysis**: By jointly analyzing five independent scRNA-seq immunotherapy cohorts (using patient as a random effect), scDist identifies a significant transcriptional difference in a subpopulation of NK cells between responders and non-responders. This finding was validated in bulk RNA-seq from 789 patients across seven independent cohorts, demonstrating the method's ability to detect robust, replicable biological signals.

## Limitations and Comparisons

scDist is designed specifically for **differential state analysis** (comparing transcriptional profiles of defined cell types), not differential abundance. It assumes linearity in the mixed-effects model and may not capture nonlinear perturbation effects. The method requires pre-defined cell type annotations. Compared to Augur, scDist is both more statistically rigorous and computationally faster. The main trade-off is that the mixed-effects framework requires multiple samples per condition, making it inappropriate for single-replicate experiments.

## Citation

Nicol PB, Paulson D, Qian G, Liu XS, Irizarry R, Sahu AD. "Robust identification of perturbed cell types in single-cell RNA-seq data." Nature Communications (2024) 15:7610. DOI: 10.1038/s41467-024-51649-3

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | scDist is a statistical analysis tool that identifies which cell types are significantly perturbed between observed conditions; it does not predict responses to unseen perturbations. |
| Cross cell-line (gene intersection) | Not evaluated | scDist is designed for differential state analysis within a study; cross-cell-line generalization is not a relevant capability for this statistical framework. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | scDist requires experimental data from both conditions being compared; zero-shot prediction on unseen cell lines is not applicable. |
| Cross perturbation technology (gene intersection) | Not evaluated | scDist is a general differential state analysis method applicable to any condition comparison, but cross-technology generalization is not evaluated. |
| Zero-shot gene misalignment | Not evaluated | scDist operates on a fixed gene set from the experimental data; gene vocabulary misalignment across datasets is not addressed. |
| Perturbation-specificity vs. simple baseline | Yes | scDist correctly identifies no false positives in negative control experiments where Augur has 93% false positive rate, and identifies novel perturbed cell types missed by existing methods in COVID-19 data. |

**Overall capability tier**: Benchmark-tool
