# GEARS: Graph Neural Network for Genetic Perturbation Prediction

## Overview

GEARS (Gene Expression And Regulation by Similarity) is a deep learning framework published in Nature Biotechnology (2023) that predicts transcriptional responses to single and combinatorial genetic perturbations. It addresses the key challenge that experimental measurement of all possible gene combination perturbations is intractable (2^n combinations for n genes), by using biological knowledge graphs to generalize to unseen perturbations.

## Problem Statement

Given:
- A set of single-gene perturbation measurements (e.g., ~100 CRISPR knockouts with scRNA-seq readout)
- Biological prior knowledge (Gene Ontology, co-expression networks)

Predict:
- Transcriptional responses to unseen single perturbations
- Transcriptional responses to unseen double (and higher-order) perturbations

This is a challenging out-of-distribution (OOD) prediction problem because the space of combinations is exponentially larger than the training data.

## Architecture

### Gene Knowledge Graph
GEARS constructs a multi-relational knowledge graph where:
- **Nodes**: Individual genes (typically 5000-18000 genes)
- **Edges**: Biological relationships from:
  - Gene Ontology (GO) term co-annotation (two genes sharing a GO term are connected)
  - Gene co-expression (Pearson correlation above threshold in normal cells)
  - Protein-protein interactions (STRING database)

### Graph Neural Network Encoder
A two-layer graph attention network (GAT) processes the gene graph:
1. Each gene node is initialized with a learnable embedding
2. Message passing aggregates information from biological neighbors
3. Output: context-aware gene embeddings that capture pathway membership

### Perturbation Embedding
For a perturbation involving gene *g*:
1. The perturbed gene's embedding is modified by a learned perturbation vector
2. This signal propagates through the graph via message passing
3. For double perturbations: two perturbation signals propagate simultaneously

### Expression Prediction
The model predicts the post-perturbation expression of all genes:
- Takes the propagated perturbation embeddings as input
- Outputs predicted log-fold changes or absolute expression values
- Trained to minimize MSE between predicted and observed expression

## Key Innovations

### Cross-perturbation Generalization
By encoding genes as graph nodes with biological context, GEARS can predict perturbation effects for genes not seen during training—as long as those genes are connected to seen genes in the knowledge graph.

### Combinatorial Prediction
Double-perturbation prediction is achieved by:
1. Running separate forward passes for each single perturbation
2. Combining the resulting graph states (via addition in latent space)
3. Predicting the combined expression profile

This additivity assumption works well for independent perturbations but can fail for strongly epistatic gene pairs.

## Training Data

GEARS was trained and validated on:
- **Norman et al. 2019**: 287 single and double gene perturbations in K562 leukemia cells (Perturb-seq)
- **Adamson et al. 2016**: 91 single perturbations in K562 cells (Perturb-seq)
- **Dixit et al. 2016**: BMDM cells with 24 perturbations

## Performance

### Benchmark Comparisons
GEARS outperforms baselines on OOD perturbation prediction:
- **GEARS** vs. mean baseline: ~30% reduction in MSE for double perturbation prediction
- **GEARS** vs. linear additive model: better capture of non-additive genetic interactions
- **GEARS** vs. scGEN (VAE-based): more interpretable, better graph-informed predictions

### Genetic Interaction Prediction
GEARS can predict genetic interaction types:
- Additive/independent pairs (most common)
- Synergistic pairs (stronger than additive)
- Antagonistic/suppressive pairs

## Limitations

1. **Additivity assumption**: Strong epistasis (synthetic lethality, pathway redundancy) is not always captured
2. **Knowledge graph coverage**: Genes with few GO annotations or interaction data have weaker embeddings
3. **Cell-type specificity**: Models trained on one cell line may not generalize to very different cell types
4. **Essential genes**: Strongly essential gene knockouts cause cell death, making training data sparse for these targets

## Usage

```python
from gears import PertData, GEARS

# Load perturbation data
pert_data = PertData('./data')
pert_data.load(data_name='norman')
pert_data.prepare_split(split='simulation')
pert_data.get_dataloader(batch_size=32, test_batch_size=128)

# Initialize and train GEARS
gears_model = GEARS(pert_data, device='cuda')
gears_model.model_initialize(hidden_size=64)
gears_model.train(epochs=20)

# Predict
gears_model.predict([['FOXA3', 'FOXF1']])  # double perturbation
```

## Related Models

| Model | Key Feature | Year |
|-------|------------|------|
| scGEN | VAE-based, conditional generation | 2019 |
| CPA | Compositional, additive latent space | 2021 |
| GEARS | Graph-informed, OOD combinatorial | 2023 |
| scGPT | Transformer foundation model | 2024 |
| PERT | BERT-based perturbation model | 2022 |

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | Yes | GEARS uses GO and co-expression graph priors to predict transcriptional responses for gene perturbations not seen during training, achieving ~30% MSE reduction over mean baseline on double-perturbation OOD splits. |
| Cross cell-line (gene intersection) | No | GEARS was trained and evaluated on K562 and BMDM cell lines separately; no explicit cross-cell-line transfer evaluation was performed. |
| Zero-shot unseen cell line (gene intersection) | No | The paper does not evaluate zero-shot transfer to completely unseen cell lines without any fine-tuning. |
| Cross perturbation technology (gene intersection) | No | GEARS targets CRISPR genetic knockouts only; no evaluation across different perturbation technologies is reported. |
| Zero-shot gene misalignment | No | GEARS requires a fixed gene vocabulary aligned to the training graph; completely different gene sets are not supported. |
| Perturbation-specificity vs. simple baseline | Yes | GEARS outperforms both additive linear models and mean expression baselines on novel double-gene perturbation combinations in the Norman dataset. |

**Overall capability tier**: Specialist
- Foundation: broad generalisation across cell lines and perturbation types
- Specialist: strong on seen conditions, limited OOD generalisation
- Benchmark-tool: primarily an evaluation or analysis framework
- Experimental-method: describes an experimental protocol, not a prediction model
