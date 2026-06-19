set shell := ["bash", "-cu"]

default:
    @just --list

build-cli out_dir="dist":
    env UV_CACHE_DIR=/tmp/uv-cache uv build --out-dir "{{out_dir}}"

install-cli:
    env UV_CACHE_DIR=/tmp/uv-cache uv tool install --force --editable .
    echo "installed editable quadra tool; run 'uv tool update-shell' if 'quadra' is not on PATH"

generate-runpod-rest-client:
    ./scripts/generate_runpod_rest_client.sh
