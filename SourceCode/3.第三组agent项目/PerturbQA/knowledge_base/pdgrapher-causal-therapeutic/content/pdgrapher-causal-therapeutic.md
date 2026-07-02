# PDGrapher: Causally Inspired GNN for Combinatorial Therapeutic Perturbation Prediction

## Overview

PDGrapher (Phenotype-Driven Grapher) is a graph neural network model that solves the inverse perturbation problem: given a diseased gene expression state, predict which set of therapeutic targets (perturbagens) would reverse the disease phenotype toward a healthy state. Gonzalez, Lin et al. (Nature Biomedical Engineering 2025) introduce this causally inspired approach that directly predicts combinatorial perturbagens without exhaustively screening all possible perturbations, making it up to 25× faster than existing indirect approaches.

## Problem Being Solved

Two dominant paradigms in drug discovery:
1. **Target-driven**: Design drugs against specific molecular targets
2. **Phenotype-driven**: Identify compounds that reverse disease phenotypes without predefined targets

Existing phenotype-driven approaches rely on libraries (CMap, LINCS) and work by: (1) predicting gene expression responses to all perturbations in the library, then (2) identifying perturbagens that produce the desired expression profile. This is indirect and computationally intensive—CellOT takes 10 hours to train for a single perturbagen in one cell line.

**PDGrapher solves the inverse problem directly**: Given a diseased gene expression profile, directly predict the perturbagen (set of gene targets) that would shift the expression toward treated states.

## Causal Framework and Architecture

PDGrapher uses a causal model where:
- **Nodes**: Genes in the causal graph
- **Edges**: Structural causal equations defining gene regulatory relationships
- **Proxy causal graphs**: PPI (protein-protein interaction) networks from BIOGRID or GRNs (gene regulatory networks) inferred by GENIE3

**Architecture**:
1. **Disease cell state encoder**: Embeds the diseased gene expression profile using a GNN that operates on the causal graph
2. **Treatment state encoder**: Embeds the treated gene expression profile similarly
3. **Perturbagen predictor**: A learned mapping from the diseased latent representation to a predicted set of gene targets (perturbagen)

Training uses paired disease-treatment data, where the model learns which gene targets best explain the transition from diseased to treated gene expression profiles. The model operates under the assumption of no unobserved confounders.

## Evaluation Design

The authors evaluate across **38 datasets** spanning:
- 2 intervention types: chemical (multi-gene) and genetic (single-gene CRISPR knockout)
- 11 cancer types: lung (A549), breast (MCF7, MDAMB231, BT20), prostate (PC3, VCAP), colon (HT29), skin (A375), cervical (HELA), ovary (ES2), head/neck (BICR6), pancreas (YAPC), stomach (AGS), brain (U251MG)
- 2 causal graph types: PPI networks and GRNs
- Both same-cell-line held-out samples and cross-cancer-type generalization

## Main Results

**Chemical perturbation datasets**: PDGrapher identifies effective perturbagens in more test samples (detects up to **13.37% more** ground-truth therapeutic targets than competing methods). Predicted targets are on average up to **11.58% closer** to ground-truth targets in the gene interaction network than random.

**Genetic perturbation datasets**: PDGrapher shows competitive performance, detecting up to 1.09% more ground-truth targets.

**Speed**: PDGrapher trains up to **25× faster** than indirect methods (scGen, CellOT) that require building separate models per perturbagen.

**Cross-cancer-type generalization**: PDGrapher maintains robust performance even on cancer types never seen during training.

**Interpretability**: PDGrapher reveals MoA for clinical drugs:
- Vorinostat (HDAC inhibitor): Identifies histone deacetylase targets
- Sorafenib (multikinase inhibitor): Captures multi-target kinase interactions
- Highlights KDR (VEGFR2) as a key target for non-small cell lung cancer, validated by multiple approved drugs (vandetanib, sorafenib, rivoceranib)

## Limitations

PDGrapher assumes no unobserved confounders—a strong causal assumption that may not hold in complex disease biology. The model uses PPI or GRN proxies for the true causal graph, introducing approximation errors. Performance on identifying entirely novel drug targets (not in training libraries) requires separate validation. Chemical perturbagen datasets are less directly applicable than genetic ones, since chemical compounds affect multiple genes simultaneously.

## Citation

Gonzalez G, Lin X, Herath I, Veselkov K, Bronstein M, Zitnik M. "Combinatorial prediction of therapeutic perturbations using causally inspired neural networks." Nature Biomedical Engineering (2025). DOI: 10.1038/s41551-025-01481-x

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | PDGrapher's inverse formulation predicts perturbagens not seen during training by learning causal mapping from disease state to therapeutic targets. |
| Cross cell-line (gene intersection) | Yes | The model is evaluated across 11 cancer types and demonstrates cross-cancer-type generalization using shared gene interaction graphs (PPI/GRN). |
| Zero-shot unseen cell line (gene intersection) | Partial | PDGrapher maintains robust performance on cancer types never seen during training, but benefits from shared causal graph structure rather than being strictly zero-shot. |
| Cross perturbation technology (gene intersection) | Partial | The model is evaluated on both chemical and genetic (CRISPR knockout) perturbations within one framework, though training on one technology and predicting another is not the primary design. |
| Zero-shot gene misalignment | No | PDGrapher relies on shared PPI or GRN graphs; completely disjoint gene vocabularies would break the causal graph structure. |
| Perturbation-specificity vs. simple baseline | Yes | PDGrapher identifies up to 13.37% more ground-truth therapeutic targets than competing methods, with predicted targets closer to ground-truth in the gene interaction network. |

**Overall capability tier**: Specialist
