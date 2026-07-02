# EpiAgent: Foundation Model for Single-Cell Epigenomics and ATAC-seq Analysis

## Overview

EpiAgent is the first large-scale foundation model specifically designed for single-cell ATAC-seq (scATAC-seq) data, addressing the unique challenges of the nearly binary, extremely sparse chromatin accessibility measurements. Chen et al. (Nature Methods 2025) pretrain EpiAgent on a manually curated Human-scATAC-Corpus (28 datasets, 31 tissues) and demonstrate capabilities across feature extraction, cell type annotation, data imputation, perturbation prediction, data integration, and in silico cis-regulatory element (CRE) knockout.

## Problem Being Solved

scATAC-seq enables epigenomic profiling at single-cell resolution, revealing chromatin accessibility landscapes that govern transcription. However:
1. The ~1M candidate cis-regulatory elements (cCREs) create extremely high-dimensional input
2. The near-binary nature and extreme sparsity of scATAC-seq data differ fundamentally from scRNA-seq
3. Existing methods are task-specific, require retraining for new data, and exclude many accessible cCREs from analysis
4. Key scientific questions—predicting cellular responses to perturbations and simulating CRE knockouts—remain unaddressed by prior tools

## Architecture: Cell Sentence Encoding

**Input representation**: EpiAgent represents each cell as a "cell sentence" by:
1. Applying TF-IDF transformation to the sparse cell × cCRE accessibility matrix to normalize for cell-level accessibility depth
2. Ranking non-zero accessibility values to identify the most informative cCREs per cell
3. Encoding the top-ranked cCREs as a sequence: [cCRE_T, cCRE_H, ..., cCRE_A, [SEP]]

**EpiAgent Transformer**: Uses **bidirectional attention** (unlike GPT-style autoregressive models) to capture regulatory network context:
- Each cCRE is represented by combining its rank embedding and cCRE identity embedding
- Bidirectional attention across the cell sentence captures co-accessibility patterns
- A [CLS] token aggregates the full-cell epigenomic state

**Dual pretraining tasks**:
1. **Cell-cCRE alignment**: Contrastive learning ensuring cell embeddings align with their constituent cCRE signals
2. **Signal reconstruction**: Masked language modeling variant predicting accessibility values of masked cCREs from context (via a signal decoder)

## Key Capabilities

**Perturbation prediction (with external embeddings)**: By incorporating external embeddings from gene expression perturbation data, EpiAgent predicts:
- Chromatin accessibility changes for **out-of-sample stimulated conditions** (e.g., cytokine treatment)
- Accessibility changes under **unseen genetic perturbations** (transcription factor knockouts)

**In silico CRE knockout**: EpiAgent can simulate the chromatin accessibility landscape resulting from deleting specific cis-regulatory elements, predicting downstream effects on cell state without experimental perturbation.

**Zero-shot cell type annotation**: EpiAgent can annotate cell types in new datasets without any labeled training examples, leveraging its pretrained understanding of epigenomic cell identity signatures.

**Reference data integration**: Enables mapping of query datasets onto reference atlases while preserving biological signal and reducing batch effects.

## Benchmark Results

EpiAgent outperforms specialized single-cell ATAC-seq tools across:
- **Unsupervised feature extraction**: Better UMAP clustering quality, ARI (Adjusted Rand Index) for cell type recovery
- **Supervised cell type annotation**: Higher accuracy than SNAP, Signac, ArchR, and other ATAC-specific tools
- **Data imputation**: Better recovery of true accessibility signals in dropout-simulated sparse data
- **Cross-dataset integration**: Better batch correction while preserving biological variation

## Why Epigenomics Needs Its Own Foundation Model

scRNA-seq models (Geneformer, scGPT) encode gene expression values, but:
- Gene expression is a downstream effector of chromatin accessibility
- cCREs (peak regions) and genes have different vocabularies and biological semantics
- The nearly binary nature and sparsity of ATAC-seq require different tokenization strategies
- Regulatory element interactions (enhancer-promoter looping) require specialized attention patterns

## Limitations

EpiAgent is trained only on human data and may not transfer to other species. The model's 28-dataset pretraining corpus is smaller than transcriptomics foundation models. Predicting perturbation effects requires external gene expression perturbation embeddings as auxiliary inputs, creating a dependency on complementary data.

## Citation

Chen X, Li K, Cui X, Wang Z, Jiang Q, Lin J, Li Z, Gao Z, Lv H, Jiang R. "EpiAgent: foundation model for single-cell epigenomics." Nature Methods (2025). DOI: 10.1038/s41592-025-02822-z

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Partial | EpiAgent predicts chromatin accessibility changes for out-of-sample stimulated conditions and unseen transcription factor knockouts, but requires external gene expression perturbation embeddings as auxiliary inputs. |
| Cross cell-line (gene intersection) | Partial | EpiAgent is evaluated on cross-dataset integration across 28 datasets and 31 tissues, but cross-cell-line perturbation generalization using shared cCRE vocabularies is not explicitly benchmarked. |
| Zero-shot unseen cell line (gene intersection) | Partial | Zero-shot cell type annotation is demonstrated, but zero-shot perturbation prediction on unseen cell lines without any data is not the primary claim. |
| Cross perturbation technology (gene intersection) | Not evaluated | EpiAgent focuses on epigenomic (ATAC-seq) data only; generalization across perturbation technologies (e.g., CRISPRi vs. cytokine treatment) is not evaluated. |
| Zero-shot gene misalignment | Not evaluated | EpiAgent operates on cis-regulatory elements (cCREs) rather than genes; misalignment across different cCRE vocabularies is not addressed. |
| Perturbation-specificity vs. simple baseline | Yes | EpiAgent outperforms specialized ATAC-seq tools (SNAP, Signac, ArchR) across unsupervised feature extraction, supervised annotation, and data imputation tasks. |

**Overall capability tier**: Specialist
