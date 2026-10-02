# `md/data` file descriptions

`md/data` currently holds six docking inputs (about 1.3 MB). There are no GROMACS or MM-GBSA outputs in that folder. This directory is gitignored.

## `3d_struct/3QQU.pdbqs` (251 KB)

The IGF1R kinase receptor used for AutoDock. It is a PDBQS file (PDB coordinates plus partial charges and AutoDock atom parameters). It contains one chain, A, with 285 residues and 2,702 atoms, starting at Glu988. The GROMACS notebook reads this as the receptor.

## `3d_struct/calxbeta_18.39.pdb` (96 KB)

The docked calx-β pose used as the MD ligand. It is a plain PDB with 119 residues and 1,190 atoms (Arg989 through Glu1107), no chain ID, and the segment name `calx`. The filename records the docked energy (−18.39 kcal/mol); that number is not written inside the file.

## `3d_struct/IVM_17.45_3QQU.pdb` (7 KB)

One ivermectin pose on 3QQU: residue `IVM`, 65 atoms, one model. AutoDock header: run 11, cluster rank 2, final docked energy −17.45 kcal/mol, estimated binding free energy −13.59 kcal/mol. The file is wrapped in an RTF (Rich Text Format) envelope, so it is not a raw PDB until that wrapper is stripped.

## `3d_struct/IVM_3qqu_mid_17.25.pdb` (7 KB)

Another ivermectin pose, also residue `IVM` with 65 atoms. Header: run 13, cluster rank 1 (2 members in that cluster), final docked energy −17.25 kcal/mol, estimated binding free energy −13.22 kcal/mol, from the parameter file `1VM_3QQU_mid.dpf`. This one is a plain PDB.

## `docking_logs/1VM_3QQU_mid.dlg` (477 KB)

AutoDock 3.05 log from 26 Mar 2026, 10:31:18, using `1VM_3QQU_mid.dpf` and grid maps `3QQU_a.gpf`. It records 25 Lamarckian genetic-algorithm runs, clustered into 21 conformations. The best cluster’s final docked energy is −17.25 kcal/mol (run 13). That pose is the one saved as `IVM_3qqu_mid_17.25.pdb`.

## `docking_logs/1VM_3QQU_mid_2.dlg` (477 KB)

A second AutoDock 3.05 log, five seconds later (10:31:23), with the same parameter file and 25 runs. Its best listed final docked energy is −18.17 kcal/mol. The −17.45 kcal/mol pose in `IVM_17.45_3QQU.pdb` (run 11) comes from this log.

## File Usage

Only the two ivermectin PDB files are opened by a notebook, and only by `md1_igf1r3qqu_calxbeta_gromacs.ipynb`. The docking logs are not used.

**`md1_igf1r3qqu_calxbeta_gromacs.ipynb`** lists every file in `data/3d_struct/`, so it opens both `IVM_17.45_3QQU.pdb` and `IVM_3qqu_mid_17.25.pdb` for the structure summary table (atom and residue counts). The 3D viewer loop then skips any path containing `IVM`. The MD pipeline uses only `3QQU.pdbqs` and `calxbeta_18.39.pdb`.

**`md2` and `md3`** do not reference either IVM PDB.

**`1VM_3QQU_mid.dlg` and `1VM_3QQU_mid_2.dlg`** are not read by any notebook. The HTML exports only repeat the table text from the MD1 export; they do not load these files.
