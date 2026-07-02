# Gene Regulatory Network Inference from Perturbation Data

## Overview

Gene regulatory networks (GRNs) model the directional regulatory relationships between transcription factors (TFs) and their target genes. Perturbation data—especially from Perturb-seq—provides uniquely powerful causal information for GRN inference, since each genetic perturbation acts as an experimental intervention rather than a mere observation.

## Why Perturbation Data Improves GRN Inference

Observational single-cell data (standard scRNA-seq) suffers from:
- Confounding: correlated expression can reflect shared upstream regulators, not direct regulation
- Non-identifiability: impossible to distinguish A→B from B→A from A←C→B by correlation alone

Perturbation data provides **interventional** observations:
- Knocking out gene A while measuring the downstream effects isolates A's direct and indirect targets
- This breaks the identifiability problem for directed edge inference
- Many perturbations measured simultaneously (Perturb-seq) provide a rich causal dataset

## Key Methods

### SCENIC/SCENIC+
- **Approach**: Co-expression-based GRN + cis-regulatory motif validation
- **Step 1**: Identify co-expression modules (regulons) via GENIE3 (Random Forest) or GRNBoost2
- **Step 2**: Prune edges using cis-regulatory element (CRE) analysis: keep only TF-target pairs where the TF's binding motif is enriched in accessible chromatin near the target gene
- **SCENIC+**: extends to multiome data (scRNA + scATAC-seq) for improved accuracy
- **Output**: Transcription factor regulons with associated target genes and binding sites

### GENIE3 (GEne Network Inference with Ensemble of trees)
- Uses feature importance from Random Forests to rank candidate regulatory edges
- Treats each gene as the regression target, with all other genes as features
- The contribution of gene j to predicting gene i implies a regulatory relationship

### Causal Graph Inference
- **NOTEARS**: optimizes a continuous DAG constraint to learn directed acyclic graphs from expression data
- **DAG-GNN**: graph neural network that learns DAG structure
- **UT-IGSP**: uses interventional data (perturbations) to improve DAG inference

### Perturbation-Specific Approaches
Norman et al. (2019) developed analysis approaches for the 287-perturbation CRISPRa dataset:
- **PhenoGraph**: clusters cells into phenotypic groups based on expression
- **Expression manifold**: UMAP embedding of perturbation centroids reveals structure of the transcriptional response space
- **Genetic interaction classification**: compares double perturbation phenotype to single perturbations to classify interaction type

## Genetic Interaction Classification

For each gene pair (A, B) with double perturbation AB, compute:
- **Expected AB** = A_effect + B_effect (additive expectation)
- **Observed AB** = measured double-perturbation effect
- **Interaction score** = Observed AB − Expected AB

| Category | Score | Interpretation |
|----------|-------|---------------|
| Additive | ≈ 0 | Genes act independently |
| Synergistic | << 0 | Double KO worse than additive (synthetic lethal) |
| Suppressive | >> 0 | Double KO better than additive (buffering) |
| Epistatic | Complex | One gene's effect masks another's |

## Downstream GRN Analysis

### Identifying Regulatory Hubs
- Transcription factors appearing as regulators of many genes = master regulators
- Examples in K562 cells: GATA1 (erythroid program), TAL1 (hematopoiesis), SP1 (housekeeping)

### Pathway Enrichment of Regulons
- Run GO enrichment or KEGG pathway analysis on each TF's target gene set
- Identifies which biological programs each TF controls

### Network Visualization
- Cytoscape or NetworkX for static network visualization
- SPRING or ForceAtlas2 for dynamic layouts
- Highlight hub nodes, feedback loops, and feed-forward motifs

## Benchmarking GRN Inference

The BEELINE benchmark (Pratapa et al. 2020) evaluated 12 GRN methods on synthetic and curated networks:
- Best performers: GENIE3, GRNBOOST2, PIDC
- Using perturbation data consistently improves performance over observational data alone
- No single method dominates across all network types

## Practical Recommendations

1. For **small datasets** (<5000 cells, <100 genes): SCENIC or correlation-based methods
2. For **large Perturb-seq datasets**: causal inference methods (UT-IGSP, DCDI) that explicitly use interventional structure
3. For **TF-target inference**: SCENIC+ with paired scRNA + scATAC data
4. For **network visualization**: focus on high-confidence edges (top 10% by score)
5. For **validation**: cross-validate predicted edges against ChIP-seq or CUT&RUN data for key TFs
