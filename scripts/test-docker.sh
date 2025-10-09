#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKERFILE_PATH="${PROJECT_ROOT}/Dockerfile"

if [[ -z "${PYTHON_VERSIONS:-}" ]]; then
  PYTHON_VERSIONS="$("${PROJECT_ROOT}/scripts/extract-python-versions.py")"
fi

read -r -a PYTHON_VERSION_ARRAY <<< "${PYTHON_VERSIONS}"

for version in "${PYTHON_VERSION_ARRAY[@]}"; do
  image_tag="hls-downloader-test:${version}"
  echo "==> Building ${image_tag}"
  docker build \
    --build-arg PYTHON_VERSION="${version}" \
    -t "${image_tag}" \
    -f "${DOCKERFILE_PATH}" \
    "${PROJECT_ROOT}"

  echo "==> Running tests in ${image_tag}"
  docker run --rm "${image_tag}"
done
