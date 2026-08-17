#!/usr/bin/env bash
# Start the tomo_2026b MD Jupyter stack.
#   ./md-run.sh              CPU  (port MD_PORT, default 8890)
#   ./md-run.sh --gpu        CUDA (port MD_GPU_PORT, default 8891; linux/amd64 + NVIDIA)
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/md/up-md.sh" "$@"
