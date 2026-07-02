# RegFormer: Mamba-Based Single-Cell Foundation Model with Gene Regulatory Hierarchies

## Overview

RegFormer is a single-cell foundation model that integrates gene regulatory networks (GRNs) with Mamba-based state-space modeling to overcome the scalability and context-length limitations of Transformer architectures. Hu et al. (Nature Communications 2026) pretrain RegFormer on 25 million human single cells spanning 45 tissues, demonstrating superior performance over scGPT, Geneformer, scFoundation, and scBERT on clustering, batch integration, cell type annotation, perturbation prediction, and drug response prediction.

## Problem Being Solved

Current single-cell foundation models (scGPT, Geneformer, scFoundation, scBERT) suffer from:
1. **Transformer scalability**: The quadratic attention complexity limits practical input length to 2,000-4,096 genes per cell, excluding lowly expressed but functionally important genes
2. **Lack of regulatory priors**: Models treat genes as unstructured sequences (analogous to NLP words) without incorporating the hierarchical regulatory relationships between genes
3. **Data sparsity handling**: Single-cell data is extremely sparse; models without sparsity-aware design struggle to learn from noisy, incomplete observations
4. **Unordered gene sequences**: Unlike natural language, gene expression lacks inherent ordering, making sequence-based models suboptimal

## Architecture: Regulatory-Informed Mamba Foundation

**Dual gene embeddings** for each gene token:
- **Value embedding**: A quantitative representation of the gene's expression level (continuous value)
- **Token embedding**: A regulatory identity representation capturing the gene's role in regulatory networks

These two embeddings provide complementary information—how much a gene is expressed AND what regulatory role it plays.

**GRN-guided gene ordering**: Genes are organized in a regulatory hierarchy:
- Top-level: Master transcription regulators
- Mid-level: Signaling pathway components
- Low-level: Effector genes

This hierarchical ordering provides meaningful structure for the Mamba state-space model to process, unlike arbitrary ordering in other models.

**Mamba backbone (State Space Model)**:
- Replaces the Transformer's attention mechanism with selective state space models
- **Linear complexity** in sequence length: O(n) vs. O(n²) for Transformers
- Can process much longer gene sequences, capturing more regulatory context
- Selective mechanism allows the model to dynamically prioritize relevant gene signals
- Designed by Gu and Dao (2023); here adapted for single-cell biology

**Pretraining**: Masked gene expression prediction on 25 million human cells from 45 tissues. The GRN ordering and dual embeddings guide the model to learn regulatory relationships naturally.

## Main Results

**Clustering accuracy**: RegFormer achieves higher ARI (Adjusted Rand Index) on held-out cell type clustering than all compared foundation models (scGPT, Geneformer, scFoundation, scBERT) across multiple benchmarking datasets.

**Batch integration**: Better harmony between biological variation preservation and batch effect removal (higher NMI, lower KBET batch mixing).

**Cell type annotation**: More precise cell type classification with fewer labeled examples needed (better few-shot performance).

**GRN reconstruction**: Biologically coherent gene regulatory network reconstruction—predicted GRNs better recover experimentally validated regulatory interactions compared to models without regulatory priors.

**Perturbation prediction**: More accurate prediction of transcriptional responses to genetic perturbations, particularly for genes in regulatory hierarchies (transcription factor targets).

**Drug response prediction**: Improved prediction of cancer cell line drug responses across diverse compounds.

## Why Mamba for Single-Cell Biology

The Mamba selective state-space model is particularly suited for scRNA-seq because:
1. Single-cell "sequences" (ordered genes) can be very long—up to 20,000 genes—requiring linear complexity
2. The selective mechanism helps ignore sparse/noisy zero-expression signals
3. State-space models naturally handle sequential regulatory cascades (TF → target → effector)
4. Linear complexity enables full-genome context without the truncation required by Transformers

## Limitations

RegFormer is pretrained only on human data. The GRN-guided ordering requires a reference GRN, which introduces assumptions about which regulatory relationships are most important. Mamba's sequential processing may miss long-range regulatory interactions that bidirectional attention captures. Performance advantages over other foundation models vary by task and dataset.

## Citation

Hu L, Qin H, Zhang Y, Lu Y, Qiu P, Guo Z, Cao L, Jiang W, Shen Y, Chen Q, Shang Y, Xia T, Deng Z, Zhao H, Xu X, Fang S, Li Y, Zhang Y. "RegFormer: a single-cell foundation model powered by gene regulatory hierarchies." Nature Communications (2026). DOI: 10.1038/s41467-026-72198-x

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | RegFormer demonstrates more accurate prediction of transcriptional responses to genetic perturbations compared to scGPT, Geneformer, scFoundation, and scBERT. |
| Cross cell-line (gene intersection) | Partial | Pretrained on 25M human cells from 45 tissues, RegFormer transfers to diverse cellular contexts, but explicit cross-cell-line perturbation generalization benchmarks are not the primary focus. |
| Zero-shot unseen cell line (gene intersection) | Partial | The model's pretraining and GRN-guided representations enable broad transfer, but zero-shot perturbation prediction for completely unseen cell lines is not explicitly evaluated. |
| Cross perturbation technology (gene intersection) | Not evaluated | The paper evaluates genetic perturbation prediction and drug response prediction separately but does not test cross-technology transfer. |
| Zero-shot gene misalignment | No | RegFormer uses a fixed human gene vocabulary with GRN-guided ordering; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | RegFormer achieves higher perturbation prediction accuracy and improved drug response prediction compared to all compared foundation models across multiple benchmarking datasets. |

**Overall capability tier**: Foundation
