# CPJUMP1: Image-Based Cell Perturbation Analysis Benchmark Dataset

## Overview

Image-based profiling of cells using microscopy (the Cell Painting assay) is a powerful but underexploited tool for biological discovery, limited primarily by the lack of ground-truth datasets with matched chemical and genetic perturbations. The JUMP Cell Painting Consortium (Joint Undertaking in Morphological Profiling) assembled **CPJUMP1**, a large-scale benchmark dataset of approximately 3 million microscopy images of human cells treated with matched chemical and genetic perturbations targeting the same genes. This resource is designed to accelerate method development for identifying perturbation similarities and drug mechanisms of action (MoA).

## Problem Being Solved

The field of image-based profiling has lagged behind transcriptomics-based profiling because: (1) there is no ground truth for whether two perturbations should produce similar morphological phenotypes, and (2) existing public datasets do not include both chemical and genetic perturbations targeting the same genes in a controlled, paired experimental design. Without such a benchmark, it is impossible to objectively evaluate and compare computational methods for learning cell representations from microscopy.

## Dataset Design

**Gene/compound selection**: 160 genes and 303 compounds were selected based on known gene-compound relationships where each gene's product is the target of at least 2 compounds in the dataset. This provides relatively trustworthy positive pairs for evaluation.

**Experimental groups**:
- **Primary group**: Chemical perturbations + CRISPR knockout (KO) + ORF overexpression (OE) in two cell types (U2OS and A549) at two time points
- **Secondary group**: Additional experimental conditions including imaging conditions, used for method optimization

**Scale**: 40 primary 384-well plates + additional secondary plates; ~3 million 5-channel images (DNA, RNA, ER, AGP/actin-Golgi-plasma membrane, Mito); 75 million single-cell profiles; well-level aggregated profiles

**Matched perturbation design**: Chemical and genetic perturbations are run in separate wells with the same experimental batch, minimizing technical confounders that plague cross-batch comparisons.

**Consortium**: 10 pharmaceutical companies + 2 non-profits (Broad Institute), designed collaboratively to ensure the dataset serves the broader community's method development needs.

## Key Findings from Baseline Analyses

**Main finding**: Identifying morphological matches between chemical and genetic perturbations targeting the same gene is surprisingly challenging, even with the ground-truth gene-compound annotations provided. Several observations:

1. **Directionality matters**: KO and OE of the same gene often produce opposite morphological effects, and chemical inhibitors may mimic KO or OE depending on the mechanism
2. **Cell type differences**: Matches do not always transfer between U2OS and A549 cells
3. **Time point sensitivity**: The optimal time point for detecting morphological effects varies by perturbation type
4. **Feature extraction gap**: Classical hand-engineered CellProfiler features often outperform early deep learning approaches, but the gap is narrowing

## Resource Value

CPJUMP1 fills a critical gap by providing:
- A standardized benchmark with known true positives (gene-compound pairs)
- Multiple experimental conditions enabling method testing across contexts
- A collaborative, community-curated design ensuring relevance to pharmaceutical discovery
- Code and data available at: https://github.com/jump-cellpainting/2024_Chandrasekaran_NatureMethods

## Comparison to Existing Datasets

Prior to CPJUMP1, RxRx3 was the main public dataset with both chemical and genetic perturbations, but it anonymizes 733 genes, has only one cell type/time point, and lacks gene-compound pair annotations. CPJUMP1 is superior in annotation depth, experimental diversity, and accessibility.

## Citation

Chandrasekaran SN, Cimini BA, Goodale A, Miller L, Kost-Alimova M, Jamali N, Doench JG, ... Singh S, Carpenter AE. "Three million images and morphological profiles of cells treated with matched chemical and genetic perturbations." Nature Methods 21, 1114–1121 (2024). DOI: 10.1038/s41592-024-02241-6
