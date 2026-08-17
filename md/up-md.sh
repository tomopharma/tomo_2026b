#!/usr/bin/env bash
# Start md container and open Jupyter in browser once ready.
#
# Usage:
#   ./up-md.sh                # CPU image (default, port MD_PORT / 8890)
#   ./up-md.sh --build        # rebuild CPU image then start
#   ./up-md.sh --gpu          # CUDA image (linux/amd64 + NVIDIA, port MD_GPU_PORT / 8891)
#   ./up-md.sh --gpu --build  # rebuild GPU image then start

set -euo pipefail
cd "$(dirname "$0")"

BUILD=false
GPU=false
while (($#)); do
    case "${1:-}" in
        --build)
            BUILD=true
            shift
            ;;
        --gpu)
            GPU=true
            shift
            ;;
        -h | --help)
            echo "Usage: $0 [--gpu] [--build]"
            echo "  --gpu    CUDA GROMACS image (linux/amd64, NVIDIA Container Toolkit)"
            echo "  --build  Rebuild image before starting"
            exit 0
            ;;
        *)
            echo "error: unknown argument: $1 (try --help)" >&2
            exit 1
            ;;
    esac
done

if [[ "${GPU}" == true ]]; then
    SERVICE="md-gpu"
    COMPOSE=(docker compose --profile gpu)
    PORT="${MD_GPU_PORT:-8891}"
    ENV_HINT="environment-gpu.yml / Dockerfile.gpu"
else
    SERVICE="md"
    COMPOSE=(docker compose)
    PORT="${MD_PORT:-8890}"
    ENV_HINT="environment.yml"
fi

if [[ "${BUILD}" == true ]]; then
    echo "Rebuilding ${SERVICE} image (${ENV_HINT})..."
    "${COMPOSE[@]}" build "${SERVICE}"
fi

echo "Starting ${SERVICE} container..."
"${COMPOSE[@]}" up -d "${SERVICE}"

echo "Waiting for Jupyter to be ready on port ${PORT}..."
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/" 2>/dev/null | grep -q "200\|302"; then
        echo "Jupyter is ready."
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo "Timeout waiting for Jupyter. Opening anyway..."
    fi
    sleep 2
done

echo "Opening browser..."
LAB_URL="http://127.0.0.1:${PORT}/"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "${LAB_URL}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "${LAB_URL}" 2>/dev/null || sensible-browser "${LAB_URL}" 2>/dev/null || echo "Open ${LAB_URL} in your browser"
else
    echo "Open ${LAB_URL} in your browser"
fi

if [[ "${GPU}" == true ]]; then
    echo "GPU check: docker compose --profile gpu exec md-gpu gmx --version | grep -i gpu"
    echo "           docker compose --profile gpu exec md-gpu nvidia-smi"
fi

echo "View logs with: ${COMPOSE[*]} logs -f ${SERVICE}"
"${COMPOSE[@]}" logs -f "${SERVICE}"
