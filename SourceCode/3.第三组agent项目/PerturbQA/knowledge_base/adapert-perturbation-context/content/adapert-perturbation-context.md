# AdaPert: Adaptive Perturbation-Conditioned Context for Robust Prediction

## Overview

AdaPert (Piao et al., 2026) addresses **mean-collapse** — a fundamental failure mode in perturbation prediction where models predict expression changes close to the global average rather than capturing perturbation-specific effects. AdaPert proposes a perturbation-conditioned framework that learns perturbation-specific subgraphs from biological knowledge graphs and separates true signals from noise using adaptive learning objectives.

## The Mean-Collapse Problem

### What is Mean-Collapse?
When models optimize MSE over all genes (the vast majority of which show no perturbation effect), they converge to a trivial solution: predicting near-zero expression change for most genes. This is particularly problematic because:

1. **Non-DEG genes dominate**: Only ~2-10% of genes are differentially expressed per perturbation
2. **MSE naturally minimizes to mean**: The mean prediction of the large non-DEG set overwhelms the small DEG signal
3. **Large effects systematically underestimated**: Strong perturbation effects are shrunk toward zero

This is illustrated in Fig. 1 of the paper: a baseline model shows predicted delta values shrinking toward zero (mean-collapse), while AdaPert maintains high correlation specifically for the biologically important differentially expressed genes.

## AdaPert Architecture

### Component 1: Perturbation-Conditioned Subgraph Extraction

Instead of using the full biological knowledge graph as a static prior (as GEARS and TxPert do), AdaPert learns a **perturbation-specific subgraph** for each knockout:

1. **Gene representation**: Each gene v gets a structural embedding h_v via message passing over the full graph G
2. **Perturbation semantic embedding**: The text description of the perturbed gene p is encoded via LLM (GPT-4o): s_p = LM(desc(p))
3. **Node scoring**: For each gene v, relevance to perturbation p is computed as: a_v = w^T σ(W_e [h_v || s̃_p])
4. **Differentiable sampling**: Gumbel-Softmax sampling selects a sparse perturbation-relevant subgraph G_{context}
5. **Context representation**: z_context = Σ_{v ∈ G_context} h_v

This design identifies which genes are causally related to the perturbed gene, restricting message passing to a biologically relevant subgraph rather than the full noisy graph.

### Component 2: Adaptive Learning for Signal-Noise Separation

Three complementary loss terms:

**Global reconstruction loss**:
L_recon = E[||X̂^P - X^P||²₂]

Ensures overall expression fidelity across all genes.

**Non-DEG robust loss**:
L_non = E_p[Σ_{i ∈ D̄(p)} ρ_δ(ΔX̂_i^P)]

A Huber penalty applied specifically to non-DEG genes, penalizing predicted changes that deviate from zero without being overly sensitive to outliers. δ is set proportional to the empirical standard deviation of non-DEG effects.

**Alignment loss**:
L_align = E[||z_context^(p) / ||z_context^(p)||₂ - t^(p) / ||t^(p)||₂||²₂]

Guides the learned subgraph representation to encode perturbation-specific DEG signals, by aligning it with the empirical DEG expression pattern y^(p).

**Total objective**:
L_total = L_recon + λ_non × L_non + λ_align × L_align

## Evaluation Metrics

AdaPert is evaluated using DEG-aware metrics that capture perturbation-specific performance:
- **Pearson-Δ**: Correlation on differential expression (relative to control)
- **Perturbation Discrimination Score (PDS)**: Ability to distinguish individual perturbations
- **Differential Expression Score@K (DES@K)**: Recovery of ground-truth DEGs among top-K predictions
- **Direction-match**: Fraction of DEGs with correct up/down regulation direction

## Results on Replogle Datasets

Benchmarked on K562.Replogle and RPE1.Replogle:

### Global Performance
AdaPert achieves best Pearson-Δ (0.619) and best PDS (0.711) on K562, outperforming:
- GEARS: Pearson-Δ = 0.298, PDS = 0.529
- TxPert: Pearson-Δ = 0.580, PDS = 0.665
- MorPH: Pearson-Δ = 0.442, PDS = 0.664

### DEG-Aware Metrics
AdaPert achieves highest DES@50 (0.263) and DES@100 (0.252) — ~20% improvement over TxPert.

### Mean-Collapse Analysis
When perturbations are stratified by effect size:
- **Small effect (<5% DEG)**: AdaPert shows much higher DES despite similar Pearson-Δ, demonstrating better signal-noise separation
- **Medium effect (5-10%)**: 15% improvement in Pearson-Δ, 28% in DES
- **Large effect (>10%)**: 4% improvement in Pearson-Δ, 19% in DES

## Impact of Subgraph vs. Full Graph

Ablation confirms that perturbation-conditioned subgraph is critical:
- Full graph: PDS = 0.665 (like TxPert)
- Perturbation-conditioned subgraph: PDS = 0.711 (+7%)

Removing z_context (no perturbation context) degrades performance across all metrics.

## Citations

Piao Y et al. (2026). Learning Adaptive Perturbation-Conditioned Contexts for Robust Transcriptional Response Prediction. *arXiv:2602.18885*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | AdaPert is benchmarked on K562.Replogle and RPE1.Replogle with held-out perturbations, achieving best Pearson-Δ (0.619) and PDS (0.711) on K562, outperforming GEARS and TxPert on OOD perturbations. |
| Cross cell-line (gene intersection) | Partial | AdaPert is evaluated on both K562 and RPE1 Replogle datasets; evaluation across the two cell lines implies some cross-cell-line capability, but the details of the training protocol are not fully specified. |
| Zero-shot unseen cell line (gene intersection) | No | The paper does not report zero-shot evaluation on completely unseen cell lines without any training data from that context. |
| Cross perturbation technology (gene intersection) | No | AdaPert focuses exclusively on CRISPR genetic knockouts; no cross-perturbation-technology evaluation is reported. |
| Zero-shot gene misalignment | No | The graph-based context and prediction head operate on a fixed gene vocabulary; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | AdaPert achieves ~20% improvement over TxPert on DES@50/100 metrics, and its perturbation-conditioned subgraph adds 7% over full-graph baselines, demonstrating perturbation-specific signal capture. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
