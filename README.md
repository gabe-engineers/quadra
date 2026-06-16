# Quadra

Quadra is a Python CLI for the four-part experiment loop:

1. create runtime
2. sync project
3. run experiment
4. destroy runtime

## Commands

```bash
quadra init bonsai
cd bonsai
quadra up
quadra sync
quadra run smoke
quadra shell
quadra destroy
quadra hard-run smoke

mkdir bonsai
cd bonsai
quadra init
```

Build a standalone CLI executable with `just build-cli`. The binary will be written to `dist/quadra`.
Install it via symlink with `just install-cli`, which links `dist/quadra` into `~/.local/bin/quadra`.

`quadra init` also works without a name. In that case it scaffolds into the current directory, uses the directory name as the project name, and leaves unrelated existing files alone.

`hard-run` is the end-to-end loop: destroy any existing runtime, create a fresh one, sync the project, run the command, then tear the runtime down.

Quadra currently targets RunPod only. Configure the `[runtime.runpod]` block in `quadra.toml`, export `RUNPOD_API_KEY`, and `quadra up` will provision or rediscover the project pod by name, attach the configured network volume, and wait for SSH readiness.

## Project Contract

`quadra init <project>` creates:

```text
<project>/
  quadra.toml
  src/
    libs/
      diffusers/
      transformers/
      vllm-omni/
    experiment/
      pyproject.toml
      main.py
      scripts/
        smoke.py
        bench.py
  models/
  caches/
  runs/
  .quadra/
```

The logical remote root is `/workspace/<project_name>`.

`sync`, `run`, and `shell` all target the live RunPod pod over SSH.
