#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/src/quadra/_generated/runpod_rest_client"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/runpod-rest-client.XXXXXX")"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export UV_TOOL_DIR="${UV_TOOL_DIR:-/tmp/uv-tools}"

uvx --from openapi-python-client openapi-python-client generate \
  --url https://rest.runpod.io/v1/openapi.json \
  --output-path "${TMP_DIR}/generated" \
  --overwrite

rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"
cp -R "${TMP_DIR}/generated/runpod_api_client/." "${TARGET_DIR}/"
