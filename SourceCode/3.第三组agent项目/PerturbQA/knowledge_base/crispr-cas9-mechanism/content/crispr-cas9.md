# CRISPR-Cas9 Mechanism of DNA Cleavage

## Overview

CRISPR-Cas9 (Clustered Regularly Interspaced Short Palindromic Repeats - CRISPR-associated protein 9) is a prokaryotic adaptive immune system repurposed as a genome editing tool. It uses a single guide RNA (sgRNA) to direct the Cas9 endonuclease to a specific DNA sequence, where it creates a double-strand break (DSB).

## Components

### Cas9 Protein
SpCas9 (from *Streptococcus pyogenes*) is a 1368-amino-acid multidomain protein containing:
- **RuvC domain**: cleaves the non-complementary (non-template) DNA strand
- **HNH domain**: cleaves the complementary strand (same strand as the sgRNA)
- **PAM-interacting (PI) domain**: recognizes the 5'-NGG-3' PAM sequence
- **Bridge helix**: makes contacts with the sgRNA:DNA heteroduplex

### Guide RNA (sgRNA)
A single guide RNA is a chimeric RNA combining:
- **crRNA (CRISPR RNA)**: ~20 nt sequence complementary to the target DNA
- **tracrRNA (trans-activating crRNA)**: scaffold that recruits and activates Cas9

The first 20 nucleotides of the sgRNA define target specificity and can be changed to redirect Cas9 to any genomic sequence.

## Mechanism of Action

### Step 1: PAM Recognition
Cas9 scans the genome by repeatedly binding and releasing double-stranded DNA. The PAM-interacting domain interrogates DNA for the PAM sequence (5'-NGG-3' for SpCas9). PAM recognition is the first checkpoint for target binding.

### Step 2: R-loop Formation
After PAM binding, Cas9 locally unwinds the DNA duplex. The sgRNA (crRNA portion) begins to hybridize to the unwound strand in a 3'→5' direction from the PAM. This creates an R-loop (RNA-DNA hybrid) that propagates through the 20-nt protospacer.

### Step 3: Conformational Activation
Complete R-loop formation triggers a conformational change in Cas9 that repositions both the HNH and RuvC nuclease domains over their respective cleavage sites. This is a kinetic checkpoint—mismatches in the seed region (positions 1-12 from PAM) prevent full R-loop formation and inhibit activation.

### Step 4: DNA Cleavage
- **HNH domain** cleaves the complementary strand (strand base-paired with sgRNA), between positions 3 and 4 upstream of the PAM
- **RuvC domain** cleaves the non-complementary strand at the same position
- Together, these produce a blunt-ended DSB approximately 3 bp upstream of the PAM

### Step 5: DNA Repair
The DSB triggers two competing repair pathways:
- **NHEJ (Non-Homologous End Joining)**: error-prone, produces small insertions or deletions (indels) → gene disruption/knockout
- **HDR (Homology-Directed Repair)**: if a DNA repair template is provided, enables precise sequence substitutions, insertions, or corrections

## PAM Requirements by Cas9 Variant

| Variant | PAM | Source organism |
|---------|-----|----------------|
| SpCas9 | NGG | *S. pyogenes* |
| SaCas9 | NNGRRT | *S. aureus* |
| Cas12a (Cpf1) | TTTV | *Acidaminococcus* |
| SpCas9-NG | NG | Engineered |
| SpRY | NRN/NYN | Engineered |

## High-Fidelity Variants

Standard SpCas9 can tolerate 1-3 mismatches between sgRNA and DNA, leading to off-target cleavage. Engineered high-fidelity variants include:
- **eSpCas9**: alanine substitutions weakening non-specific DNA contacts
- **HiFi Cas9 (R691A)**: single substitution reducing mismatch tolerance
- **HypaCas9**: mutations in the REC3 domain improve discrimination
- **evoCas9**: directed evolution for improved specificity

## Key Specifications (SpCas9)
- Target length: 20 nt protospacer
- DSB position: 3 bp upstream of PAM
- Cleavage type: blunt-ended DSB
- Off-target tolerance: up to 3-5 mismatches (PAM-distal region)
- Seed region: positions 1-12 from PAM (mismatch-intolerant)
