#!/usr/bin/env bash
# Build a service subfolder as linux/amd64 and push to Google Artifact Registry.
#
# Usage:
#   ./deploy-to-gcp.sh          # builds md/container (CPU Dockerfile, default)
#   ./deploy-to-gcp.sh container
# GPU image (linux/amd64 CUDA): build locally with
#   docker compose --profile gpu build md-gpu
# or tag/push tomo_2026b_md_gpu after Dockerfile.gpu.
#
# Environment (defaults shown):
#   PROJECT_ID   GCP project (default: tomopharma)
#   REGION       Artifact Registry region (default: us-west1)
#   ART_REPO     Repository name in Artifact Registry (default: tomopharma)
#   IMAGE        Image name in that repo (default: plat-<subfolder>, e.g. md)
#   TAG          Tag to push (default: latest)
#
# Prerequisites: Docker with buildx, gcloud authenticated, Artifact Registry repo exists,
# and permission to push. Run once per machine:
#   gcloud auth configure-docker "${REGION}-docker.pkg.dev"

set -euo pipefail

SUBFOLDER="${1:-container}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f "${SUBFOLDER}/Dockerfile" ]]; then
  echo "ERROR: No Dockerfile at ${SCRIPT_DIR}/${SUBFOLDER}/Dockerfile" >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-tomopharma}"
REGION="${REGION:-us-west1}"
ART_REPO="${ART_REPO:-tomopharma}"
TAG="${TAG:-latest}"
IMAGE="${IMAGE:-tomo_2026b_md}"

FULL_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ART_REPO}/${IMAGE}:${TAG}"

BUILDER_NAME="tomo-plat-gcp-builder"
if ! docker buildx inspect "${BUILDER_NAME}" >/dev/null 2>&1; then
  docker buildx create --name "${BUILDER_NAME}" --driver docker-container --use
else
  docker buildx use "${BUILDER_NAME}"
fi

if command -v gcloud >/dev/null 2>&1; then
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
fi

echo "Building and pushing: ${FULL_IMAGE}"
echo "  Dockerfile: ${SUBFOLDER}/Dockerfile  context: ${SUBFOLDER}/  platform: linux/amd64"
echo ""

docker buildx build \
  --platform linux/amd64 \
  -f "${SUBFOLDER}/Dockerfile" \
  -t "${FULL_IMAGE}" \
  --push \
  "${SUBFOLDER}"

echo ""
echo "Done: ${FULL_IMAGE}"
