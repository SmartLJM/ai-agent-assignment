# scGPT: Foundation Model for Single-Cell Multi-omics

## Overview

scGPT (Cui et al., Nature Methods 2024) is a large-scale transformer-based foundation model for single-cell biology, pre-trained on over 33 million human single-cell RNA-seq profiles. It introduces a generative pre-training approach with specialized masked attention mechanisms suited to the sparse, high-dimensional nature of single-cell gene expression data, then fine-tunes on downstream tasks including perturbation response prediction, batch correction, cell type annotation, and multi-omics integration.

## Key Innovations

### Architecture
- **Generative Pre-training**: scGPT is trained to predict masked gene expression values autoregressively, processing gene tokens (gene identity + expression magnitude) with a transformer decoder.
- **Masked Attention**: Specialized attention masks ensure the model attends to the correct subset of genes during different pre-training objectives (cell-level masking, gene-level masking).
- **Gene Embeddings**: Each gene is represented as a learned embedding combining its identity (gene token) and its continuous expression level (value token), enabling the model to reason about expression magnitudes.
- **Cell Embeddings**: Global cell representations are extracted from the transformer output for downstream tasks.

### Pre-training Data
- **33 million cells**: Drawn from human cell atlas and other large-scale single-cell datasets spanning diverse tissues and cell types.
- **Self-supervised objectives**: Masked gene expression prediction, forcing the model to learn regulatory dependencies between genes.

## Perturbation Prediction Capability

scGPT is fine-tuned for perturbation prediction using Perturb-seq datasets:
- **Datasets**: Adamson et al. (2016, unfolded protein response, 105 perturbations) and Norman et al. (2019, combinatorial perturbations, 287 perturbation conditions).
- **Approach**: After fine-tuning, the model predicts the mean post-perturbation gene expression profile from the unperturbed control state plus the identity of the knocked-out gene.
- **Performance**: scGPT achieves competitive performance compared to GEARS and CPA on single-gene perturbations, with particularly strong performance on the Adamson dataset.

## Advantages Over Prior Methods

1. **Transfer Learning**: Unlike GEARS (which trains from scratch) or CPA (which uses no biological prior), scGPT brings large-scale pre-trained biological knowledge.
2. **Multi-task**: The same pre-trained backbone handles perturbation prediction, batch correction, cell type annotation, and multi-omics alignment.
3. **Scalability**: Foundation model paradigm allows rapid adaptation to new datasets with limited perturbation data.

## Limitations

1. **Perturbation suppression**: As shown by Jiang et al. (2026, PerturbedVAE), foundation models like scGPT encode perturbation-invariant cellular programs that dominate representations, causing perturbation-specific signals (which are sparse) to be suppressed.
2. **Linear probing**: FMs including scGPT show weaker linear decodability of perturbation labels than a simple PCA baseline, suggesting limited accessibility of perturbation-related information.
3. **Linear baselines**: Ahlmann-Eltze et al. (2025) showed that on Norman and Replogle datasets, scGPT does not significantly outperform simple additive linear models when using well-controlled evaluation metrics.
4. **Single-cell heterogeneity**: Like most mean-prediction models, scGPT predicts population-average responses and struggles with the inherent heterogeneity of single-cell measurements.

## Comparison with Other Models

| Model | Approach | Key Strength |
|-------|----------|--------------|
| scGPT | Foundation model (33M cells) | Transfer learning, multi-task |
| GEARS | GNN + GO/co-expression graph | Combinatorial prediction, biological interpretability |
| CPA | Compositional VAE | Drug/covariate compositionality |
| Scouter | LLM embeddings (GenePT) | Semantic gene knowledge without graphs |

## Downstream Applications

Beyond perturbation prediction, scGPT has been applied to:
- **Batch correction**: Harmonizing data across experimental conditions
- **Cell type annotation**: Predicting cell identities in new datasets
- **Multi-omics**: Integrating scRNA-seq with ATAC-seq
- **GRN inference**: Deriving gene regulatory relationships from attention weights

## Citations

Cui B et al. (2024). scGPT: Toward Building a Foundation Model for Single-Cell Multi-omics Using Generative AI. *Nature Methods*, doi:10.1038/s41592-024-02201-0.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | scGPT is fine-tuned for perturbation prediction on Adamson and Norman datasets, achieving competitive performance compared to GEARS and CPA on held-out single-gene perturbations. |
| Cross cell-line (gene intersection) | Partial | The 33M-cell pre-training corpus spans diverse cell types, enabling transfer via fine-tuning across cell contexts, though explicit cross-cell-line perturbation transfer with gene intersection is not the primary evaluation. |
| Zero-shot unseen cell line (gene intersection) | Partial | scGPT's pre-trained representations encode broad cell-state knowledge, enabling partial zero-shot adaptation; however, full perturbation prediction without any fine-tuning on the new cell line is not demonstrated. |
| Cross perturbation technology (gene intersection) | No | scGPT perturbation fine-tuning focuses on CRISPR knockouts; no cross-technology transfer between perturbation modalities is evaluated. |
| Zero-shot gene misalignment | Yes | scGPT's masked attention mechanism allows processing arbitrary gene subsets, enabling prediction into different gene vocabularies without re-training on the full gene set. |
| Perturbation-specificity vs. simple baseline | No | Ahlmann-Eltze et al. (2025) showed that scGPT does not significantly outperform simple additive linear models on Norman and Replogle datasets under well-controlled evaluation metrics. |

**Overall capability tier**: Foundation
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
