# TranSiGen: Deep Representation Learning for Chemical Perturbation Profiles

## Overview

TranSiGen (Tong et al., Nature Communications 2024) is a variational autoencoder (VAE) designed to predict chemical-induced transcriptional profiles at the cell line and gene expression level. Unlike genetic perturbation models (GEARS, CPA, scGPT) that focus on CRISPR knockouts, TranSiGen targets small molecule drug perturbations at the bulk RNA-seq level using the CMAP LINCS 2020 dataset — the largest available collection of drug-induced gene expression signatures.

## Background: CMAP LINCS 2020 Dataset

The Connectivity Map (CMAP) and Library of Integrated Network-Based Cellular Signatures (LINCS) L1000 dataset contains:
- **8,316 compounds** tested across multiple cell lines
- **164 cell lines** covering diverse tissue types (cancer, normal)
- Gene expression measured for ~978 "landmark" genes (selected for high informativity)
- Multiple concentrations and time points

This dataset is fundamentally different from Perturb-seq data:
- **Bulk RNA-seq** (not single-cell): Measures population averages, no single-cell resolution
- **Chemical perturbations**: Small molecules with complex polypharmacology
- **Existing drugs**: Many FDA-approved compounds with known targets
- **Drug repurposing context**: Primary application is finding new uses for existing drugs

## TranSiGen Architecture

### Self-Supervised Pre-training
TranSiGen uses a self-supervised approach where the model reconstructs the input expression profile, forcing it to learn compact representations that capture the essential biological content of transcriptional responses.

Pre-training objectives:
1. **Reconstruction**: Decode the full expression signature from the latent code
2. **Consistency**: The same drug in different cell lines should have similar latent representations (biological activity is cell-type independent at some level)

### Variational Latent Space
The VAE encoder maps drug+cell transcriptional profiles to a Gaussian latent distribution:
- **Latent dimension**: Compact (typically 128-256 dimensions)
- **Drug latent component**: Captures drug-specific mechanism of action
- **Cell line latent component**: Captures cell-type-specific response context

### Prediction Task
Given:
- Drug molecular fingerprints or SMILES (for novel compounds)
- Cell line identity (for the target context)

TranSiGen predicts the transcriptional profile for this drug-cell combination, even if never observed during training.

## Key Results

### Drug Repurposing Performance
On the CMAP LINCS 2020 benchmark:
- **Spearman correlation**: TranSiGen achieves higher correlation between predicted and observed signatures than baseline methods
- **Drug ranking**: Successfully ranks known active compounds above inactive compounds
- **Novel cell line generalization**: Predicts signatures for cell lines not in training data

### Drug Repurposing Validation
TranSiGen-predicted signatures are used to query existing drug databases to identify:
- Cancer drugs that could be repurposed for other indications
- Compounds with unexpected activity against specific gene signatures
- Drug combination synergy predictions

## Differences from Single-Cell Perturbation Models

| Aspect | TranSiGen | GEARS/CPA/scGPT |
|--------|-----------|----------------|
| Data type | Bulk RNA-seq | Single-cell RNA-seq |
| Perturbation type | Small molecules (drugs) | CRISPR gene knockouts |
| Dataset | CMAP LINCS 2020 | Perturb-seq (Norman, Replogle) |
| Gene coverage | ~978 landmark genes | 2,000-20,000 genes |
| Application | Drug repurposing | Gene function, target identification |
| Cellular resolution | None (bulk average) | Single cell |

## Drug Repurposing Application

TranSiGen enables:

1. **Transcriptional fingerprint queries**: Given a disease gene expression signature, find drugs whose predicted transcriptional effects "reverse" the disease signature
2. **Polypharmacology prediction**: For multi-target drugs, predict the combined transcriptional effect
3. **Virtual screening**: Rank large chemical libraries by predicted efficacy in target cell lines
4. **Combination therapy**: Predict synergistic vs. antagonistic drug combinations based on transcriptional profile overlap

## Limitations

1. **Bulk resolution**: Cannot predict single-cell heterogeneity or rare cell type responses
2. **Landmark gene restriction**: LINCS L1000 measures only 978 genes; full transcriptome predictions require imputation
3. **Chemical space coverage**: Training on known drugs may not generalize to structurally novel chemical scaffolds
4. **Indirect mechanism**: Transcriptional profiles are downstream of drug binding; mechanistic interpretation is challenging

## Citations

Tong M et al. (2024). Deep representation learning of chemical-induced transcriptional profile for phenotype-based drug discovery. *Nature Communications*, 15, 5350. doi:10.1038/s41467-024-49620-3.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | TranSiGen predicts transcriptional profiles for novel compounds using molecular fingerprints or SMILES, achieving higher Spearman correlation than baseline methods on held-out drugs in CMAP LINCS 2020. |
| Cross cell-line (gene intersection) | Yes | TranSiGen predicts signatures for cell lines not in training data by leveraging the cell-line latent component, demonstrating novel cell-line generalization on the LINCS benchmark. |
| Zero-shot unseen cell line (gene intersection) | Partial | TranSiGen predicts for unseen cell lines using cell-line identity as a covariate, though the extent of truly zero-shot (no training examples) generalization is not fully quantified. |
| Cross perturbation technology (gene intersection) | No | TranSiGen focuses exclusively on small molecule drug perturbations using CMAP LINCS bulk RNA-seq; genetic perturbation modalities are not addressed. |
| Zero-shot gene misalignment | No | TranSiGen outputs predictions for the ~978 LINCS L1000 landmark genes only; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | TranSiGen achieves higher Spearman correlation between predicted and observed drug signatures than baseline methods and successfully ranks known active compounds above inactive compounds. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
