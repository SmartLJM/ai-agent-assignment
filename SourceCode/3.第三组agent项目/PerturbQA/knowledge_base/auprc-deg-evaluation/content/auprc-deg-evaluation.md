# AUPRC: Area Under Precision-Recall Curve for Perturbation Evaluation

## Overview

Zhu et al. (Briefings in Bioinformatics 2025) propose the Area Under the Precision-Recall Curve (AUPRC) as a superior metric for evaluating perturbation prediction models, specifically for the task of identifying differentially expressed genes (DEGs). The paper demonstrates that the widely used R² metric is fundamentally inadequate for this purpose and that AUPRC provides a more informative and biologically meaningful evaluation.

## The Problem with R² Metric

### Why R² is Misleading
Standard R² (coefficient of determination) measures the proportion of total variance explained. For perturbation prediction:

1. **Dominated by non-DEGs**: In any perturbation experiment, only 2-10% of genes are differentially expressed. R² computed over all genes is dominated by the 90-98% of non-responding genes.

2. **Non-zero predictions not needed**: A model that predicts zero change for all genes achieves R² ≈ 0.5 for most perturbations (because most genes don't change and the mean prediction is close to zero change).

3. **Penalizes magnitude**: R² penalizes predictions that correctly identify DEG direction but over- or under-estimate magnitude — a biologically less important error.

4. **Discordance with DEG performance**: A model can achieve high R² (>0.8) while having near-zero ability to identify the actual DEGs (AUPRC near random baseline 0.1-0.2).

### Empirical Discordance
The paper shows empirically that R² and AUPRC are **discordant** across models:
- Some models achieve R² = 0.85 but AUPRC = 0.15 (identifying DEGs no better than random)
- Models with high R² may differ in AUPRC by 5-10 fold
- Rankings of models change substantially when switching from R² to AUPRC

## AUPRC as a Metric for DEG Identification

### Task Formulation
The DEG identification task is formulated as a binary classification problem:
- **Positive**: Genes that are truly differentially expressed (by some threshold, e.g., |log2FC| > 1, FDR < 0.05)
- **Negative**: Genes with minimal expression change
- **Prediction score**: The predicted absolute expression change |ŷ_g - ŷ_control|

### Precision-Recall Curve
At each threshold on the predicted change:
- **Precision**: Among genes predicted as DEG, what fraction are truly DEG?
- **Recall**: Among all true DEGs, what fraction are predicted?

AUPRC summarizes the full precision-recall tradeoff in a single number (0-1, where 1 = perfect ranking).

### Why AUPRC is Better
1. **DEG-focused**: Directly measures the ability to find the genes that matter
2. **No magnitude penalty**: Correctly ranking a true DEG above a true non-DEG is rewarded regardless of predicted magnitude
3. **Handles class imbalance**: PR curves are more informative than ROC for imbalanced data (few DEGs vs many non-DEGs)
4. **Biologically interpretable**: Directly answers "can this model guide which genes to follow up experimentally?"

## Practical Threshold Choices

The paper analyzes sensitivity of AUPRC to DEG threshold choices:
- **Strict threshold** (|log2FC| > 1, FDR < 0.01): Fewer DEGs, higher precision of the positive set
- **Relaxed threshold** (|log2FC| > 0.5, FDR < 0.1): More DEGs, noisier positive set

AUPRC is relatively robust to threshold choice for large-effect perturbations, but thresholds matter for low-effect knockouts where few genes change.

## Recommendations

Based on the analysis, the authors recommend:
1. **Primary metric**: AUPRC for DEG identification
2. **Supplementary**: Pearson correlation on top-50 DEGs (consistent with GEARS and Systema)
3. **Avoid**: R² on all genes as sole metric
4. **Report**: Effect size stratification (small/medium/large effect perturbations)

## Relationship to Other Evaluation Papers

- **Systema**: Addresses systematic variation bias; AUPRC is complementary (tests ranking, not bias)
- **Miller et al.**: Dynamic Range Fraction addresses similar issues of calibrating effect sizes
- **GGE**: Includes AUPRC as one of its standardized metrics in its Python framework

## Citations

Zhu H et al. (2025). AUPRC: a metric for evaluating the performance of in-silico perturbation methods in identifying differentially expressed genes. *Briefings in Bioinformatics*. doi:10.1093/bib/bbaf426.
