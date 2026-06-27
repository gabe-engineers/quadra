from __future__ import annotations

import hashlib
import importlib.resources
import json
import logging
import os
import posixpath
import re
import subprocess
import sys
import textwrap
import time
import tomllib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path, PurePosixPath
from typing import Any

import click
import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from quadra import __version__
from quadra.errors import QuadraError
from quadra.runpod_rest import RunpodRestClient, normalize_gpu_type_groups

logger = logging.getLogger("quadra")

CONFIG_FILENAME = "quadra.toml"
GLOBAL_CONFIG_ENV = "QUADRA_CONFIG"
GLOBAL_CONFIG_PATH = Path("~/.config/quadra/config.toml")
STATE_DIRNAME = ".quadra"
LAST_RUN_FILENAME = "last-run.json"
SYNC_MANIFEST_FILENAME = "sync-manifest.json"
WORKER_BOOTSTRAP_LOG_FILENAME = "worker-bootstrap.log"
RUN_MANIFEST_FILENAME = "run-manifest.json"
SYNC_MANIFEST_VERSION = 1
CONFIG_SCHEMA_VERSION = 3
RUNPOD_VOLUME_ROOT = PurePosixPath("/runpod-volume")
DEFAULT_TEMPLATE_VOLUME_MOUNT_PATH = str(RUNPOD_VOLUME_ROOT)
DEFAULT_PROJECT_DIR = "{volume_mount_path}/projects/{project_name}"
FINAL_JOB_STATES = {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
POLL_PROGRESS_INTERVAL_SECONDS = 10
GPU_SUPPLY_REFRESH_INTERVAL_SECONDS = 30
DEFAULT_RUNPOD_QUEUE_TIMEOUT_SECONDS = 900
DEFAULT_RUNPOD_ALL_EXITED_THRESHOLD_SECONDS = 60
BOOTSTRAP_LOG_TAIL_LINES = 40
QUADRA_WORKER_FILENAME = "quadra_worker.py"
DEFAULT_TEMPLATE_IMAGE = "pytorch/pytorch:2.12.1-cuda13.2-cudnn9-runtime"
DEFAULT_RUNPOD_ENDPOINT_API_BASE_URL = "https://api.runpod.ai/v2"
DEFAULT_RUNPOD_GRAPHQL_API_URL = "https://api.runpod.io/graphql"
DEFAULT_TEMPLATE_NAME = "quadra-{project_name}-serverless-worker"
DEFAULT_TEMPLATE_BOOTSTRAP_COMMAND = textwrap.dedent(
    """\
    worker_path="{worker_path}"
    bootstrap_log="{worker_bootstrap_log_path}"
    worker_runtime_path="{worker_runtime_path}"
    isolated_worker_python="$worker_runtime_path/bin/python"
    worker_python="python"
    worker_site_packages="{project_dir}/.quadra/worker-site-packages"
    mkdir -p "$(dirname "$bootstrap_log")"
    : > "$bootstrap_log"
    _rc_file=/tmp/quadra-bootstrap-$$
    _worker_python_file=/tmp/quadra-worker-python-$$
    _worker_env_file=/tmp/quadra-worker-env-$$
    (
      echo "[runpod bootstrap] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "[runpod bootstrap] python: $(python --version 2>&1)"
      echo "[runpod bootstrap] worker path: $worker_path"
      if [ ! -f "$worker_path" ]; then
        echo "[runpod bootstrap] worker script missing"
        echo 1 > "$_rc_file"
        exit 1
      fi
      if python -c 'import runpod' >/dev/null 2>&1; then
        echo "[runpod bootstrap] python package 'runpod' already available in system python"
      else
        if [ ! -x "$isolated_worker_python" ]; then
          echo "[runpod bootstrap] creating isolated worker runtime at $worker_runtime_path"
          if python -m venv "$worker_runtime_path"; then
            echo "[runpod bootstrap] isolated worker runtime created"
          else
            echo "[runpod bootstrap] python venv unavailable, falling back to isolated package directory at $worker_site_packages"
          fi
        fi
        if [ -x "$isolated_worker_python" ]; then
          if "$isolated_worker_python" -c 'import runpod' >/dev/null 2>&1; then
            echo "[runpod bootstrap] python package 'runpod' already available in isolated worker runtime"
            printf '%s\n' "$isolated_worker_python" > "$_worker_python_file"
          elif "$isolated_worker_python" -m pip --version >/dev/null 2>&1; then
            echo "[runpod bootstrap] installing python package 'runpod' into isolated worker runtime"
            "$isolated_worker_python" -m pip install --disable-pip-version-check --no-cache-dir runpod || { echo 1 > "$_rc_file"; exit 1; }
            printf '%s\n' "$isolated_worker_python" > "$_worker_python_file"
          else
            echo "[runpod bootstrap] isolated worker runtime is missing pip, falling back to isolated package directory at $worker_site_packages"
          fi
        fi
        if [ ! -f "$_worker_python_file" ]; then
          printf '%s\n' "$worker_site_packages" > "$_worker_env_file"
          PYTHONPATH="$worker_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -c 'import runpod' >/dev/null 2>&1
          if [ $? -eq 0 ]; then
            echo "[runpod bootstrap] python package 'runpod' already available in isolated package directory"
          else
            echo "[runpod bootstrap] installing python package 'runpod' into isolated package directory"
            mkdir -p "$worker_site_packages"
            python -m pip install --disable-pip-version-check --no-cache-dir --target "$worker_site_packages" runpod || { echo 1 > "$_rc_file"; exit 1; }
          fi
        fi
      fi
      echo "[runpod bootstrap] launching worker"
      echo 0 > "$_rc_file"
    ) 2>&1 | tee -a "$bootstrap_log"
    _bootstrap_rc=$(cat "$_rc_file" 2>/dev/null || echo 1)
    rm -f "$_rc_file"
    if [ "$_bootstrap_rc" != "0" ]; then
      rm -f "$_worker_python_file" "$_worker_env_file"
      exit 1
    fi
    if [ -f "$_worker_python_file" ]; then
      worker_python=$(cat "$_worker_python_file")
    fi
    if [ -f "$_worker_env_file" ]; then
      _extra_path=$(cat "$_worker_env_file")
      export PYTHONPATH="${_extra_path}${PYTHONPATH:+:$PYTHONPATH}"
    fi
    rm -f "$_worker_python_file" "$_worker_env_file"
    exec "$worker_python" -u "$worker_path"
    """
).strip()
PREVIOUS_TEMPLATE_BOOTSTRAP_COMMAND_VENV = textwrap.dedent(
    """\
    worker_path="{worker_path}"
    bootstrap_log="{worker_bootstrap_log_path}"
    worker_runtime_path="{worker_runtime_path}"
    worker_python="$worker_runtime_path/bin/python"
    mkdir -p "$(dirname "$bootstrap_log")"
    : > "$bootstrap_log"
    {
      echo "[runpod bootstrap] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "[runpod bootstrap] python: $(python --version 2>&1)"
      echo "[runpod bootstrap] worker path: $worker_path"
      if [ ! -f "$worker_path" ]; then
        echo "[runpod bootstrap] worker script missing"
        exit 1
      fi
      if [ ! -x "$worker_python" ]; then
        echo "[runpod bootstrap] creating isolated worker runtime at $worker_runtime_path"
        python -m venv "$worker_runtime_path" || exit 1
      fi
      if "$worker_python" -c 'import runpod' >/dev/null 2>&1; then
        echo "[runpod bootstrap] python package 'runpod' already available in isolated worker runtime"
      else
        echo "[runpod bootstrap] installing python package 'runpod' into isolated worker runtime"
        "$worker_python" -m pip install --disable-pip-version-check --no-cache-dir runpod || exit 1
      fi
      echo "[runpod bootstrap] launching worker"
    } >>"$bootstrap_log" 2>&1 && exec "$worker_python" -u "$worker_path"
    """
).strip()
DEFAULT_TEMPLATE_DOCKER_START_CMD = (
    "/bin/sh",
    "-lc",
    DEFAULT_TEMPLATE_BOOTSTRAP_COMMAND,
)
PREVIOUS_TEMPLATE_BOOTSTRAP_COMMAND = textwrap.dedent(
    """\
    worker_path="{worker_path}"
    bootstrap_log="{worker_bootstrap_log_path}"
    mkdir -p "$(dirname "$bootstrap_log")"
    : > "$bootstrap_log"
    {
      echo "[quadra] bootstrap started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "[quadra] python: $(python --version 2>&1)"
      echo "[quadra] worker path: $worker_path"
      if [ ! -f "$worker_path" ]; then
        echo "[quadra] worker script missing"
        exit 1
      fi
      if python -c 'import runpod' >/dev/null 2>&1; then
        echo "[quadra] python package 'runpod' already available"
      else
        echo "[quadra] installing python package 'runpod'"
        python -m pip install --disable-pip-version-check --no-cache-dir runpod || exit 1
      fi
      echo "[quadra] launching worker"
    } >>"$bootstrap_log" 2>&1 && exec python -u "$worker_path"
    """
).strip()
PREVIOUS_TEMPLATE_DOCKER_START_CMD = (
    "/bin/sh",
    "-lc",
    PREVIOUS_TEMPLATE_BOOTSTRAP_COMMAND,
)
INITIAL_TEMPLATE_DOCKER_START_CMD = (
    "/bin/sh",
    "-lc",
    "(python -c 'import runpod' >/dev/null 2>&1 || "
    "python -m pip install --disable-pip-version-check --no-cache-dir runpod) && "
    "exec python -u {worker_path}",
)
DEFAULT_SETUP_COMMAND = textwrap.dedent(
    """\
    uv_runtime_path="{project_dir}/.quadra/uv-runtime"
    uv_python="$uv_runtime_path/bin/python"
    uv_site_packages="{project_dir}/.quadra/uv-site-packages"
    export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
    if command -v uv >/dev/null 2>&1; then
      cd "{experiment_dir}" && "$(command -v uv)" sync
    elif PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv --version >/dev/null 2>&1; then
      cd "{experiment_dir}" && PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv sync
    else
      if [ ! -x "$uv_python" ]; then
        if python -m venv "$uv_runtime_path"; then
          if "$uv_python" -m pip --version >/dev/null 2>&1; then
            "$uv_python" -m pip install --disable-pip-version-check --no-cache-dir uv || exit 1
            cd "{experiment_dir}" && "$uv_python" -m uv sync
          else
            mkdir -p "$uv_site_packages"
            python -m pip install --disable-pip-version-check --no-cache-dir --target "$uv_site_packages" uv || exit 1
            cd "{experiment_dir}" && PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv sync
          fi
        else
          mkdir -p "$uv_site_packages"
          python -m pip install --disable-pip-version-check --no-cache-dir --target "$uv_site_packages" uv || exit 1
          cd "{experiment_dir}" && PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv sync
        fi
      elif "$uv_python" -m uv --version >/dev/null 2>&1; then
        cd "{experiment_dir}" && "$uv_python" -m uv sync
      elif "$uv_python" -m pip --version >/dev/null 2>&1; then
        "$uv_python" -m pip install --disable-pip-version-check --no-cache-dir uv || exit 1
        cd "{experiment_dir}" && "$uv_python" -m uv sync
      else
        mkdir -p "$uv_site_packages"
        python -m pip install --disable-pip-version-check --no-cache-dir --target "$uv_site_packages" uv || exit 1
        cd "{experiment_dir}" && PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv sync
      fi
    fi
    """
).strip()
PREVIOUS_SETUP_COMMAND_VENV = textwrap.dedent(
    """\
    uv_runtime_path="{project_dir}/.quadra/uv-runtime"
    uv_bin=""
    if command -v uv >/dev/null 2>&1; then
      uv_bin="$(command -v uv)"
    else
      uv_bin="$uv_runtime_path/bin/uv"
      if [ ! -x "$uv_bin" ]; then
        python -m venv "$uv_runtime_path" || exit 1
        "$uv_runtime_path/bin/pip" install --disable-pip-version-check --no-cache-dir uv || exit 1
      fi
    fi
    cd "{experiment_dir}" && "$uv_bin" sync
    """
).strip()
PREVIOUS_SETUP_COMMAND = (
    "(command -v uv >/dev/null 2>&1 || "
    "python -m pip install --disable-pip-version-check --no-cache-dir uv) && "
    "uv sync"
)
MANAGED_TEMPLATE_DOCKER_START_CMD_VARIANTS = frozenset(
    {
        DEFAULT_TEMPLATE_DOCKER_START_CMD,
        ("/bin/sh", "-lc", PREVIOUS_TEMPLATE_BOOTSTRAP_COMMAND_VENV),
        PREVIOUS_TEMPLATE_DOCKER_START_CMD,
        INITIAL_TEMPLATE_DOCKER_START_CMD,
    }
)
MANAGED_SETUP_COMMAND_VARIANTS = frozenset(
    {
        DEFAULT_SETUP_COMMAND,
        PREVIOUS_SETUP_COMMAND_VENV,
        PREVIOUS_SETUP_COMMAND,
    }
)
DEFAULT_NETWORK_VOLUME_SIZE_GB = 50
BANNER_ASSET_DIR = importlib.resources.files("quadra").joinpath("assets")
BANNER_TAGLINE = "\n".join(
    [
        "        QUADRA",
        "        accelerate remote GPU development",
    ]
)
DEFAULT_IGNORES = {
    ".git",
    ".quadra",
    ".DS_Store",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
DEFAULT_MAIN_COMMAND = "python main.py"
DEFAULT_COMMANDS = {
    "smoke": DEFAULT_MAIN_COMMAND,
    "main": DEFAULT_MAIN_COMMAND,
}
LEGACY_SMOKE_COMMAND = "python scripts/smoke.py"
TERMINAL_WORKER_DESIRED_STATUSES = {"EXITED", "TERMINATED"}
UNHEALTHY_WORKER_TEXT_HINTS = (
    "unhealthy",
    "image_auth_error",
    "image pull",
    "failed to pull",
    "cannotpullcontainererror",
    "crashloop",
    "back-off",
    "backoff",
    "unauthorized",
)
S3_ENDPOINTS = {
    "EU-CZ-1": "https://s3api-eu-cz-1.runpod.io/",
    "EU-RO-1": "https://s3api-eu-ro-1.runpod.io/",
    "EUR-IS-1": "https://s3api-eur-is-1.runpod.io/",
    "EUR-NO-1": "https://s3api-eur-no-1.runpod.io/",
    "US-CA-2": "https://s3api-us-ca-2.runpod.io/",
    "US-GA-2": "https://s3api-us-ga-2.runpod.io/",
    "US-IL-1": "https://s3api-us-il-1.runpod.io/",
    "US-KS-2": "https://s3api-us-ks-2.runpod.io/",
    "US-MD-1": "https://s3api-us-md-1.runpod.io/",
    "US-MO-1": "https://s3api-us-mo-1.runpod.io/",
    "US-MO-2": "https://s3api-us-mo-2.runpod.io/",
    "US-NC-1": "https://s3api-us-nc-1.runpod.io/",
    "US-NC-2": "https://s3api-us-nc-2.runpod.io/",
    "US-NE-1": "https://s3api-us-ne-1.runpod.io/",
    "US-WA-1": "https://s3api-us-wa-1.runpod.io/",
}
SERVERLESS_GPU_POOL_COMMENT_LINES = (
    "# Valid serverless gpu_ids pool IDs:",
    "#   AMPERE_16     16+ GB   A4000, A4500, RTX 4000 Ada, RTX 2000 Ada",
    "#   AMPERE_24     24 GB    L4, A5000, RTX 3090",
    "#   ADA_24        24 GB    RTX 4090",
    "#   AMPERE_48     48 GB    A6000, A40",
    "#   ADA_48_PRO    48 GB    L40, L40S, RTX 6000 Ada",
    "#   AMPERE_80     80 GB    A100",
    "#   ADA_80_PRO    80 GB    H100",
    "#   HOPPER_141    141 GB   H200",
    "#   ADA_32_PRO    32 GB    RTX 5000 Ada, RTX PRO 4500 Blackwell",
    "#   BLACKWELL_96  96 GB    RTX PRO 6000 Blackwell",
    "#   BLACKWELL_180 180 GB   B200",
)


@dataclass(frozen=True)
class ProjectPaths:
    libs: str
    experiment: str
    models: str
    caches: str
    runs: str


@dataclass(frozen=True)
class RunpodTemplateConfig:
    id: str | None
    name: str
    image_name: str
    ports: tuple[str, ...] = ()
    docker_entrypoint: tuple[str, ...] = ()
    docker_start_cmd: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)
    container_disk_gb: int = 20
    readme: str = ""


@dataclass(frozen=True)
class RunpodConfig:
    api_key_env: str = "RUNPOD_API_KEY"
    endpoint_id: str | None = None
    endpoint_name: str | None = None
    gpu_ids: str = "AMPERE_16"
    gpu_count: int = 1
    workers_min: int = 0
    workers_max: int = 1
    idle_timeout: int = 5
    scaler_type: str = "QUEUE_DELAY"
    scaler_value: int = 4
    flashboot: bool = False
    locations: str | None = None
    network_volume_id: str | None = None
    network_volume_name: str | None = None
    network_volume_size_gb: int = DEFAULT_NETWORK_VOLUME_SIZE_GB
    volume_mount_path: str = DEFAULT_TEMPLATE_VOLUME_MOUNT_PATH
    allowed_cuda_versions: tuple[str, ...] = ()
    timeout_seconds: int = 600
    s3_access_key_env: str | None = "AWS_ACCESS_KEY_ID"
    s3_secret_key_env: str | None = "AWS_SECRET_ACCESS_KEY"
    template: RunpodTemplateConfig = field(
        default_factory=lambda: RunpodTemplateConfig(
            id=None,
            name="quadra-worker",
            image_name=DEFAULT_TEMPLATE_IMAGE,
            docker_start_cmd=DEFAULT_TEMPLATE_DOCKER_START_CMD,
        )
    )


@dataclass(frozen=True)
class RuntimeConfig:
    project_dir: str
    setup_command: str | None
    runpod: RunpodConfig


@dataclass(frozen=True)
class ProjectConfig:
    schema_version: int
    name: str
    root: Path
    paths: ProjectPaths
    runtime: RuntimeConfig
    commands: dict[str, str] = field(default_factory=dict)
    is_ephemeral: bool = False

    @property
    def quadra_dir(self) -> Path:
        return self.root / STATE_DIRNAME

    @property
    def runs_dir(self) -> Path:
        return self.root / self.paths.runs

    @property
    def last_run_file(self) -> Path:
        return self.quadra_dir / LAST_RUN_FILENAME


@dataclass(frozen=True)
class VolumeHandle:
    id: str
    name: str
    data_center_id: str | None


RUNTIME_NETWORK_VOLUME_OVERRIDES: dict[Path, VolumeHandle] = {}


@dataclass(frozen=True)
class EndpointHandle:
    id: str
    name: str


@dataclass(frozen=True)
class TemplateHandle:
    id: str
    name: str
    updated: bool = False


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    image_name: str
    ports: tuple[str, ...]
    docker_entrypoint: tuple[str, ...]
    docker_start_cmd: tuple[str, ...]
    volume_mount_path: str
    env: dict[str, str]
    container_disk_gb: int
    readme: str


@dataclass(frozen=True)
class RunReference:
    run_id: str
    job_id: str
    endpoint_id: str
    workflow: str
    submitted_at: str


@dataclass(frozen=True)
class EndpointQueueDiagnostics:
    progress_summary: str | None = None
    blocking_workers: tuple[str, ...] = ()
    exited_workers: tuple[str, ...] = ()


@dataclass(frozen=True)
class GpuPoolSupply:
    pool_id: str
    status: str


class PlainRunRenderer:
    interactive = False

    def __enter__(self) -> PlainRunRenderer:
        return self

    def __exit__(self, *exc_info: object) -> None:
        del exc_info

    def announce_stream(self, label: str) -> None:
        report_remote_stream(label)

    def write(self, text: str, *, err: bool = False) -> None:
        click.echo(text, nl=False, err=err)

    def update(
        self,
        reference: RunReference,
        status: str,
        *,
        has_remote_output: bool,
        elapsed_seconds: int,
        queue_diagnostics: EndpointQueueDiagnostics,
        gpu_supply: tuple[GpuPoolSupply, ...],
        data_center_id: str | None,
    ) -> None:
        report_poll_status(
            reference,
            status,
            has_remote_output=has_remote_output,
            elapsed_seconds=elapsed_seconds,
            detail=(
                queue_diagnostics.progress_summary if status == "IN_QUEUE" else None
            ),
        )
        if status == "IN_QUEUE":
            report_gpu_supply_dashboard(
                gpu_supply,
                data_center_id=data_center_id,
            )


class LiveRunRenderer:
    interactive = True

    def __init__(self, reference: RunReference) -> None:
        self.reference = reference
        self.console = Console(
            file=click.get_text_stream("stdout"),
            force_terminal=True,
            color_system="auto",
            no_color=os.getenv("NO_COLOR") is not None,
        )
        self._renderable = self._build_panel(
            status="CONNECTING",
            has_remote_output=False,
            elapsed_seconds=0,
            queue_diagnostics=EndpointQueueDiagnostics(),
            gpu_supply=(),
            data_center_id=None,
        )
        self.live = Live(
            self._renderable,
            console=self.console,
            auto_refresh=False,
            transient=False,
            vertical_overflow="visible",
        )

    def __enter__(self) -> LiveRunRenderer:
        self.live.start(refresh=True)
        return self

    def __exit__(self, *exc_info: object) -> None:
        del exc_info
        self.live.stop()

    def announce_stream(self, label: str) -> None:
        self.live.console.print(
            Text(f"[quadra] streaming {label}...", style="dim")
        )

    def write(self, text: str, *, err: bool = False) -> None:
        del err
        self.live.console.print(Text.from_ansi(text), end="", soft_wrap=True)

    def update(
        self,
        reference: RunReference,
        status: str,
        *,
        has_remote_output: bool,
        elapsed_seconds: int,
        queue_diagnostics: EndpointQueueDiagnostics,
        gpu_supply: tuple[GpuPoolSupply, ...],
        data_center_id: str | None,
    ) -> None:
        self.reference = reference
        self._renderable = self._build_panel(
            status=status,
            has_remote_output=has_remote_output,
            elapsed_seconds=elapsed_seconds,
            queue_diagnostics=queue_diagnostics,
            gpu_supply=gpu_supply,
            data_center_id=data_center_id,
        )
        self.live.update(self._renderable, refresh=True)

    def _build_panel(
        self,
        *,
        status: str,
        has_remote_output: bool,
        elapsed_seconds: int,
        queue_diagnostics: EndpointQueueDiagnostics,
        gpu_supply: tuple[GpuPoolSupply, ...],
        data_center_id: str | None,
    ) -> Panel:
        status_style = {
            "COMPLETED": "bold green",
            "FAILED": "bold red",
            "TIMED_OUT": "bold red",
            "CANCELLED": "bold yellow",
            "IN_PROGRESS": "bold cyan",
            "RUNNING": "bold cyan",
            "IN_QUEUE": "bold yellow",
        }.get(status, "bold")
        description = describe_job_status(
            status,
            has_remote_output=has_remote_output,
        )

        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(style="dim", width=16, no_wrap=True)
        grid.add_column(ratio=1)
        grid.add_row("Workflow", self.reference.workflow)
        grid.add_row(
            "Status",
            Text.assemble((description, status_style), ("  "), (status, "dim")),
        )
        grid.add_row("Elapsed", format_duration(elapsed_seconds))
        if queue_diagnostics.progress_summary:
            grid.add_row(
                "Workers",
                queue_diagnostics.progress_summary.removeprefix("workers: "),
            )
        if status == "IN_QUEUE" and gpu_supply:
            supply_text = Text()
            for index, pool in enumerate(gpu_supply):
                if index:
                    supply_text.append("   ")
                color = {
                    "HIGH": "green",
                    "MEDIUM": "yellow",
                    "LOW": "red",
                    "UNAVAILABLE": "bold red",
                    "UNKNOWN": "bright_black",
                }.get(pool.status, "bright_black")
                supply_text.append(f"● {pool.pool_id} {pool.status}", style=color)
            location = data_center_id or "all regions"
            grid.add_row(f"GPU · {location}", supply_text)
        grid.add_row("Run", self.reference.run_id)
        grid.add_row("Job", self.reference.job_id)
        grid.add_row("Endpoint", self.reference.endpoint_id)
        return Panel(grid, title="[bold]Quadra run[/bold]", border_style="bright_black")


def supports_live_dashboard(*, follow: bool) -> bool:
    if not follow or os.getenv("QUADRA_NO_TUI"):
        return False
    output = click.get_text_stream("stdout")
    isatty = getattr(output, "isatty", None)
    return bool(
        callable(isatty)
        and isatty()
        and os.getenv("TERM") != "dumb"
    )


def create_run_renderer(
    reference: RunReference,
    *,
    follow: bool,
    interactive: bool | None,
) -> PlainRunRenderer | LiveRunRenderer:
    use_live = (
        supports_live_dashboard(follow=follow)
        if interactive is None
        else interactive
    )
    if use_live and follow:
        return LiveRunRenderer(reference)
    return PlainRunRenderer()


def supports_color(stream: Any | None = None) -> bool:
    output = stream or sys.stdout
    isatty = getattr(output, "isatty", None)
    return (
        callable(isatty)
        and isatty()
        and os.getenv("NO_COLOR") is None
        and os.getenv("TERM") != "dumb"
    )


def load_banner_text(*, color: bool | None = None) -> str:
    use_color = supports_color() if color is None else color
    banner_name = "banner.ansi" if use_color else "banner.txt"

    try:
        banner_text = BANNER_ASSET_DIR.joinpath(banner_name).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

    if banner_name.endswith(".ansi"):
        banner_text = banner_text.replace("\\033", "\033")
    return f"{banner_text.rstrip()}\n{BANNER_TAGLINE}\n"


def print_banner() -> bool:
    banner_text = load_banner_text()
    if not banner_text:
        return False

    click.echo(banner_text, nl=False)
    return True


def configure_library_logging() -> None:
    if os.getenv("QUADRA_HTTP_DEBUG"):
        return
    for logger_name in ("httpx", "httpcore"):
        logger = logging.getLogger(logger_name)
        if logger.level == logging.NOTSET or logger.level < logging.WARNING:
            logger.setLevel(logging.WARNING)


def report_step(message: str) -> None:
    if click.get_current_context(silent=True) is None:
        return
    click.echo(f"[quadra] {message}")


def report_remote_stream(label: str) -> None:
    if click.get_current_context(silent=True) is None:
        return
    click.echo(f"[quadra] streaming {label} from RunPod...")


def normalize_managed_setup_command(command: str | None) -> str | None:
    if command is None:
        return None
    if command in MANAGED_SETUP_COMMAND_VARIANTS:
        return DEFAULT_SETUP_COMMAND
    return command


def normalize_managed_docker_start_cmd(
    command: tuple[str, ...],
) -> tuple[str, ...]:
    if command in MANAGED_TEMPLATE_DOCKER_START_CMD_VARIANTS:
        return DEFAULT_TEMPLATE_DOCKER_START_CMD
    return command


def normalize_managed_commands(commands: dict[str, str]) -> dict[str, str]:
    normalized = dict(commands)
    if (
        normalized.get("smoke") == LEGACY_SMOKE_COMMAND
        and normalized.get("main", DEFAULT_MAIN_COMMAND) == DEFAULT_MAIN_COMMAND
    ):
        normalized["smoke"] = DEFAULT_MAIN_COMMAND
    return normalized


class BannerGroup(click.Group):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            if print_banner():
                click.echo()
        return super().parse_args(ctx, args)


class RunpodClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint_base_url = os.getenv(
            "RUNPOD_ENDPOINT_BASE_URL", DEFAULT_RUNPOD_ENDPOINT_API_BASE_URL
        ).rstrip("/")
        self.rest_client = RunpodRestClient(self.api_key)

    def _endpoint_request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timeout_seconds: int = 10,
    ) -> dict[str, Any]:
        url = f"{self.endpoint_base_url}/{path.lstrip('/')}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            response = httpx.request(
                method,
                url,
                headers=headers,
                json=payload,
                timeout=timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise QuadraError(f"RunPod endpoint request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuadraError(f"RunPod endpoint request failed: {exc}") from exc

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise QuadraError("Unauthorized request, please check your RunPod API key.")
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            message = response.text.strip() or response.reason_phrase or str(response.status_code)
            raise QuadraError(
                f"RunPod endpoint API returned HTTP {response.status_code}: {message}"
            )

        try:
            parsed = response.json()
        except ValueError as exc:
            raise QuadraError("RunPod endpoint API returned an invalid JSON response.") from exc
        if not isinstance(parsed, dict):
            raise QuadraError("RunPod endpoint API returned an invalid JSON response.")
        return parsed

    def get_network_volumes(self) -> list[dict[str, Any]]:
        return self.rest_client.get_network_volumes()

    def create_network_volume(
        self, *, name: str, data_center_id: str, size_gb: int
    ) -> dict[str, Any]:
        return self.rest_client.create_network_volume(
            name=name,
            data_center_id=data_center_id,
            size_gb=size_gb,
        )

    def get_endpoints(self) -> list[dict[str, Any]]:
        return self.rest_client.get_endpoints()

    def get_templates(self) -> list[dict[str, Any]]:
        return self.rest_client.get_templates()

    def get_template(self, template_id: str) -> dict[str, Any]:
        return self.rest_client.get_template(template_id)

    def create_template(
        self,
        *,
        name: str,
        image_name: str,
        ports: tuple[str, ...],
        docker_entrypoint: tuple[str, ...],
        docker_start_cmd: tuple[str, ...],
        volume_mount_path: str,
        env: dict[str, str],
        container_disk_gb: int,
        readme: str,
    ) -> dict[str, Any]:
        return self.rest_client.create_template(
            name=name,
            image_name=image_name,
            ports=ports,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            volume_mount_path=volume_mount_path,
            env=env,
            container_disk_gb=container_disk_gb,
            readme=readme,
        )

    def update_template(
        self,
        template_id: str,
        *,
        name: str,
        image_name: str,
        ports: tuple[str, ...],
        docker_entrypoint: tuple[str, ...],
        docker_start_cmd: tuple[str, ...],
        volume_mount_path: str,
        env: dict[str, str],
        container_disk_gb: int,
        readme: str,
    ) -> dict[str, Any]:
        return self.rest_client.update_template(
            template_id,
            name=name,
            image_name=image_name,
            ports=ports,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            volume_mount_path=volume_mount_path,
            env=env,
            container_disk_gb=container_disk_gb,
            readme=readme,
        )

    def create_endpoint(
        self,
        *,
        name: str,
        template_id: str,
        gpu_ids: str,
        network_volume_id: str,
        locations: str | None,
        idle_timeout: int,
        scaler_type: str,
        scaler_value: int,
        workers_min: int,
        workers_max: int,
        flashboot: bool,
        allowed_cuda_versions: tuple[str, ...],
        gpu_count: int,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        return self.rest_client.create_endpoint(
            name=name,
            template_id=template_id,
            gpu_ids=gpu_ids,
            network_volume_id=network_volume_id,
            locations=locations,
            idle_timeout=idle_timeout,
            scaler_type=scaler_type,
            scaler_value=scaler_value,
            workers_min=workers_min,
            workers_max=workers_max,
            flashboot=flashboot,
            allowed_cuda_versions=allowed_cuda_versions,
            gpu_count=gpu_count,
            timeout_seconds=timeout_seconds,
        )

    def update_endpoint(
        self,
        endpoint_id: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.rest_client.update_endpoint(endpoint_id, payload, **kwargs)

    def run_job(
        self, endpoint_id: str, request_input: dict[str, Any]
    ) -> dict[str, Any]:
        payload = (
            request_input
            if request_input.get("input")
            else {"input": request_input}
        )
        job = self._endpoint_request(
            "POST",
            f"{endpoint_id}/run",
            payload=payload,
        )
        job_id = optional_str(job.get("id"))
        if not job_id:
            raise QuadraError("RunPod endpoint API returned a job response without an id.")
        return {"id": job_id}

    def get_job(
        self, endpoint_id: str, job_id: str, *, source: str = "status"
    ) -> dict[str, Any] | None:
        try:
            return self._endpoint_request(
                "GET",
                f"{endpoint_id}/{source}/{job_id}",
            )
        except QuadraError as exc:
            if "HTTP 404" in str(exc):
                return None
            if "timed out" in str(exc).lower():
                return None
            raise

    def stream_job(self, endpoint_id: str, job_id: str) -> list[dict[str, Any]]:
        url = f"{self.endpoint_base_url}/{endpoint_id}/stream/{job_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            response = httpx.request("GET", url, headers=headers, timeout=30)
        except httpx.TimeoutException:
            return []
        except httpx.HTTPError as exc:
            raise QuadraError(f"RunPod endpoint request failed: {exc}") from exc
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise QuadraError("Unauthorized request, please check your RunPod API key.")
        if response.status_code == HTTPStatus.NOT_FOUND:
            return []
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            message = response.text.strip() or response.reason_phrase or str(response.status_code)
            raise QuadraError(
                f"RunPod endpoint API returned HTTP {response.status_code}: {message}"
            )
        try:
            parsed = response.json()
        except ValueError as exc:
            raise QuadraError("RunPod endpoint API returned an invalid JSON response.") from exc
        if isinstance(parsed, list):
            return parsed
        return []

    def get_endpoint(
        self, endpoint_id: str, *, include_workers: bool = False
    ) -> dict[str, Any]:
        return self.rest_client.get_endpoint(
            endpoint_id,
            include_workers=include_workers,
        )

    def get_gpu_supply(
        self,
        gpu_type_ids: tuple[str, ...],
        *,
        data_center_id: str | None,
        gpu_count: int,
        allowed_cuda_versions: tuple[str, ...],
    ) -> dict[str, str | None]:
        price_input: dict[str, Any] = {
            "gpuCount": gpu_count,
            "includeAiApi": True,
        }
        if data_center_id:
            price_input["dataCenterId"] = data_center_id
        if allowed_cuda_versions:
            price_input["allowedCudaVersions"] = list(allowed_cuda_versions)

        query = """
        query QuadraGpuSupply($priceInput: GpuLowestPriceInput) {
          gpuTypes {
            id
            lowestPrice(input: $priceInput) {
              stockStatus
            }
          }
        }
        """
        try:
            response = httpx.request(
                "POST",
                os.getenv(
                    "RUNPOD_GRAPHQL_API_URL",
                    DEFAULT_RUNPOD_GRAPHQL_API_URL,
                ),
                params={"api_key": self.api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "query": query,
                    "variables": {"priceInput": price_input},
                },
                timeout=10,
            )
        except httpx.TimeoutException as exc:
            raise QuadraError(f"RunPod GPU supply request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuadraError(f"RunPod GPU supply request failed: {exc}") from exc

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise QuadraError("Unauthorized request, please check your RunPod API key.")
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            message = response.text.strip() or response.reason_phrase or str(
                response.status_code
            )
            raise QuadraError(
                f"RunPod GPU supply API returned HTTP {response.status_code}: {message}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise QuadraError(
                "RunPod GPU supply API returned an invalid JSON response."
            ) from exc
        if not isinstance(payload, dict):
            raise QuadraError(
                "RunPod GPU supply API returned an invalid JSON response."
            )
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first_error = errors[0]
            if isinstance(first_error, dict):
                message = optional_str(first_error.get("message"))
            else:
                message = optional_str(first_error)
            raise QuadraError(
                f"RunPod GPU supply API returned an error: {message or 'unknown error'}"
            )

        data = payload.get("data")
        rows = data.get("gpuTypes") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise QuadraError(
                "RunPod GPU supply API returned an invalid GPU type response."
            )

        requested = set(gpu_type_ids)
        supply: dict[str, str | None] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            gpu_type_id = optional_str(row.get("id"))
            if gpu_type_id not in requested:
                continue
            lowest_price = row.get("lowestPrice")
            stock_status = (
                optional_str(lowest_price.get("stockStatus"))
                if isinstance(lowest_price, dict)
                else None
            )
            supply[gpu_type_id] = stock_status
        return supply

    def delete_endpoint(self, endpoint_id: str) -> None:
        self.rest_client.delete_endpoint(endpoint_id)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def generate_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def split_csv(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def global_config_path() -> Path:
    configured = os.getenv(GLOBAL_CONFIG_ENV)
    if configured:
        return Path(configured).expanduser()
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home).expanduser() / "quadra" / "config.toml"
    return GLOBAL_CONFIG_PATH.expanduser()


def load_global_config() -> dict[str, Any]:
    path = global_config_path()
    if not path.exists():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise QuadraError(f"Failed to read global config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise QuadraError(f"Global config {path} must contain TOML tables.")
    return data


def render_global_config(
    *,
    api_key_env: str,
    data_center_id: str,
    volume_name: str,
    volume_size_gb: int,
    volume_mount_path: str,
    endpoint_name: str,
    gpu_ids: str,
    gpu_count: int,
    workers_min: int,
    workers_max: int,
    idle_timeout: int,
    scaler_type: str,
    scaler_value: int,
    flashboot: bool,
    timeout_seconds: int,
    template_name: str,
    image_name: str,
    container_disk_gb: int,
) -> str:
    return textwrap.dedent(
        f"""\
        [runpod]
        api_key_env = {json.dumps(api_key_env)}
        default_data_center_id = {json.dumps(data_center_id)}

        [runpod.network_volume]
        name = {json.dumps(volume_name)}
        size_gb = {volume_size_gb}
        mount_path = {json.dumps(volume_mount_path)}

        [runpod.serverless]
        endpoint_name = {json.dumps(endpoint_name)}
        gpu_ids = {json.dumps(gpu_ids)}
        gpu_count = {gpu_count}
        workers_min = {workers_min}
        workers_max = {workers_max}
        idle_timeout = {idle_timeout}
        scaler_type = {json.dumps(scaler_type)}
        scaler_value = {scaler_value}
        flashboot = {str(flashboot).lower()}
        timeout_seconds = {timeout_seconds}

        [runpod.template]
        name = {json.dumps(template_name)}
        image_name = {json.dumps(image_name)}
        container_disk_gb = {container_disk_gb}
        """
    )


def write_global_config(
    path: Path,
    *,
    force: bool,
    api_key_env: str,
    data_center_id: str,
    volume_name: str,
    volume_size_gb: int,
    volume_mount_path: str,
    endpoint_name: str,
    gpu_ids: str,
    gpu_count: int,
    workers_min: int,
    workers_max: int,
    idle_timeout: int,
    scaler_type: str,
    scaler_value: int,
    flashboot: bool,
    timeout_seconds: int,
    template_name: str | None,
    image_name: str,
    container_disk_gb: int,
) -> Path:
    resolved_path = path.expanduser()
    if resolved_path.exists() and not force:
        raise QuadraError(
            f"Global config already exists: {resolved_path}. Pass --force to overwrite it."
        )
    resolved_template_name = template_name or f"{endpoint_name}-serverless-worker"
    text = render_global_config(
        api_key_env=api_key_env,
        data_center_id=data_center_id,
        volume_name=volume_name,
        volume_size_gb=volume_size_gb,
        volume_mount_path=volume_mount_path,
        endpoint_name=endpoint_name,
        gpu_ids=gpu_ids,
        gpu_count=gpu_count,
        workers_min=workers_min,
        workers_max=workers_max,
        idle_timeout=idle_timeout,
        scaler_type=scaler_type,
        scaler_value=scaler_value,
        flashboot=flashboot,
        timeout_seconds=timeout_seconds,
        template_name=resolved_template_name,
        image_name=image_name,
        container_disk_gb=container_disk_gb,
    )
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise QuadraError(f"Failed to write global config {resolved_path}: {exc}") from exc
    return resolved_path


def optional_table(data: dict[str, Any], key: str, field_name: str) -> dict[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise QuadraError(f"{field_name} must be a table.")
    return value


def merged_optional_str(
    project_table: dict[str, Any],
    global_table: dict[str, Any],
    key: str,
    default: str | None = None,
) -> str | None:
    return (
        optional_str(project_table.get(key))
        or optional_str(global_table.get(key))
        or default
    )


def runpod_queue_timeout_seconds() -> int:
    raw_value = os.getenv("QUADRA_RUNPOD_QUEUE_TIMEOUT_SECONDS")
    if raw_value is None:
        return DEFAULT_RUNPOD_QUEUE_TIMEOUT_SECONDS
    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_RUNPOD_QUEUE_TIMEOUT_SECONDS
    if parsed <= 0:
        return DEFAULT_RUNPOD_QUEUE_TIMEOUT_SECONDS
    return parsed


def runpod_all_exited_threshold_seconds() -> int:
    raw_value = os.getenv("QUADRA_RUNPOD_ALL_EXITED_THRESHOLD_SECONDS")
    if raw_value is None:
        return DEFAULT_RUNPOD_ALL_EXITED_THRESHOLD_SECONDS
    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_RUNPOD_ALL_EXITED_THRESHOLD_SECONDS
    if parsed <= 0:
        return DEFAULT_RUNPOD_ALL_EXITED_THRESHOLD_SECONDS
    return parsed


def supports_interactive_prompts() -> bool:
    stdin = click.get_text_stream("stdin")
    stdout = click.get_text_stream("stdout")
    stdin_isatty = getattr(stdin, "isatty", None)
    stdout_isatty = getattr(stdout, "isatty", None)
    return bool(
        callable(stdin_isatty)
        and stdin_isatty()
        and callable(stdout_isatty)
        and stdout_isatty()
    )


def persist_network_volume_link(config: ProjectConfig, volume: VolumeHandle) -> None:
    config_path = config.root / CONFIG_FILENAME
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise QuadraError(f"Failed to read {config_path}: {exc}") from exc

    section_match = re.search(
        r"(?ms)^\[runtime\.runpod\]\n(?P<body>.*?)(?=^\[|\Z)",
        text,
    )
    if section_match is None:
        raise QuadraError("Missing required config section: runtime.runpod")

    body = section_match.group("body")
    network_volume_id_line = f'network_volume_id = "{volume.id}"'
    id_match = re.search(r"(?m)^(?P<indent>\s*)network_volume_id\s*=.*$", body)
    if id_match is not None:
        indent = id_match.group("indent")
        new_body = re.sub(
            r"(?m)^(?P<indent>\s*)network_volume_id\s*=.*$",
            f"{indent}{network_volume_id_line}",
            body,
            count=1,
        )
    else:
        name_match = re.search(
            r"(?m)^(?P<indent>\s*)network_volume_name\s*=.*$",
            body,
        )
        if name_match is not None:
            indent = name_match.group("indent")
            insert_at = name_match.start()
            new_body = (
                body[:insert_at]
                + f"{indent}{network_volume_id_line}\n"
                + body[insert_at:]
            )
        else:
            new_body = body
            if new_body and not new_body.endswith("\n"):
                new_body += "\n"
            new_body += f"{network_volume_id_line}\n"

    updated_text = (
        text[: section_match.start("body")]
        + new_body
        + text[section_match.end("body") :]
    )
    try:
        config_path.write_text(updated_text, encoding="utf-8")
    except OSError as exc:
        raise QuadraError(f"Failed to write {config_path}: {exc}") from exc


def remember_selected_network_volume(config: ProjectConfig, volume: VolumeHandle) -> None:
    RUNTIME_NETWORK_VOLUME_OVERRIDES[config.root] = volume


def normalize_str_sequence(value: object | None, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                values.append(text)
        return tuple(values)
    raise QuadraError(f"{field_name} must be a string or list of strings.")


def normalize_gpu_ids_config(value: object | None) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            raise QuadraError(
                "runtime.runpod.gpu_ids must be a string or list of strings."
            )
        return ",".join(item.strip() for item in value if item.strip())
    raise QuadraError("runtime.runpod.gpu_ids must be a string or list of strings.")


def normalize_string_map(value: object | None, field_name: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise QuadraError(f"{field_name} must be a table or inline table.")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized[str(key)] = str(item)
    return normalized


def normalize_allowed_cuda_versions(value: object | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, list):
        return tuple(str(part).strip() for part in value if str(part).strip())
    raise QuadraError(
        "runtime.runpod.allowed_cuda_versions must be a list or comma-separated string."
    )


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / CONFIG_FILENAME).exists():
            return candidate
    raise QuadraError(
        f"Could not find {CONFIG_FILENAME}. Run `quadra init <project>` first."
    )


def build_project_config(
    root: Path,
    data: dict[str, Any],
    *,
    require_global_config: bool = False,
    is_ephemeral: bool = False,
) -> ProjectConfig:
    try:
        project = data["project"]
    except KeyError as exc:
        raise QuadraError(f"Missing required config section: {exc.args[0]}") from exc

    paths = optional_table(data, "paths", "paths")
    runtime = optional_table(data, "runtime", "runtime")
    runpod_data = optional_table(runtime, "runpod", "runtime.runpod")
    project_name = str(project["name"])

    global_data = load_global_config()
    if require_global_config and not global_data:
        raise QuadraError(
            "No Quadra project config was found and no global config is configured. "
            "Run `quadra configure` first, or run `quadra init` in this project."
        )
    global_runpod = optional_table(global_data, "runpod", "runpod")
    global_network_volume = optional_table(
        global_runpod, "network_volume", "runpod.network_volume"
    )
    global_serverless = optional_table(
        global_runpod, "serverless", "runpod.serverless"
    )
    global_template = optional_table(global_runpod, "template", "runpod.template")

    volume_mount_path = (
        optional_str(runpod_data.get("volume_mount_path"))
        or optional_str(global_network_volume.get("mount_path"))
        or DEFAULT_TEMPLATE_VOLUME_MOUNT_PATH
    )
    project_dir = str(
        runtime.get("project_dir")
        or DEFAULT_PROJECT_DIR.format(
            volume_mount_path=volume_mount_path.rstrip("/"),
            project_name=project_name,
        )
    )
    template_data = optional_table(
        runpod_data, "template", "runtime.runpod.template"
    )

    docker_start_cmd = normalize_managed_docker_start_cmd(
        normalize_str_sequence(
            template_data.get("docker_start_cmd")
            or global_template.get("docker_start_cmd")
            or list(DEFAULT_TEMPLATE_DOCKER_START_CMD),
            "runtime.runpod.template.docker_start_cmd",
        )
    )
    setup_command = normalize_managed_setup_command(
        optional_str(runtime.get("setup_command", DEFAULT_SETUP_COMMAND))
    )

    template_config = RunpodTemplateConfig(
        id=optional_str(template_data.get("id")) or optional_str(global_template.get("id")),
        name=(
            optional_str(template_data.get("name"))
            or optional_str(global_template.get("name"))
            or DEFAULT_TEMPLATE_NAME.format(project_name=project_name)
        ),
        image_name=str(
            template_data.get(
                "image_name",
                global_template.get("image_name", DEFAULT_TEMPLATE_IMAGE),
            )
        ).strip(),
        ports=normalize_str_sequence(
            template_data.get("ports", global_template.get("ports")),
            "runtime.runpod.template.ports",
        ),
        docker_entrypoint=normalize_str_sequence(
            template_data.get(
                "docker_entrypoint", global_template.get("docker_entrypoint")
            ),
            "runtime.runpod.template.docker_entrypoint",
        ),
        docker_start_cmd=docker_start_cmd,
        env=normalize_string_map(
            template_data.get("env", global_template.get("env")),
            "runtime.runpod.template.env",
        ),
        container_disk_gb=int(
            template_data.get(
                "container_disk_gb",
                global_template.get("container_disk_gb", 20),
            )
        ),
        readme=str(
            template_data.get(
                "readme",
                global_template.get(
                    "readme",
                    "Managed by Quadra. Runs {worker_path} from the synced project volume.",
                ),
            )
        ),
    )

    runpod_config = RunpodConfig(
        api_key_env=(
            merged_optional_str(runpod_data, global_runpod, "api_key_env")
            or "RUNPOD_API_KEY"
        ),
        endpoint_id=merged_optional_str(
            runpod_data, global_serverless, "endpoint_id"
        ),
        endpoint_name=merged_optional_str(
            runpod_data, global_serverless, "endpoint_name"
        ),
        gpu_ids=normalize_gpu_ids_config(
            runpod_data.get(
                "gpu_ids", global_serverless.get("gpu_ids", "AMPERE_16")
            )
        ),
        gpu_count=int(
            runpod_data.get("gpu_count", global_serverless.get("gpu_count", 1))
        ),
        workers_min=int(
            runpod_data.get("workers_min", global_serverless.get("workers_min", 0))
        ),
        workers_max=int(
            runpod_data.get("workers_max", global_serverless.get("workers_max", 1))
        ),
        idle_timeout=int(
            runpod_data.get("idle_timeout", global_serverless.get("idle_timeout", 5))
        ),
        scaler_type=str(
            runpod_data.get(
                "scaler_type", global_serverless.get("scaler_type", "QUEUE_DELAY")
            )
        ).strip(),
        scaler_value=int(
            runpod_data.get("scaler_value", global_serverless.get("scaler_value", 4))
        ),
        flashboot=bool(
            runpod_data.get("flashboot", global_serverless.get("flashboot", False))
        ),
        locations=(
            optional_str(runpod_data.get("locations"))
            or optional_str(global_serverless.get("locations"))
            or optional_str(global_runpod.get("default_data_center_id"))
        ),
        network_volume_id=(
            optional_str(runpod_data.get("network_volume_id"))
            or optional_str(global_network_volume.get("id"))
        ),
        network_volume_name=(
            optional_str(runpod_data.get("network_volume_name"))
            or optional_str(global_network_volume.get("name"))
        ),
        network_volume_size_gb=int(
            runpod_data.get(
                "network_volume_size_gb",
                global_network_volume.get("size_gb", DEFAULT_NETWORK_VOLUME_SIZE_GB),
            )
        ),
        volume_mount_path=volume_mount_path,
        allowed_cuda_versions=normalize_allowed_cuda_versions(
            runpod_data.get(
                "allowed_cuda_versions", global_serverless.get("allowed_cuda_versions")
            )
        ),
        timeout_seconds=int(
            runpod_data.get(
                "timeout_seconds", global_serverless.get("timeout_seconds", 600)
            )
        ),
        s3_access_key_env=optional_str(
            runpod_data.get(
                "s3_access_key_env",
                global_runpod.get("s3_access_key_env", "AWS_ACCESS_KEY_ID"),
            )
        ),
        s3_secret_key_env=optional_str(
            runpod_data.get(
                "s3_secret_key_env",
                global_runpod.get("s3_secret_key_env", "AWS_SECRET_ACCESS_KEY"),
            )
        ),
        template=template_config,
    )

    return ProjectConfig(
        schema_version=int(data.get("schema_version", CONFIG_SCHEMA_VERSION)),
        name=str(project["name"]),
        root=root,
        paths=ProjectPaths(
            libs=str(paths.get("libs", "src/libs")),
            experiment=str(paths.get("experiment", "src/experiment")),
            models=str(paths.get("models", "models")),
            caches=str(paths.get("caches", "caches")),
            runs=str(paths.get("runs", "runs")),
        ),
        runtime=RuntimeConfig(
            project_dir=project_dir,
            setup_command=setup_command,
            runpod=runpod_config,
        ),
        commands=normalize_managed_commands(
            {str(key): str(value) for key, value in data.get("commands", {}).items()}
        ),
        is_ephemeral=is_ephemeral,
    )


def load_project(start: Path | None = None) -> ProjectConfig:
    root = find_project_root(start)
    config_path = root / CONFIG_FILENAME
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise QuadraError(f"Failed to read {config_path}: {exc}") from exc

    return build_project_config(root, data)


def pyproject_declares_python_project(pyproject_path: Path) -> bool:
    if not pyproject_path.exists():
        return False
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False

    if isinstance(data.get("project"), dict):
        return True
    if isinstance(data.get("build-system"), dict):
        return True
    if isinstance(data.get("dependency-groups"), dict):
        return True

    tool = data.get("tool")
    if not isinstance(tool, dict):
        return False
    return any(isinstance(tool.get(name), dict) for name in ("uv", "poetry", "pdm", "hatch"))


def load_runnable_project(start: Path | None = None) -> ProjectConfig:
    try:
        return load_project(start)
    except QuadraError as exc:
        if f"Could not find {CONFIG_FILENAME}" not in str(exc):
            raise

    root = (start or Path.cwd()).resolve()
    setup_command = DEFAULT_SETUP_COMMAND if pyproject_declares_python_project(root / "pyproject.toml") else None
    data: dict[str, Any] = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "project": {"name": root.name},
        "paths": {
            "libs": "src/libs",
            "experiment": ".",
            "models": "models",
            "caches": "caches",
            "runs": "runs",
        },
        "runtime": {"setup_command": setup_command},
        "commands": {},
    }
    return build_project_config(
        root,
        data,
        require_global_config=True,
        is_ephemeral=True,
    )


def init_project(target_root: Path, project_name: str) -> None:
    scaffold_dirs = [
        target_root / "src" / "libs" / "diffusers",
        target_root / "src" / "libs" / "transformers",
        target_root / "src" / "libs" / "vllm-omni",
        target_root / "src" / "experiment",
        target_root / "models",
        target_root / "caches",
        target_root / "runs",
        target_root / STATE_DIRNAME,
    ]
    scaffold_files = {
        target_root / CONFIG_FILENAME: render_quadra_config(
            project_name,
            use_global_backend=bool(load_global_config()),
        ),
        target_root / QUADRA_WORKER_FILENAME: render_project_worker_py(),
        target_root / "src" / "experiment" / "pyproject.toml": render_experiment_pyproject(
            project_name
        ),
        target_root / "src" / "experiment" / "main.py": render_main_py(project_name),
    }

    if target_root.exists():
        if not target_root.is_dir():
            raise QuadraError(
                f"Target path already exists and is not a directory: {target_root}"
            )
    else:
        target_root.mkdir(parents=True, exist_ok=False)

    for directory in scaffold_dirs:
        if directory.exists():
            if not directory.is_dir():
                raise QuadraError(f"Refusing to overwrite existing path: {directory}")
            continue
        directory.mkdir(parents=True, exist_ok=True)

    for keep_dir in scaffold_dirs:
        if keep_dir.name == STATE_DIRNAME:
            continue

        gitkeep = keep_dir / ".gitkeep"
        if gitkeep.exists():
            if not gitkeep.is_file():
                raise QuadraError(f"Refusing to overwrite existing path: {gitkeep}")
            continue
        gitkeep.write_text("", encoding="utf-8")

    for path, content in scaffold_files.items():
        if path.exists():
            if not path.is_file():
                raise QuadraError(f"Refusing to overwrite existing path: {path}")
            continue
        path.write_text(content, encoding="utf-8")


def render_quadra_config(project_name: str, *, use_global_backend: bool = False) -> str:
    if use_global_backend:
        return textwrap.dedent(
            f"""\
            schema_version = {CONFIG_SCHEMA_VERSION}

            [project]
            name = "{project_name}"

            [paths]
            libs = "src/libs"
            experiment = "src/experiment"
            models = "models"
            caches = "caches"
            runs = "runs"

            [commands]
            smoke = "{DEFAULT_MAIN_COMMAND}"
            main = "{DEFAULT_MAIN_COMMAND}"
            """
        )

    project_dir = DEFAULT_PROJECT_DIR.format(
        volume_mount_path=DEFAULT_TEMPLATE_VOLUME_MOUNT_PATH,
        project_name=project_name,
    )
    gpu_pool_comments = "\n        ".join(SERVERLESS_GPU_POOL_COMMENT_LINES)
    template_name = DEFAULT_TEMPLATE_NAME.format(project_name=project_name)
    setup_command = json.dumps(DEFAULT_SETUP_COMMAND)
    docker_start_cmd = json.dumps(list(DEFAULT_TEMPLATE_DOCKER_START_CMD))
    return textwrap.dedent(
        f"""\
        schema_version = {CONFIG_SCHEMA_VERSION}

        [project]
        name = "{project_name}"

        [paths]
        libs = "src/libs"
        experiment = "src/experiment"
        models = "models"
        caches = "caches"
        runs = "runs"

        [runtime]
        project_dir = "{project_dir}"
        # Setup command tokens: {{project_name}}, {{project_dir}}, {{experiment_dir}}
        # Bootstraps uv into an isolated runtime on first run when the base image does not include it yet.
        setup_command = {setup_command}

        [runtime.runpod]
        api_key_env = "RUNPOD_API_KEY"
        endpoint_name = "quadra-{project_name}"
        {gpu_pool_comments}
        gpu_ids = "AMPERE_16"
        gpu_count = 1
        workers_min = 0
        workers_max = 1
        idle_timeout = 5
        scaler_type = "QUEUE_DELAY"
        scaler_value = 4
        flashboot = false
        network_volume_name = "{project_name}"
        s3_access_key_env = "AWS_ACCESS_KEY_ID"
        s3_secret_key_env = "AWS_SECRET_ACCESS_KEY"
        timeout_seconds = 600

        [runtime.runpod.template]
        id = ""
        name = "{template_name}"
        image_name = "{DEFAULT_TEMPLATE_IMAGE}"
        # Template string tokens: {{project_name}}, {{project_dir}}, {{experiment_dir}}, {{worker_path}}, {{worker_bootstrap_log_path}}, {{worker_runtime_path}}
        docker_start_cmd = {docker_start_cmd}
        container_disk_gb = 20
        env = {{}}
        readme = "Managed by Quadra. Runs {{worker_path}} from the synced project volume."

        [commands]
        smoke = "{DEFAULT_MAIN_COMMAND}"
        main = "{DEFAULT_MAIN_COMMAND}"
        """
    )


def render_experiment_pyproject(project_name: str) -> str:
    return textwrap.dedent(
        f"""\
        [project]
        name = "{project_name}-experiment"
        version = "0.1.0"
        requires-python = ">=3.11"
        """
    )


def render_project_worker_py() -> str:
    return importlib.resources.files("quadra").joinpath("serverless_worker.py").read_text(encoding="utf-8")


def render_main_py(project_name: str) -> str:
    return textwrap.dedent(
        f"""\
        def main() -> None:
            print("{project_name} experiment entrypoint")


        if __name__ == "__main__":
            main()
        """
    )


def infer_repo_name_from_fork_url(fork_url: str) -> str:
    candidate = fork_url.strip().rstrip("/")
    if not candidate:
        raise QuadraError("Fork URL cannot be empty.")
    if candidate.endswith(".git"):
        candidate = candidate[:-4]
    repo_name = candidate.rsplit("/", 1)[-1]
    if ":" in repo_name:
        repo_name = repo_name.rsplit(":", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", repo_name):
        raise QuadraError(
            f"Could not infer a safe library directory name from fork URL: {fork_url}"
        )
    return repo_name


def validate_package_name(package_name: str) -> str:
    normalized = package_name.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", normalized):
        raise QuadraError(
            "Package name must contain only letters, numbers, dots, underscores, and hyphens."
        )
    return normalized


def pep508_dependency_name(requirement: str) -> str:
    return re.split(r"\s*(?:\[|<|>|=|!|~|;|@)", requirement.strip(), maxsplit=1)[0]


def package_dependency_exists(dependencies: object, package_name: str) -> bool:
    if dependencies is None:
        return False
    if not isinstance(dependencies, list):
        raise QuadraError(
            "project.dependencies must be a list in experiment pyproject.toml."
        )
    expected = package_name.lower().replace("_", "-")
    for dependency in dependencies:
        if not isinstance(dependency, str):
            raise QuadraError(
                "project.dependencies must contain only strings in experiment pyproject.toml."
            )
        dependency_name = pep508_dependency_name(dependency).lower().replace("_", "-")
        if dependency_name == expected:
            return True
    return False


def find_toml_table_bounds(lines: list[str], table_name: str) -> tuple[int, int] | None:
    table_header = f"[{table_name}]"
    table_start: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("["):
            continue
        if stripped == table_header:
            table_start = index
            continue
        if table_start is not None:
            return table_start, index
    if table_start is None:
        return None
    return table_start, len(lines)


def format_dependency_lines(dependencies: list[str]) -> list[str]:
    return ["dependencies = [\n"] + [
        f"    {json.dumps(dependency)},\n" for dependency in dependencies
    ] + ["]\n"]


def ensure_project_dependency(
    lines: list[str],
    data: dict[str, Any],
    package_name: str,
) -> list[str]:
    dependencies = data.get("project", {}).get("dependencies")
    if package_dependency_exists(dependencies, package_name):
        return lines

    project_bounds = find_toml_table_bounds(lines, "project")
    if project_bounds is None:
        raise QuadraError("Missing [project] table in experiment pyproject.toml.")
    project_start, project_end = project_bounds
    dependency_lines = format_dependency_lines([package_name])

    if dependencies is None:
        insert_at = project_end
        for index in range(project_start + 1, project_end):
            if lines[index].strip().startswith("requires-python"):
                insert_at = index + 1
                break
        return lines[:insert_at] + dependency_lines + lines[insert_at:]

    if not isinstance(dependencies, list):
        raise QuadraError(
            "project.dependencies must be a list in experiment pyproject.toml."
        )

    updated_dependencies = [
        str(dependency) for dependency in dependencies
    ] + [package_name]
    for index in range(project_start + 1, project_end):
        if not re.match(r"\s*dependencies\s*=", lines[index]):
            continue

        if "[" in lines[index] and "]" in lines[index]:
            return (
                lines[:index]
                + format_dependency_lines(updated_dependencies)
                + lines[index + 1 :]
            )

        dependency_end = index + 1
        while dependency_end < project_end:
            if "]" in lines[dependency_end]:
                break
            dependency_end += 1
        if dependency_end >= project_end:
            raise QuadraError(
                "Could not parse project.dependencies in experiment pyproject.toml."
            )
        return (
            lines[:index]
            + format_dependency_lines(updated_dependencies)
            + lines[dependency_end + 1 :]
        )

    raise QuadraError(
        "Could not locate project.dependencies in experiment pyproject.toml."
    )


def toml_quoted_key(key: str) -> str:
    return json.dumps(key)


def format_uv_source_line(package_name: str, source_path: str) -> str:
    return (
        f"{toml_quoted_key(package_name)} = "
        f"{{ path = {json.dumps(source_path)}, editable = true }}\n"
    )


def ensure_uv_path_source(
    lines: list[str],
    package_name: str,
    source_path: str,
) -> list[str]:
    source_line = format_uv_source_line(package_name, source_path)
    sources_bounds = find_toml_table_bounds(lines, "tool.uv.sources")
    if sources_bounds is None:
        prefix = ["\n"] if lines and lines[-1].strip() else []
        return lines + prefix + ["[tool.uv.sources]\n", source_line]

    sources_start, sources_end = sources_bounds
    quoted_key_pattern = re.escape(toml_quoted_key(package_name))
    bare_key_pattern = re.escape(package_name)
    key_pattern = rf"\s*(?:{quoted_key_pattern}|{bare_key_pattern})\s*="
    for index in range(sources_start + 1, sources_end):
        if re.match(key_pattern, lines[index]):
            return lines[:index] + [source_line] + lines[index + 1 :]
    return lines[:sources_end] + [source_line] + lines[sources_end:]


def wire_experiment_to_local_fork(
    config: ProjectConfig,
    *,
    package_name: str,
    lib_dir: Path,
) -> tuple[Path, bool]:
    """Wire the experiment to a local fork checkout.

    Returns (pyproject_path, wired). When the experiment pyproject has no
    PEP 621 [project] table (e.g. setup.py-based libraries like diffusers),
    uv [tool.uv.sources] redirection does not apply, so wiring is skipped and
    wired=False is returned. The fork is still cloned and synced.
    """
    experiment_dir = config.root / config.paths.experiment
    pyproject_path = experiment_dir / "pyproject.toml"
    if not pyproject_path.exists():
        return pyproject_path, False

    try:
        text = pyproject_path.read_text(encoding="utf-8")
        data = tomllib.loads(text)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise QuadraError(f"Failed to read {pyproject_path}: {exc}") from exc

    if not isinstance(data.get("project"), dict):
        return pyproject_path, False

    source_path = os.path.relpath(lib_dir, experiment_dir).replace(os.sep, "/")
    lines = text.splitlines(keepends=True)
    lines = ensure_project_dependency(lines, data, package_name)
    lines = ensure_uv_path_source(lines, package_name, source_path)
    pyproject_path.write_text("".join(lines), encoding="utf-8")
    return pyproject_path, True


def prepare_library_destination(
    config: ProjectConfig, repo_name: str
) -> tuple[Path, bool]:
    """Return (destination, skip_clone).

    skip_clone is True when the destination already exists and is non-empty,
    so callers can warn and skip re-cloning instead of erroring.
    """
    libs_dir = config.root / config.paths.libs
    destination = libs_dir / repo_name
    if destination.exists() and not destination.is_dir():
        raise QuadraError(f"Refusing to overwrite existing path: {destination}")
    if destination.exists():
        children = list(destination.iterdir())
        if (
            len(children) == 1
            and children[0].name == ".gitkeep"
            and children[0].is_file()
        ):
            children[0].unlink()
            children = []
        if children:
            return destination, True
        return destination, False
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination, False


def clone_fork_into_project(
    config: ProjectConfig,
    *,
    fork_url: str,
    package_name: str | None = None,
) -> tuple[Path, Path, str, bool, bool]:
    repo_name = infer_repo_name_from_fork_url(fork_url)
    resolved_package_name = validate_package_name(package_name or repo_name)
    destination, skip_clone = prepare_library_destination(config, repo_name)

    if not skip_clone:
        try:
            subprocess.run(
                ["git", "clone", fork_url, str(destination)],
                cwd=str(config.root),
                check=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise QuadraError("git is required to clone fork URLs.") from exc
        except subprocess.CalledProcessError as exc:
            raise QuadraError(f"Failed to clone fork URL into {destination}.") from exc

    pyproject_path, wired = wire_experiment_to_local_fork(
        config,
        package_name=resolved_package_name,
        lib_dir=destination,
    )
    return destination, pyproject_path, resolved_package_name, wired, skip_clone


def apply_fork_specs(
    config: ProjectConfig,
    fork_specs: list[tuple[str, str | None]],
) -> None:
    """Clone and wire each fork URL into the project before running a command."""
    for fork_url, package_name in fork_specs:
        destination, _pyproject_path, resolved_package_name, wired, skip_clone = (
            clone_fork_into_project(
                config,
                fork_url=fork_url,
                package_name=package_name,
            )
        )
        if skip_clone:
            click.echo(
                f"warning: library destination already exists, skipping clone: "
                f"{destination}"
            )
        else:
            click.echo(f"forked {fork_url}")
        click.echo(f"library: {destination}")
        click.echo(f"package: {resolved_package_name}")
        if not wired:
            click.echo(
                "note: experiment pyproject has no [project] table; fork cloned "
                "but not wired as a uv dependency. Wire it via your command or "
                "setup_command (e.g. PYTHONPATH)."
            )


def load_runpod_client(config: ProjectConfig) -> Any:
    api_key = os.getenv(config.runtime.runpod.api_key_env)
    if not api_key:
        raise QuadraError(
            f"RunPod API key not configured. Set {config.runtime.runpod.api_key_env}."
        )

    return RunpodClient(api_key)


def runpod_endpoint_name(config: ProjectConfig) -> str:
    return config.runtime.runpod.endpoint_name or f"quadra-{config.name}"


def remote_volume_state_path(config: ProjectConfig, filename: str) -> str:
    return str(
        PurePosixPath(config.runtime.runpod.volume_mount_path)
        / STATE_DIRNAME
        / filename
    )


def remote_worker_path(config: ProjectConfig) -> str:
    return remote_volume_state_path(config, QUADRA_WORKER_FILENAME)


def remote_worker_bootstrap_log_path(config: ProjectConfig) -> str:
    return str(
        PurePosixPath(config.runtime.project_dir)
        / STATE_DIRNAME
        / WORKER_BOOTSTRAP_LOG_FILENAME
    )


def remote_worker_runtime_path(config: ProjectConfig) -> str:
    return remote_volume_state_path(config, "worker-runtime")


def managed_worker_source() -> bytes:
    return importlib.resources.files("quadra").joinpath(
        "serverless_worker.py"
    ).read_text(encoding="utf-8").encode("utf-8")


def managed_sync_files() -> dict[str, bytes]:
    worker_source = managed_worker_source()
    return {
        f"{STATE_DIRNAME}/{QUADRA_WORKER_FILENAME}": worker_source,
    }


def sync_global_worker(s3: Any, bucket: str, config: ProjectConfig) -> None:
    worker_key = remote_global_state_key(QUADRA_WORKER_FILENAME)
    worker_source = managed_worker_source()
    try:
        response = s3.get_object(Bucket=bucket, Key=worker_key)
        if response["Body"].read() == worker_source:
            return
    except Exception:
        pass

    try:
        s3.put_object(
            Bucket=bucket,
            Key=worker_key,
            Body=worker_source,
            ContentType="text/x-python",
        )
    except Exception as exc:
        raise QuadraError("Failed to sync global Quadra worker to volume.") from exc


def remote_experiment_dir(config: ProjectConfig) -> str:
    return str(PurePosixPath(config.runtime.project_dir) / config.paths.experiment)


def expand_template_tokens(value: str, config: ProjectConfig) -> str:
    return (
        value.replace("{project_name}", config.name)
        .replace("{project_dir}", config.runtime.project_dir)
        .replace("{experiment_dir}", remote_experiment_dir(config))
        .replace("{worker_path}", remote_worker_path(config))
        .replace(
            "{worker_bootstrap_log_path}",
            remote_worker_bootstrap_log_path(config),
        )
        .replace("{worker_runtime_path}", remote_worker_runtime_path(config))
        .replace("{runpod_volume_root}", config.runtime.runpod.volume_mount_path)
    )


def expand_runtime_tokens(value: str, config: ProjectConfig) -> str:
    return (
        value.replace("{project_name}", config.name)
        .replace("{project_dir}", config.runtime.project_dir)
        .replace("{experiment_dir}", remote_experiment_dir(config))
        .replace("{runpod_volume_root}", config.runtime.runpod.volume_mount_path)
    )


def build_template_spec(config: ProjectConfig) -> TemplateSpec:
    template = config.runtime.runpod.template
    return TemplateSpec(
        name=expand_template_tokens(template.name, config),
        image_name=expand_template_tokens(template.image_name, config),
        ports=tuple(expand_template_tokens(item, config) for item in template.ports),
        docker_entrypoint=tuple(
            expand_template_tokens(item, config) for item in template.docker_entrypoint
        ),
        docker_start_cmd=tuple(
            expand_template_tokens(item, config) for item in template.docker_start_cmd
        ),
        volume_mount_path=config.runtime.runpod.volume_mount_path,
        env={
            key: expand_template_tokens(value, config)
            for key, value in template.env.items()
        },
        container_disk_gb=template.container_disk_gb,
        readme=expand_template_tokens(template.readme, config),
    )


def format_runpod_volume_option(volume: dict[str, Any]) -> str:
    volume_id = optional_str(volume.get("id")) or "unknown-id"
    name = optional_str(volume.get("name")) or "<unnamed>"
    data_center_id = optional_str(volume.get("dataCenterId")) or "unknown-dc"
    size = volume.get("size")
    size_label = f"{size} GB" if isinstance(size, int) else "size unknown"
    return f"{volume_id}  {name!r}  {data_center_id}  {size_label}"


def prompt_resolve_missing_runpod_volume(
    config: ProjectConfig,
    client: Any,
    *,
    target_name: str,
    volumes: list[dict[str, Any]],
) -> VolumeHandle | None:
    if not supports_interactive_prompts():
        return None

    click.echo(f"No RunPod network volume named {target_name!r} was found.")
    linkable_volumes = [
        volume
        for volume in volumes
        if optional_str(volume.get("id"))
        and optional_str(volume.get("dataCenterId")) in S3_ENDPOINTS
    ]
    if linkable_volumes:
        action = click.prompt(
            "How would you like to continue",
            type=click.Choice(("create", "link", "cancel"), case_sensitive=False),
            default="create",
            show_choices=True,
        )
        if action == "cancel":
            return None
        if action == "link":
            sorted_linkable_volumes = sorted(
                linkable_volumes,
                key=lambda volume: (
                    optional_str(volume.get("name")) or "",
                    optional_str(volume.get("id")) or "",
                ),
            )
            click.echo("Available RunPod network volumes:")
            for index, volume in enumerate(sorted_linkable_volumes, start=1):
                click.echo(f"  {index}. {format_runpod_volume_option(volume)}")
            selection = click.prompt(
                "Select a RunPod network volume to link",
                type=click.IntRange(min=1, max=len(sorted_linkable_volumes)),
            )
            selected = sorted_linkable_volumes[selection - 1]
            linked_volume = VolumeHandle(
                id=str(selected["id"]),
                name=optional_str(selected.get("name")) or target_name,
                data_center_id=optional_str(selected.get("dataCenterId")),
            )
            if not config.is_ephemeral:
                persist_network_volume_link(config, linked_volume)
            remember_selected_network_volume(config, linked_volume)
            click.echo(
                f"linked {config.name} to RunPod network volume {linked_volume.id} "
                f"({linked_volume.name!r}, {linked_volume.data_center_id or 'unknown-dc'})"
            )
            if config.is_ephemeral:
                click.echo("using linked volume for this command")
            else:
                click.echo(
                    f"updated runtime.runpod.network_volume_id in {config.root / CONFIG_FILENAME}"
                )
            return linked_volume
    elif volumes:
        click.echo(
            "Existing RunPod network volumes were found, but none are in an "
            "S3-supported datacenter that Quadra can use."
        )
        if not click.confirm(
            "Create a new RunPod network volume now? This allocates billable storage.",
            default=False,
        ):
            return None
    elif not click.confirm(
        "Create it now? This allocates billable RunPod storage.",
        default=False,
    ):
        return None

    configured_locations = split_csv(config.runtime.runpod.locations)
    configured_supported_locations = tuple(
        location for location in configured_locations if location in S3_ENDPOINTS
    )
    if configured_supported_locations:
        location_choices = configured_supported_locations
    else:
        location_choices = tuple(sorted(S3_ENDPOINTS))
        if configured_locations:
            click.echo(
                "runtime.runpod.locations does not name an S3-supported datacenter, "
                "so choose one explicitly for the new network volume."
            )

    if len(location_choices) == 1:
        data_center_id = location_choices[0]
        click.echo(
            f"Using RunPod datacenter {data_center_id} for the new network volume."
        )
    else:
        data_center_id = click.prompt(
            "RunPod datacenter for the new network volume",
            type=click.Choice(location_choices, case_sensitive=False),
            default=location_choices[0],
            show_choices=True,
        )

    size_gb = click.prompt(
        "Network volume size in GB",
        type=click.IntRange(min=1),
        default=config.runtime.runpod.network_volume_size_gb,
        show_default=True,
    )
    volume = client.create_network_volume(
        name=target_name,
        data_center_id=data_center_id,
        size_gb=size_gb,
    )
    resolved_data_center_id = optional_str(volume.get("dataCenterId")) or data_center_id
    resolved_name = optional_str(volume.get("name")) or target_name
    click.echo(
        f"created RunPod network volume {volume['id']} "
        f"({resolved_name!r}, {resolved_data_center_id}, {size_gb} GB)"
    )
    created_volume = VolumeHandle(
        id=str(volume["id"]),
        name=resolved_name,
        data_center_id=resolved_data_center_id,
    )
    remember_selected_network_volume(config, created_volume)
    return created_volume


def resolve_runpod_volume(
    config: ProjectConfig, client: Any, *, offer_create: bool = False
) -> VolumeHandle:
    override = RUNTIME_NETWORK_VOLUME_OVERRIDES.get(config.root)
    if override is not None:
        return override

    target_id = config.runtime.runpod.network_volume_id
    target_name = config.runtime.runpod.network_volume_name or config.name
    report_step("resolving RunPod network volume...")
    volumes = list(client.get_network_volumes())

    if target_id:
        for volume in volumes:
            if optional_str(volume.get("id")) == target_id:
                return VolumeHandle(
                    id=target_id,
                    name=optional_str(volume.get("name")) or target_id,
                    data_center_id=optional_str(volume.get("dataCenterId")),
                )
        raise QuadraError(f"RunPod network volume {target_id} was not found.")

    matches = [
        volume for volume in volumes if optional_str(volume.get("name")) == target_name
    ]
    if len(matches) == 1:
        volume = matches[0]
        return VolumeHandle(
            id=str(volume["id"]),
            name=optional_str(volume.get("name")) or target_name,
            data_center_id=optional_str(volume.get("dataCenterId")),
        )
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod network volumes are named {target_name!r}. "
            "Set runtime.runpod.network_volume_id."
        )
    if offer_create:
        created = prompt_resolve_missing_runpod_volume(
            config,
            client,
            target_name=target_name,
            volumes=volumes,
        )
        if created is not None:
            return created
    raise QuadraError(
        f"No RunPod network volume named {target_name!r} was found. "
        "Create it in RunPod, link runtime.runpod.network_volume_id to an existing "
        "volume, rerun an interactive Quadra command to resolve it now, or configure "
        "runtime.runpod.network_volume_id."
    )


def fetch_template_details(client: Any, template: dict[str, Any]) -> dict[str, Any]:
    template_id = optional_str(template.get("id"))
    if not template_id or not hasattr(client, "get_template"):
        return template
    try:
        detailed = client.get_template(template_id)
    except (QuadraError, KeyError):
        return template
    return detailed if isinstance(detailed, dict) else template


def fetch_endpoint_details(client: Any, endpoint: dict[str, Any]) -> dict[str, Any]:
    endpoint_id = optional_str(endpoint.get("id"))
    if not endpoint_id or not hasattr(client, "get_endpoint"):
        return endpoint
    try:
        detailed = client.get_endpoint(endpoint_id, include_workers=True)
    except (QuadraError, KeyError):
        return endpoint
    return detailed if isinstance(detailed, dict) else endpoint


def template_matches_spec(template: dict[str, Any], spec: TemplateSpec) -> bool:
    return (
        optional_str(template.get("name")) == spec.name
        and optional_str(template.get("imageName")) == spec.image_name
        and tuple(str(item) for item in template.get("ports") or []) == spec.ports
        and tuple(str(item) for item in template.get("dockerEntrypoint") or [])
        == spec.docker_entrypoint
        and tuple(str(item) for item in template.get("dockerStartCmd") or [])
        == spec.docker_start_cmd
        and optional_str(template.get("volumeMountPath")) == spec.volume_mount_path
        and {
            str(key): str(value)
            for key, value in (template.get("env") or {}).items()
        }
        == spec.env
        and int(template.get("containerDiskInGb", spec.container_disk_gb))
        == spec.container_disk_gb
        and str(template.get("readme", "")) == spec.readme
    )


def endpoint_has_only_nonviable_workers(endpoint: dict[str, Any]) -> bool:
    workers_value = endpoint.get("workers")
    if not isinstance(workers_value, list):
        return False

    workers = [worker for worker in workers_value if isinstance(worker, dict)]
    if not workers:
        return False

    for worker in workers:
        desired_status = optional_str(worker.get("desiredStatus")) or optional_str(
            worker.get("desired_status")
        )
        if desired_status == "RUNNING" and not worker_looks_unhealthy(worker):
            return False
        if desired_status not in TERMINAL_WORKER_DESIRED_STATUSES and not worker_looks_unhealthy(
            worker
        ):
            return False

    return True


def resolve_template(config: ProjectConfig, client: Any) -> TemplateHandle:
    template_id = config.runtime.runpod.template.id
    spec = build_template_spec(config)
    template_name = spec.name

    report_step("resolving RunPod template...")
    if template_id:
        templates = list(client.get_templates())
        for template in templates:
            if optional_str(template.get("id")) == template_id:
                detailed_template = fetch_template_details(client, template)
                needs_update = not template_matches_spec(detailed_template, spec)
                if needs_update:
                    report_step(f"updating RunPod template {template_id!r}...")
                    template = client.update_template(
                        template_id,
                        name=spec.name,
                        image_name=spec.image_name,
                        ports=spec.ports,
                        docker_entrypoint=spec.docker_entrypoint,
                        docker_start_cmd=spec.docker_start_cmd,
                        volume_mount_path=spec.volume_mount_path,
                        env=spec.env,
                        container_disk_gb=spec.container_disk_gb,
                        readme=spec.readme,
                    )
                return TemplateHandle(
                    id=template_id,
                    name=optional_str(template.get("name")) or template_id,
                    updated=needs_update,
                )
        return TemplateHandle(id=template_id, name=template_name)

    templates = list(client.get_templates())
    matches = [
        template
        for template in templates
        if optional_str(template.get("name")) == template_name
    ]
    if len(matches) == 1:
        template = fetch_template_details(client, matches[0])
        needs_update = not template_matches_spec(template, spec)
        if needs_update:
            report_step(f"updating RunPod template {template_name!r}...")
            template = client.update_template(
                str(template["id"]),
                name=spec.name,
                image_name=spec.image_name,
                ports=spec.ports,
                docker_entrypoint=spec.docker_entrypoint,
                docker_start_cmd=spec.docker_start_cmd,
                volume_mount_path=spec.volume_mount_path,
                env=spec.env,
                container_disk_gb=spec.container_disk_gb,
                readme=spec.readme,
            )
        return TemplateHandle(
            id=str(template["id"]),
            name=optional_str(template.get("name")) or template_name,
            updated=needs_update,
        )
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod templates are named {template_name!r}. "
            "Set runtime.runpod.template.id."
        )

    report_step(f"creating RunPod template {spec.name!r}...")
    template = client.create_template(
        name=spec.name,
        image_name=spec.image_name,
        ports=spec.ports,
        docker_entrypoint=spec.docker_entrypoint,
        docker_start_cmd=spec.docker_start_cmd,
        volume_mount_path=spec.volume_mount_path,
        env=spec.env,
        container_disk_gb=spec.container_disk_gb,
        readme=spec.readme,
    )
    return TemplateHandle(
        id=str(template["id"]),
        name=optional_str(template.get("name")) or spec.name,
    )


def ensure_volume_supports_s3(volume: VolumeHandle) -> str:
    if not volume.data_center_id:
        raise QuadraError(
            f"RunPod network volume {volume.id} does not report a datacenter."
        )
    endpoint_url = S3_ENDPOINTS.get(volume.data_center_id)
    if not endpoint_url:
        raise QuadraError(
            f"RunPod network volume {volume.id} is in {volume.data_center_id}, "
            "which does not currently support the RunPod S3 API. "
            "Quadra serverless sync/pull requires a volume in an S3-supported datacenter."
        )
    return endpoint_url


def remote_project_key(config: ProjectConfig) -> str:
    project_dir = PurePosixPath(config.runtime.project_dir)
    volume_mount_path = PurePosixPath(config.runtime.runpod.volume_mount_path)
    try:
        relative = project_dir.relative_to(volume_mount_path)
    except ValueError as exc:
        raise QuadraError(
            f"runtime.project_dir must live under {volume_mount_path} for RunPod Serverless."
        ) from exc
    return relative.as_posix()


def remote_run_key_prefix(config: ProjectConfig, run_id: str) -> str:
    return posixpath.join(
        remote_project_key(config), config.paths.runs.replace("\\", "/"), run_id
    )


def remote_run_file_key(config: ProjectConfig, run_id: str, filename: str) -> str:
    return posixpath.join(remote_run_key_prefix(config, run_id), filename)


def remote_run_manifest_key(config: ProjectConfig, run_id: str) -> str:
    return remote_run_file_key(config, run_id, RUN_MANIFEST_FILENAME)


def remote_state_file_key(config: ProjectConfig, filename: str) -> str:
    return posixpath.join(remote_project_key(config), STATE_DIRNAME, filename)


def remote_sync_manifest_key(config: ProjectConfig) -> str:
    return remote_state_file_key(config, SYNC_MANIFEST_FILENAME)


def remote_global_state_key(filename: str) -> str:
    return posixpath.join(STATE_DIRNAME, filename)


def build_s3_client(config: ProjectConfig, volume: VolumeHandle) -> Any:
    endpoint_url = ensure_volume_supports_s3(volume)
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError as exc:
        raise QuadraError(
            "This Quadra installation is missing the `boto3` package required for volume sync."
        ) from exc

    client_kwargs: dict[str, Any] = {
        "service_name": "s3",
        "endpoint_url": endpoint_url,
        "region_name": volume.data_center_id,
    }

    access_key_env = config.runtime.runpod.s3_access_key_env
    secret_key_env = config.runtime.runpod.s3_secret_key_env
    access_key = os.getenv(access_key_env) if access_key_env else None
    secret_key = os.getenv(secret_key_env) if secret_key_env else None
    if access_key and secret_key:
        client_kwargs["aws_access_key_id"] = access_key
        client_kwargs["aws_secret_access_key"] = secret_key

    s3 = boto3.client(**client_kwargs)

    try:
        s3.list_objects_v2(Bucket=volume.id, MaxKeys=1)
    except NoCredentialsError as exc:
        raise QuadraError(
            "RunPod S3 credentials are not configured. Set the configured S3 credential env vars "
            "or configure the AWS CLI with your RunPod S3 API key."
        ) from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"InvalidAccessKeyId", "SignatureDoesNotMatch", "AccessDenied"}:
            raise QuadraError(
                "RunPod S3 credentials were rejected. Use your RunPod user ID as the access key "
                "and a RunPod S3 API key secret as the secret key."
            ) from exc
        raise QuadraError(
            f"Failed to access RunPod S3 volume {volume.id}: {exc}"
        ) from exc

    return s3


def iter_local_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in dir_names if name not in DEFAULT_IGNORES]
        for file_name in file_names:
            if file_name.endswith(".pyc"):
                continue
            file_path = Path(current_root) / file_name
            relative = file_path.relative_to(root).as_posix()
            if any(part in DEFAULT_IGNORES for part in Path(relative).parts):
                continue
            files[relative] = file_path
    return files


def hash_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise QuadraError(f"Failed to hash {path}: {exc}") from exc
    return digest.hexdigest()


def hash_bytes_sha256(payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(payload)
    return digest.hexdigest()


def build_local_sync_manifest(
    local_files: dict[str, Path],
) -> dict[str, dict[str, str | int]]:
    manifest: dict[str, dict[str, str | int]] = {}
    for relative, file_path in sorted(local_files.items()):
        try:
            size = file_path.stat().st_size
        except OSError as exc:
            raise QuadraError(f"Failed to stat {file_path}: {exc}") from exc
        manifest[relative] = {
            "sha256": hash_file_sha256(file_path),
            "size": size,
        }
    return manifest


def list_remote_keys(s3: Any, bucket: str, prefix: str) -> set[str]:
    keys: set[str] = set()
    continuation_token: str | None = None
    while True:
        params: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            params["ContinuationToken"] = continuation_token
        response = s3.list_objects_v2(**params)
        for item in response.get("Contents", []):
            keys.add(str(item["Key"]))
        if not response.get("IsTruncated"):
            return keys
        continuation_token = response.get("NextContinuationToken")


def load_remote_sync_manifest(
    s3: Any, bucket: str, key: str
) -> dict[str, dict[str, str | int]]:
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except Exception:
        return {}

    try:
        body = response["Body"].read()
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return {}

    if not isinstance(payload, dict):
        return {}
    if payload.get("version") != SYNC_MANIFEST_VERSION:
        return {}

    files = payload.get("files")
    if not isinstance(files, dict):
        return {}

    manifest: dict[str, dict[str, str | int]] = {}
    for relative, metadata in files.items():
        if not isinstance(relative, str) or not isinstance(metadata, dict):
            continue
        sha256 = metadata.get("sha256")
        size = metadata.get("size")
        if not isinstance(sha256, str):
            continue
        if not isinstance(size, int) or size < 0:
            continue
        manifest[relative] = {"sha256": sha256, "size": size}
    return manifest


def write_remote_sync_manifest(
    s3: Any,
    bucket: str,
    key: str,
    manifest: dict[str, dict[str, str | int]],
) -> None:
    payload = {
        "version": SYNC_MANIFEST_VERSION,
        "generated_at": now_utc(),
        "files": manifest,
    }
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=(json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            ContentType="application/json",
        )
    except Exception as exc:
        raise QuadraError(f"Failed to write remote sync manifest {key}: {exc}") from exc


def _looks_like_s3_redirect_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    error = response.get("Error")
    if not isinstance(error, dict):
        return False
    code = str(error.get("Code", "")).strip()
    message = str(error.get("Message", "")).strip().lower()
    if code in {"307", "TemporaryRedirect", "PermanentRedirect"}:
        return True
    return "redirect" in message


def delete_remote_keys(s3: Any, bucket: str, keys: list[str]) -> None:
    if not keys:
        return

    delete_payload = {"Objects": [{"Key": key} for key in keys]}
    try:
        response = s3.delete_objects(Bucket=bucket, Delete=delete_payload)
    except Exception as exc:
        if _looks_like_s3_redirect_error(exc) and hasattr(s3, "delete_object"):
            for key in keys:
                try:
                    s3.delete_object(Bucket=bucket, Key=key)
                except Exception as delete_exc:
                    raise QuadraError(
                        f"Failed to delete remote file {key}: {delete_exc}"
                    ) from delete_exc
            return
        raise QuadraError(f"Failed to delete remote files: {exc}") from exc

    errors = response.get("Errors") if isinstance(response, dict) else None
    if isinstance(errors, list) and errors:
        formatted = ", ".join(
            f"{item.get('Key', '<unknown>')}: {item.get('Code', '<unknown>')}"
            for item in errors
            if isinstance(item, dict)
        )
        raise QuadraError(f"Failed to delete remote files: {formatted}")


def tracked_remote_keys_from_manifest(
    config: ProjectConfig, manifest: dict[str, dict[str, str | int]]
) -> set[str]:
    prefix = remote_project_key(config)
    return {posixpath.join(prefix, relative) for relative in manifest}


def sync_project(config: ProjectConfig) -> tuple[VolumeHandle, int, int]:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client, offer_create=True)
    report_step(
        f"connecting to RunPod S3 volume {volume.id} "
        f"({volume.data_center_id or 'unknown-dc'})..."
    )
    s3 = build_s3_client(config, volume)
    sync_global_worker(s3, volume.id, config)

    prefix = remote_project_key(config)
    report_step("scanning local project files...")
    local_files = iter_local_files(config.root)
    managed_files = managed_sync_files()
    report_step("hashing local project files...")
    local_manifest = build_local_sync_manifest(local_files)
    for relative, payload in managed_files.items():
        local_manifest[relative] = {
            "sha256": hash_bytes_sha256(payload),
            "size": len(payload),
        }
    manifest_key = remote_sync_manifest_key(config)
    report_step("loading remote sync manifest...")
    remote_manifest = load_remote_sync_manifest(s3, volume.id, manifest_key)
    report_step("checking remote project for stale files...")
    changed_files = [
        (relative, posixpath.join(prefix, relative))
        for relative in sorted(local_manifest)
        if remote_manifest.get(relative) != local_manifest[relative]
    ]
    if changed_files:
        with click.progressbar(
            changed_files,
            label=f"[quadra] uploading {len(changed_files)} changed files",
        ) as progress:
            for relative, key in progress:
                managed_payload = managed_files.get(relative)
                if managed_payload is not None:
                    s3.put_object(
                        Bucket=volume.id,
                        Key=key,
                        Body=managed_payload,
                        ContentType="text/x-python",
                    )
                    continue
                s3.upload_file(str(local_files[relative]), volume.id, key)
    else:
        report_step("uploading 0 changed files...")

    expected_keys = {posixpath.join(prefix, relative) for relative in local_manifest}
    expected_keys.add(manifest_key)
    tracked_remote_keys = tracked_remote_keys_from_manifest(config, remote_manifest)
    stale_keys = sorted(
        tracked_remote_keys - expected_keys - {manifest_key}
    )
    if stale_keys:
        report_step(f"deleting {len(stale_keys)} stale remote files...")
        delete_remote_keys(s3, volume.id, stale_keys)

    if (
        remote_manifest != local_manifest
        or bool(stale_keys)
    ):
        report_step("writing remote sync manifest...")
        write_remote_sync_manifest(s3, volume.id, manifest_key, local_manifest)

    return volume, len(changed_files), len(stale_keys)


def ensure_project_synced(config: ProjectConfig, volume: VolumeHandle) -> None:
    report_step(
        f"connecting to RunPod S3 volume {volume.id} "
        f"({volume.data_center_id or 'unknown-dc'})..."
    )
    s3 = build_s3_client(config, volume)
    sync_global_worker(s3, volume.id, config)
    report_step("checking remote project sync state...")
    key = (
        remote_sync_manifest_key(config)
        if config.is_ephemeral
        else posixpath.join(remote_project_key(config), CONFIG_FILENAME)
    )
    try:
        s3.head_object(Bucket=volume.id, Key=key)
    except Exception as exc:
        raise QuadraError(
            "Remote project has not been synced yet. Run `quadra sync` first."
        ) from exc


def create_runpod_endpoint(
    config: ProjectConfig,
    client: Any,
    volume: VolumeHandle,
    *,
    endpoint_name: str,
    template_id: str,
) -> dict[str, Any]:
    return client.create_endpoint(
        name=endpoint_name,
        template_id=template_id,
        gpu_ids=config.runtime.runpod.gpu_ids,
        network_volume_id=volume.id,
        locations=config.runtime.runpod.locations,
        idle_timeout=config.runtime.runpod.idle_timeout,
        scaler_type=config.runtime.runpod.scaler_type,
        scaler_value=config.runtime.runpod.scaler_value,
        workers_min=config.runtime.runpod.workers_min,
        workers_max=config.runtime.runpod.workers_max,
        flashboot=config.runtime.runpod.flashboot,
        allowed_cuda_versions=config.runtime.runpod.allowed_cuda_versions,
        gpu_count=config.runtime.runpod.gpu_count,
        timeout_seconds=config.runtime.runpod.timeout_seconds,
    )


def resolve_endpoint(
    config: ProjectConfig, client: Any, volume: VolumeHandle
) -> EndpointHandle:
    report_step("resolving RunPod endpoint...")
    template = resolve_template(config, client)
    endpoints = list(client.get_endpoints())
    endpoint_id = config.runtime.runpod.endpoint_id
    endpoint_name = runpod_endpoint_name(config)

    if endpoint_id:
        matches = [
            endpoint
            for endpoint in endpoints
            if optional_str(endpoint.get("id")) == endpoint_id
        ]
        if len(matches) == 1:
            endpoint = matches[0]
            detailed_endpoint = fetch_endpoint_details(client, endpoint)
            if endpoint_has_only_nonviable_workers(detailed_endpoint) and hasattr(
                client, "delete_endpoint"
            ):
                report_step(
                    f"recreating RunPod endpoint {endpoint_id!r} because existing workers are not viable..."
                )
                client.delete_endpoint(str(endpoint["id"]))
                endpoint = create_runpod_endpoint(
                    config,
                    client,
                    volume,
                    endpoint_name=endpoint_name,
                    template_id=template.id,
                )
            else:
                report_step(f"updating RunPod endpoint {endpoint_id!r}...")
                endpoint = client.update_endpoint(
                    str(endpoint["id"]),
                    template_id=template.id,
                    network_volume_id=volume.id,
                )
            return EndpointHandle(
                id=str(endpoint["id"]),
                name=optional_str(endpoint.get("name")) or endpoint_id,
            )
        raise QuadraError(f"RunPod endpoint {endpoint_id} was not found.")

    matches = [
        endpoint
        for endpoint in endpoints
        if optional_str(endpoint.get("name")) == endpoint_name
    ]
    if len(matches) == 1:
        endpoint = matches[0]
        detailed_endpoint = fetch_endpoint_details(client, endpoint)
        if endpoint_has_only_nonviable_workers(detailed_endpoint) and hasattr(
            client, "delete_endpoint"
        ):
            report_step(
                f"recreating RunPod endpoint {endpoint_name!r} because existing workers are not viable..."
            )
            client.delete_endpoint(str(endpoint["id"]))
            endpoint = create_runpod_endpoint(
                config,
                client,
                volume,
                endpoint_name=endpoint_name,
                template_id=template.id,
            )
        else:
            report_step(f"updating RunPod endpoint {endpoint_name!r}...")
            endpoint = client.update_endpoint(
                str(endpoint["id"]),
                template_id=template.id,
                network_volume_id=volume.id,
            )
        return EndpointHandle(
            id=str(endpoint["id"]),
            name=optional_str(endpoint.get("name")) or endpoint_name,
        )
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod endpoints are named {endpoint_name!r}. "
            "Set runtime.runpod.endpoint_id."
        )

    report_step(f"creating RunPod endpoint {endpoint_name!r}...")
    endpoint = create_runpod_endpoint(
        config,
        client,
        volume,
        endpoint_name=endpoint_name,
        template_id=template.id,
    )
    return EndpointHandle(
        id=str(endpoint["id"]),
        name=optional_str(endpoint.get("name")) or endpoint_name,
    )


def resolve_run_command(
    config: ProjectConfig, command_parts: tuple[str, ...], project_root: Path
) -> tuple[str, str]:
    raw_command = " ".join(command_parts).strip()
    if not raw_command:
        raise QuadraError("Missing command. Pass a named workflow or shell command.")

    main_path = project_root / config.paths.experiment / "main.py"
    if len(command_parts) == 1:
        command_name = command_parts[0]
        if command_name in config.commands:
            return config.commands[command_name], command_name
        if command_name in {"smoke", "main"} and main_path.exists():
            return DEFAULT_MAIN_COMMAND, command_name
        script_path = (
            project_root / config.paths.experiment / "scripts" / f"{command_name}.py"
        )
        if script_path.exists():
            return f"python scripts/{command_name}.py", command_name

    return raw_command, raw_command


def build_job_payload(
    config: ProjectConfig,
    *,
    run_id: str,
    command: str,
    workflow: str,
    setup_command: str | None,
) -> dict[str, Any]:
    project_dir = PurePosixPath(config.runtime.project_dir)
    experiment_dir = project_dir / config.paths.experiment
    run_dir = project_dir / config.paths.runs / run_id
    if setup_command:
        setup_command = expand_runtime_tokens(setup_command, config)
    return {
        "quadra": {
            "project_name": config.name,
            "workflow": workflow,
            "run_id": run_id,
            "project_dir": str(project_dir),
            "experiment_dir": str(experiment_dir),
            "run_dir": str(run_dir),
            "artifacts_dir": str(run_dir / "artifacts"),
            "setup_command": setup_command,
            "command": command,
            "env": {
                "QUADRA_PROJECT_NAME": config.name,
                "QUADRA_RUN_ID": run_id,
                "QUADRA_PROJECT_DIR": str(project_dir),
                "QUADRA_EXPERIMENT_DIR": str(experiment_dir),
                "QUADRA_RUN_DIR": str(run_dir),
            },
        }
    }


def save_last_run(config: ProjectConfig, reference: RunReference) -> None:
    config.quadra_dir.mkdir(parents=True, exist_ok=True)
    config.last_run_file.write_text(
        json.dumps(reference.__dict__, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m{remaining_seconds:02d}s"
    hours, remaining_minutes = divmod(minutes, 60)
    return f"{hours}h{remaining_minutes:02d}m{remaining_seconds:02d}s"


def format_bootstrap_log_tail(
    text: str, *, max_lines: int = BOOTSTRAP_LOG_TAIL_LINES
) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text.rstrip()
    return "\n".join(lines[-max_lines:]).rstrip()


def describe_job_status(status: str, *, has_remote_output: bool) -> str:
    if status == "IN_QUEUE":
        return "queued on RunPod"
    if status in {"IN_PROGRESS", "RUNNING"}:
        if has_remote_output:
            return "worker running"
        return "worker running, waiting for remote logs"
    if status == "COMPLETED":
        return "completed"
    if status == "FAILED":
        return "failed"
    if status == "TIMED_OUT":
        return "timed out"
    if status == "CANCELLED":
        return "cancelled"
    return status.replace("_", " ").lower()


def report_poll_status(
    reference: RunReference,
    status: str,
    *,
    has_remote_output: bool,
    elapsed_seconds: int,
    detail: str | None = None,
) -> None:
    description = describe_job_status(status, has_remote_output=has_remote_output)
    detail_suffix = f"; {detail}" if detail else ""
    click.echo(
        f"[quadra] {reference.workflow}: {description} "
        f"(status {status}, elapsed {format_duration(elapsed_seconds)}{detail_suffix})"
    )


def format_worker_diagnostic(worker: dict[str, Any]) -> str:
    worker_id = optional_str(worker.get("id")) or "<unknown-worker>"
    details: list[str] = []
    desired_status = optional_str(worker.get("desiredStatus")) or optional_str(
        worker.get("desired_status")
    )
    if desired_status:
        details.append(desired_status)
    worker_status = optional_str(worker.get("status"))
    if worker_status and worker_status != desired_status:
        details.append(worker_status)
    last_status_change = optional_str(worker.get("lastStatusChange")) or optional_str(
        worker.get("last_status_change")
    )
    if last_status_change:
        details.append(last_status_change)
    if not details:
        return worker_id
    return f"{worker_id} ({'; '.join(details)})"


def worker_looks_unhealthy(worker: dict[str, Any]) -> bool:
    desired_status = optional_str(worker.get("desiredStatus")) or optional_str(
        worker.get("desired_status")
    )
    worker_status = optional_str(worker.get("status"))
    last_status_change = optional_str(worker.get("lastStatusChange")) or optional_str(
        worker.get("last_status_change")
    )
    state_text = " ".join(
        part.lower()
        for part in (desired_status, worker_status, last_status_change)
        if part
    )
    return any(hint in state_text for hint in UNHEALTHY_WORKER_TEXT_HINTS)


def inspect_endpoint_queue(
    endpoint: dict[str, Any] | None,
) -> EndpointQueueDiagnostics:
    if not isinstance(endpoint, dict):
        return EndpointQueueDiagnostics()

    workers_value = endpoint.get("workers")
    if not isinstance(workers_value, list):
        return EndpointQueueDiagnostics()

    workers = [worker for worker in workers_value if isinstance(worker, dict)]
    if not workers:
        return EndpointQueueDiagnostics(progress_summary="workers: none reported yet")

    running_count = 0
    starting_count = 0
    exited_count = 0
    blocked_workers: list[str] = []
    exited_workers: list[str] = []
    for worker in workers:
        desired_status = optional_str(worker.get("desiredStatus")) or optional_str(
            worker.get("desired_status")
        )
        is_terminal = desired_status in TERMINAL_WORKER_DESIRED_STATUSES
        is_unhealthy = worker_looks_unhealthy(worker)

        if desired_status == "RUNNING" and not is_unhealthy:
            running_count += 1
            continue
        if is_unhealthy:
            blocked_workers.append(format_worker_diagnostic(worker))
            continue
        if is_terminal:
            exited_count += 1
            exited_workers.append(format_worker_diagnostic(worker))
            continue
        starting_count += 1

    summary_parts: list[str] = []
    if running_count:
        summary_parts.append(f"{running_count} running")
    if starting_count:
        summary_parts.append(f"{starting_count} starting")
    if exited_count:
        summary_parts.append(f"{exited_count} exited")
    if blocked_workers:
        summary_parts.append(f"{len(blocked_workers)} blocked")
    summary = "workers: " + ", ".join(summary_parts)
    if not summary_parts:
        summary = "workers: status unavailable"

    if blocked_workers and not running_count and not starting_count:
        return EndpointQueueDiagnostics(
            progress_summary=summary,
            blocking_workers=tuple(blocked_workers),
        )

    if exited_workers and not running_count and not starting_count:
        return EndpointQueueDiagnostics(
            progress_summary=summary,
            exited_workers=tuple(exited_workers),
        )

    return EndpointQueueDiagnostics(progress_summary=summary)


def get_endpoint_queue_diagnostics(
    client: Any,
    endpoint_id: str,
) -> EndpointQueueDiagnostics:
    if not hasattr(client, "get_endpoint"):
        return EndpointQueueDiagnostics()
    try:
        endpoint = client.get_endpoint(endpoint_id, include_workers=True)
    except (QuadraError, KeyError):
        return EndpointQueueDiagnostics()
    return inspect_endpoint_queue(endpoint)


def aggregate_gpu_supply_status(statuses: list[str | None]) -> str:
    normalized = [
        status.strip().upper()
        for status in statuses
        if isinstance(status, str) and status.strip()
    ]
    if not normalized:
        return "UNKNOWN"

    for status in ("HIGH", "MEDIUM", "LOW"):
        if status in normalized:
            return status
    if all(
        any(hint in status for hint in ("NONE", "OUT", "UNAVAILABLE", "ZERO"))
        for status in normalized
    ):
        return "UNAVAILABLE"
    return normalized[0]


def unknown_gpu_pool_supply(config: ProjectConfig) -> tuple[GpuPoolSupply, ...]:
    return tuple(
        GpuPoolSupply(pool_id=pool_id, status="UNKNOWN")
        for pool_id, _gpu_type_ids in normalize_gpu_type_groups(
            config.runtime.runpod.gpu_ids
        )
    )


def get_gpu_pool_supply(
    client: Any,
    config: ProjectConfig,
    *,
    data_center_id: str | None,
) -> tuple[GpuPoolSupply, ...]:
    groups = normalize_gpu_type_groups(config.runtime.runpod.gpu_ids)
    unknown = unknown_gpu_pool_supply(config)
    if not hasattr(client, "get_gpu_supply"):
        return unknown

    gpu_type_ids = tuple(
        gpu_type_id
        for _pool_id, group_gpu_type_ids in groups
        for gpu_type_id in group_gpu_type_ids
    )
    try:
        supply = client.get_gpu_supply(
            gpu_type_ids,
            data_center_id=data_center_id,
            gpu_count=config.runtime.runpod.gpu_count,
            allowed_cuda_versions=config.runtime.runpod.allowed_cuda_versions,
        )
    except (QuadraError, KeyError, TypeError) as exc:
        logger.debug("RunPod GPU supply lookup failed: %s", exc)
        return unknown
    if not isinstance(supply, dict):
        return unknown

    return tuple(
        GpuPoolSupply(
            pool_id=pool_id,
            status=aggregate_gpu_supply_status(
                [supply.get(gpu_type_id) for gpu_type_id in group_gpu_type_ids]
            ),
        )
        for pool_id, group_gpu_type_ids in groups
    )


def format_gpu_supply_chip(pool: GpuPoolSupply) -> str:
    color_by_status = {
        "HIGH": "green",
        "MEDIUM": "yellow",
        "LOW": "red",
        "UNAVAILABLE": "red",
        "UNKNOWN": "bright_black",
    }
    color = color_by_status.get(pool.status, "bright_black")
    return click.style(
        f"● {pool.pool_id} {pool.status}",
        fg=color,
        bold=pool.status in {"LOW", "UNAVAILABLE"},
    )


def report_gpu_supply_dashboard(
    supply: tuple[GpuPoolSupply, ...],
    *,
    data_center_id: str | None,
) -> None:
    location = data_center_id or "all regions"
    chips = "  ".join(format_gpu_supply_chip(pool) for pool in supply)
    click.echo(f"[quadra] GPU supply · {location}  {chips}")


def load_last_run(config: ProjectConfig) -> RunReference:
    if not config.last_run_file.exists():
        raise QuadraError(
            "No recent run is recorded locally. Run `quadra submit` first."
        )
    try:
        data = json.loads(config.last_run_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QuadraError(f"Failed to read {config.last_run_file}: {exc}") from exc
    return RunReference(
        run_id=str(data["run_id"]),
        job_id=str(data["job_id"]),
        endpoint_id=str(data["endpoint_id"]),
        workflow=str(data["workflow"]),
        submitted_at=str(data["submitted_at"]),
    )


def submit_workflow(
    config: ProjectConfig,
    command_parts: tuple[str, ...],
    *,
    setup_command: str | None,
) -> tuple[RunReference, EndpointHandle]:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client, offer_create=True)
    ensure_project_synced(config, volume)
    endpoint = resolve_endpoint(config, client, volume)
    command, workflow = resolve_run_command(config, command_parts, config.root)
    report_step(f"submitting {workflow} to RunPod endpoint {endpoint.id}...")
    run_id = generate_run_id()
    payload = build_job_payload(
        config,
        run_id=run_id,
        command=command,
        workflow=workflow,
        setup_command=setup_command,
    )
    job = client.run_job(endpoint.id, payload)
    reference = RunReference(
        run_id=run_id,
        job_id=str(job["id"]),
        endpoint_id=endpoint.id,
        workflow=workflow,
        submitted_at=now_utc(),
    )
    save_last_run(config, reference)
    return reference, endpoint


def read_text_object(
    s3: Any, bucket: str, key: str, *, label: str | None = None
) -> str:
    tag = f"[{label}] " if label else ""
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except Exception as exc:
        logger.warning(
            "%sget_object failed for s3://%s/%s: %s: %s",
            tag,
            bucket,
            key,
            type(exc).__name__,
            exc,
        )
        return ""
    try:
        body = response["Body"].read()
    except Exception as exc:
        logger.warning(
            "%sbody read failed for s3://%s/%s: %s: %s",
            tag,
            bucket,
            key,
            type(exc).__name__,
            exc,
        )
        return ""
    if not body:
        logger.debug("%sempty body for s3://%s/%s", tag, bucket, key)
    return body.decode("utf-8", errors="replace")


def download_prefix(s3: Any, bucket: str, prefix: str, destination_root: Path) -> int:
    keys = sorted(list_remote_keys(s3, bucket, prefix))
    if not keys:
        raise QuadraError(f"No files were found under remote prefix {prefix}.")

    downloaded = 0
    for key in keys:
        relative = key[len(prefix) :].lstrip("/")
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(bucket, key, str(destination))
        downloaded += 1
    return downloaded


def parse_run_manifest(text: str) -> tuple[str, ...] | None:
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    files_value = payload.get("files")
    if not isinstance(files_value, list):
        return None

    files: list[str] = []
    seen: set[str] = set()
    for item in files_value:
        if not isinstance(item, str):
            continue
        candidate = item.strip()
        if not candidate:
            continue
        path = PurePosixPath(candidate)
        if path.is_absolute() or ".." in path.parts:
            continue
        normalized = path.as_posix()
        if normalized == RUN_MANIFEST_FILENAME or normalized in seen:
            continue
        seen.add(normalized)
        files.append(normalized)
    return tuple(files)


def download_run_files_from_manifest(
    s3: Any,
    bucket: str,
    run_prefix: str,
    destination_root: Path,
    *,
    manifest_text: str,
) -> int:
    files = parse_run_manifest(manifest_text)
    if files is None:
        raise QuadraError(
            "Remote run manifest is invalid. Re-run the workflow with the current Quadra worker."
        )

    destination_root.mkdir(parents=True, exist_ok=True)
    (destination_root / RUN_MANIFEST_FILENAME).write_text(
        manifest_text,
        encoding="utf-8",
    )

    downloaded = 1
    for relative in files:
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(bucket, posixpath.join(run_prefix, relative), str(destination))
        downloaded += 1
    return downloaded


def download_core_run_files(
    s3: Any,
    bucket: str,
    run_prefix: str,
    destination_root: Path,
) -> int:
    downloaded = 0
    for filename in ("stdout.log", "stderr.log", "status.json"):
        destination = destination_root / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            s3.download_file(bucket, posixpath.join(run_prefix, filename), str(destination))
        except Exception:
            continue
        downloaded += 1
    return downloaded


def stream_logs(
    config: ProjectConfig,
    reference: RunReference,
    *,
    follow: bool,
    interactive: bool | None = None,
    live_dashboard: bool = True,
) -> str:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client)
    report_step(
        f"connecting to RunPod S3 volume {volume.id} "
        f"({volume.data_center_id or 'unknown-dc'})..."
    )
    s3 = build_s3_client(config, volume)
    renderer = create_run_renderer(
        reference,
        follow=follow,
        interactive=interactive if live_dashboard else False,
    )

    with renderer:
        return _stream_logs(
            config,
            reference,
            follow=follow,
            client=client,
            volume=volume,
            s3=s3,
            renderer=renderer,
        )


def _stream_logs(
    config: ProjectConfig,
    reference: RunReference,
    *,
    follow: bool,
    client: Any,
    volume: VolumeHandle,
    s3: Any,
    renderer: PlainRunRenderer | LiveRunRenderer,
) -> str:

    bootstrap_key = remote_state_file_key(config, WORKER_BOOTSTRAP_LOG_FILENAME)
    status_key = remote_run_file_key(config, reference.run_id, "status.json")
    last_bootstrap = ""
    announced_bootstrap = False
    announced_stream = False
    has_remote_output = False
    last_stream_index = -1
    last_reported_status: str | None = None
    last_progress_at = 0.0
    submitted_at = parse_utc_timestamp(reference.submitted_at)
    queue_timeout_seconds = runpod_queue_timeout_seconds()
    all_exited_threshold_seconds = runpod_all_exited_threshold_seconds()
    all_exited_since: float | None = None
    gpu_supply = unknown_gpu_pool_supply(config)
    last_gpu_supply_refresh_at: float | None = None

    while True:
        saw_output_this_iteration = False

        bootstrap_text = read_text_object(s3, volume.id, bootstrap_key, label="bootstrap")
        if bootstrap_text.startswith(last_bootstrap):
            chunk = bootstrap_text[len(last_bootstrap) :]
        else:
            chunk = bootstrap_text
        if chunk:
            if not announced_bootstrap:
                renderer.announce_stream("worker bootstrap log")
                announced_bootstrap = True
            renderer.write(chunk)
            has_remote_output = True
            saw_output_this_iteration = True
        last_bootstrap = bootstrap_text

        stream_chunks = client.stream_job(reference.endpoint_id, reference.job_id)
        if isinstance(stream_chunks, list):
            for chunk_item in stream_chunks:
                if not isinstance(chunk_item, dict):
                    continue
                metrics = chunk_item.get("metrics")
                if isinstance(metrics, dict):
                    idx = metrics.get("stream_index")
                    if isinstance(idx, int):
                        if idx <= last_stream_index:
                            continue
                        last_stream_index = idx
                output = chunk_item.get("output")
                if isinstance(output, dict):
                    stream_name = str(output.get("stream", "stdout"))
                    text = str(output.get("text", ""))
                    if text:
                        if not announced_stream:
                            renderer.announce_stream("worker output")
                            announced_stream = True
                        renderer.write(text, err=(stream_name == "stderr"))
                        has_remote_output = True
                        saw_output_this_iteration = True

        job = client.get_job(reference.endpoint_id, reference.job_id)
        if job is not None:
            status = str(job["status"])
        else:
            status_text = read_text_object(s3, volume.id, status_key, label="status")
            if status_text:
                try:
                    status_payload = json.loads(status_text)
                    status = str(status_payload.get("status", "COMPLETED")).upper()
                except json.JSONDecodeError:
                    status = "COMPLETED"
            else:
                status = "COMPLETED"

        elapsed_seconds = 0
        if submitted_at is not None:
            elapsed_seconds = max(
                0,
                int((datetime.now(timezone.utc) - submitted_at).total_seconds()),
            )

        now_monotonic = time.monotonic()
        queue_diagnostics = EndpointQueueDiagnostics()
        if status == "IN_QUEUE":
            queue_diagnostics = get_endpoint_queue_diagnostics(
                client,
                reference.endpoint_id,
            )
            if (
                last_gpu_supply_refresh_at is None
                or now_monotonic - last_gpu_supply_refresh_at
                >= GPU_SUPPLY_REFRESH_INTERVAL_SECONDS
            ):
                gpu_supply = get_gpu_pool_supply(
                    client,
                    config,
                    data_center_id=volume.data_center_id,
                )
                last_gpu_supply_refresh_at = now_monotonic

        should_report = False
        if status != last_reported_status:
            should_report = True
        elif (
            follow
            and now_monotonic - last_progress_at >= POLL_PROGRESS_INTERVAL_SECONDS
            and not saw_output_this_iteration
        ):
            should_report = True
        elif (
            not follow
            and not saw_output_this_iteration
            and last_reported_status is None
        ):
            should_report = True

        if renderer.interactive or should_report:
            renderer.update(
                reference,
                status,
                has_remote_output=has_remote_output,
                elapsed_seconds=elapsed_seconds,
                queue_diagnostics=queue_diagnostics,
                gpu_supply=gpu_supply,
                data_center_id=volume.data_center_id,
            )
        if should_report:
            last_reported_status = status
            last_progress_at = now_monotonic

        if status == "IN_QUEUE" and queue_diagnostics.exited_workers:
            if all_exited_since is None:
                all_exited_since = now_monotonic
        else:
            all_exited_since = None

        if status == "IN_QUEUE" and queue_diagnostics.blocking_workers:
            worker_details = "; ".join(queue_diagnostics.blocking_workers[:3])
            raise QuadraError(
                f"RunPod endpoint {reference.endpoint_id} has no viable workers while "
                f"job {reference.job_id} is still queued: {worker_details}. "
                "Check the template image and worker startup command."
            )

        if (
            status == "IN_QUEUE"
            and queue_diagnostics.exited_workers
            and all_exited_since is not None
            and now_monotonic - all_exited_since >= all_exited_threshold_seconds
        ):
            worker_details = "; ".join(queue_diagnostics.exited_workers[:3])
            bootstrap_tail = format_bootstrap_log_tail(last_bootstrap)
            message = (
                f"RunPod endpoint {reference.endpoint_id} has no viable workers while "
                f"job {reference.job_id} is still queued: worker(s) {worker_details} "
                f"exited and no replacement worker started within "
                f"{format_duration(all_exited_threshold_seconds)}. "
                "The worker bootstrap is failing repeatedly."
            )
            if bootstrap_tail:
                message += (
                    "\n\nLast worker bootstrap log lines:\n"
                    f"{bootstrap_tail}\n\n"
                    "Check the template image, worker startup command, and worker script "
                    "for errors."
                )
            else:
                message += (
                    " No worker bootstrap log was produced. Check the template image "
                    "and worker startup command."
                )
            raise QuadraError(message)

        if (
            status == "IN_QUEUE"
            and submitted_at is not None
            and elapsed_seconds >= queue_timeout_seconds
        ):
            detail = queue_diagnostics.progress_summary or "workers: status unavailable"
            raise QuadraError(
                f"RunPod job {reference.job_id} has been queued for "
                f"{format_duration(elapsed_seconds)} with no remote logs. "
                f"Endpoint {reference.endpoint_id} {detail}. "
                "Check worker health in RunPod, or set "
                "QUADRA_RUNPOD_QUEUE_TIMEOUT_SECONDS if this queue wait is expected."
            )

        if not follow or status in FINAL_JOB_STATES:
            return status
        time.sleep(1)


def pull_run(
    config: ProjectConfig,
    *,
    run_id: str,
    destination_root: Path | None = None,
) -> Path:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client)
    report_step(
        f"connecting to RunPod S3 volume {volume.id} "
        f"({volume.data_center_id or 'unknown-dc'})..."
    )
    s3 = build_s3_client(config, volume)

    destination = destination_root or (config.runs_dir / run_id)
    destination.mkdir(parents=True, exist_ok=True)
    prefix = remote_run_key_prefix(config, run_id)
    report_step(f"downloading remote files for {run_id}...")
    manifest_key = remote_run_manifest_key(config, run_id)
    manifest_text = read_text_object(s3, volume.id, manifest_key)
    if manifest_text:
        download_run_files_from_manifest(
            s3,
            volume.id,
            prefix,
            destination,
            manifest_text=manifest_text,
        )
        download_core_run_files(s3, volume.id, prefix, destination)
        return destination

    downloaded = download_core_run_files(s3, volume.id, prefix, destination)
    if downloaded:
        report_step(
            "remote run manifest is missing; downloaded core run logs only. "
            "Re-run with the current Quadra worker to pull artifact directories."
        )
        return destination

    raise QuadraError(
        f"No files were found for remote run {run_id}. "
        "If this run predates manifest-based pulls, re-run it with the current Quadra worker."
    )
    return destination


def run_command(
    config: ProjectConfig,
    command_parts: tuple[str, ...],
    *,
    setup_command: str | None,
    interactive: bool | None = None,
) -> int:
    click.echo(f"syncing {config.name} -> {config.runtime.project_dir}")
    volume, uploaded, deleted = sync_project(config)
    click.echo(
        f"volume: {volume.id} ({volume.data_center_id or 'unknown-dc'}), "
        f"uploaded: {uploaded}, deleted: {deleted}"
    )
    _command, workflow = resolve_run_command(config, command_parts, config.root)
    click.echo(f"submitting {workflow}")
    reference, endpoint = submit_workflow(
        config,
        command_parts,
        setup_command=setup_command,
    )
    click.echo(f"run_id: {reference.run_id}")
    click.echo(f"job_id: {reference.job_id}")
    click.echo(f"endpoint_id: {endpoint.id}")
    click.echo("polling RunPod job status and streaming remote worker logs...")
    status = stream_logs(
        config,
        reference,
        follow=True,
        interactive=interactive,
    )
    click.echo(f"pulling artifacts for {reference.run_id}")
    pull_run(config, run_id=reference.run_id)
    return 0 if status == "COMPLETED" else 1


def run_named_workflow(
    config: ProjectConfig,
    workflow: str,
    *,
    interactive: bool | None = None,
) -> int:
    return run_command(
        config,
        (workflow,),
        setup_command=config.runtime.setup_command,
        interactive=interactive,
    )


def resolve_cli_setup_command(
    config: ProjectConfig,
    *,
    setup_command: str | None,
    no_setup: bool,
) -> str | None:
    if setup_command is not None and no_setup:
        raise QuadraError("--setup-command and --no-setup cannot be used together.")
    if no_setup:
        return None
    if setup_command is not None:
        return setup_command
    return config.runtime.setup_command


@click.group(cls=BannerGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="quadra")
def cli() -> None:
    """Quadra runs experiments on RunPod Serverless."""
    configure_library_logging()


@cli.command()
@click.argument("project_name", required=False)
def init(project_name: str | None) -> None:
    """Create a serverless Quadra project scaffold."""
    current_dir = Path.cwd()
    resolved_project_name = project_name or current_dir.name
    if not resolved_project_name:
        raise click.ClickException(
            "Could not infer a project name from the current directory. Pass one explicitly."
        )

    target_root = current_dir if project_name is None else current_dir / project_name
    try:
        init_project(target_root, resolved_project_name)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"initialized {resolved_project_name}")
    click.echo(target_root)


@cli.command()
@click.option(
    "--path",
    "config_path",
    type=click.Path(path_type=Path, dir_okay=False, writable=True),
    help="Global config path. Defaults to QUADRA_CONFIG or ~/.config/quadra/config.toml.",
)
@click.option("--force", is_flag=True, help="Overwrite an existing global config.")
@click.option("--api-key-env", default="RUNPOD_API_KEY", show_default=True)
@click.option("--data-center", default="US-IL-1", show_default=True)
@click.option("--volume-name", default="quadra-dev", show_default=True)
@click.option(
    "--volume-size-gb",
    default=DEFAULT_NETWORK_VOLUME_SIZE_GB,
    show_default=True,
    type=click.IntRange(min=1),
)
@click.option(
    "--volume-mount-path",
    default=DEFAULT_TEMPLATE_VOLUME_MOUNT_PATH,
    show_default=True,
)
@click.option("--endpoint-name", default="quadra-dev", show_default=True)
@click.option("--gpu-ids", default="AMPERE_16", show_default=True)
@click.option("--gpu-count", default=1, show_default=True, type=click.IntRange(min=1))
@click.option("--workers-min", default=0, show_default=True, type=click.IntRange(min=0))
@click.option("--workers-max", default=1, show_default=True, type=click.IntRange(min=1))
@click.option("--idle-timeout", default=5, show_default=True, type=click.IntRange(min=0))
@click.option("--scaler-type", default="QUEUE_DELAY", show_default=True)
@click.option("--scaler-value", default=4, show_default=True, type=click.IntRange(min=0))
@click.option("--flashboot/--no-flashboot", default=False, show_default=True)
@click.option(
    "--timeout-seconds",
    default=600,
    show_default=True,
    type=click.IntRange(min=1),
)
@click.option(
    "--template-name",
    default=None,
    help="RunPod template name. Defaults to '<endpoint-name>-serverless-worker'.",
)
@click.option("--image-name", default=DEFAULT_TEMPLATE_IMAGE, show_default=True)
@click.option(
    "--container-disk-gb",
    default=20,
    show_default=True,
    type=click.IntRange(min=1),
)
def configure(
    config_path: Path | None,
    force: bool,
    api_key_env: str,
    data_center: str,
    volume_name: str,
    volume_size_gb: int,
    volume_mount_path: str,
    endpoint_name: str,
    gpu_ids: str,
    gpu_count: int,
    workers_min: int,
    workers_max: int,
    idle_timeout: int,
    scaler_type: str,
    scaler_value: int,
    flashboot: bool,
    timeout_seconds: int,
    template_name: str | None,
    image_name: str,
    container_disk_gb: int,
) -> None:
    """Create Quadra's machine-level RunPod backend config."""
    try:
        path = write_global_config(
            config_path or global_config_path(),
            force=force,
            api_key_env=api_key_env,
            data_center_id=data_center,
            volume_name=volume_name,
            volume_size_gb=volume_size_gb,
            volume_mount_path=volume_mount_path,
            endpoint_name=endpoint_name,
            gpu_ids=gpu_ids,
            gpu_count=gpu_count,
            workers_min=workers_min,
            workers_max=workers_max,
            idle_timeout=idle_timeout,
            scaler_type=scaler_type,
            scaler_value=scaler_value,
            flashboot=flashboot,
            timeout_seconds=timeout_seconds,
            template_name=template_name,
            image_name=image_name,
            container_disk_gb=container_disk_gb,
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"wrote global config: {path}")


@cli.command()
def sync() -> None:
    """Sync the project into the RunPod network volume over S3."""
    try:
        config = load_project()
        volume, uploaded, deleted = sync_project(config)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"synced {config.name} -> {config.runtime.project_dir}")
    click.echo(
        f"volume: {volume.id} ({volume.data_center_id or 'unknown-dc'}), "
        f"uploaded: {uploaded}, deleted: {deleted}"
    )


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("command_parts", nargs=-1, required=True, type=click.UNPROCESSED)
@click.option(
    "--setup-command",
    help=(
        "Override the configured setup command for this run. "
        "Place before the workload command."
    ),
)
@click.option(
    "--no-setup",
    is_flag=True,
    help="Disable the configured setup command for this run.",
)
def submit(
    command_parts: tuple[str, ...],
    setup_command: str | None,
    no_setup: bool,
) -> None:
    """Submit a workflow to the configured RunPod Serverless endpoint."""
    try:
        config = load_runnable_project()
        effective_setup_command = resolve_cli_setup_command(
            config,
            setup_command=setup_command,
            no_setup=no_setup,
        )
        reference, endpoint = submit_workflow(
            config,
            command_parts,
            setup_command=effective_setup_command,
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"submitted {reference.workflow}")
    click.echo(f"run_id: {reference.run_id}")
    click.echo(f"job_id: {reference.job_id}")
    click.echo(f"endpoint_id: {endpoint.id}")
    click.echo("")
    click.echo("next:")
    click.echo("quadra logs")
    click.echo("quadra pull")


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("command_parts", nargs=-1, required=True, type=click.UNPROCESSED)
@click.option(
    "--fork",
    "fork_urls",
    multiple=True,
    help=(
        "Clone a fork URL into src/libs and wire it as a local editable dependency "
        "before running. Repeatable. Place before the command."
    ),
)
@click.option(
    "--fork-package",
    "fork_packages",
    multiple=True,
    help=(
        "Package name for the corresponding --fork when it differs from the repo name. "
        "Repeatable; paired with --fork by position."
    ),
)
@click.option(
    "--setup-command",
    help=(
        "Override the configured setup command for this run. "
        "Place before the workload command."
    ),
)
@click.option(
    "--no-setup",
    is_flag=True,
    help="Disable the configured setup command for this run.",
)
@click.option("--plain", is_flag=True, help="Disable the live terminal dashboard.")
def run(
    command_parts: tuple[str, ...],
    fork_urls: tuple[str, ...],
    fork_packages: tuple[str, ...],
    setup_command: str | None,
    no_setup: bool,
    plain: bool,
) -> None:
    """Sync, run a command remotely, stream logs, and pull artifacts."""
    try:
        config = load_runnable_project()
        effective_setup_command = resolve_cli_setup_command(
            config,
            setup_command=setup_command,
            no_setup=no_setup,
        )
        if len(fork_packages) > len(fork_urls):
            raise QuadraError(
                "More --fork-package values than --fork URLs were provided."
            )
        fork_specs: list[tuple[str, str | None]] = [
            (fork_url, fork_packages[index] if index < len(fork_packages) else None)
            for index, fork_url in enumerate(fork_urls)
        ]
        apply_fork_specs(config, fork_specs)
        code = run_command(
            config,
            command_parts,
            setup_command=effective_setup_command,
            interactive=False if plain else None,
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


@cli.command()
@click.argument("fork_url")
@click.option(
    "--package",
    "package_name",
    help="Python package name to depend on when it differs from the fork repo name.",
)
def fork(fork_url: str, package_name: str | None) -> None:
    """Clone a fork into src/libs and use it from the experiment project."""
    try:
        config = load_project()
        destination, pyproject_path, resolved_package_name, wired, skip_clone = (
            clone_fork_into_project(
                config,
                fork_url=fork_url,
                package_name=package_name,
            )
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if skip_clone:
        click.echo(
            f"warning: library destination already exists, skipping clone: "
            f"{destination}"
        )
    else:
        click.echo(f"cloned {fork_url}")
    click.echo(f"library: {destination}")
    click.echo(f"package: {resolved_package_name}")
    if wired:
        click.echo(f"updated: {pyproject_path}")
    else:
        click.echo(
            "note: experiment pyproject has no [project] table; fork cloned "
            "but not wired as a uv dependency. Wire it via your command or "
            "setup_command (e.g. PYTHONPATH)."
        )


@cli.command()
@click.option(
    "--follow/--no-follow",
    default=False,
    help="Poll until the job completes instead of fetching the current logs once.",
)
@click.option("--plain", is_flag=True, help="Disable the live terminal dashboard.")
def logs(follow: bool, plain: bool) -> None:
    """Fetch logs for the most recently submitted run."""
    try:
        config = load_runnable_project()
        reference = load_last_run(config)
        status = stream_logs(
            config,
            reference,
            follow=follow,
            interactive=False if plain else None,
            live_dashboard=False,
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"\nstatus: {status}")
    if status != "COMPLETED":
        raise click.exceptions.Exit(1)


@cli.command()
@click.argument("run_id", required=False)
@click.argument("destination", required=False)
def pull(run_id: str | None, destination: str | None) -> None:
    """Download a completed run directory from the RunPod volume."""
    try:
        config = load_runnable_project()
        resolved_run_id = run_id or load_last_run(config).run_id
        destination_root = Path(destination).resolve() if destination else None
        pulled_to = pull_run(
            config, run_id=resolved_run_id, destination_root=destination_root
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"pulled {resolved_run_id}")
    click.echo(pulled_to)


@cli.command()
@click.option("--plain", is_flag=True, help="Disable the live terminal dashboard.")
def smoke(plain: bool) -> None:
    """Sync, submit, stream logs, and pull artifacts for the smoke workflow."""
    try:
        config = load_runnable_project()
        code = run_named_workflow(
            config,
            "smoke",
            interactive=False if plain else None,
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


if __name__ == "__main__":
    cli()
