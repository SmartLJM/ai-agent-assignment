# PerturbGraph: GNN with Biological Priors for Unseen Gene Perturbation

## Overview

PerturbGraph (Dip & Zhang, bioRxiv 2026) is a biologically informed graph learning framework for predicting transcriptional responses to **unseen gene perturbations** — genes whose effects have never been experimentally observed during training. The framework builds on the insight that perturbation effects propagate through molecular interaction networks, and can be inferred by representing each perturbation as a stable transcriptional shift program (latent perturbation signature) rather than raw expression values.

## Key Innovation: Perturbation Signatures as Latent Programs

Unlike models that predict absolute post-perturbation expression profiles, PerturbGraph operates on **perturbation signatures** — the differential expression relative to control cells:

Δ_i = x_i^pert - x^ctrl

These signatures represent the transcriptional shift induced by each perturbation, independent of baseline expression. Key advantages:
1. **Removes cell-type confounding**: Signatures are comparable across cell types
2. **Stable representation**: Less noisy than absolute expression values
3. **Biologically interpretable**: Directly represents what the perturbation causes

## Latent Perturbation Programs via SVD

Because perturbation signatures are high-dimensional and noisy (~8,563 genes in Replogle), PerturbGraph first compresses them using Truncated Singular Value Decomposition (SVD):

X ≈ H × V

where:
- X ∈ ℝ^{N×d}: matrix of all perturbation signatures (N perturbations, d genes)
- H ∈ ℝ^{N×K}: latent perturbation programs (K < d)
- V ∈ ℝ^{K×d}: transcriptional basis vectors (K dominant modes)

The K latent programs capture the dominant transcriptional variation across all perturbations. The task then becomes predicting H (the latent program) for unseen genes, which is then decoded to expression space via V.

## Biological Node Features

Each gene in the interaction graph is represented with multi-source biological features:

### 1. Node2Vec Structural Embeddings
Graph topology embeddings from the STRING protein-protein interaction network, capturing a gene's network neighborhood structure without requiring functional labels.

### 2. Baseline Expression Statistics
Gene-level statistics from control cells:
- Mean expression level
- Variance across cells
- Detection frequency (fraction of cells expressing the gene)
- Neighborhood statistics in the interaction network

### 3. Gene Ontology (GO) Functional Embeddings
Functional annotation embeddings derived from GO term associations, encoding:
- Biological process participation
- Molecular function
- Cellular component location

The final gene representation combines all three: x_i = [z_i || b_i || g_i]

## Graph Convolutional Network Architecture

PerturbGraph uses Graph Convolutional Networks (GCN) to propagate information:

H^{(l+1)} = σ(Â H^{(l)} W^{(l)})

where Â is the normalized adjacency matrix of the STRING interaction graph.

The GCN propagates information across gene-gene interactions, enabling prediction of unseen gene perturbations based on their graph neighbors' known perturbation programs.

## Unseen-Perturbation Evaluation Protocol

A strict unseen-perturbation setting is used:
- Training, validation, and test perturbations correspond to **disjoint** gene sets
- Test genes are **never** seen during training
- The model must predict responses purely from graph context and node features

## Results on Replogle and Norman

### Primary Benchmark (Replogle, K562)
PerturbGraph achieves best performance across all metrics vs. 9 baselines:
- **Cosine similarity**: 0.592 vs. next-best Ridge (0.447)
- **Spearman correlation**: 0.340 vs. next-best CPA (0.326)
- **DirAcc**: 0.619 (correctly predicting up/down regulation direction)
- **Prec@50**: 0.277 (recovering top-50 DE genes)

### Generalization (Norman, K562)
On an additional cross-dataset check, PerturbGraph achieves cosine = 0.940, Spearman = 0.815, demonstrating robust generalization.

### Contribution of Each Biological Prior
Ablation study shows incremental improvements:
- Graph only: cosine = 0.566
- + Biological statistics: 0.571
- + GO embeddings: 0.580
- + All features: 0.592

All three sources of biological prior contribute additively, with GO embeddings providing the largest gain.

## Network Structure Insights

PerturbGraph reveals how network structure affects prediction quality:
- **Graph distance matters**: Genes close (1-2 hops) to training perturbations are predicted more accurately
- **Degree matters**: Highly connected hub genes (high STRING degree) are predicted more accurately
- **Local training support**: Genes with many perturbed neighbors in training data achieve higher accuracy

## Limitations

1. **Program-level, not cell-level**: Operates on pseudo-bulk perturbation signatures, not single cells
2. **STRING completeness**: Prediction depends on STRING edge coverage; genes with few known interactions are harder to predict
3. **Linear SVD assumption**: The SVD latent space assumes linear structure in perturbation programs

## Citations

Dip SA, Zhang L (2026). Predicting Unseen Gene Perturbation Response Using Graph Neural Networks with Biological Priors. *bioRxiv*, doi:10.64898/2026.03.23.713780. Under review at ECCB 2026.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | PerturbGraph uses a strict unseen-perturbation protocol where test genes are completely disjoint from training, achieving cosine similarity 0.592 vs. next-best 0.447 on Replogle K562. |
| Cross cell-line (gene intersection) | Partial | PerturbGraph is evaluated on both Replogle (K562) and Norman (K562) datasets and shows robust generalization (cosine = 0.940 on Norman), though both are K562 cells rather than truly different cell lines. |
| Zero-shot unseen cell line (gene intersection) | No | No zero-shot prediction to a completely unseen cell line without fine-tuning is evaluated; both datasets tested are K562. |
| Cross perturbation technology (gene intersection) | No | PerturbGraph operates on CRISPR knockout perturbation signatures only; no cross-technology transfer is evaluated. |
| Zero-shot gene misalignment | No | PerturbGraph predicts into the fixed SVD basis from training data; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | PerturbGraph outperforms Ridge regression (the best linear baseline) by 32% in cosine similarity on the strict unseen-perturbation benchmark. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
