#!/usr/bin/env bash
# Stage a new Zenodo version in which only the code changes: code.zip, README.md and MANIFEST.sha256.
# The data files carry over from the published record; their checksums are taken from its manifest.
#
# Usage:
#   ./new_version.sh <published record id>            # stage in ~/zenodo_tomo_2026b_new
#   STAGE=/path ./new_version.sh 23966851
# Then: python zenodo_upload.py --stage <STAGE> --new-version-of <record id>
#
# Prerequisites: curl, zip, shasum, git.

set -euo pipefail

RECORD="${1:?published record id, e.g. 23966851}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE="${STAGE:-$HOME/zenodo_tomo_2026b_new}"
OUT="$STAGE/upload"
mkdir -p "$OUT"
rm -f "$OUT"/*

curl -fsSL "https://zenodo.org/records/$RECORD/files/MANIFEST.sha256?download=1" -o "$STAGE/MANIFEST.previous"
"$HERE/code_zip.sh" "$OUT/code.zip"
cp "$HERE/deposit_README.md" "$OUT/README.md"

# Previous checksums for the unchanged files, fresh ones for the files replaced here.
{
  grep -v -E '  (code\.zip|README\.md)$' "$STAGE/MANIFEST.previous"
  (cd "$OUT" && shasum -a 256 code.zip README.md)
} | sort -k2 > "$OUT/MANIFEST.sha256"

echo
echo "Staged in $OUT (files replaced in the new version):"
ls -l "$OUT"
echo "Manifest lists $(wc -l < "$OUT/MANIFEST.sha256" | tr -d ' ') files."
