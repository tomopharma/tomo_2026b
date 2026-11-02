#!/usr/bin/env bash
# Assemble the Zenodo deposit for the calx-β–IGF1R MD (replicates 1–3) in a local staging folder.
#
# Usage:
#   ./build_deposit.sh                  # stage in ~/zenodo_tomo_2026b
#   STAGE=/Volumes/big/zenodo ./build_deposit.sh
#
# Environment (defaults shown):
#   STAGE      staging folder; needs about 23 GB free (downloads + archives)
#   GCS_HOME   gs://ephemeralvm02-ephemeral-work/users/usr_00a477d6/home  (the Ephemeral VM's /workspace)
#   DATA_DIR   md/data of the main checkout (docking inputs; gitignored, so not in this worktree)
#   REPS       "1 2 3"
#
# Sources: the synced data folder (tomo_2026b/data/md_calx_3qqu_full), the production checkpoint
# backup (md_checkpoints/tomo_2026b; authoritative md.tpr / md.edr / md.log and the full md.xtc),
# the SI analysis outputs (md_results/tomo_2026b/si), and this repository at HEAD (notebooks, containers).
#
# Output in $STAGE/upload: the files to upload, a README.md and MANIFEST.sha256. Checkpoints (*.cpt),
# GROMACS backups (#…#) and equilibration coordinates are left out. Run zenodo_upload.py afterwards.
#
# Prerequisites: gcloud authenticated (gcloud auth login), zip, shasum, git.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
MAIN_CHECKOUT="$(git -C "$HERE" worktree list --porcelain | awk '/^worktree /{print $2; exit}')"
STAGE="${STAGE:-$HOME/zenodo_tomo_2026b}"
GCS_HOME="${GCS_HOME:-gs://ephemeralvm02-ephemeral-work/users/usr_00a477d6/home}"
DATA_DIR="${DATA_DIR:-$MAIN_CHECKOUT/md/data}"
REPS="${REPS:-1 2 3}"

DATA="$GCS_HOME/tomo_2026b/data/md_calx_3qqu_full"
CKPT="$GCS_HOME/md_checkpoints/tomo_2026b"
SI="$GCS_HOME/md_results/tomo_2026b/si"
RAW="$STAGE/raw"
OUT="$STAGE/upload"

for tool in gcloud zip shasum git; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
gcloud storage ls "$DATA/system_summary.json" >/dev/null || {
  echo "Cannot read $DATA — run: gcloud auth login" >&2; exit 1; }
for f in 3QQU.pdbqs calxbeta_18.39.pdb; do
  [[ -f "$DATA_DIR/3d_struct/$f" ]] || { echo "Missing docking input $DATA_DIR/3d_struct/$f (set DATA_DIR)" >&2; exit 1; }
done

mkdir -p "$RAW" "$OUT"
echo "Staging in $STAGE"

# --- Download (rsync skips files already present with the same size and date) ---
# Data folder: everything except checkpoints, GROMACS backups and equilibration coordinates.
gcloud storage rsync -r "$DATA" "$RAW/data" \
  --exclude='.*\.cpt$|.*#[^/]*#$|.*/(nvt|npt[0-9])\.gro$'
for r in $REPS; do
  gcloud storage rsync "$CKPT/rep$r" "$RAW/ckpt/rep$r" --exclude='.*\.cpt$|.*\.gro$'
done
gcloud storage rsync -r "$SI" "$RAW/si"

zip_dir() {  # zip_dir <archive> <folder> <entries…>: archive entries relative to <folder>
  local archive="$1" dir="$2"; shift 2
  rm -f "$OUT/$archive"
  (cd "$dir" && zip -q -r -X "$OUT/$archive" "$@")
}

# --- Code: notebooks and container definitions at HEAD ---
COMMIT="$(git -C "$REPO" rev-parse HEAD)"
rm -f "$OUT/code.zip"
git -C "$REPO" archive --format=zip --prefix=tomo_2026b/ -o "$OUT/code.zip" HEAD \
  md/notebooks/md1_igf1r3qqu_calxbeta_gromacs.ipynb \
  md/notebooks/md2_igf1r3qqu_calxbeta_pbsa_gbsa.ipynb \
  md/notebooks/md3_igf1r3qqu_calxbeta_binding_inspection.ipynb \
  md/container md/docker-compose.yml md/zenodo
echo "$COMMIT" > "$RAW/COMMIT.txt"
(cd "$RAW" && zip -q -X "$OUT/code.zip" COMMIT.txt)

# --- Docking inputs ---
rm -f "$OUT/inputs.zip"
(cd "$DATA_DIR" && zip -q -X "$OUT/inputs.zip" 3d_struct/3QQU.pdbqs 3d_struct/calxbeta_18.39.pdb)

# --- Shared system build ---
# complex_solv.gro and ions.tpr predate ion placement, so they are left out: each replicate's md.tpr
# holds the full solvated, ionized system and its topology.
mkdir -p "$RAW/system_build"
cp "$RAW/data/system_summary.json" "$RAW/data/ligand_calxbeta_chainB.pdb" \
   "$RAW/si/protonation_states.csv" "$RAW/system_build/"
zip_dir system_build.zip "$RAW" system_build

# --- Per replicate: analysis bundle and full trajectory ---
for r in $REPS; do
  rep="$RAW/rep${r}_analysis"
  rm -rf "$rep" && mkdir -p "$rep"
  # Everything in the data folder's rep dir except the equilibration stages (rep2 has its own archive).
  (cd "$RAW/data/rep$r" && find . -type f ! -name 'nvt*' ! -name 'npt*' ! -name 'mdout.mdp' -print0 \
     | xargs -0 -I{} rsync -R {} "$rep/")
  # The checkpoint backup holds the complete production md.tpr / md.edr / md.log.
  cp "$RAW/ckpt/rep$r/md.tpr" "$RAW/ckpt/rep$r/md.edr" "$RAW/ckpt/rep$r/md.log" "$RAW/ckpt/rep$r/md.mdp" "$rep/"
  zip_dir "rep${r}_analysis.zip" "$RAW" "rep${r}_analysis"
  # The trajectory is already compressed (xtc); a hard link avoids a second 3.6 GB copy.
  ln -f "$RAW/ckpt/rep$r/md.xtc" "$OUT/rep${r}_md_full.xtc"
done

# --- Replicate 2 equilibration (the only replicate whose stage files survived) ---
mkdir -p "$RAW/rep2_equilibration"
(cd "$RAW/data/rep2" && find . -maxdepth 1 -type f \( -name 'nvt*' -o -name 'npt*' \) -print0 \
   | xargs -0 -I{} cp {} "$RAW/rep2_equilibration/")
zip_dir rep2_equilibration.zip "$RAW" rep2_equilibration

# --- Summaries and SI analysis outputs ---
mkdir -p "$RAW/summaries_si"
cp "$RAW/data/mmpbsa_summary.json" "$RAW/data/binding_inspection_summary.json" "$RAW/summaries_si/"
cp -R "$RAW/si/." "$RAW/summaries_si/si/"
zip_dir summaries_si.zip "$RAW" summaries_si

# --- README and checksums ---
cp "$HERE/deposit_README.md" "$OUT/README.md"
(cd "$OUT" && find . -maxdepth 1 -type f ! -name MANIFEST.sha256 -print | sed 's#^\./##' | sort \
   | xargs shasum -a 256 > MANIFEST.sha256)

echo
echo "Deposit staged in $OUT (commit $COMMIT):"
ls -lh "$OUT"
du -sh "$OUT"
