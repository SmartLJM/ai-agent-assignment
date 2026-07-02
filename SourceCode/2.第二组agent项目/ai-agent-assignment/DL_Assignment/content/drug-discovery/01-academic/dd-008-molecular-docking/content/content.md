# Molecular Docking

**Knowledge set ID:** `dd-008-molecular-docking`  
**Theme:** `drug-discovery`  
**Source:** AutoDock Vina: improving the speed and accuracy of docking  

## Curated Content

Molecular docking predicts how a small molecule may orient within a target binding site and
estimates relative binding affinity using a scoring function. Docking can generate binding-pose
hypotheses, rank compounds, and support virtual screening. It requires target preparation, ligand
preparation, binding-site definition, conformational sampling, scoring, and pose inspection.
Docking is useful because it is faster and cheaper than testing every compound experimentally.
However, docking scores are not direct measurements of binding free energy, and they can be affected
by protein flexibility, water molecules, protonation states, covalent chemistry, metal coordination,
and scoring-function limitations.  A rigorous use of docking includes validation against known
ligands, visual inspection of plausible interactions, rescoring or consensus scoring where
appropriate, and experimental follow-up. The agent should not claim that the top docking score
automatically identifies the best drug.

## Key Concepts

- `molecular-docking`
- `binding-pose`
- `scoring-function`
- `virtual-screening`

## Retrieval Note

This self-contained knowledge set is used by the agent for grounded drug-discovery Q&A, benchmark citation, memory distillation, and dynamic orchestration evidence.
