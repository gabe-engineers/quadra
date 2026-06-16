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
```

`hard-run` is the end-to-end loop: destroy any existing runtime, create a fresh one, sync the project, run the command, then tear the runtime down.

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

The logical remote root is `/workspace/projects/<project_name>`.

For the MVP, Quadra stages the synced remote workspace under `.quadra/runtime/<runtime_id>/...` so `run` and `shell` execute against the synced copy instead of the source tree.
