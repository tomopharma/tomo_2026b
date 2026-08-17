#!/usr/bin/env bash
# Start Jupyter so Ephemeral can serve it under /s/<session-id>/ (JUPYTER_BASE_URL).
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
export WORKSPACE_DIR
mkdir -p "${WORKSPACE_DIR}"

exec jupyter notebook \
  --config=/opt/tomo/jupyter_notebook_config.py \
  --ip=0.0.0.0 \
  --port=8888 \
  --allow-root \
  --no-browser \
  --notebook-dir="${WORKSPACE_DIR}"
