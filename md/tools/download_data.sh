#!/usr/bin/env bash
# Download the shared GCS prefix into md/data/ (see README.md).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/gcs_data.py" download "$@"
