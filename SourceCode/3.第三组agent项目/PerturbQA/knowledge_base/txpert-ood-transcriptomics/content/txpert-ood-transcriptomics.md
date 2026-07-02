# TxPert: Multi-Graph GNN for OOD Transcriptomic Perturbation Prediction

## Overview

TxPert (Wenkel et al., 2025; from Valence Labs/Recursion) addresses out-of-distribution (OOD) transcriptomic perturbation prediction by building a multi-graph GNN that integrates multiple complementary sources of biochemical knowledge. The central thesis is that accurate OOD prediction requires combining protein-protein interactions, functional annotations, pathway maps, and transcriptomic maps into a unified multi-graph representation.

## Problem: OOD Generalization

The core challenge in perturbation prediction is generalizing to genes never seen during training. Three OOD settings are defined:
1. **Unseen gene perturbations**: The perturbed gene has no training data
2. **New cell type**: The cell type context is different from training
3. **Unseen gene + new context**: Combined OOD condition

Most models (GEARS, CPA, scGPT) struggle significantly under strict OOD settings where the target gene has no training examples.

## Multi-Graph Architecture

TxPert builds four complementary biological graphs:

### 1. STRINGdb (Protein-Protein Interaction)
- Physical and functional protein interactions
- Confidence-weighted edges from experimental evidence
- Captures direct molecular interactions relevant to perturbation propagation

### 2. Gene Ontology (GO)
- Hierarchical biological process, molecular function, and cellular component annotations
- Shared GO terms connect functionally related genes
- Provides functional context for unknown perturbation targets

### 3. PxMap (Phenotypic Map)
- Gene-phenotype associations from large-scale genetic studies
- Connects genes that produce similar phenotypes when perturbed
- Enables prediction based on phenotypic similarity

### 4. TxMap (Transcriptomic Map)
- Transcriptomic similarity between gene perturbation profiles
- Genes with similar transcriptomic signatures share regulatory mechanisms
- Derived from existing Perturb-seq datasets

## Model Architecture

### Basal State Encoder
Encodes the unperturbed cell gene expression profile into a latent cell state representation, capturing cell-type identity and baseline regulatory state.

### GNN Perturbation Encoder
A graph neural network propagates perturbation information across all four graphs simultaneously:
- Each graph provides different structural information
- Messages from all four graphs are aggregated
- The perturbation representation is the gene node embedding after multi-graph propagation

### Prediction Head
Combines the basal state and GNN-derived perturbation embedding to predict post-perturbation expression.

## OOD Performance

TxPert achieves state-of-the-art on three OOD tasks:
- **Unseen perturbations**: Significantly outperforms GEARS and CPA
- **New cell types**: Better generalization through multi-graph knowledge
- **Combined OOD**: Largest gains when both gene and context are novel

The multi-graph approach is particularly important for OOD scenarios: when a gene has no training data, its multi-graph neighborhood provides rich prior information about likely effects.

## Comparison with GEARS

| Aspect | TxPert | GEARS |
|--------|--------|-------|
| Graphs | 4 (STRING, GO, PxMap, TxMap) | 2 (GO, co-expression) |
| OOD focus | Explicit OOD benchmarks | Combinatorial (seen genes) |
| Cell state encoding | Explicit basal encoder | Implicit in architecture |
| Institution | Valence Labs / Recursion | Stanford |

## Key Findings

1. All four graphs contribute; removing any one degrades OOD performance
2. TxMap (transcriptomic similarity) is most informative for seen-gene generalization
3. GO and STRINGdb are most critical for truly unseen (zero-shot) genes
4. PxMap adds unique phenotypic information not captured by other graphs

## Limitations

1. **Graph quality dependency**: Performance depends on completeness and accuracy of the four biological databases
2. **Mean-collapse**: Like other methods, TxPert still predicts population averages and struggles with capturing single-cell heterogeneity
3. **Computational overhead**: Four separate GNN computations increase inference cost

## Citations

Wenkel F et al. (2025). TxPert: Leveraging Biochemical Relationships for Out-of-Distribution Transcriptomic Perturbation Prediction. *arXiv:2505.14919*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | TxPert explicitly benchmarks unseen gene perturbations (genes with no training data) and achieves 8-25% improvement over GEARS and CPA under strict OOD conditions. |
| Cross cell-line (gene intersection) | Yes | TxPert evaluates "new cell type" generalization as one of its three OOD settings, testing transfer from Norman (K562) to RPE1 cell line contexts. |
| Zero-shot unseen cell line (gene intersection) | No | While TxPert tests new cell types, it requires at least some context representation; fully zero-shot prediction with no training data from the target cell line is not the primary claim. |
| Cross perturbation technology (gene intersection) | No | TxPert focuses on CRISPR genetic knockouts; no cross-technology transfer between perturbation modalities is evaluated. |
| Zero-shot gene misalignment | No | TxPert's multi-graph GNN requires genes to be present in the shared STRING/GO/PxMap/TxMap vocabulary; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | TxPert achieves 8-25% improvement over existing methods including GEARS and CPA across unseen perturbation OOD scenarios, and all four graphs contribute additively to perturbation-specific performance. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
