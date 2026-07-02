# Mixscale and Scalable Perturb-seq for Molecular Pathway Signature Reconstruction

## Overview

This paper demonstrates a highly scalable Perturb-seq workflow to systematically characterize the transcriptional targets of signaling regulators across diverse biological contexts. The work from Satija lab (Jiang et al., Nature Cell Biology 2025) combines two key innovations: (1) a scalable experimental platform using Parse Biosciences combinatorial indexing compatible with Ultima Genomics sequencing, and (2) a new computational method called **Mixscale** that handles continuous perturbation efficiency gradients in CRISPRi data.

## Problem Being Solved

Understanding how signaling pathway regulators (IFN-β, IFNγ, TGF-β, TNF, insulin) affect transcriptional outputs requires profiling perturbations across many cell lines and biological contexts—a scale challenge that existing protocols cannot handle cost-effectively. Additionally, CRISPRi experiments produce continuous response gradients (cells differ in knockdown efficiency), and the previous binary Mixscape method oversimplifies this by classifying cells as "perturbed" or "not perturbed."

## Experimental Design

The authors performed Perturb-seq across:
- **6 cancer cell lines**: A549 (lung), MCF7 (breast), HT29 (colon), HAP1 (bone marrow), BxPC3 (pancreas), K562 (bone marrow)
- **5 signaling stimuli**: IFN-β, IFNγ, TGF-β, TNF, and insulin
- **5 pathway-specific CRISPRi libraries**: 44–61 genes per pathway, 3 sgRNAs per gene
- Total: **2.6 million cells** sequenced across two experimental replicates, generating >1,500 perturbation-context combinations

The scalable workflow used the Parse Biosciences Evercode Whole Transcriptome Mega kit, enabling fixed-sample multiplexing, and sequenced with Ultima Genomics' sequencing-by-synthesis technology with Illumina validation.

## Mixscale: Key Computational Innovation

Mixscale replaces the binary "perturbed/not perturbed" classification of Mixscape with a **continuous scalar perturbation score** for each cell:

1. For each sgRNA-targeting group, Mixscale estimates a "perturbation vector" by computing differential expression between targeted cells and their most similar non-targeting (NT) control cells.
2. Each targeted cell's expression profile is projected onto this perturbation vector to obtain a scalar score reflecting degree of perturbation.
3. For non-effect perturbations, all cells receive a uniform score of 1, reverting to unweighted analysis.

Downstream DEG analysis uses these scores as continuous weights via weighted regression, improving sensitivity and power. The approach is validated by showing that the Mixscale score correlates with the degree of target gene knockdown.

## Downstream Analysis: Signature Discovery

The conserved perturbation programs are discovered by:
1. Computing DEG lists for each perturbation-context combination
2. Using non-negative matrix factorization (NMF) or similar dimensionality reduction to identify coherent gene programs conserved across cell lines
3. Linking programs to specific pathway regulators

These data-driven signatures are then used for gene set enrichment scoring to infer signaling pathway activation in **in vivo** and **in situ** datasets of immune disorders (IBD, inflammation) and intestinal disorders—demonstrating that lab-derived perturbation signatures can characterize real disease states.

## Main Results

- Mixscale significantly outperforms binary classification at detecting differential expression in CRISPRi datasets
- The 1,500+ perturbation-context dataset reveals context-specific and conserved transcriptional responses to known pathway regulators
- Derived pathway signatures accurately infer pathway activation in independent in vivo scRNA-seq datasets
- The Ultima Genomics platform produces data quality comparable to Illumina at lower cost, validating sequencing platform scalability

## Limitations

The approach profiles known pathway regulators rather than discovering new ones. Generalization to other biological systems requires repeating the Perturb-seq assay. CRISPRi (knockdown) may not fully recapitulate knockout effects.

## Citation

Jiang L, Dalgarno C, Papalexi E, Mascio I, Wessels HH, Yun H, Iremadze N, Lithwick-Yanai G, Lipson D, Satija R. "Systematic reconstruction of molecular pathway signatures using scalable single-cell perturbation screens." Nature Cell Biology 27, 505–517 (2025). DOI: 10.1038/s41556-025-01622-z

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | Mixscale is a computational method for analyzing existing CRISPRi Perturb-seq data; it does not predict responses to perturbations not yet experimentally performed. |
| Cross cell-line (gene intersection) | Not evaluated | The Mixscale method processes continuous perturbation scores within a dataset; cross-cell-line perturbation prediction is not a capability of this experimental-computational workflow. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | Mixscale requires experimental Perturb-seq data from the target cells; zero-shot prediction on unseen cell lines is not applicable to this approach. |
| Cross perturbation technology (gene intersection) | Not evaluated | The workflow is specific to CRISPRi with continuous knockdown scoring; cross-technology generalization is not evaluated. |
| Zero-shot gene misalignment | Not evaluated | Mixscale operates on the gene expression data from the experimental dataset; gene vocabulary misalignment is not a relevant scenario. |
| Perturbation-specificity vs. simple baseline | Yes | Mixscale significantly outperforms binary Mixscape classification for detecting differential expression in CRISPRi datasets, with derived pathway signatures accurately characterizing in vivo disease states. |

**Overall capability tier**: Experimental-method
