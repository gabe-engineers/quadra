from __future__ import annotations

import importlib.resources
import json
import os
import posixpath
import shutil
import sys
import textwrap
import time
import tomllib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import click

from quadra import __version__
from quadra.errors import QuadraError
from quadra.runpod_rest import RunpodRestClient

CONFIG_FILENAME = "quadra.toml"
STATE_DIRNAME = ".quadra"
LAST_RUN_FILENAME = "last-run.json"
CONFIG_SCHEMA_VERSION = 3
RUNPOD_VOLUME_ROOT = PurePosixPath("/runpod-volume")
DEFAULT_PROJECT_DIR = "/runpod-volume/projects/{project_name}"
FINAL_JOB_STATES = {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
POLL_PROGRESS_INTERVAL_SECONDS = 10
QUADRA_WORKER_FILENAME = "quadra_worker.py"
DEFAULT_TEMPLATE_IMAGE = "runpod/base:0.6.1-cuda12.4.1"
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
    workers_max: int = 3
    idle_timeout: int = 5
    scaler_type: str = "QUEUE_DELAY"
    scaler_value: int = 4
    flashboot: bool = False
    locations: str | None = None
    network_volume_id: str | None = None
    network_volume_name: str | None = None
    allowed_cuda_versions: tuple[str, ...] = ()
    timeout_seconds: int = 600
    s3_access_key_env: str | None = "AWS_ACCESS_KEY_ID"
    s3_secret_key_env: str | None = "AWS_SECRET_ACCESS_KEY"
    template: RunpodTemplateConfig = field(
        default_factory=lambda: RunpodTemplateConfig(
            id=None,
            name="quadra-worker",
            image_name=DEFAULT_TEMPLATE_IMAGE,
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


@dataclass(frozen=True)
class EndpointHandle:
    id: str
    name: str


@dataclass(frozen=True)
class TemplateHandle:
    id: str
    name: str


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    image_name: str
    ports: tuple[str, ...]
    docker_entrypoint: tuple[str, ...]
    docker_start_cmd: tuple[str, ...]
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


class BannerGroup(click.Group):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            if print_banner():
                click.echo()
        return super().parse_args(ctx, args)


class RunpodClient:
    def __init__(self, runpod_module: Any, api_key: str):
        self.runpod = runpod_module
        self.runpod.api_key = api_key
        self.api_key = api_key
        self.rest_client = RunpodRestClient(api_key)

    def get_network_volumes(self) -> list[dict[str, Any]]:
        return self.rest_client.get_network_volumes()

    def get_endpoints(self) -> list[dict[str, Any]]:
        return self.rest_client.get_endpoints()

    def get_templates(self) -> list[dict[str, Any]]:
        return self.rest_client.get_templates()

    def create_template(
        self,
        *,
        name: str,
        image_name: str,
        ports: tuple[str, ...],
        docker_entrypoint: tuple[str, ...],
        docker_start_cmd: tuple[str, ...],
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
        endpoint = self.runpod.Endpoint(endpoint_id, api_key=self.api_key)
        job = endpoint.run(request_input)
        return {"id": job.job_id}

    def get_job(
        self, endpoint_id: str, job_id: str, *, source: str = "status"
    ) -> dict[str, Any]:
        from runpod.endpoint.runner import Job

        endpoint = self.runpod.Endpoint(endpoint_id, api_key=self.api_key)
        return Job(endpoint_id, job_id, endpoint.rp_client)._fetch_job(source=source)


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


def load_project(start: Path | None = None) -> ProjectConfig:
    root = find_project_root(start)
    config_path = root / CONFIG_FILENAME
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise QuadraError(f"Failed to read {config_path}: {exc}") from exc

    try:
        project = data["project"]
        paths = data["paths"]
        runtime = data["runtime"]
    except KeyError as exc:
        raise QuadraError(f"Missing required config section: {exc.args[0]}") from exc

    runpod_data = runtime.get("runpod")
    if not isinstance(runpod_data, dict):
        raise QuadraError("Missing required config section: runtime.runpod")

    project_name = str(project["name"])
    project_dir = str(runtime["project_dir"])
    template_data = runpod_data.get("template")
    if template_data is None:
        template_data = {}
    if not isinstance(template_data, dict):
        raise QuadraError("runtime.runpod.template must be a table.")

    template_config = RunpodTemplateConfig(
        id=optional_str(template_data.get("id"))
        or optional_str(runpod_data.get("template_id")),
        name=optional_str(template_data.get("name")) or f"quadra-{project_name}-worker",
        image_name=str(template_data.get("image_name", DEFAULT_TEMPLATE_IMAGE)).strip(),
        ports=normalize_str_sequence(
            template_data.get("ports"), "runtime.runpod.template.ports"
        ),
        docker_entrypoint=normalize_str_sequence(
            template_data.get("docker_entrypoint"),
            "runtime.runpod.template.docker_entrypoint",
        ),
        docker_start_cmd=normalize_str_sequence(
            template_data.get("docker_start_cmd") or ["python", "-u", "{worker_path}"],
            "runtime.runpod.template.docker_start_cmd",
        ),
        env=normalize_string_map(
            template_data.get("env"), "runtime.runpod.template.env"
        ),
        container_disk_gb=int(template_data.get("container_disk_gb", 20)),
        readme=str(
            template_data.get(
                "readme",
                "Managed by Quadra. Runs {worker_path} from the synced project volume.",
            )
        ),
    )

    runpod_config = RunpodConfig(
        api_key_env=str(runpod_data.get("api_key_env", "RUNPOD_API_KEY")),
        endpoint_id=optional_str(runpod_data.get("endpoint_id")),
        endpoint_name=optional_str(runpod_data.get("endpoint_name")),
        gpu_ids=str(runpod_data.get("gpu_ids", "AMPERE_16")).strip(),
        gpu_count=int(runpod_data.get("gpu_count", 1)),
        workers_min=int(runpod_data.get("workers_min", 0)),
        workers_max=int(runpod_data.get("workers_max", 3)),
        idle_timeout=int(runpod_data.get("idle_timeout", 5)),
        scaler_type=str(runpod_data.get("scaler_type", "QUEUE_DELAY")).strip(),
        scaler_value=int(runpod_data.get("scaler_value", 4)),
        flashboot=bool(runpod_data.get("flashboot", False)),
        locations=optional_str(runpod_data.get("locations")),
        network_volume_id=optional_str(runpod_data.get("network_volume_id")),
        network_volume_name=optional_str(runpod_data.get("network_volume_name")),
        allowed_cuda_versions=normalize_allowed_cuda_versions(
            runpod_data.get("allowed_cuda_versions")
        ),
        timeout_seconds=int(runpod_data.get("timeout_seconds", 600)),
        s3_access_key_env=optional_str(
            runpod_data.get("s3_access_key_env", "AWS_ACCESS_KEY_ID")
        ),
        s3_secret_key_env=optional_str(
            runpod_data.get("s3_secret_key_env", "AWS_SECRET_ACCESS_KEY")
        ),
        template=template_config,
    )

    return ProjectConfig(
        schema_version=int(data.get("schema_version", CONFIG_SCHEMA_VERSION)),
        name=str(project["name"]),
        root=root,
        paths=ProjectPaths(
            libs=str(paths["libs"]),
            experiment=str(paths["experiment"]),
            models=str(paths["models"]),
            caches=str(paths["caches"]),
            runs=str(paths["runs"]),
        ),
        runtime=RuntimeConfig(
            project_dir=project_dir,
            setup_command=optional_str(runtime.get("setup_command", "uv sync")),
            runpod=runpod_config,
        ),
        commands={
            str(key): str(value) for key, value in data.get("commands", {}).items()
        },
    )


def init_project(
    target_root: Path, project_name: str, *, allow_existing: bool = False
) -> None:
    scaffold_dirs = [
        target_root / "src" / "libs" / "diffusers",
        target_root / "src" / "libs" / "transformers",
        target_root / "src" / "libs" / "vllm-omni",
        target_root / "src" / "experiment" / "scripts",
        target_root / "models",
        target_root / "caches",
        target_root / "runs",
        target_root / STATE_DIRNAME,
    ]
    scaffold_files = [
        target_root / CONFIG_FILENAME,
        target_root / QUADRA_WORKER_FILENAME,
        target_root / "src" / "experiment" / "pyproject.toml",
        target_root / "src" / "experiment" / "main.py",
        target_root / "src" / "experiment" / "scripts" / "smoke.py",
        target_root / "src" / "experiment" / "scripts" / "bench.py",
    ]

    if target_root.exists():
        if any(target_root.iterdir()) and not allow_existing:
            raise QuadraError(
                f"Target directory already exists and is not empty: {target_root}"
            )
        for path in [*scaffold_dirs, *scaffold_files]:
            if path.exists():
                raise QuadraError(f"Refusing to overwrite existing path: {path}")
    else:
        target_root.mkdir(parents=True, exist_ok=False)

    for directory in scaffold_dirs:
        directory.mkdir(parents=True, exist_ok=True)

    for keep_dir in scaffold_dirs:
        if keep_dir.name != STATE_DIRNAME:
            (keep_dir / ".gitkeep").write_text("", encoding="utf-8")

    scaffold_files[0].write_text(render_quadra_config(project_name), encoding="utf-8")
    scaffold_files[1].write_text(render_project_worker_py(), encoding="utf-8")
    scaffold_files[2].write_text(
        render_experiment_pyproject(project_name),
        encoding="utf-8",
    )
    scaffold_files[3].write_text(render_main_py(project_name), encoding="utf-8")
    scaffold_files[4].write_text(render_smoke_py(project_name), encoding="utf-8")
    scaffold_files[5].write_text(render_bench_py(project_name), encoding="utf-8")


def render_quadra_config(project_name: str) -> str:
    project_dir = DEFAULT_PROJECT_DIR.format(project_name=project_name)
    gpu_pool_comments = "\n        ".join(SERVERLESS_GPU_POOL_COMMENT_LINES)
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
        setup_command = "uv sync"

        [runtime.runpod]
        api_key_env = "RUNPOD_API_KEY"
        endpoint_name = "quadra-{project_name}"
        {gpu_pool_comments}
        gpu_ids = "AMPERE_16"
        gpu_count = 1
        workers_min = 0
        workers_max = 3
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
        name = "quadra-{project_name}-worker"
        image_name = "{DEFAULT_TEMPLATE_IMAGE}"
        # Template string tokens: {{project_name}}, {{project_dir}}, {{worker_path}}
        docker_start_cmd = ["python", "-u", "{{worker_path}}"]
        container_disk_gb = 20
        env = {{}}
        readme = "Managed by Quadra. Runs {{worker_path}} from the synced project volume."

        [commands]
        smoke = "python scripts/smoke.py"
        bench = "python scripts/bench.py"
        main = "python main.py"
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
    return textwrap.dedent(
        """\
        from __future__ import annotations

        import json
        import os
        import subprocess
        import time
        from pathlib import Path
        from typing import Any

        import runpod


        def _now() -> str:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


        def _write_status(path: Path, payload: dict[str, Any]) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\\n",
                encoding="utf-8",
            )


        def _run_shell(
            command: str,
            *,
            cwd: Path,
            env: dict[str, str],
            stdout_path: Path,
            stderr_path: Path,
        ) -> subprocess.CompletedProcess[str]:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stderr_path.parent.mkdir(parents=True, exist_ok=True)
            with stdout_path.open("a", encoding="utf-8") as stdout_handle:
                with stderr_path.open("a", encoding="utf-8") as stderr_handle:
                    return subprocess.run(
                        ["/bin/sh", "-lc", command],
                        cwd=str(cwd),
                        env=env,
                        stdout=stdout_handle,
                        stderr=stderr_handle,
                        text=True,
                        check=False,
                    )


        def handler(job: dict[str, Any]) -> dict[str, Any]:
            payload = (job or {}).get("input") or {}
            spec = payload.get("quadra") if isinstance(payload.get("quadra"), dict) else payload

            required = [
                "project_name",
                "run_id",
                "project_dir",
                "experiment_dir",
                "run_dir",
                "command",
            ]
            missing = [key for key in required if not spec.get(key)]
            if missing:
                raise ValueError(
                    f"Missing required Quadra payload fields: {', '.join(missing)}"
                )

            project_name = str(spec["project_name"])
            run_id = str(spec["run_id"])
            workflow = str(spec.get("workflow", spec["command"]))
            project_dir = Path(str(spec["project_dir"]))
            experiment_dir = Path(str(spec["experiment_dir"]))
            run_dir = Path(str(spec["run_dir"]))
            artifacts_dir = Path(str(spec.get("artifacts_dir", run_dir / "artifacts")))
            stdout_path = run_dir / "stdout.log"
            stderr_path = run_dir / "stderr.log"
            status_path = run_dir / "status.json"

            run_dir.mkdir(parents=True, exist_ok=True)
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            env = os.environ.copy()
            env.update({str(key): str(value) for key, value in (spec.get("env") or {}).items()})

            status_payload = {
                "project_name": project_name,
                "run_id": run_id,
                "workflow": workflow,
                "project_dir": str(project_dir),
                "experiment_dir": str(experiment_dir),
                "run_dir": str(run_dir),
                "artifacts_dir": str(artifacts_dir),
                "status": "running",
                "started_at": _now(),
                "setup_command": spec.get("setup_command"),
                "command": spec["command"],
            }
            _write_status(status_path, status_payload)

            if not project_dir.exists():
                status_payload.update(
                    {
                        "status": "failed",
                        "step": "prepare",
                        "finished_at": _now(),
                        "error": f"Project directory does not exist: {project_dir}",
                    }
                )
                _write_status(status_path, status_payload)
                raise RuntimeError(status_payload["error"])

            if not experiment_dir.exists():
                status_payload.update(
                    {
                        "status": "failed",
                        "step": "prepare",
                        "finished_at": _now(),
                        "error": f"Experiment directory does not exist: {experiment_dir}",
                    }
                )
                _write_status(status_path, status_payload)
                raise RuntimeError(status_payload["error"])

            setup_command = spec.get("setup_command")
            if setup_command:
                setup_result = _run_shell(
                    str(setup_command),
                    cwd=project_dir,
                    env=env,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                )
                if setup_result.returncode != 0:
                    status_payload.update(
                        {
                            "status": "failed",
                            "step": "setup",
                            "finished_at": _now(),
                            "exit_code": setup_result.returncode,
                            "error": (
                                "Setup command failed with exit code "
                                f"{setup_result.returncode}"
                            ),
                        }
                    )
                    _write_status(status_path, status_payload)
                    raise RuntimeError(status_payload["error"])

            command_result = _run_shell(
                str(spec["command"]),
                cwd=experiment_dir,
                env=env,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
            )
            if command_result.returncode != 0:
                status_payload.update(
                    {
                        "status": "failed",
                        "step": "command",
                        "finished_at": _now(),
                        "exit_code": command_result.returncode,
                        "error": (
                            "Command failed with exit code "
                            f"{command_result.returncode}"
                        ),
                    }
                )
                _write_status(status_path, status_payload)
                raise RuntimeError(status_payload["error"])

            status_payload.update(
                {
                    "status": "completed",
                    "finished_at": _now(),
                    "exit_code": 0,
                }
            )
            _write_status(status_path, status_payload)
            return {
                "run_id": run_id,
                "status": "completed",
                "run_dir": str(run_dir),
                "artifacts_dir": str(artifacts_dir),
            }


        if __name__ == "__main__":
            runpod.serverless.start({"handler": handler})
        """
    )


def render_main_py(project_name: str) -> str:
    return textwrap.dedent(
        f"""\
        def main() -> None:
            print("{project_name} experiment entrypoint")


        if __name__ == "__main__":
            main()
        """
    )


def render_smoke_py(project_name: str) -> str:
    return textwrap.dedent(
        f"""\
        def main() -> None:
            print("{project_name} smoke ok")


        if __name__ == "__main__":
            main()
        """
    )


def render_bench_py(project_name: str) -> str:
    return textwrap.dedent(
        f"""\
        def main() -> None:
            print("{project_name} bench placeholder")


        if __name__ == "__main__":
            main()
        """
    )


def load_runpod_client(config: ProjectConfig) -> Any:
    api_key = os.getenv(config.runtime.runpod.api_key_env)
    if not api_key:
        raise QuadraError(
            f"RunPod API key not configured. Set {config.runtime.runpod.api_key_env}."
        )

    try:
        import runpod
    except ImportError as exc:
        raise QuadraError(
            "This Quadra installation is missing the `runpod` package."
        ) from exc

    return RunpodClient(runpod, api_key)


def runpod_endpoint_name(config: ProjectConfig) -> str:
    return config.runtime.runpod.endpoint_name or f"quadra-{config.name}"


def remote_worker_path(config: ProjectConfig) -> str:
    return str(PurePosixPath(config.runtime.project_dir) / QUADRA_WORKER_FILENAME)


def expand_template_tokens(value: str, config: ProjectConfig) -> str:
    return (
        value.replace("{project_name}", config.name)
        .replace("{project_dir}", config.runtime.project_dir)
        .replace("{worker_path}", remote_worker_path(config))
        .replace("{runpod_volume_root}", str(RUNPOD_VOLUME_ROOT))
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
        env={
            key: expand_template_tokens(value, config)
            for key, value in template.env.items()
        },
        container_disk_gb=template.container_disk_gb,
        readme=expand_template_tokens(template.readme, config),
    )


def resolve_runpod_volume(config: ProjectConfig, client: Any) -> VolumeHandle:
    target_id = config.runtime.runpod.network_volume_id
    target_name = config.runtime.runpod.network_volume_name or config.name
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
    raise QuadraError(
        f"No RunPod network volume named {target_name!r} was found. "
        "Create it in RunPod and retry, or configure runtime.runpod.network_volume_id."
    )


def resolve_template(config: ProjectConfig, client: Any) -> TemplateHandle:
    template_id = config.runtime.runpod.template.id
    template_name = build_template_spec(config).name

    if template_id:
        templates = list(client.get_templates())
        for template in templates:
            if optional_str(template.get("id")) == template_id:
                return TemplateHandle(
                    id=template_id,
                    name=optional_str(template.get("name")) or template_id,
                )
        return TemplateHandle(id=template_id, name=template_name)

    templates = list(client.get_templates())
    matches = [
        template
        for template in templates
        if optional_str(template.get("name")) == template_name
    ]
    if len(matches) == 1:
        template = matches[0]
        return TemplateHandle(
            id=str(template["id"]),
            name=optional_str(template.get("name")) or template_name,
        )
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod templates are named {template_name!r}. "
            "Set runtime.runpod.template.id."
        )

    spec = build_template_spec(config)
    template = client.create_template(
        name=spec.name,
        image_name=spec.image_name,
        ports=spec.ports,
        docker_entrypoint=spec.docker_entrypoint,
        docker_start_cmd=spec.docker_start_cmd,
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
    try:
        relative = project_dir.relative_to(RUNPOD_VOLUME_ROOT)
    except ValueError as exc:
        raise QuadraError(
            "runtime.project_dir must live under /runpod-volume for RunPod Serverless."
        ) from exc
    return relative.as_posix()


def remote_run_key_prefix(config: ProjectConfig, run_id: str) -> str:
    return posixpath.join(
        remote_project_key(config), config.paths.runs.replace("\\", "/"), run_id
    )


def remote_run_file_key(config: ProjectConfig, run_id: str, filename: str) -> str:
    return posixpath.join(remote_run_key_prefix(config, run_id), filename)


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


def sync_project(config: ProjectConfig) -> tuple[VolumeHandle, int, int]:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client)
    s3 = build_s3_client(config, volume)

    prefix = remote_project_key(config)
    local_files = iter_local_files(config.root)
    uploaded = 0

    for relative, file_path in sorted(local_files.items()):
        key = posixpath.join(prefix, relative)
        s3.upload_file(str(file_path), volume.id, key)
        uploaded += 1

    remote_keys = list_remote_keys(s3, volume.id, prefix)
    expected_keys = {posixpath.join(prefix, relative) for relative in local_files}
    stale_keys = sorted(remote_keys - expected_keys)
    if stale_keys:
        delete_payload = {"Objects": [{"Key": key} for key in stale_keys]}
        s3.delete_objects(Bucket=volume.id, Delete=delete_payload)

    return volume, uploaded, len(stale_keys)


def ensure_project_synced(config: ProjectConfig, volume: VolumeHandle) -> None:
    s3 = build_s3_client(config, volume)
    key = posixpath.join(remote_project_key(config), CONFIG_FILENAME)
    try:
        s3.head_object(Bucket=volume.id, Key=key)
    except Exception as exc:
        raise QuadraError(
            "Remote project has not been synced yet. Run `quadra sync` first."
        ) from exc


def resolve_endpoint(
    config: ProjectConfig, client: Any, volume: VolumeHandle
) -> EndpointHandle:
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
        return EndpointHandle(
            id=str(endpoint["id"]),
            name=optional_str(endpoint.get("name")) or endpoint_name,
        )
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod endpoints are named {endpoint_name!r}. "
            "Set runtime.runpod.endpoint_id."
        )

    template = resolve_template(config, client)
    endpoint = client.create_endpoint(
        name=endpoint_name,
        template_id=template.id,
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

    if len(command_parts) == 1:
        command_name = command_parts[0]
        if command_name in config.commands:
            return config.commands[command_name], command_name
        script_path = (
            project_root / config.paths.experiment / "scripts" / f"{command_name}.py"
        )
        if script_path.exists():
            return f"python scripts/{command_name}.py", command_name

    return raw_command, raw_command


def build_job_payload(
    config: ProjectConfig, *, run_id: str, command: str, workflow: str
) -> dict[str, Any]:
    project_dir = PurePosixPath(config.runtime.project_dir)
    experiment_dir = project_dir / config.paths.experiment
    run_dir = project_dir / config.paths.runs / run_id
    return {
        "quadra": {
            "project_name": config.name,
            "workflow": workflow,
            "run_id": run_id,
            "project_dir": str(project_dir),
            "experiment_dir": str(experiment_dir),
            "run_dir": str(run_dir),
            "artifacts_dir": str(run_dir / "artifacts"),
            "setup_command": config.runtime.setup_command,
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
) -> None:
    description = describe_job_status(status, has_remote_output=has_remote_output)
    click.echo(
        f"[quadra] {reference.workflow}: {description} "
        f"(status {status}, elapsed {format_duration(elapsed_seconds)})"
    )


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
    config: ProjectConfig, command_parts: tuple[str, ...]
) -> tuple[RunReference, EndpointHandle]:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client)
    ensure_project_synced(config, volume)
    endpoint = resolve_endpoint(config, client, volume)
    command, workflow = resolve_run_command(config, command_parts, config.root)
    run_id = generate_run_id()
    payload = build_job_payload(
        config, run_id=run_id, command=command, workflow=workflow
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


def read_text_object(s3: Any, bucket: str, key: str) -> str:
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except Exception:
        return ""
    body = response["Body"].read()
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


def stream_logs(config: ProjectConfig, reference: RunReference, *, follow: bool) -> str:
    client = load_runpod_client(config)
    volume = resolve_runpod_volume(config, client)
    s3 = build_s3_client(config, volume)

    stdout_key = remote_run_file_key(config, reference.run_id, "stdout.log")
    stderr_key = remote_run_file_key(config, reference.run_id, "stderr.log")
    last_stdout = ""
    last_stderr = ""
    has_remote_output = False
    last_reported_status: str | None = None
    last_progress_at = 0.0
    submitted_at = parse_utc_timestamp(reference.submitted_at)

    while True:
        saw_output_this_iteration = False
        stdout_text = read_text_object(s3, volume.id, stdout_key)
        stderr_text = read_text_object(s3, volume.id, stderr_key)

        if stdout_text.startswith(last_stdout):
            chunk = stdout_text[len(last_stdout) :]
        else:
            chunk = stdout_text
        if chunk:
            click.echo(chunk, nl=False)
            has_remote_output = True
            saw_output_this_iteration = True
        last_stdout = stdout_text

        if stderr_text.startswith(last_stderr):
            chunk = stderr_text[len(last_stderr) :]
        else:
            chunk = stderr_text
        if chunk:
            click.echo(chunk, err=True, nl=False)
            has_remote_output = True
            saw_output_this_iteration = True
        last_stderr = stderr_text

        job = client.get_job(reference.endpoint_id, reference.job_id)
        status = str(job["status"])
        elapsed_seconds = 0
        if submitted_at is not None:
            elapsed_seconds = max(
                0,
                int((datetime.now(timezone.utc) - submitted_at).total_seconds()),
            )

        now_monotonic = time.monotonic()
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

        if should_report:
            report_poll_status(
                reference,
                status,
                has_remote_output=has_remote_output,
                elapsed_seconds=elapsed_seconds,
            )
            last_reported_status = status
            last_progress_at = now_monotonic

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
    s3 = build_s3_client(config, volume)

    destination = destination_root or (config.runs_dir / run_id)
    destination.mkdir(parents=True, exist_ok=True)
    prefix = remote_run_key_prefix(config, run_id)
    download_prefix(s3, volume.id, prefix, destination)
    return destination


def run_named_workflow(config: ProjectConfig, workflow: str) -> int:
    click.echo(f"syncing {config.name} -> {config.runtime.project_dir}")
    volume, uploaded, deleted = sync_project(config)
    click.echo(
        f"volume: {volume.id} ({volume.data_center_id or 'unknown-dc'}), "
        f"uploaded: {uploaded}, deleted: {deleted}"
    )
    click.echo(f"submitting {workflow}")
    reference, endpoint = submit_workflow(config, (workflow,))
    click.echo(f"run_id: {reference.run_id}")
    click.echo(f"job_id: {reference.job_id}")
    click.echo(f"endpoint_id: {endpoint.id}")
    click.echo("polling RunPod job status and remote logs...")
    status = stream_logs(config, reference, follow=True)
    click.echo(f"pulling artifacts for {reference.run_id}")
    pull_run(config, run_id=reference.run_id)
    return 0 if status == "COMPLETED" else 1


@click.group(cls=BannerGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="quadra")
def cli() -> None:
    """Quadra runs experiments on RunPod Serverless."""


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
        init_project(
            target_root, resolved_project_name, allow_existing=project_name is None
        )
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"initialized {resolved_project_name}")
    click.echo(target_root)


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
def submit(command_parts: tuple[str, ...]) -> None:
    """Submit a workflow to the configured RunPod Serverless endpoint."""
    try:
        config = load_project()
        reference, endpoint = submit_workflow(config, command_parts)
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


@cli.command()
@click.option(
    "--follow/--no-follow", default=True, help="Poll until the job completes."
)
def logs(follow: bool) -> None:
    """Stream logs for the most recently submitted run."""
    try:
        config = load_project()
        reference = load_last_run(config)
        status = stream_logs(config, reference, follow=follow)
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
        config = load_project()
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
def smoke() -> None:
    """Sync, submit, stream logs, and pull artifacts for the smoke workflow."""
    try:
        config = load_project()
        code = run_named_workflow(config, "smoke")
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


@cli.command()
def bench() -> None:
    """Sync, submit, stream logs, and pull artifacts for the bench workflow."""
    try:
        config = load_project()
        code = run_named_workflow(config, "bench")
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


if __name__ == "__main__":
    cli()
