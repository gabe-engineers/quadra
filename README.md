<p align="center">
  <img src="assets/readme-banner.png" alt="Quadra banner" width="960">
</p>

<h1 align="center">QUADRA</h1>

<p align="center">
  <strong>accelerate remote GPU development</strong>
</p>

<p align="center">
  Quadra is a Python CLI for shipping local experiment code to RunPod Serverless,
  running workflows against a persistent network volume, streaming logs, and
  pulling artifacts back into your project.
</p>

## Quick Start

```bash
quadra init bonsai
cd bonsai
quadra sync
quadra submit smoke
quadra logs
quadra pull
```

For the built-in workflow shortcuts:

```bash
quadra smoke
```

If you are already inside the target directory, `quadra init` also works without a
project name:

```bash
mkdir bonsai
cd bonsai
quadra init
```

## Core Commands

- `quadra init [project_name]` scaffolds a Quadra project in a new or current directory.
  Re-running it is safe: missing scaffold files are recreated and existing files are preserved.
- `quadra sync` pushes the local project into the configured RunPod network volume.
  If the configured volume does not exist yet, Quadra can offer to create one or
  link the project to an existing compatible volume interactively.
  Sync keeps a small remote manifest under `.quadra/` and only re-uploads files whose contents changed.
- `quadra submit <workflow>` submits a workflow job to the configured Serverless endpoint.
- `quadra logs` streams logs for the most recently submitted run.
- `quadra pull [run_id] [destination]` downloads a completed run into `runs/<run_id>/`.
- `quadra smoke` runs the full sync-submit-logs-pull loop for the default workflow.
  In the default scaffold, `smoke` runs `python main.py`.

## RunPod Serverless Model

Quadra targets RunPod Serverless only.

- Project sync and artifact pull use the RunPod S3-compatible API against the configured network volume.
- `quadra init` writes valid serverless `gpu_ids` pool values into `quadra.toml` as inline comments.
- `quadra init` also writes a `quadra_worker.py` worker script plus a configurable `[runtime.runpod.template]` block.
- The remote project directory defaults to `/runpod-volume/projects/<project_name>`.
- The first `submit` creates the configured RunPod template and endpoint if they do not already exist.
- `submit` sends a workflow job to a persistent Serverless endpoint.
- `logs` uses the saved local run reference to follow the latest submission.
- `pull` downloads the remote run directory back into the local project.

Your network volume must live in a RunPod datacenter that supports the S3-compatible API. Quadra checks this up front and fails early when the selected volume cannot be used for sync and artifact pull.

## Worker Contract

By default, Quadra creates a serverless template that starts:

```bash
python -u /runpod-volume/projects/<project_name>/quadra_worker.py
```

That worker script can be replaced by editing `[runtime.runpod.template]` in `quadra.toml`.

The default worker configures the serverless template to mount the RunPod network volume at `/runpod-volume`, runs the configured setup command, executes the workflow inside `src/experiment`, and writes logs, status, and artifacts under:

```text
/runpod-volume/projects/<project_name>/runs/<run_id>/
```

The scaffolded default uses a public CUDA-enabled `pytorch/pytorch` runtime image, bootstraps the `runpod` worker package into an isolated runtime under `/runpod-volume/projects/<project_name>/.quadra/worker-runtime`, writes worker startup traces to `/runpod-volume/projects/<project_name>/.quadra/worker-bootstrap.log`, and uses a `setup_command` that bootstraps `uv` into an isolated runtime under `/runpod-volume/projects/<project_name>/.quadra/uv-runtime` only when the image does not already provide it.

`timeout_seconds` in `runtime.runpod` is applied to the endpoint execution timeout when Quadra creates the endpoint.

## Build And Install

Build the package distributions with:

```bash
just build-cli
```

This writes a wheel and source distribution to `dist/`.

Install the current checkout as a uv-managed CLI tool with:

```bash
just install-cli
```

That command force-reinstalls `quadra` in editable mode via `uv tool install`, so local source changes are reflected without rebuilding. If `quadra` is not on your `PATH`, run `uv tool update-shell`.

## Regenerate RunPod REST Client

Quadra vendors generated control-plane client code under `src/quadra/_generated/runpod_rest_client/`.

Regenerate it from RunPod's official REST OpenAPI spec with:

```bash
just generate-runpod-rest-client
```

That script fetches `https://rest.runpod.io/v1/openapi.json` and re-runs `openapi-python-client`, so it requires outbound network access.

## Project Layout

`quadra init <project>` creates:

```text
<project>/
  quadra.toml
  quadra_worker.py
  src/
    libs/
      diffusers/
      transformers/
      vllm-omni/
    experiment/
      pyproject.toml
      main.py
  models/
  caches/
  runs/
  .quadra/
```
