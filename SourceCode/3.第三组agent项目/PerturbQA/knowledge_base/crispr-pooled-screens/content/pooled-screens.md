# CRISPR Pooled Screens: Design and Analysis

## Overview

Pooled CRISPR screens deliver a library of thousands of sgRNAs collectively to a large cell population and read out phenotypes by deep sequencing. They enable genome-wide functional genomics at lower cost and higher throughput than arrayed formats.

## Screen Types

### Negative Selection (Dropout) Screens
- **Goal**: identify genes essential for cell viability or proliferation
- **Mechanism**: sgRNAs targeting essential genes cause cell death → those sgRNAs drop out of the population
- **Readout**: sgRNA abundance decreases over time (T0 vs. endpoint comparison)
- **Examples**: essential gene identification, sensitivity to chemotherapy

### Positive Selection Screens
- **Goal**: identify genes whose loss confers a selective advantage
- **Mechanism**: resistant cells survive selective pressure → sgRNAs against resistance genes become enriched
- **Readout**: sgRNA abundance increases during selection
- **Examples**: drug resistance, immune evasion, oncogene bypass

### Reporter-based Screens
- Sort cells based on a reporter (GFP, luciferase) driven by a gene of interest
- sgRNAs that affect reporter expression are enriched or depleted

## Library Design Principles

### sgRNA Coverage
- **Standard**: 3-6 sgRNAs per gene (more = greater statistical power)
- **GeCKO v2**: ~6 sgRNAs/gene, genome-wide (~200,000 sgRNAs for human)
- **Brunello**: 4 sgRNAs/gene, optimized for activity (77,441 sgRNAs)

### sgRNA Activity Optimization
- Select top-ranked sgRNAs by Rule Set 2 (Doench score) or Azimuth
- GC content: 40-70%
- Avoid poly-T runs (>4 consecutive T's terminate Pol III)
- Target early exons to maximize protein loss

### Controls
- **Negative controls**: 500-1000 non-targeting sgRNAs (scrambled sequences) for normalization
- **Positive controls**: 100-200 sgRNAs targeting known essential genes (e.g., RPL11, RPS19)
- Positive controls validate screen quality (should deplete in dropout screens)

### Transduction (MOI)
- MOI < 0.3 ensures ~26% of cells are transduced (Poisson distribution), mostly with one sgRNA
- Multiple integrations confound sgRNA assignment

## MAGeCK Analysis Pipeline

MAGeCK (Model-based Analysis of Genome-wide CRISPR Knockout) is the standard analysis tool.

### Step 1: Read Count Generation
```bash
mageck count -l library.txt -n sample --sample-label "T0,T14" \
  --fastq T0_R1.fastq T14_R1.fastq
```
Outputs a count table: rows = sgRNAs, columns = samples

### Step 2: Normalization
- Median ratio normalization (similar to DESeq2 size factors)
- Corrects for sequencing depth differences between samples

### Step 3: sgRNA-Level Test
- Negative binomial model for count data (accounts for overdispersion)
- Tests each sgRNA for significant changes between conditions
- Output: log2 fold-change, p-value, FDR per sgRNA

### Step 4: Gene-Level Score (RRA)
- **Robust Rank Aggregation (RRA)**: combines p-values from multiple sgRNAs per gene
- Ranks sgRNAs by their individual p-values, then tests if those ranks are biased (stochastically smaller than expected by chance)
- RRA score: smaller = more significant depletion/enrichment
- Generates separate positive and negative selection scores

```bash
mageck test -k count_table.txt -t T14 -c T0 -n results
```

### Step 5: Quality Control Metrics
- **Gini index**: measures sgRNA count distribution uniformity (low = good library coverage)
- **Positive control enrichment**: essential gene sgRNAs should deplete
- **Correlation**: replicate Pearson/Spearman correlation (>0.95 expected)
- **Read mapping rate**: >70% of reads mapping to library

## Screen Quality Metrics

| Metric | Good | Acceptable |
|--------|------|-----------|
| Sequencing depth | >500 reads/sgRNA | >200 reads/sgRNA |
| Mapping rate | >90% | >70% |
| Gini index | <0.2 | <0.35 |
| Replicate correlation | >0.98 | >0.95 |
| Essential gene AUC | >0.85 | >0.7 |

## Statistical Considerations

### Library Coverage
- Maintain ≥200-500 cells per sgRNA at all time points
- For a 100,000-sgRNA library: maintain ≥20-50 million cells at each step
- Cell bottlenecks cause statistical noise (reduced representation)

### Replicates
- Minimum 2 biological replicates
- Pool replicates by weighting or use replicate-aware analysis (DESeq2, MAGeCK MLE)

### Hit Calling
- FDR < 0.05 is standard threshold
- Validate top hits with individual sgRNAs in secondary screens

## Alternative Analysis Tools

| Tool | Key Feature |
|------|------------|
| MAGeCK MLE | Maximum likelihood estimation, handles multiple conditions |
| BAGEL2 | Bayesian analysis, better for essential gene calls |
| CRISPhieRmix | Mixture model for improved sensitivity |
| PBNPA | Permutation-based, robust to model misspecification |
