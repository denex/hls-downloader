#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

versions="$("${PROJECT_ROOT}/scripts/extract-python-versions.py")"
if [[ -z "${versions}" ]]; then
  echo "No Python versions found in workflow definition" >&2
  exit 1
fi

export PYTHON_VERSIONS="${versions}"
exec "${PROJECT_ROOT}/scripts/test-docker.sh"
