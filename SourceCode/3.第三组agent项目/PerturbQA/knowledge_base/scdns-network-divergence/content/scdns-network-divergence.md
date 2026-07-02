# scDNS: Network Divergence Analysis for Characterizing Gene Perturbations in Single Cells

## Overview

Most analyses of single-cell perturbation data focus on differential gene expression or differential cell abundance, but many biologically significant gene perturbations manifest primarily through **network rewiring**—changes in regulatory relationships rather than changes in transcript levels. scDNS (single-cell Differential Network Score) is a framework by Huang, Li, Fa et al. (Nature Communications 2026) that quantifies gene-specific functional perturbations by measuring information-theoretic divergence between condition-specific gene interaction network configurations, enabling discovery of regulatory programs that are invisible to expression-based analyses.

## Problem Being Solved

Gene functional shifts don't always cause mRNA abundance changes. Examples:
- **IRF4 T95R mutation**: Modifies DNA-binding affinity, restructuring target gene networks and causing immunodeficiency without necessarily changing IRF4 expression
- **TP53 mutations**: Reorganize transcriptional modules in lineage-specific ways
- **PKM2**: Changes interaction network upon EGFR-ERK pathway activation without changing expression

Existing tools (mixscape, CINEMA-OT, MELD) focus on differential expression or cell abundance, not on network rewiring. Cell populations undergoing perturbation may appear transcriptionally similar to controls in bulk while undergoing profound regulatory reorganization.

## Key Method: Network Divergence Scoring

**scDNS** quantifies how much a gene's **interaction network configuration** changes between conditions:

1. **Gene interaction network (GIN) construction**: For each condition (control vs. perturbed), construct a single-cell-resolved gene interaction network from co-expression patterns or regulatory signals. The network captures pairwise gene interaction strengths for each cell.

2. **Information-theoretic divergence**: For each gene, compute the **KL divergence** (or Jensen-Shannon divergence) between the distributions of its interaction patterns across conditions. A gene with high divergence has changed its regulatory relationships even if its own mRNA level is unchanged.

3. **Cell population assignment**: scDNS identifies which cell populations show the strongest network divergence for each perturbed gene, linking gene functional shifts to specific cellular states—not just aggregate changes.

**Mathematical formulation**: For gene g in condition c, the network configuration is characterized by the distribution of pairwise interaction strengths between g and all other genes across cells. The divergence D_g = KL(P_g^c1 || P_g^c2) quantifies the magnitude of network rewiring for gene g between conditions c1 and c2.

## Applications

**Immunodeficiency mutations**: scDNS identifies key regulatory changes in IRF4-mutant B cells that standard DE analysis misses, recovering known biology of B-cell maturation defects.

**Stimulus responses**: In cytokine stimulation experiments, scDNS identifies which regulatory programs are activated in different cell subpopulations, revealing heterogeneous responder states.

**Viral infection**: In SARS-CoV-2 infection data, scDNS prioritizes hidden regulatory programs activated specifically in infected cells, identifying antiviral response regulators not apparent from simple gene expression analysis.

**Pancreatic cancer - TIMM44 discovery**: In pancreatic cancer data, scDNS nominates **TIMM44** (a mitochondrial inner membrane translocase component) as a mitochondrial sensitizer that enhances gemcitabine efficacy. This prediction was validated experimentally: TIMM44 modulation increased cancer cell sensitivity to gemcitabine treatment. This represents a novel mechanistic target for improving standard-of-care chemotherapy.

## Main Results

- Simulation studies confirm scDNS prioritizes regulatory genes even when expression changes are minimal but network rewiring is pronounced
- False discovery rate control is better calibrated than expression-based methods in settings with network perturbations
- Identifies responder cell subpopulations with high sensitivity in heterogeneous datasets
- The TIMM44 discovery in pancreatic cancer is experimentally validated, demonstrating translational impact

## Limitations

scDNS requires sufficient cells per condition to estimate reliable gene interaction distributions. The approach is computationally intensive compared to simple DE analysis. It depends on the quality of single-cell network inference, which is affected by data sparsity.

## Citation

Huang C, Li Y, Fa B, Zhu J, Liu Z, Ma Y, Zhang Z, Xu Y, Xu Q, Xiao Z. "Characterizing gene perturbations in single cells via network divergence analysis." Nature Communications (2026). DOI: 10.1038/s41467-026-71507-8

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | scDNS quantifies network divergence in observed perturbation data; it does not predict transcriptional responses to perturbations not yet measured experimentally. |
| Cross cell-line (gene intersection) | Not evaluated | scDNS is an analysis framework for characterizing gene network changes within experimental datasets; cross-cell-line generalization is not a relevant capability. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | scDNS requires single-cell data from both control and perturbed conditions to compute network divergence scores; zero-shot prediction is not applicable. |
| Cross perturbation technology (gene intersection) | Not evaluated | scDNS is evaluated across different biological applications (mutations, cytokine stimulation, viral infection) but cross-technology generalization in the perturbation prediction sense is not relevant. |
| Zero-shot gene misalignment | Not evaluated | scDNS operates on the gene interaction network from the experimental data; gene vocabulary misalignment is not a relevant scenario. |
| Perturbation-specificity vs. simple baseline | Yes | scDNS identifies regulatory changes (e.g., in IRF4-mutant B cells and TIMM44 in pancreatic cancer) invisible to standard differential expression analysis, with experimental validation of key predictions. |

**Overall capability tier**: Benchmark-tool
