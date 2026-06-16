set shell := ["bash", "-cu"]

default:
    @just --list

build-cli out_dir="dist":
    env UV_CACHE_DIR=/tmp/uv-cache uv run --extra build pyinstaller \
      --noconfirm \
      --clean \
      --onefile \
      --name quadra \
      --paths src \
      --add-data "$PWD/src/quadra/assets:quadra/assets" \
      --distpath {{out_dir}} \
      --workpath .quadra/build/pyinstaller/work \
      --specpath .quadra/build/pyinstaller/spec \
      src/quadra/__main__.py

install-cli bin_dir="${HOME}/.local/bin":
    just build-cli
    mkdir -p "{{bin_dir}}"
    ln -sfn "$PWD/dist/quadra" "{{bin_dir}}/quadra"
    echo "linked {{bin_dir}}/quadra -> $PWD/dist/quadra"
