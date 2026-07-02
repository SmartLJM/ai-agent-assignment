# scFoundation: 100M-Parameter Foundation Model on Single-Cell Transcriptomics

## Overview

scFoundation (also named xTrimoscFoundationα) is a large-scale single-cell foundation model with 100 million parameters covering approximately 20,000 genes, pretrained on over 50 million human single-cell transcriptomic profiles. Hao et al. (Nature Methods 2024) address three unique challenges of scaling foundation models to single-cell data: comprehensive data collection, handling the ~20,000-gene "long sentence" problem, and dealing with highly variable sequencing read depth across datasets.

## Problem Being Solved

Adapting foundation model paradigms from NLP to single-cell transcriptomics faces unique challenges not present in NLP:
1. **Data collection**: scRNA-seq datasets are scattered across databases in diverse formats, lacking a comprehensive unified resource
2. **Sequence length**: With ~20,000 protein-coding genes, each cell forms an exceptionally long "sentence" that traditional transformers cannot efficiently handle
3. **Read depth variation**: Total sequencing read counts vary enormously across datasets and technologies, creating systematic technical biases that impede learning uniform representations

## Architecture: xTrimoGene Asymmetric Design

**Key innovation: Asymmetric encoder-decoder architecture** inspired by masked autoencoders (MAE) in computer vision, but adapted for scRNA-seq sparsity:

- **Encoder**: Processes only the **non-masked** genes (typically observed/non-zero genes), enabling efficient encoding despite the full ~20,000-gene vocabulary
- **Decoder**: Predicts the expression values of **masked** (zeroed) genes from the encoder output
- This asymmetry is critical for efficiency: the expensive encoder operates on a small subset of non-zero genes, while the lightweight decoder handles full-gene reconstruction

**Embedding module**: Converts continuous gene expression scalar values into learnable high-dimensional vectors, preserving full resolution of raw expression values (unlike bin-based methods like scGPT).

**Pretraining task: Read-Depth-Aware (RDA) Modeling**:
- Extension of masked language modeling that accounts for read depth variation
- For each cell, creates a "source" (downsampled/low read depth) and "target" (full read depth) version
- The model predicts masked gene expression in the target profile given the source profile
- Two total count indicators T (target) and S (source) are provided to the model
- This teaches the model to: (1) learn gene co-expression patterns AND (2) harmonize cells with different read depths
- At inference: Feed a cell's raw expression, set T higher than S to enhance to higher read-depth equivalent

## Training Data

- Over 50 million human scRNA-seq profiles collected from GEO, Single Cell Portal, HCA, hECA, DISCO, EMBL-EBI
- 19,264 protein-coding and mitochondrial genes (HGNC standard)
- Spans 100+ tissue types across diseases, tumors, and normal states

## Downstream Task Architecture

scFoundation produces two types of contextual embeddings:

1. **Cell-level embeddings** (from encoder): Used for:
   - Cell clustering (intra- and inter-dataset)
   - Bulk drug response prediction (GDSC, PRISM datasets)
   - Single-cell drug response classification
   - Cell type annotation

2. **Gene-level context embeddings** (from decoder): Used for:
   - Single-cell perturbation prediction (gene expression changes after CRISPR)
   - Gene module inference and co-expression analysis

Non-fine-tuned or lightly fine-tuned scFoundation embeddings are adapted to downstream task-specific models, reducing the computational burden for users.

## Main Results

**Scaling laws**: Validated power-law decline in validation loss with increasing model parameters and FLOPs—the first scaling law characterization for single-cell foundation models.

**Read depth enhancement**: Without fine-tuning, scFoundation enhances downsampled cells (to 1%, 5%, 10%, 20% of original reads) with ~50% reduction in MAE and MRE compared to downsampled inputs.

**Perturbation prediction**: Outperforms task-specific models (CPA, GEARS) on held-out gene perturbation prediction tasks.

**Drug response**: State-of-the-art on GDSC bulk drug response prediction and PRISM drug screen classification.

**Cell type annotation**: Competitive with or better than scGPT and Geneformer on standard benchmarks.

**Gene module inference**: scFoundation gene embeddings correctly cluster known co-expressed gene modules (ribosomal genes, mitochondrial genes, cell cycle genes).

## Limitations

scFoundation covers human transcriptomics only; no cross-species capabilities. The asymmetric MAE architecture requires careful calibration of masking ratio and read-depth augmentation. The model is available at BioMap's servers with access restrictions for very large-scale inference.

## Citation

Hao M, Gong J, Zeng X, Liu C, Guo Y, Cheng X, Wang T, Ma J, Zhang X, Song L. "Large-scale foundation model on single-cell transcriptomics." Nature Methods (2024). DOI: 10.1038/s41592-024-02305-7

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | scFoundation outperforms task-specific models (CPA, GEARS) on held-out gene perturbation prediction tasks using gene-level context embeddings from the decoder. |
| Cross cell-line (gene intersection) | Partial | Pretrained on 50M+ human cells across 100+ tissue types, scFoundation transfers to diverse cellular contexts, but explicit cross-cell-line perturbation benchmarks are limited in the paper. |
| Zero-shot unseen cell line (gene intersection) | Partial | The model's broad pretraining enables some transfer to new contexts, but zero-shot perturbation prediction on completely unseen cell lines without any fine-tuning data is not specifically demonstrated. |
| Cross perturbation technology (gene intersection) | Not evaluated | scFoundation evaluates genetic perturbation prediction and drug response prediction separately but does not test cross-technology generalization. |
| Zero-shot gene misalignment | No | scFoundation covers human protein-coding genes (19,264 genes); cross-species or completely disjoint gene vocabularies are not addressed. |
| Perturbation-specificity vs. simple baseline | Yes | scFoundation outperforms CPA and GEARS on held-out perturbation prediction and achieves state-of-the-art on GDSC bulk drug response prediction. |

**Overall capability tier**: Foundation
