# River: Interpretable Deep Learning for Perturbation-Responsive Spatial Gene Patterns

## Overview

As spatially resolved transcriptomics datasets expand from single slices to dozens of slices across multiple biological conditions (embryogenesis stages, disease states, treatment groups), there is a pressing need for methods to identify genes whose spatial expression patterns change meaningfully between conditions. This paper introduces **River** and a new analytical task called **Differential Spatial Expression Pattern (DSEP) gene prioritization**—identifying genes that exhibit condition-relevant spatial changes across multiple tissue sections.

## Problem Being Solved

Existing spatially variable gene (SVG) methods (SpatialDE, SPARK, SPARK-X, Sepal, etc.) focus on finding genes with spatial dependencies within a single slice, not identifying cross-condition spatial differences. The key challenges in DSEP prioritization are: (1) modeling complex spatial variation across multiple slices from different conditions, (2) scaling to large spatial datasets with millions of cells, and (3) disentangling inter-slice heterogeneity from condition-relevant signals.

## Key Methods and Architecture

**River** uses a two-branch predictive architecture:

1. **Gene expression branch**: Processes spatial gene expression data (RNA, protein) with a gene expression encoder that captures co-expression patterns.
2. **Spatial information branch**: Encodes position information (X, Y coordinates) using a position encoder that learns spatial dependencies.

The two branches are combined via heterogeneous alignment (concatenation of extracted features) and fed into a prediction layer (classifier) that predicts condition labels from cell/spot features. This is a supervised classification task: given cells from multiple conditions, the model learns to predict condition from gene expression and spatial context.

**Attribution strategy**: River employs a post-hoc attribution method applied to the trained model to rank genes by their contribution to condition discrimination. Each gene receives an "attribution score" reflecting how much it influences the model's condition predictions. Rank aggregation across multiple model runs or cross-validation folds is used to produce stable gene rankings.

**Spatial decoupling**: River decomposes gene contributions into spatial and non-spatial components, enhancing interpretability by separating spatially driven signals from purely expression-level changes.

**Distribution-agnostic design**: River is compatible with diverse spatial data types including 10x Visium, MERFISH, Slide-seq, and multimodal data (simultaneous RNA and protein).

## Main Results

River was evaluated on:
- **Simulated data**: Correctly prioritizes ground-truth DSEP genes while controlling false discovery rates
- **Embryogenesis**: Identifies spatially dynamic genes during developmental stage transitions
- **Diabetes-affected spermatogenesis**: Reveals spatial disruption of gene programs in diabetic tissue versus controls
- **Lupus-associated splenic changes**: Prioritizes genes with spatially heterogeneous lupus-specific expression patterns
- **Triple-negative breast cancer (TNBC)**: River-prioritized spatial gene patterns are associated with patient survival and generalize across patients, demonstrating translational relevance

Compared to existing methods that lack cross-condition spatial analysis, River achieves superior sensitivity and interpretability in identifying biologically meaningful DSEP genes.

## Limitations

River requires multiple tissue slices per condition for statistical power. The supervised classification framework may be influenced by slice-level batch effects if not properly controlled. The computational cost scales with the number of cells and slices, though the spatially-informed architecture improves efficiency versus naive approaches.

## Citation

Cui Y, Yuan Z. "Prioritizing perturbation-responsive gene patterns using interpretable deep learning." Nature Communications (2025) 16:6095. DOI: 10.1038/s41467-025-61476-9

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | River identifies spatially differentially expressed genes between observed conditions; it does not predict transcriptional responses to perturbations not yet measured. |
| Cross cell-line (gene intersection) | Not evaluated | River is designed for spatial transcriptomics cross-condition analysis within a study; cross-cell-line perturbation generalization is not a relevant capability. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | River requires multiple tissue slices from both conditions for supervised DSEP prioritization; zero-shot prediction on unseen cell lines is not applicable. |
| Cross perturbation technology (gene intersection) | Not evaluated | River is applied to diverse biological conditions (embryogenesis, disease, treatment) but cross-technology perturbation generalization is not evaluated. |
| Zero-shot gene misalignment | Not evaluated | River operates on the gene expression data from the spatial transcriptomics dataset; gene vocabulary misalignment is not a relevant scenario. |
| Perturbation-specificity vs. simple baseline | Yes | River achieves superior sensitivity and interpretability compared to existing spatially variable gene methods for identifying biologically meaningful DSEP genes, with TNBC findings generalizing across patients. |

**Overall capability tier**: Benchmark-tool
