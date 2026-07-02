# XPert: Dual-Branch Transformer for Drug-Induced Cellular Perturbation Modeling

## Overview

XPert is a transformer-based model for predicting drug-induced transcriptional perturbation effects that addresses key limitations of existing approaches: over-denoising by VAE-based models, inadequate modeling of dose-time dynamics, and inability to resolve gene-specific drug effects. Guo et al. (Nature Machine Intelligence 2026) present XPert with a dual-branch architecture that separately models pre-perturbation and post-perturbation cellular states, achieving superior performance in drug perturbation prediction including multi-dose multi-time scenarios.

## Problem Being Solved

Several fundamental challenges in drug perturbation modeling:
1. **VAE over-denoising**: TranSiGen, PRnet, CPA use VAEs that learn to denoise gene expression, but can inadvertently remove biologically relevant perturbation signals along with noise
2. **Gene-specific vs. global effects**: Most methods concatenate drug and cell features to capture global state alterations, missing gene-specific regulatory responses
3. **Dose-time dynamics**: Previous approaches use simplistic one-hot encodings for dose and time, failing to model nonlinear pharmacodynamic curves (e.g., inverted U-shapes)
4. **Clinical translation**: Large-scale preclinical data exists but is rarely leveraged for patient-specific clinical predictions

## Architecture: Dual-Branch Design

XPert uses two parallel transformer branches:

**Base encoder branch (pre-perturbation)**:
- Processes the unperturbed gene expression profile
- Each cell is represented as a "sentence" of gene tokens with a [CLS] global state token
- Gene tokens are initialized with functional representations and binned expression values
- Self-attention models complex gene-gene regulatory interactions across diverse cellular contexts
- Captures the intrinsic transcriptional landscape of the cell

**Perturb encoder branch (post-perturbation)**:
- Uses cross-attention between gene tokens and drug feature tokens
- Captures cell-drug interactions specific to each drug perturbation
- Condition tokens (dose, time) encode nonlinear pharmacodynamic responses

**Drug feature encoding**:
- **Chemical features**: UniMol (3D molecular model) extracts 3D structure-aware drug representations
- **Biological features**: A knowledge-informed heterogeneous graph (HG) integrates Drug-Target Interactions (DTI), Protein-Protein Interactions (PPI), and Drug-Drug Structure Similarity (DDS)
- Unsupervised HG pretraining bridges the chemical-biological spaces

**Condition tokens**: Special tokens for dose and time enable modeling of nonlinear dose-response relationships, including inverted U-shaped curves that simple one-hot encodings miss.

## Loss Function and Outputs

XPert simultaneously outputs:
- **xpert**: Post-perturbation cell expression profile
- **xdeg**: Gene expression change (xpert - xbase), the difference profile

Dual outputs enable focused evaluation on subtle perturbation signals. Training minimizes MSE on both outputs with ablation studies confirming the necessity of each component.

## Main Results

**Single-dose single-time benchmark on L1000 dataset**:
- XPert surpasses the next-best model (TranSiGen) by 8.2% (warm-start), 15.9% (cold-drug), and **36.7%** (cold-cell) in Pearson correlation of xdeg
- 78.2% lower MSE in cold-cell generalization—the most clinically relevant scenario

**Multi-dose multi-time prediction**: XPert accurately resolves pharmacodynamic trajectories across dose and time dimensions, enabling interrogation of time-dependent drug mechanisms.

**Clinical knowledge transfer**: Pre-training on large-scale preclinical LINCS data and fine-tuning on limited clinical samples achieves up to 15.04% improvement in patient-specific drug response predictions—enabling translation from lab to clinic.

**Mechanistic interpretability**: XPert identifies clinically validated drug resistance biomarkers through attention analysis, demonstrating that its learned representations are biologically meaningful.

## Ablation Studies

Ablations confirm:
- Dual-branch design is essential (single-branch variants underperform)
- HG biological knowledge integration improves cold-cell generalization
- UniMol 3D chemical features outperform Morgan fingerprints
- Condition tokens for dose/time are critical for multi-dose/multi-time scenarios

## Limitations

XPert requires drug-target interaction data for knowledge graph construction, which may be incomplete for novel compounds. The model architecture is more complex than baseline VAE approaches, requiring more training data and longer training times.

## Citation

Guo Y, Zhang H, Hu H, Wu J, Cao J, Hsieh CY, Yang B. "Modelling drug-induced cellular perturbation responses with a biologically informed dual-branch transformer." Nature Machine Intelligence 8, 96–112 (2026). DOI: 10.1038/s42256-025-01165-w

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | XPert is evaluated in cold-drug and cold-cell scenarios, predicting responses to drugs and cell lines not seen during training, improving over TranSiGen by 15.9% and 36.7% respectively. |
| Cross cell-line (gene intersection) | Yes | The cold-cell generalization benchmark explicitly tests prediction on unseen cell lines using shared gene features, achieving 78.2% lower MSE than next-best model. |
| Zero-shot unseen cell line (gene intersection) | Partial | Cold-cell performance is demonstrated but relies on fine-tuning on clinical samples; fully zero-shot transfer without any target cell line data is shown only for pre-training-to-clinical transfer. |
| Cross perturbation technology (gene intersection) | Not evaluated | XPert focuses on drug (chemical) perturbations only; cross-technology generalization from genetic to chemical perturbations is not evaluated. |
| Zero-shot gene misalignment | No | XPert requires a shared L1000 gene vocabulary between training and test datasets; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | XPert surpasses the next-best model (TranSiGen) by 8.2% in warm-start Pearson correlation and by 36.7% in the most clinically relevant cold-cell scenario. |

**Overall capability tier**: Specialist
