# GeneCompass: Knowledge-Informed Cross-Species Foundation Model for Gene Regulation

## Overview

GeneCompass is a cross-species single-cell foundation model pretrained on 101.76 million human and mouse single-cell transcriptomes, incorporating four types of biological prior knowledge. Yang et al. (Cell Research 2024) demonstrate that integrating structured biological knowledge with large-scale self-supervised learning on cross-species data enables superior understanding of universal gene regulatory mechanisms, achieving state-of-the-art performance across diverse downstream tasks and successfully predicting cell fate regulators experimentally validated in human embryonic stem cells.

## Problem Being Solved

Existing single-cell foundation models (scGPT, Geneformer, UCE, scFoundation) have two critical limitations:
1. They rely on a single species (primarily human), missing the opportunity to leverage conserved regulatory mechanisms across species
2. They do not incorporate structured biological prior knowledge (gene networks, promoter sequences, gene families), relying solely on expression patterns

Cross-species integration offers major advantages: regulatory mechanisms are highly conserved between mouse and human, and mouse data is more experimentally tractable (genetic manipulations, developmental time courses), providing complementary perspectives.

## Dataset: scCompass-126M

- Raw collection: 126 million human and mouse single-cell transcriptomes
- After quality control: **101,768,420 cells** used for pretraining
- Human-mouse gene alignment: 17,465 homologous genes represented by human Ensembl IDs; species-specific genes labeled separately
- Broad tissue and cell type coverage across development, disease, and normal tissues

## Architecture and Prior Knowledge Integration

**Input representation**: Combines rank-based gene encoding (top 2,048 genes sorted by expression, following Geneformer) with absolute expression values (stronger supervised constraint).

**Four types of integrated prior knowledge** (each encoded into a unified embedding space):

1. **Gene Regulatory Network (GRN)**: Known transcription factor-target gene relationships, encoding regulatory hierarchies
2. **Promoter sequences**: DNA sequence features near gene transcription start sites, capturing regulatory element information
3. **Gene family annotation**: Genes grouped by structural/functional families, encoding evolutionary relationships
4. **Gene co-expression relationships**: Known co-expression patterns from databases, encoding functional associations

A species token prepended to each cell enables the model to distinguish human vs. mouse contexts during pretraining.

**Pretraining task**: Masked language modeling strategy masks 15% of gene inputs and requires recovery of both gene IDs and expression values simultaneously, providing stronger supervision than expression-only recovery.

**Architecture**: 12-layer transformer framework, ~100 million parameters. The model uses self-attention to encode cells with context-aware gene representations.

## Key Results

**Cross-species gene embedding validation**: GeneCompass's gene embeddings show significantly higher cosine similarity between homologous human-mouse gene pairs than non-homologous genes—validated across B cells, hepatocytes, macrophages, and other cell types. This demonstrates successful capture of evolutionary conservation.

**Cross-species downstream tasks**:
- Cell type annotation: Outperforms or matches state-of-the-art single-species models
- Gene perturbation simulation: Better prediction of transcriptional changes after perturbation
- Drug target prediction: Identified candidate targets validated by literature
- GRN inference: More accurate reconstruction of known regulatory relationships

**Cell fate prediction experiment**: GeneCompass was used to predict transcription factors driving gonadal cell fate in human embryonic stem cells. The **predicted candidate genes were experimentally validated** to successfully induce gonadal differentiation—a direct functional validation of the model's regulatory understanding.

## Comparison to Other Foundation Models

| Model | Species | Training cells | Prior knowledge | Parameters |
|-------|---------|----------------|-----------------|------------|
| Geneformer | Human | 30M → 104M | None | 40M |
| scGPT | Human | 33M | None | - |
| scFoundation | Human | 50M | None | 100M |
| UCE | Human+Mouse+... | 36M | Protein LM | 650M |
| **GeneCompass** | **Human+Mouse** | **101.76M** | **4 types** | **100M** |

## Limitations

The model was validated primarily on mouse and human—generalization to other organisms requires further work. The homologous gene alignment excludes species-specific genes (17,465 of 36,092 total). The incorporation of four prior knowledge types adds complexity to pretraining but may not always outperform simpler models on tasks where prior knowledge is irrelevant.

## Citation

Yang X, Liu G, Feng G, Bu D, Wang P, Jiang J, Chen S, Yang Q, Miao H, ... Guo J, Zhao Y, Zhou Y, Li F, Liu J, Chen Y, Yang G, Li X. "GeneCompass: deciphering universal gene regulatory mechanisms with a knowledge-informed cross-species foundation model." Cell Research 34, 830–845 (2024). DOI: 10.1038/s41422-024-01034-y

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | GeneCompass demonstrates better prediction of transcriptional changes after genetic perturbations compared to single-species models in benchmark evaluations. |
| Cross cell-line (gene intersection) | Yes | Pretrained on 101.76M human and mouse cells across diverse tissues, GeneCompass transfers to new cell lines using 17,465 shared homologous gene representations. |
| Zero-shot unseen cell line (gene intersection) | Partial | The model's cross-species pretraining enables transfer to new cellular contexts, but explicitly zero-shot unseen cell line perturbation prediction is not separately benchmarked. |
| Cross perturbation technology (gene intersection) | Not evaluated | The paper evaluates gene perturbation simulation but does not test training on one perturbation technology and predicting on another. |
| Zero-shot gene misalignment | No | GeneCompass requires species-aligned homologous gene vocabularies; completely disjoint gene sets between train and test are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | GeneCompass outperforms single-species foundation models on gene perturbation simulation and drug target prediction tasks, with experimental validation of cell fate regulator predictions. |

**Overall capability tier**: Foundation
