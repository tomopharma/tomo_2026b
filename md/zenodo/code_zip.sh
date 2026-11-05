#!/usr/bin/env bash
# Write code.zip: the whole repository at HEAD under tomo_2026b/, plus COMMIT.txt.
#
# Usage: ./code_zip.sh <out.zip>
# Untracked and ignored files (data, md/.local.env) are never included.

set -euo pipefail

OUT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
REPO="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

rm -f "$OUT"
git -C "$REPO" archive --format=zip --prefix=tomo_2026b/ -o "$OUT" HEAD
git -C "$REPO" rev-parse HEAD > "$TMP/COMMIT.txt"
(cd "$TMP" && zip -q -X "$OUT" COMMIT.txt)
echo "code.zip: $(unzip -Z1 "$OUT" | grep -vc '/$') files at $(cat "$TMP/COMMIT.txt")"
