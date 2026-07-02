# Perturb-seq: CRISPR Screens with Single-Cell Transcriptomics

## Overview

Perturb-seq is a high-throughput method that couples pooled CRISPR genetic screens with single-cell RNA sequencing (scRNA-seq). It enables simultaneous measurement of (1) which gene was perturbed (via sgRNA identity) and (2) the resulting genome-wide transcriptional response in each individual cell. This transforms a conventional pooled screen from a single-endpoint fitness readout into a rich multi-dimensional phenotyping platform.

## Experimental Workflow

### 1. Library Design and Cloning
- Design an sgRNA library targeting genes of interest (typically 2-10 sgRNAs/gene)
- Each sgRNA is paired with a unique perturbation barcode (PB) cloned into the 3' UTR of a reporter transcript (e.g., GFP or EGFP driven by a constitutive promoter)
- Library is cloned into a lentiviral backbone (e.g., pU6-sgRNA-EF1α-puro-PB)

### 2. Lentiviral Delivery
- Produce lentiviral particles from the library
- Transduce target cells at low multiplicity of infection (MOI < 0.3) to ensure most cells receive exactly one sgRNA
- Select transduced cells using puromycin or other selectable markers
- Allow 5-7 days for gene knockout to occur

### 3. Single-Cell Capture (10x Genomics / Drop-seq)
- Encapsulate individual cells into droplets together with barcoded beads
- Each droplet captures mRNA from a single cell, including:
  - Endogenous mRNAs (transcriptome)
  - Reporter mRNA containing the perturbation barcode (identifies the sgRNA)

### 4. Sequencing and Demultiplexing
- Library construction: endogenous transcriptome + targeted perturbation barcode amplification
- Sequencing: 2x paired-end reads
- Demultiplexing: match cell barcodes (from 10x) to perturbation barcodes to assign each cell its sgRNA identity
- Typical recovery: 500-5000 cells per perturbation condition

### 5. Analysis
- Cells are grouped by their sgRNA assignment
- Differential expression analysis compares cells with each perturbation vs. control (non-targeting sgRNA) cells
- Dimensionality reduction (PCA, UMAP) visualizes perturbation-induced transcriptional programs

## Key Technical Considerations

### Cell Coverage
- Minimum 50-100 cells per perturbation for reliable differential expression
- Larger screens (hundreds of genes) require careful upfront library size estimation

### Multiplets (Doublets)
- Cells receiving two sgRNAs (doublets) must be identified and removed
- Methods: Scrublet, DoubletFinder, or genetic demultiplexing

### Perturbation Efficiency
- Knockout efficiency varies by sgRNA; cells with non-functional sgRNAs reduce signal
- Some protocols verify editing by surveyor assay or amplicon sequencing of the target locus

### Batch Effects
- Large libraries may require multiple sequencing batches; careful batch correction is essential

## Variant Methods

| Method | Key Feature | Reference |
|--------|------------|-----------|
| Perturb-seq (original) | Perturbation barcodes in reporter 3' UTR | Dixit et al. 2016 |
| CROP-seq | sgRNA barcode in Pol III transcript | Datlinger et al. 2017 |
| CRISP-seq | Enriched populations + scRNA-seq | Jaitin et al. 2016 |
| Perturb-CITE-seq | Adds protein readout (ADT) | Frangieh et al. 2021 |
| Direct capture Perturb-seq | sgRNA captured directly by poly-dT | Replogle et al. 2022 |

## Applications

1. **Transcription factor network dissection**: Map which TFs regulate which gene expression programs
2. **Signaling pathway mapping**: Perturb multiple nodes and measure transcriptional consequences
3. **Genetic interaction mapping**: Double perturbations reveal epistatic relationships
4. **Drug mechanism of action**: Genetic modifiers of drug response
5. **Disease modeling**: Identify perturbations that recapitulate disease gene expression signatures

## Data Scale

The Replogle et al. 2022 "genome-scale Perturb-seq" study profiled ~2.5 million cells with ~10,000 gene perturbations in K562 cells—demonstrating the scalability of the approach to near-complete genome coverage.

## Analysis Pipeline (Recommended)

1. **Read alignment**: STARsolo or CellRanger
2. **sgRNA assignment**: CellRanger Feature Barcoding or custom scripts
3. **Quality filtering**: min_genes, max_genes, mt_fraction thresholds
4. **Normalization**: scran or total count normalization + log1p
5. **Perturbation DE**: pseudo-bulk DESeq2 or MAST for single-cell DE
6. **Visualization**: Scanpy/AnnData ecosystem
