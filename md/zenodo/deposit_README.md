# calx-β–IGF1R kinase: molecular dynamics and MM-GBSA data

Data behind the molecular dynamics supplement of a manuscript on calx-β binding to the IGF1R kinase,
submitted to *Biomolecules* (MDPI).

- **System:** docked calx-β domain (integrin β4 residues 989–1107) on the full IGF1R kinase domain
  (PDB 3QQU, residues 988–1282). Residues 1094–1103 have no coordinates in 3QQU; the kinase chain is
  split there and both new ends are capped (ACE/NME), as are all other chain ends.
- **Simulation:** AMBER99SB-ILDN, TIP3P, 0.150 M NaCl, rhombic dodecahedron, 97,551 atoms.
  Staged equilibration (3 ns), then 100 ns production at 300 K and 1 bar; three replicates with
  velocity seeds 1001, 1002, 1003. GROMACS 2025.4.
- **Binding energy:** single-trajectory MM-GBSA with gmx_MMPBSA 1.7.1 on 1,001 frames per replicate
  (every 100 ps). GBn2 (igb = 8, mbondi3) is the primary model, OBC-II (igb = 5, mbondi2) the
  sensitivity check. Computational alanine scanning of K1020A, D1021A, E1022A (the 3A mutant) and of
  three far-field controls (K1251A, D1183A, E1224A).

## Files

| File | Contents |
| --- | --- |
| `README.md` | This file |
| `MANIFEST.sha256` | SHA-256 checksum of every other file (`shasum -a 256 -c MANIFEST.sha256`) |
| `code.zip` | Notebooks md1 (system build and MD), md2 (MM-GBSA), md3 (binding inspection); container definitions; `COMMIT.txt` = repository commit |
| `inputs.zip` | Docking inputs: `3QQU.pdbqs` (receptor) and `calxbeta_18.39.pdb` (docked calx-β pose) |
| `system_build.zip` | `system_summary.json` (build facts: caps, charge, ions, box, minimization), `protonation_states.csv` (PROPKA at pH 7.4), `ligand_calxbeta_chainB.pdb` |
| `rep{1,2,3}_md_full.xtc` | Full 100 ns production trajectory, all atoms, every 10 ps (about 3.6 GB each) |
| `rep{1,2,3}_analysis.zip` | Per replicate: production `md.tpr` / `md.edr` / `md.log` / `md.mdp`, topology (`topol.top`, `*.itp`), `md_pbc.xtc` (protein only, made whole in one periodic image, every 100 ps), `md_binding_metrics.csv`, `mmpbsa/` (every gmx_MMPBSA input and result, per-frame ΔG and ΔΔG) |
| `rep2_equilibration.zip` | Replicate 2 equilibration stages NVT and NPT1–NPT4: run inputs, logs and energy files where kept (NPT1 has no log, NPT4 no energy file; its averages are in `npt4.log`) |
| `summaries_si.zip` | `mmpbsa_summary.json` (all MM-GBSA and alanine-scan results), `binding_inspection_summary.json`, and `si/` (energy, periodic-image and kinase-gap analyses used in the supplement) |

## Loading the data

- Each `md.tpr` holds the complete solvated, ionized system with its parameters. To view a full
  trajectory: `gmx trjconv -s rep1_analysis/md.tpr -f rep1_md_full.xtc -pbc mol -center`.
- `md_pbc.xtc` matches the protein-only run input `mmpbsa/complex.tpr` in the same archive; with
  MDTraj use `md_protein.gro` as the topology.
- Units are GROMACS units (nm, ps, kJ mol⁻¹) except MM-GBSA results, which are in kcal mol⁻¹.
  ΔΔG = ΔG(mutant) − ΔG(wild type); positive means the mutation weakens binding.

## Provenance notes

- **Replicate 1**, according to its log, was started as a 1 ns run and extended to 100 ns from its checkpoint; `md.edr`
  and `md.xtc` cover the full 100 ns (50,000,000 steps).
- **Equilibration** stage files survive for replicate 2 only. Replicates 1 and 3 used the same
  protocol from the same minimized structure; their production files are complete.
- **`protonation_states.csv`** was regenerated with the md1 notebook from the same inputs after the
  original file was lost. It reproduces the recorded build exactly (same caps, the same two
  non-standard residues GLU1115 → GLH and ASP1191 → ASH, the same 59 interface residues).
- The solvated box before minimization is not included; each `md.tpr` contains the full system.

## Licence

Creative Commons Attribution 4.0 International (CC BY 4.0). The 3QQU coordinates derive from the
Protein Data Bank entry 3QQU.
