#!/usr/bin/env bash
# Build a service subfolder as linux/amd64 and push to Google Artifact Registry.
#
# Usage:
#   ./deploy-to-gcp.sh                 # builds md/container (CPU Dockerfile, default)
#   ./deploy-to-gcp.sh container
#   ./deploy-to-gcp.sh --gpu           # builds container/Dockerfile.gpu (CUDA) for the Ephemeral VM
#   ./deploy-to-gcp.sh --gpu container
#
# Environment (defaults shown as CPU / --gpu):
#   PROJECT_ID   GCP project            (tomopharma / ephemeralvm02)
#   REGION       Artifact Registry region (us-west1 / us-west1)
#   ART_REPO     Repository in Artifact Registry (tomopharma / ephemeral-containers)
#   IMAGE        Image name in that repo (tomo_2026b_md / tomo-2026b-md-gpu)
#   TAG          Tag to push            (latest / today's date, e.g. 2026-10-27)
#
# A --gpu push does not change what Ephemeral runs: point the deployment at the new tag.
# The image holds only the environment; notebooks reach /workspace separately.
#
# Prerequisites: Docker with buildx, gcloud authenticated, Artifact Registry repo exists,
# and permission to push. Run once per machine:
#   gcloud auth configure-docker "${REGION}-docker.pkg.dev"

set -euo pipefail

GPU=false
SUBFOLDER="container"
for arg in "$@"; do
  case "$arg" in
    --gpu) GPU=true ;;
    -*)
      echo "ERROR: unknown option ${arg} (only --gpu is supported)" >&2
      exit 1
      ;;
    *) SUBFOLDER="$arg" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "$GPU" == true ]]; then
  DOCKERFILE="${SUBFOLDER}/Dockerfile.gpu"
  PROJECT_ID="${PROJECT_ID:-ephemeralvm02}"
  ART_REPO="${ART_REPO:-ephemeral-containers}"
  IMAGE="${IMAGE:-tomo-2026b-md-gpu}"
  TAG="${TAG:-$(date +%Y-%m-%d)}"
else
  DOCKERFILE="${SUBFOLDER}/Dockerfile"
  PROJECT_ID="${PROJECT_ID:-tomopharma}"
  ART_REPO="${ART_REPO:-tomopharma}"
  IMAGE="${IMAGE:-tomo_2026b_md}"
  TAG="${TAG:-latest}"
fi
REGION="${REGION:-us-west1}"

if [[ ! -f "${DOCKERFILE}" ]]; then
  echo "ERROR: No Dockerfile at ${SCRIPT_DIR}/${DOCKERFILE}" >&2
  exit 1
fi

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
echo "  Dockerfile: ${DOCKERFILE}  context: ${SUBFOLDER}/  platform: linux/amd64"
echo ""

docker buildx build \
  --platform linux/amd64 \
  -f "${DOCKERFILE}" \
  -t "${FULL_IMAGE}" \
  --push \
  "${SUBFOLDER}"

echo ""
echo "Done: ${FULL_IMAGE}"
