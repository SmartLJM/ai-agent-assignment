# scBIG: Module-Inductive Representations for Gene Perturbation Prediction

## Overview

scBIG (Ruan et al., 2026) is a module-inductive perturbation prediction framework that explicitly models coordinated, program-level transcriptional changes rather than treating genes as independent units. The core insight is that genetic perturbations activate coherent gene programs (groups of co-regulated genes in biological pathways), not random individual gene changes. scBIG is the first framework to formalize module-level inductive bias for generative perturbation prediction.

## Motivation: Beyond Gene-Wise Prediction

### Why Gene-Wise Prediction Fails
All existing approaches treat genes as independent tokens:
- **Foundation models** (scGPT, GeneCompass): Represent each gene independently
- **Graph-based models** (GEARS, CellOracle): Propagate signals gene-by-gene through static graphs
- **Generative models** (CPA, CellFlow): Compress gene expression into flat latent codes

This independence assumption misses a fundamental biological property: perturbations induce **coordinated program-level changes** where groups of functionally related genes co-regulate to execute cellular processes.

### Evidence for Program-Level Responses
- Cell cycle pathway genes co-regulate upon cell cycle perturbations
- DNA repair pathway genes respond coordinately to DNA damage
- Metabolic pathway genes shift together during metabolic stress

## scBIG Framework: Three Components

### 1. Gene-Relation Clustering (GRC)

GRC induces K biologically coherent gene modules (clusters) from data:

**Cost matrix formulation**:
C_{ik} = D^sem(E_i, μ_k) + D^PPI(i, k)

where:
- D^sem: Cosine dissimilarity between GeneCompass/ESM2 gene embeddings and cluster centroid
- D^PPI: Penalizes low PPI (protein-protein interaction) coherence within cluster

**Balanced assignment via OT**: Optimal Transport with uniform marginals forces approximately equal-sized clusters (~64 genes/cluster), ensuring all modules receive sufficient attention.

GRC groups genes into K=32 functionally coherent modules that capture both semantic similarity (from foundation models) and biological interaction (from STRING).

### 2. Gene-Cluster Aware Encoder (GCAE)

GCAE builds hierarchical representations capturing inter-module dependencies:

**Per-cluster representation** (dual-stream fusion):
h_k^{(0)} = Proj_exp(x_{c_k}) + Proj_sem(1/|c_k| Σ_{g∈c_k} E_g)

**Perceiver-style bottleneck**: M inducing points I ∈ ℝ^{M×D} (M < K) compress global inter-module interactions through cross-attention, then broadcast back to cluster representations.

**Final embedding**: Z = Linear(1/K Σ_k h_k^{(1)})

This hierarchical architecture explicitly captures how modules interact with each other — regulatory crosstalk between pathways.

### 3. Structure-Aware Alignment

Two structural regularization objectives preserve module-level coordination:

**Cluster Correlation Alignment**:
L_corr = ||R(x̂₁) - R*_gt||_F

where R(x̂₁) is the K×K Pearson correlation matrix between predicted cluster expressions, and R*_gt is the precomputed target correlation. This constrains predictions to preserve inter-module co-expression patterns.

**Pathway-Informed Optimal Transport**:
L_pathway = W_e(Sx̂₁, S*_gt)

where S ∈ {0,1}^{P×G} is a pathway membership matrix from Reactome, mapping genes to biological pathways. The Sinkhorn distance between predicted and ground-truth pathway activations enforces phenotypic plausibility.

## Perturbation Prediction via Conditional Flow Matching

scBIG uses conditional flow matching as the generative backbone:
- Learns to transform GCAE embeddings of control cells (z₀) to GCAE embeddings of perturbed cells (z₁)
- The flow vector field v_θ(z_t, t, c) is parameterized by an MLP conditioned on ESM2 perturbation embeddings c
- Enables continuous, probabilistic prediction of perturbed cell distributions

## Benchmark Results

### Norman Dataset (Additive Split — Combinatorial Generalization)
Against 13 baselines across all metric types:

| Method | ρΔ | ρΔ^D | ACC_Δ | DES | PDS |
|--------|-----|------|-------|-----|-----|
| CellFlow | 0.7892 | 0.7275 | 0.9151 | 0.8113 | 0.7581 |
| **scBIG** | **0.8496** | **0.8230** | **0.9197** | **0.8593** | **0.8548** |

scBIG improves 7.7% over CellFlow on ρΔ and 6.5% on GeneCompass on PDS.

### Holdout Split (Unseen Gene Perturbations)
On single-gene unseen perturbations:
- scBIG: ρΔ = 0.6507, DES = 0.6333 vs. CellFlow: 0.5930, 0.6280
- On double unseen perturbations: scBIG 20.6% better on ρΔ^D, 35.9% on DES

### RPE1 Dataset
Surpasses CellFlow by 25.7% on ρΔ and 34.9% on ρΔ^D.

## Biological Analysis

GRC module assignments are validated by pathway enrichment analysis:
- Norman: Cluster 9 → Cell Cycle; Cluster 3 → DNA/RNA-related pathways
- RPE1: Cluster 14 → Cell Cycle; Cluster 15 → Metabolism and Signaling

Attention shift analysis shows that NOL8 knockdown (ribosome biogenesis) increases attention to Cluster 8 (mTORC1/Metabolic), consistent with known biology.

## Citations

Ruan J et al. (2026). Beyond Independent Genes: Learning Module-Inductive Representations for Gene Perturbation Prediction. *arXiv:2602.04901*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | scBIG is evaluated on single and double unseen gene perturbations (holdout split), outperforming CellFlow by 9.7% on ρΔ for single-gene and 20.6% on ρΔ^D for double-gene OOD predictions. |
| Cross cell-line (gene intersection) | Yes | scBIG is tested on both Norman (K562) and RPE1 datasets, surpassing CellFlow by 25.7% on ρΔ on RPE1, demonstrating cross-cell-line generalization. |
| Zero-shot unseen cell line (gene intersection) | No | While scBIG generalizes to RPE1, this appears to require training on RPE1 data rather than zero-shot transfer; full zero-shot protocol is not explicitly reported. |
| Cross perturbation technology (gene intersection) | No | scBIG focuses on CRISPR genetic knockouts; no cross-technology transfer evaluation is reported. |
| Zero-shot gene misalignment | No | The GCAE module requires fixed gene module assignments from the training vocabulary; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | scBIG improves 7.7% over CellFlow on ρΔ and 6.5% over GeneCompass on PDS, demonstrating perturbation-specific signal beyond existing strong baselines. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
