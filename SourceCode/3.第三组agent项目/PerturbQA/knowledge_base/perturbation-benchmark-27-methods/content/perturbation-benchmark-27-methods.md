# Comprehensive Benchmark of 27 Methods for Generalizable Single-Cell Perturbation Prediction

## Overview

As computational methods for predicting single-cell perturbation responses proliferate—including both specialized models and large foundation models—there is an urgent need for rigorous, standardized evaluation. Wei et al. (Nature Methods 2025) present a comprehensive benchmark of **27 methods** (23 published + 4 baselines) evaluated on **29 datasets** using **6 complementary metrics**, systematically assessing generalizability across two key challenge scenarios. The work provides actionable guidance on method selection and identifies fundamental limitations of current approaches, including foundation models.

## Two Evaluation Scenarios

**Scenario 1: Cellular Context Generalization**
- Train on perturbation effects in known cell lines; predict effects of the same perturbations in a new, unseen cell line
- 14 methods evaluated on 12 datasets (8 cross-cell-line, 3 cross-patient, 1 cross-species)
- Key challenge: inter-cellular heterogeneity means perturbation effects are cell-type-specific

**Scenario 2: Perturbation Generalization**
- Train on effects of known perturbations in one context; predict effects of new, unseen perturbations
- 18 methods evaluated on 17 datasets
- Key challenge: predicting responses to genes or compounds never seen during training

## Methods Evaluated

**Cellular context generalization (14 methods)**: biolord, CellOT, inVAE, scDisInFact, scGen, scPRAM, scPreGAN, SCREEN, scVIDR, trVAE, plus 4 baselines

**Perturbation generalization (18 methods)**: AttentionPert, biolord, CPA, GEARS, GenePert, linearModel, scFoundation, scGPT, chemCPA, scouter, scELMo, GeneCompass, PRnet, cycleCDR, plus 4 baselines (baseReg, baseMLP, baseControl, trainMean)

## 6 Evaluation Metrics

1. **MSE**: Mean squared error of predicted vs. observed expression
2. **PCC-delta**: Pearson correlation of predicted vs. observed expression changes
3. **E-distance**: Energy distance between predicted and observed distributions
4. **Wasserstein distance**: Optimal transport distance between distributions
5. **KL-divergence**: Kullback–Leibler divergence between distributions
6. **Common-DEGs**: Overlap of top differentially expressed genes

## Key Findings

**Finding 1 - No universal winner**: No single method consistently outperforms across all datasets and scenarios. Method performance varies significantly by dataset characteristics.

**Finding 2 - Context generalization is a critical unsolved problem**: In the cellular context generalization scenario, ALL methods—including foundation models—perform poorly when predicting perturbation effects in a substantially different cell type from training. Some methods perform worse than simple baselines, revealing that ignoring cellular context specificity is a fundamental failure mode.

**Finding 3 - Foundation models need sufficient fine-tuning data**: In the perturbation generalization scenario, baseline models tend to outperform foundation models on small datasets. Foundation models (scGPT, scFoundation) show advantages only when fine-tuning datasets are sufficiently large. This overturns assumptions that pre-training always helps.

**Finding 4 - Cellular context embedding as a solution**: A cellular context embedding strategy—incorporating information about the target cell type's identity and state—shows promise for improving generalization across cell types. This is identified as a key direction for future method development.

**Finding 5 - Simulated data for scalability assessment**: The paper uses simulated data to evaluate methods under varying levels of noise and sparsity, finding that most methods degrade substantially under realistic noise conditions.

## Tool Selection Guidance

The authors provide a decision framework for method selection based on:
- Training dataset size (small vs. large)
- Whether the task requires cross-cell-line generalization or cross-perturbation generalization
- Whether perturbation metadata (dose, time) is available

## Limitations of the Benchmark

The benchmark focuses on transcriptomic readouts (scRNA-seq). Not all methods support all input formats, requiring some compromises. Some methods were excluded due to reproducibility or compatibility issues (noted in Supplementary Note 1).

## Citation

Wei Z, Wang Y, Gao Y, Wang S, Li P, Si D, Gao Y, Wu S, Li D, Dong K, Yang X, Tang C, Fu S, Chen X, Li W, You Y, Zhang C, Liang A, Chuai G, Liu Q. "Benchmarking algorithms for generalizable single-cell perturbation response prediction." Nature Methods (2025). DOI: 10.1038/s41592-025-02980-0

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Not evaluated | This is a benchmark framework that evaluates other methods on unseen perturbation prediction; it does not itself predict perturbation outcomes. |
| Cross cell-line (gene intersection) | Not evaluated | The benchmark evaluates 14 methods on cellular context generalization across 12 datasets, but scDist itself is a framework, not a predictive model. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | The framework characterizes that ALL methods perform poorly in zero-shot cross-cell-line generalization, but does not itself perform this prediction. |
| Cross perturbation technology (gene intersection) | Not evaluated | This benchmark does not itself perform cross-technology prediction; it evaluates existing methods on their generalization capabilities. |
| Zero-shot gene misalignment | Not evaluated | The benchmark does not address or evaluate methods on gene vocabulary misalignment scenarios. |
| Perturbation-specificity vs. simple baseline | Not evaluated | The benchmark finds that baseline models sometimes outperform foundation models on small datasets; this is an evaluation finding, not a capability of the benchmark itself. |

**Overall capability tier**: Benchmark-tool
