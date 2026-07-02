# CPA: Compositional Perturbation Autoencoder

## Overview

CPA (Compositional Perturbation Autoencoder; Lotfollahi et al., Molecular Systems Biology 2023) is a generative model that learns to disentangle cellular responses into three independent components: the basal cell state, the perturbation effect, and covariate embeddings (e.g., cell line, dosage). By making these components compositional, CPA can predict responses to unseen combination of perturbations and experimental conditions that were never observed together during training.

## Core Architecture

### Disentangled Latent Space
CPA encodes each cell into a basal state representation z_basal that is stripped of perturbation and covariate information. Separately, the model learns:
- **Perturbation embeddings**: One embedding vector per perturbation condition (drug or genetic)
- **Covariate embeddings**: One embedding vector per experimental covariate (cell line, dose)

The predicted perturbed cell state is:
z_perturbed = z_basal + Σ(perturbation_embeddings) + Σ(covariate_embeddings)

### Adversarial Training
To ensure that z_basal contains no perturbation information, CPA uses adversarial discriminators:
- **Perturbation discriminator**: Trained to predict the perturbation from z_basal; the encoder is trained adversarially to fool it.
- **Covariate discriminator**: Similarly removes covariate information from z_basal.

This adversarial disentanglement is the key mechanism that allows compositional prediction.

### Decoder
A neural network decoder reconstructs gene expression profiles from the combined latent representation, trained with reconstruction loss (typically negative binomial likelihood for count data).

## Training Datasets

- **Norman et al. (2019)**: ~287 combinatorial CRISPR perturbation conditions in K562 cells
- **Adamson et al. (2016)**: ~105 single-gene perturbations related to UPR
- **sci-Plex (Srivatsan et al., 2020)**: Large-scale drug perturbation screen across multiple cell lines and drug concentrations — CPA's benchmark dataset for drug response

## Strengths

1. **Combinatorial generalization**: Because perturbation and covariate embeddings are additive, CPA can predict responses to combinations of perturbations or drug+cell line combos not seen during training.
2. **Drug dose interpolation**: With dosage as a covariate, CPA can predict responses at intermediate doses.
3. **Multi-condition**: Single model handles genetic knockouts, small molecule drugs, and arbitrary covariates.
4. **Interpretable embeddings**: Perturbation embeddings can be visualized and clustered to discover biological structure among perturbations.

## Limitations

1. **Linearity assumption**: The additive composition of embeddings assumes perturbation effects combine linearly — epistatic/synergistic interactions are poorly modeled.
2. **No graph priors**: Unlike GEARS, CPA does not incorporate gene regulatory networks, limiting its ability to generalize to completely novel genes.
3. **Mean prediction**: CPA predicts population-average responses, not single-cell distributions.
4. **Adversarial instability**: Adversarial training can be unstable; results depend on training hyperparameters.

## Comparison with GEARS

| Aspect | CPA | GEARS |
|--------|-----|-------|
| Biological prior | None | GO + co-expression graph |
| Perturbation representation | Learned embeddings | Gene node embeddings in graph |
| Drug support | Yes (molecular features) | Limited |
| OOD generalization | Combinatorial by composition | Graph-based propagation |

## Key Results

On sci-Plex (188 drugs × 3 cell lines × 4 doses):
- CPA achieves R² > 0.85 for most drug conditions
- Successfully predicts dose-response curves for held-out concentrations
- Learns biologically meaningful drug embedding space where similar drugs cluster

## Citations

Lotfollahi M et al. (2023). Predicting cellular responses to complex perturbations in high-throughput screens. *Molecular Systems Biology*, 19(6), MSB202211517. doi:10.15252/msb.202211517.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | CPA's compositional latent space allows prediction of drug or genetic perturbation combinations never seen during training by combining learned perturbation embeddings additively. |
| Cross cell-line (gene intersection) | Partial | CPA encodes cell-line identity as a covariate embedding enabling partial cross-cell-line transfer, but requires the target cell line to be represented during training as a covariate. |
| Zero-shot unseen cell line (gene intersection) | No | CPA cannot generalize to cell lines absent from training; the covariate embedding for a new cell line does not exist. |
| Cross perturbation technology (gene intersection) | No | CPA was evaluated on drug perturbations (sci-Plex) and genetic knockouts separately; no cross-technology transfer was assessed. |
| Zero-shot gene misalignment | No | CPA assumes a fixed gene output vocabulary matching the training dataset; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | CPA achieves R² > 0.85 on held-out drug conditions in sci-Plex, substantially outperforming mean-expression and linear baselines on novel drug-dose combinations. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
