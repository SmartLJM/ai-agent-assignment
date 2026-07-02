# Perturbation-Response Score (PS): Decoding Heterogeneous Single-Cell Perturbation Responses

## Overview

Understanding how individual cells respond differently to the same genetic perturbation is fundamental to systems biology, but existing methods fail to accurately quantify these heterogeneous responses. This paper from Song et al. (Nature Cell Biology 2025) introduces the **Perturbation-Response Score (PS)**, a method that quantifies diverse perturbation responses at single-cell resolution, enabling dose-to-function analysis, buffered/sensitive response classification, and discovery of cell-type-specific responses to genetic perturbation.

## Problem Being Solved

In Perturb-seq experiments, cells receiving the same CRISPR guide RNA often display highly heterogeneous responses due to: (1) variable on-target editing efficiency leading to partial knockouts, (2) cell-intrinsic factors like cell state and co-regulatory factor activity, and (3) off-target effects and in-frame deletions. Current metrics (AUC from Augur, simple differential expression, existing perturbation scores) fail to disentangle these sources and quantify partial perturbation effects with biological accuracy.

## Method: PS Score Computation

PS is computed through a three-step constrained optimization framework:

**Step 1: Target gene identification**
- For each perturbation, identify marker genes (target gene signature) through differential expression between perturbed cells and negative controls
- Result: a gene signature matrix encoding which genes are affected by each perturbation

**Step 2: Average perturbation effect estimation**
- Estimate the expected (average) perturbation effect across all cells receiving a given perturbation
- Uses the gene signature to define the "maximum perturbation effect" direction in expression space

**Step 3: PS estimation via constrained optimization**
- For each single cell, solve a constrained optimization problem to find the scalar PS value (between 0 and 1) that best explains the cell's expression given:
  - A "no effect" baseline (PS = 0)
  - The maximum perturbation effect (PS = 1)
  - User-defined or automatically identified gene signatures
- The optimization minimizes reconstruction error subject to non-negativity and bounds constraints

This formulation allows PS to naturally handle partial perturbations, continuous dosage effects, and heterogeneous responses—without requiring titration experiments or pre-defined thresholds.

## Key Applications

**Partial perturbation quantification**: In CRISPR-Cas9 knockout experiments with in-frame deletions, PS accurately quantifies the fraction of functional protein remaining, outperforming existing methods (Augur AUC, target gene expression alone, previous perturbation scores) that show bimodal or noisy distributions.

**Single-cell dosage analysis**: PS enables dosage-response curves at single-cell resolution without physically titrating CRISPR reagents. By correlating PS with known dosage labels in validation experiments, the authors demonstrate PS faithfully recapitulates dose-response relationships.

**Buffered vs. sensitive essential gene classification**: Essential gene knockdown shows two distinct patterns:
- **Buffered genes**: Moderate perturbation causes little downstream effect (PS plateau at low values)
- **Sensitive genes**: Even moderate perturbation triggers strong downstream cascades (PS rises steeply)

This classification maps onto gene network topology—hub genes tend to be buffered while specific effectors are sensitive.

**Biological discovery**: Applied to T cell stimulation, HIV-1 latency reversal, and pancreatic differentiation datasets, PS reveals cell-state-specific responses and interaction effects invisible to bulk metrics. Notably, PS identifies a previously unknown role for **CCDC6** in regulating liver and pancreatic cell fate decisions through analysis of perturbation response heterogeneity.

## Main Results

PS outperforms existing methods (including Mixscape perturbation score, target gene expression, Augur AUC) across:
- Accuracy of partial perturbation quantification (Pearson r with known partial knockout levels)
- Sensitivity to biologically meaningful dose-response relationships
- Discovery of buffered/sensitive gene categories consistent with known biology

## Limitations

PS requires pre-existing gene signatures (can be user-defined or computed from the data). The constrained optimization is computationally more intensive than simple differential expression. The method is primarily validated in CRISPR screens and may need adaptation for other perturbation modalities.

## Citation

Song B, Liu D, Dai W, McMyn NF, Wang Q, Yang D, Krejci A, Vasilyev A, Untermoser N, Loregger A, Song D, Williams B, Rosen B, Cheng X, Chao L, Kale HT, Zhang H, Diao Y, Burckstummer T, Siliciano JD, Li JJ, Siliciano RF, Huangfu D, Li W. "Decoding heterogeneous single-cell perturbation responses." Nature Cell Biology 27, 493–504 (2025). DOI: 10.1038/s41556-025-01626-9

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | The Perturbation-Response Score (PS) quantifies the degree of existing perturbation responses in cells; it is an analysis tool, not a predictive model for unseen perturbations. |
| Cross cell-line (gene intersection) | Not evaluated | PS is an analysis framework applied to Perturb-seq datasets; cross-cell-line generalization is not a relevant capability for this scoring method. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | PS requires experimental Perturb-seq data from the target conditions to compute scores; zero-shot prediction is not applicable. |
| Cross perturbation technology (gene intersection) | Not evaluated | PS is validated primarily for CRISPR screens and may need adaptation for other perturbation modalities; cross-technology generalization is not evaluated. |
| Zero-shot gene misalignment | Not evaluated | PS operates on existing experimental data using defined gene signatures; gene vocabulary misalignment is not a relevant scenario. |
| Perturbation-specificity vs. simple baseline | Yes | PS outperforms existing methods (Mixscape perturbation score, target gene expression, Augur AUC) in accuracy of partial perturbation quantification and dose-response relationship detection. |

**Overall capability tier**: Benchmark-tool
