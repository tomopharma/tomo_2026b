#!/usr/bin/env bash
# Upload md/data/ to the shared GCS prefix (see README.md).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/gcs_data.py" upload "$@"
