# CellFM: 800M-Parameter Foundation Model Pretrained on 100 Million Human Cells

## Overview

CellFM is a large-scale single-cell foundation model with 800 million parameters pretrained on approximately 100 million human cells from diverse tissues and diseases. Zeng et al. (Nature Communications 2025) address the key gap in existing single-species models (typically 50M cells, <100M parameters) by curating a unified dataset and training a significantly larger model using the ERetNet (Extended Recurrent Retention Network) architecture on the MindSpore framework with Huawei Ascend910 NPUs.

## Problem Being Solved

Single-cell foundation models face several challenges:
1. **Data heterogeneity**: Single-cell datasets are stored in diverse formats (FASTQ, h5ad, Seurat objects, 10x Genomics) across scattered repositories
2. **Scale limitation**: Prior human-only models were limited to ~50M cells; larger corpora required multi-species mixing
3. **Model capacity**: With <100M parameters, prior models may underfit the complexity of the full transcriptome
4. **Efficiency-performance trade-off**: Transformers have quadratic attention complexity; scaling requires architectural innovations

## Dataset: 100 Million Human Cells

The authors curated datasets from:
- NCBI GEO, European Nucleotide Archive (ENA), Genome Sequence Archive (GSA), ImmPort
- Raw FASTQ processed through manufacturer software + SynEcoSys® standardization pipeline
- Quality control filtering, HGNC gene name standardization, unified sparse matrix format
- **Final dataset**: 19,914 samples, 102,304,686 human cells
- **Cell type composition**: ~70M annotated cells including T cells (19.2M), mononuclear phagocytes (7.01M), neurons (6.29M), fibroblasts (3M)
- **Disease diversity**: 46.3M normal cells, 7.1M viral infection, 3.5M lung cancer, and more

## Architecture: ERetNet

CellFM uses a **value-projection-based** pretraining strategy (unlike rank-based Geneformer or bin-based scGPT):

**Core: ERetNet (Extended Recurrent Retention Network)**
- A Transformer variant with **linear complexity** in sequence length, enabling efficient processing of the ~20,000-gene input
- Each ERetNet block integrates: Multi-Head Attention (MHA), Simple Gated Linear Unit (SGLU), Layer Normalization (LN)
- Linear complexity is critical for scaling to full-transcriptome representation

**Embedding module**: Converts scalar gene expression values into initial token vectors (each gene × its expression value)

**Low-Rank Adaptation (LoRA)**: Applied during fine-tuning to minimize the number of trainable parameters while adapting the 800M-parameter model to downstream tasks

**Pretraining objective**: Value projection—the model recovers vector embeddings of masked genes derived from their linear projections based on gene expression values. Unlike bin-based approaches, this preserves full resolution of expression values.

## Training Infrastructure

Trained on Huawei MindSpore AI framework using 4× Huawei Atlas800 servers (each with 8× Ascend910 NPUs = 32 NPUs total). This represents a significant deviation from standard PyTorch/CUDA implementations.

## Main Results

CellFM outperforms existing models (scGPT, Geneformer, scFoundation, GeneCompass, UCE) across:

**Cell type annotation**: Highest accuracy on held-out cell type classification tasks, leveraging the 800M parameters to learn fine-grained cell state distinctions

**Perturbation prediction**: Superior prediction of post-perturbation gene expression changes compared to smaller foundation models and task-specific baselines

**Gene function prediction**: Better encoding of gene functional information as inferred by gene ontology term recovery and gene module coherence

**Gene-gene relationship inference**: More accurate capture of known co-expression and regulatory relationships

The authors observe clear scaling benefits—CellFM's performance advantage is most pronounced in tasks requiring nuanced cell state distinctions, consistent with the expectation that larger models capture more complex regulatory patterns.

## Limitations

CellFM is human-only (no cross-species generalization). The MindSpore/Ascend framework may limit reproducibility for researchers using standard PyTorch/CUDA pipelines. The ERetNet architecture is less widely validated than standard Transformer architectures. LoRA-based fine-tuning may not capture all task-specific adaptation.

## Citation

Zeng Y, Xie J, Shangguan N, Wei Z, Li W, Su Y, Yang S, Zhang C, Zhang J, Fang N, Zhang H, Lu Y, Zhao H, Fan J, Yu W, Yang Y. "CellFM: a large-scale foundation model pretrained on transcriptomics of 100 million human cells." Nature Communications 16, 4679 (2025). DOI: 10.1038/s41467-025-59926-5

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | CellFM demonstrates superior perturbation prediction of post-perturbation gene expression changes compared to smaller foundation models and task-specific baselines. |
| Cross cell-line (gene intersection) | Partial | CellFM is pretrained on diverse human tissues and cell types, enabling broad transfer, but explicit cross-cell-line perturbation benchmarks are not the primary focus. |
| Zero-shot unseen cell line (gene intersection) | Partial | The model's pretraining on 100M human cells from diverse tissues provides general representations, but zero-shot perturbation prediction on completely unseen cell lines is not explicitly evaluated. |
| Cross perturbation technology (gene intersection) | Not evaluated | The paper does not evaluate training on one perturbation technology and predicting on another. |
| Zero-shot gene misalignment | No | CellFM operates on a fixed human HGNC gene vocabulary; cross-species or completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | CellFM outperforms scGPT, Geneformer, scFoundation, GeneCompass, and UCE on perturbation prediction tasks, with advantages most pronounced in tasks requiring nuanced cell state distinctions. |

**Overall capability tier**: Foundation
