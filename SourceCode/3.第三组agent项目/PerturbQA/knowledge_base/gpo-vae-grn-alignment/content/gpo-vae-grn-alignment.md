# GPO-VAE: GRN-Aligned Parameter Optimization for Perturbation Prediction

## Overview

GPO-VAE (Baek et al., 2025) extends CRADLE-VAE by incorporating Gene Regulatory Network (GRN) structure directly into the parameter optimization process. Rather than using the GRN only at the input feature level (as GEARS does), GPO-VAE constrains which model parameters are allowed to change when modeling a specific perturbation, guided by the network topology of the perturbed gene's regulatory neighborhood.

## Core Concept: GRN-Aligned Parameter Update

The central innovation is that when predicting the effect of knocking out gene g, GPO-VAE selectively updates only the subset of model parameters associated with genes in the k-hop regulatory neighborhood of g in the GRN. This creates:
1. **Sparse parameter updates**: Most of the model is frozen; only the biologically relevant parameters change.
2. **Interpretable perturbation effects**: The updated parameters map directly to regulatory relationships.
3. **Reduced overfitting**: Limiting parameter degrees of freedom prevents the model from fitting noise.

## Architecture

### Base Model: CRADLE-VAE
GPO-VAE inherits CRADLE-VAE's three-subspace latent decomposition:
- z_b: basal cell state
- z_p: perturbation effect
- z_a: experimental artifacts

### GRN Construction
The regulatory network is built from:
1. **Primary GRN**: Loaded from a pre-trained transcription factor regulatory database or inferred from the training data
2. **K-hop expansion**: For perturbation of gene g, the k-hop neighborhood (typically k=2 or 3) identifies the set of directly and indirectly regulated genes
3. **Co-expression augmentation**: Pearson correlation between genes supplements the GRN edges

### Parameter Optimization Layer
For each perturbation g, a mask is generated:
M_g ∈ {0,1}^(param_dim)

The gradient update during perturbation prediction training is:
θ_new = θ + α × M_g × ∇L(θ)

Only parameters in M_g (corresponding to the GRN neighborhood of g) receive gradient updates.

## DGE Loss: Differential Gene Expression Training Signal

GPO-VAE introduces a dedicated Differential Gene Expression (DGE) loss that directly supervises the model on the top differentially expressed genes rather than all genes equally:

L_DGE = MSE(ŷ[DEG_g], y[DEG_g])

where DEG_g is the set of top-k differentially expressed genes for perturbation g (identified from training data). This focuses the model on the most biologically meaningful prediction targets.

## GRN Explainability

Because parameter updates are GRN-constrained, GPO-VAE provides interpretable explanations:
- **Regulatory path attribution**: The magnitude of parameter updates along a regulatory path reflects the importance of that path for the perturbation response.
- **Gene influence scores**: Genes in the k-hop neighborhood are ranked by their contribution to the predicted perturbation effect.
- **Network visualization**: Updated parameters can be visualized as edge weights in the GRN subgraph.

## Results

On Norman et al. (2019) and Replogle et al. (2022):
- **DEG identification**: GPO-VAE achieves higher precision@k for top differentially expressed genes compared to CRADLE-VAE, CPA, and GEARS
- **OOD generalization**: Better performance on perturbations with no training data nearby in GRN topology
- **Interpretability**: Recovered regulatory relationships match known TF-target gene interactions

## Comparison with GEARS

| Aspect | GPO-VAE | GEARS |
|--------|---------|-------|
| GRN usage | Parameter mask (which params update) | Graph message passing |
| GRN source | Custom TF regulatory DB | Gene Ontology + co-expression |
| Explainability | Parameter-level attribution | Node embedding importance |
| Architecture | VAE (generative) | Regression (discriminative) |
| Drug support | Via CRADLE-VAE | Limited |

## Citations

Baek M, Oh S, Kim WJ (2025). GPO-VAE: Modeling Explainable Gene Perturbation Responses utilizing GRN-Aligned Parameter Optimization. *arXiv:2501.18973*.

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | GPO-VAE achieves better OOD generalization than CRADLE-VAE on perturbations with no training data nearby in GRN topology, evaluated on Norman and Replogle datasets. |
| Cross cell-line (gene intersection) | Partial | The paper evaluates on Norman and Replogle (different cell lines) and reports improved performance, though full cross-cell-line protocol details are limited. |
| Zero-shot unseen cell line (gene intersection) | No | No zero-shot unseen cell line evaluation without fine-tuning is reported; the model requires cell-line-specific training data. |
| Cross perturbation technology (gene intersection) | No | GPO-VAE focuses exclusively on CRISPR genetic perturbations; no cross-technology transfer is evaluated. |
| Zero-shot gene misalignment | No | GRN-aligned parameter masks are defined over the fixed training gene vocabulary; completely disjoint gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | GPO-VAE achieves higher precision@k for top differentially expressed genes compared to CRADLE-VAE, CPA, and GEARS, demonstrating perturbation-specific signal learning. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
