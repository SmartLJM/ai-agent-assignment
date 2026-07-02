# Pertpy: End-to-End Python Framework for Single-Cell Perturbation Analysis

## Overview

Pertpy is a comprehensive Python-based modular framework for analyzing large-scale single-cell perturbation experiments. Heumos et al. (Nature Methods 2025) address the fragmentation in the single-cell perturbation analysis ecosystem—where tools are scattered, use incompatible data structures, and are limited to specific perturbation types—by building an integrated, extensible framework within the scverse ecosystem (compatible with Scanpy, scvi-tools, scirpy).

## Problem Being Solved

The explosion of high-throughput perturbation experiments (Perturb-seq, CROP-seq, Sci-plex) has created both analytical opportunities and challenges:
1. **Fragmentation**: Methods are scattered across R/Python, use incompatible data structures, and require separate installation
2. **Scale**: Existing frameworks (MUSIC, ScMAGeCK, SCEPTRE, GSFA, FR-Perturb) focus only on CRISPR screens and cannot scale to genome-scale datasets
3. **Context gap**: No framework integrates public annotations (cell line databases, compound databases, perturbation metadata) with measured data
4. **Limited generality**: Tools target specific perturbation types (genetic OR chemical OR disease) not multiple types simultaneously

## Framework Architecture

**Core data structures**: AnnData and MuData objects (scverse standard), ensuring interoperability with the broader single-cell ecosystem (Scanpy, squidpy, muon)

**Modular design**: 100+ composable, interoperable analysis functions organized in modules:

| Module | Functions |
|--------|-----------|
| Data loaders | Access to harmonized perturbation datasets |
| Metadata annotation | API requests to public databases (ChEMBL, KEGG, etc.) |
| gRNA assignment | Threshold-based + Poisson-Gaussian mixture for CRISPR guide assignment |
| Differential expression | Formulaic interface supporting multiple models |
| Pooled CRISPR screens | Mixscape (Papalexi et al.), scMAGeCK integration |
| Differential abundance | Milo, scCODA 2.0, tascCODA 2.0 |
| Multicellular programs | DIALOGUE for cell-cell interaction programs |
| Enrichment | Drug2Cell for drug signature enrichment |
| Response evaluation | Custom distance metrics, Augur, CINEMA-OT integration |

**GPU acceleration**: Sparse and memory-efficient implementations leveraging JAX parallelization, making pertpy implementations substantially faster than original tool implementations.

**Metadata integration**: Pertpy connects measured data with public annotation databases (drug targets, pathway annotations, compound metadata) automatically—enabling unprecedented biological contextualization.

## Key Use Cases Demonstrated

**Use Case 1 - CRISPRa Perturb-seq analysis**:
- CRISPR activation screen projected onto meaningful perturbation space
- Evaluation of preprocessing strategies' effect on perturbation discovery
- Identification of novel gene programs activated by transcription factor overexpression

**Use Case 2 - Drug response deconvolution**:
- Large-scale gene expression + drug response screen (sciPlex)
- Decomposition of perturbation responses into viability-dependent and viability-independent components
- Integration with ChEMBL metadata to contextualize compound effects

**Use Case 3 - Triple-negative breast cancer (TNBC)**:
- Compositional changes in cell type proportions
- Ranking of perturbation effects for candidate drug identification
- Integration with clinical metadata

## Installation and Availability

- GitHub: https://github.com/scverse/pertpy
- PyPI: installable via `pip install pertpy`
- Documentation and 15+ tutorials: https://pertpy.readthedocs.io
- Interoperates with scverse ecosystem tools

## Performance Advantages

Pertpy's JAX-based implementations of computationally intensive analyses (optimal transport, distance metrics, cell type composition testing) are substantially faster than original Python/R implementations, with Extended Data Fig. 1 showing 10-100x speedups depending on the analysis.

## Design Philosophy

Unlike prior tools that are analysis-specific, pertpy is designed as:
1. **Modular**: Functions can be chained into custom pipelines
2. **Extensible**: New methods can be added following scverse community guidelines
3. **Context-aware**: Integrates biological metadata to enrich interpretation
4. **Scale-appropriate**: GPU-accelerated for genome-scale perturbation data

## Limitations

Pertpy is primarily designed for scRNA-seq readouts; support for ATAC-seq and proteomic perturbation readouts is more limited. The framework is Python-only, which may exclude R-centric research groups. As a meta-framework wrapping many tools, ensuring consistent behavior across method updates requires ongoing maintenance.

## Citation

Heumos L, Ji Y, May L, Green TD, Peidli S, Zhang X, Wu X, Ostner J, Schumacher A, Hrovatin K, Muller M, Chong F, Sturm G, Tejada A, Dann E, Dong M, Pinto G, Bahrami M, Gold I, Rybakov S, Namsaraeva A, Moinfar AA, Zheng Z, Roellin E, Mekki I, Sander C, Lotfollahi M, Schiller HB, Theis FJ. "Pertpy: an end-to-end framework for perturbation analysis." Nature Methods (2025). DOI: 10.1038/s41592-025-02909-7

## Capability Summary

| Question | Answer | Evidence |
|----------|--------|----------|
| Unseen perturbation prediction | No | Pertpy is an analysis framework that wraps existing tools; it does not itself predict responses to unseen perturbations, though it integrates tools that can. |
| Cross cell-line (gene intersection) | Not evaluated | Pertpy provides the infrastructure for perturbation analysis including cross-cell-line scenarios, but is an integration framework rather than a predictive model. |
| Zero-shot unseen cell line (gene intersection) | Not evaluated | Pertpy wraps models that may support zero-shot transfer, but the framework itself is not a predictive model and does not evaluate this capability. |
| Cross perturbation technology (gene intersection) | Not evaluated | Pertpy is designed to handle multiple perturbation types (genetic, chemical, disease), but cross-technology generalization benchmarking is not a primary function of the framework. |
| Zero-shot gene misalignment | Not evaluated | As an analysis framework, Pertpy does not address gene vocabulary misalignment; this depends on the underlying tools it integrates. |
| Perturbation-specificity vs. simple baseline | Not evaluated | Pertpy provides 10-100x speedups over original tool implementations and integrates biological metadata, but is an infrastructure framework rather than a prediction model to compare against baselines. |

**Overall capability tier**: Benchmark-tool
