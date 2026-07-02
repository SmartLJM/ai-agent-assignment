# MorphDiff: Transcriptome-Guided Diffusion Model for Predicting Cell Morphology Under Perturbations

## Overview

Cell morphology changes are a key readout in phenotypic drug discovery, but the vast perturbation space makes it impractical to experimentally profile morphological responses for all compounds and genetic perturbations. Wang et al. (Nature Communications 2025) present **MorphDiff**, a transcriptome-guided latent diffusion model that simulates high-fidelity cell morphological responses to genetic and chemical perturbations using L1000 gene expression profiles as the conditioning signal.

## Problem Being Solved

High-throughput image-based profiling (Cell Painting assay) measures cell morphology to infer drug mechanisms of action (MoA) and compound bioactivity. However:
1. The vast number of synthesizable compounds and genes makes complete morphological profiling infeasible
2. Existing in silico morphology prediction methods (IMPA, MorphNet) only perform well for perturbations similar to training examples
3. Structurally similar drugs can have different effects, requiring perturbation-specific representations for generalization
4. Cell morphology data has high noise from batch effects and well position effects

**Key insight**: Gene expression is intermediate between perturbation and morphology. Since L1000 transcriptomics data is far more abundant than Cell Painting morphology data, using gene expression as a conditioning signal leverages this data advantage.

## Architecture

**MorphDiff** has two main components:

**1. Morphology VAE (MVAE)**:
- Encoder: Compresses 5-channel Cell Painting images (DNA, RNA, ER, AGP, Mito) into low-dimensional latent representations
- Decoder: Reconstructs morphology images from latent representations
- Trained to learn a compact morphological space capturing biologically meaningful variation

**2. Latent Diffusion Model (LDM)**:
- **Noising process**: Gaussian noise is sequentially added to the latent morphology representation over T steps (T=1000), producing standard Gaussian noise at the endpoint
- **Denoising process**: A denoising U-Net (convolutional architecture with attention) learns to remove noise conditioned on L1000 gene expression, reversing the noising process
- **Conditioning**: L1000 gene expression profiles are incorporated into the attention mechanism (as key and value) of the U-Net at every denoising step
- Training minimizes the variational upper bound (noise prediction error)

## Two Operating Modes

**MorphDiff(G2I)** - Gene expression to image:
- Takes L1000 gene expression as condition
- Generates cell morphology from random noise distribution
- Used for predicting morphological effects of novel perturbations

**MorphDiff(I2I)** - Image to perturbed image:
- Takes unperturbed cell morphology + L1000 perturbed gene expression as conditions
- Transforms unperturbed morphology to predicted perturbed morphology
- Simulates the continuous morphological transition from control to treated state
- No additional training required—uses the pre-trained model directly

## Main Results

Evaluated on three large-scale datasets:
1. Two drug perturbation datasets (L1000 matched with Cell Painting)
2. One genetic perturbation dataset

**Morphology prediction accuracy**:
- MorphDiff outperforms baselines (including IMPA, MorphNet, and direct structural encoding approaches) on both standard image generation metrics (FID, structural similarity) and biology-specific morphological feature metrics (CellProfiler, DeepProfiler feature recovery)

**MoA retrieval**:
- MorphDiff-generated morphologies achieve **comparable performance to ground-truth morphologies** in MoA retrieval tasks
- **Outperforms baseline methods by 16.9%** and gene expression-based approaches by **8.0%** in MoA retrieval accuracy
- Demonstrates that in silico morphology can substitute for experimental morphology in mechanistic analysis

**Structurally diverse drug similarity**: MorphDiff can identify drugs with different molecular structures but similar MoA through morphological similarity—a key drug repurposing application.

## Advantages Over Previous Methods

MorphDiff is the only tool that:
1. Supports generation from gene expression to morphology (G2I mode)
2. Supports morphology transformation from unperturbed to perturbed (I2I mode)
3. Is robust to batch/well effects via the diffusion noise model
4. Generalizes to unseen perturbations through the gene expression conditioning signal

## Limitations

MorphDiff requires paired L1000 gene expression and Cell Painting morphology data for training. The model assumes that gene expression is a sufficient intermediate representation of morphological change—this may not hold for perturbations that affect post-transcriptional processes. Computational cost of diffusion sampling is higher than GAN-based alternatives.

## Citation

Wang X, Fan Y, Guo Y, Fu C, Lee K, Dallakyan K, Li Y, Yin Q, Li Y, Song L. "Prediction of cellular morphology changes under perturbations with a transcriptome-guided diffusion model." Nature Communications 16, 8210 (2025). DOI: 10.1038/s41467-025-63478-z

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | MorphDiff generalizes to unseen perturbations through gene expression conditioning, outperforming baselines (IMPA, MorphNet) that only perform well for perturbations similar to training examples. |
| Cross cell-line (gene intersection) | Partial | MorphDiff conditions on L1000 gene expression profiles to generate morphology, enabling some cross-cell-line generalization, but explicit cross-cell-line benchmarks are not the primary focus. |
| Zero-shot unseen cell line (gene intersection) | Partial | The gene expression conditioning provides perturbation specificity for unseen contexts, but fully zero-shot prediction on unseen cell lines without any training data is not separately demonstrated. |
| Cross perturbation technology (gene intersection) | Partial | MorphDiff is evaluated on both drug and genetic perturbation datasets using a unified L1000 gene expression conditioning approach, but cross-technology transfer is not explicitly tested. |
| Zero-shot gene misalignment | No | MorphDiff requires L1000 gene expression profiles as conditioning signals; completely disjoint gene vocabularies are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | MorphDiff-generated morphologies achieve comparable MoA retrieval to ground-truth morphologies and outperform baseline methods by 16.9% in MoA retrieval accuracy. |

**Overall capability tier**: Specialist
