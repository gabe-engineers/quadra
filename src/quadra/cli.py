from __future__ import annotations

import importlib
import os
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import click

from quadra import __version__

CONFIG_FILENAME = "quadra.toml"
STATE_DIRNAME = ".quadra"
CONFIG_SCHEMA_VERSION = 2
DEFAULT_REMOTE_ROOT = "/workspace/{project_name}"
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


@dataclass(frozen=True)
class ProjectPaths:
    libs: str
    experiment: str
    models: str
    caches: str
    runs: str


@dataclass(frozen=True)
class RuntimeConfig:
    remote_root: str
    runpod: "RunpodConfig"


@dataclass(frozen=True)
class RunpodConfig:
    api_key_env: str = "RUNPOD_API_KEY"
    image: str | None = None
    template_id: str | None = None
    gpu_type: str | None = None
    gpu_count: int = 1
    cloud_type: str = "ALL"
    ports: str | None = "22/tcp"
    support_public_ip: bool = True
    start_ssh: bool = True
    container_disk_gb: int | None = 10
    min_vcpu_count: int = 1
    min_memory_in_gb: int = 1
    data_center_id: str | None = None
    network_volume_id: str | None = None
    network_volume_name: str | None = None
    volume_mount_path: str | None = None
    instance_id: str | None = None
    allowed_cuda_versions: tuple[str, ...] = ()
    timeout_seconds: int = 300


@dataclass(frozen=True)
class ProjectConfig:
    schema_version: int
    name: str
    root: Path
    paths: ProjectPaths
    runtime: RuntimeConfig
    commands: dict[str, str] = field(default_factory=dict)

    @property
    def experiment_dir(self) -> Path:
        return self.root / self.paths.experiment

    @property
    def libs_dir(self) -> Path:
        return self.root / self.paths.libs

    @property
    def models_dir(self) -> Path:
        return self.root / self.paths.models

    @property
    def caches_dir(self) -> Path:
        return self.root / self.paths.caches

    @property
    def runs_dir(self) -> Path:
        return self.root / self.paths.runs

    @property
    def quadra_dir(self) -> Path:
        return self.root / STATE_DIRNAME


@dataclass(frozen=True)
class RunpodConnection:
    pod_id: str
    pod_name: str
    ssh_host: str
    ssh_port: int
    public_ports: list[dict[str, Any]] = field(default_factory=list)


class QuadraError(RuntimeError):
    pass


def optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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

    runpod_config = RunpodConfig(
        api_key_env=str(runpod_data.get("api_key_env", "RUNPOD_API_KEY")),
        image=optional_str(runpod_data.get("image")),
        template_id=optional_str(runpod_data.get("template_id")),
        gpu_type=optional_str(runpod_data.get("gpu_type")),
        gpu_count=int(runpod_data.get("gpu_count", 1)),
        cloud_type=str(runpod_data.get("cloud_type", "ALL")).strip().upper(),
        ports=optional_str(runpod_data.get("ports", "22/tcp")),
        support_public_ip=bool(runpod_data.get("support_public_ip", True)),
        start_ssh=bool(runpod_data.get("start_ssh", True)),
        container_disk_gb=(
            int(runpod_data["container_disk_gb"])
            if runpod_data.get("container_disk_gb") is not None
            else None
        ),
        min_vcpu_count=int(runpod_data.get("min_vcpu_count", 1)),
        min_memory_in_gb=int(runpod_data.get("min_memory_in_gb", 1)),
        data_center_id=optional_str(runpod_data.get("data_center_id")),
        network_volume_id=optional_str(runpod_data.get("network_volume_id")),
        network_volume_name=optional_str(runpod_data.get("network_volume_name")),
        volume_mount_path=optional_str(runpod_data.get("volume_mount_path")),
        instance_id=optional_str(runpod_data.get("instance_id")),
        allowed_cuda_versions=normalize_allowed_cuda_versions(
            runpod_data.get("allowed_cuda_versions")
        ),
        timeout_seconds=int(runpod_data.get("timeout_seconds", 300)),
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
            remote_root=str(runtime["remote_root"]),
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
    scaffold_files[1].write_text(
        render_experiment_pyproject(project_name),
        encoding="utf-8",
    )
    scaffold_files[2].write_text(render_main_py(project_name), encoding="utf-8")
    scaffold_files[3].write_text(render_smoke_py(project_name), encoding="utf-8")
    scaffold_files[4].write_text(render_bench_py(project_name), encoding="utf-8")


def render_quadra_config(project_name: str) -> str:
    remote_root = DEFAULT_REMOTE_ROOT.format(project_name=project_name)
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
        remote_root = "{remote_root}"

        [runtime.runpod]
        api_key_env = "RUNPOD_API_KEY"
        image = "runpod/pytorch:latest"
        gpu_type = "NVIDIA RTX 2000 Ada"
        gpu_count = 1
        cloud_type = "ALL"
        ports = "22/tcp,8888/http"
        container_disk_gb = 25
        network_volume_name = "{project_name}"
        timeout_seconds = 300

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


def cleanup_legacy_state_file(config: ProjectConfig) -> None:
    legacy_state_file = config.quadra_dir / "state.json"
    if legacy_state_file.exists():
        legacy_state_file.unlink()


def resolve_runtime(config: ProjectConfig) -> RunpodConfig:
    runpod_config = config.runtime.runpod
    if not runpod_config.image and not runpod_config.template_id:
        raise QuadraError(
            "RunPod runtime requires `runtime.runpod.image` or `runtime.runpod.template_id`."
        )
    return runpod_config


def load_runpod_sdk(config: ProjectConfig) -> Any:
    runpod_config = resolve_runtime(config)
    try:
        runpod = importlib.import_module("runpod")
    except ImportError as exc:
        raise QuadraError(
            "RunPod support requires the `runpod` package. Install project dependencies first."
        ) from exc

    api_key = os.getenv(runpod_config.api_key_env)
    if api_key:
        runpod.api_key = api_key
    elif not getattr(runpod, "api_key", None):
        raise QuadraError(
            f"RunPod API key not configured. Set {runpod_config.api_key_env} or configure the SDK."
        )

    return runpod


def runpod_pod_name(config: ProjectConfig) -> str:
    return f"quadra-{config.name}"


def find_runpod_volume(runpod: Any, config: ProjectConfig) -> dict[str, Any]:
    runpod_config = resolve_runtime(config)
    target_id = runpod_config.network_volume_id
    target_name = runpod_config.network_volume_name or config.name
    volumes = list(runpod.get_user().get("networkVolumes", []))

    if target_id:
        for volume in volumes:
            if volume.get("id") == target_id:
                return volume
        raise QuadraError(f"RunPod network volume {target_id} was not found.")

    matches = [volume for volume in volumes if volume.get("name") == target_name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod network volumes are named {target_name!r}. Set runtime.runpod.network_volume_id."
        )
    raise QuadraError(
        f"No RunPod network volume named {target_name!r} was found. "
        "Create it in RunPod and retry, or configure runtime.runpod.network_volume_id."
    )


def find_runpod_pod(runpod: Any, config: ProjectConfig) -> dict[str, Any] | None:
    pod_name = runpod_pod_name(config)
    matches = [pod for pod in runpod.get_pods() if pod.get("name") == pod_name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise QuadraError(
            f"Multiple RunPod pods are named {pod_name!r}. Clean them up before retrying."
        )
    return None


def extract_public_ports(pod: dict[str, Any]) -> list[dict[str, Any]]:
    runtime = pod.get("runtime") or {}
    ports = runtime.get("ports") or []
    return [port for port in ports if isinstance(port, dict)]


def extract_ssh_endpoint(ports: list[dict[str, Any]]) -> tuple[str | None, int | None]:
    for port in ports:
        if port.get("privatePort") == 22 and port.get("publicPort") is not None:
            host = port.get("ip")
            if host:
                return str(host), int(port["publicPort"])
    return None, None


def wait_for_runpod_pod(
    runpod: Any, pod_id: str, timeout_seconds: int
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_pod: dict[str, Any] | None = None

    while time.time() < deadline:
        pod = runpod.get_pod(pod_id)
        last_pod = pod
        ports = extract_public_ports(pod)
        desired_status = pod.get("desiredStatus")
        ssh_host, ssh_port = extract_ssh_endpoint(ports)

        if desired_status == "RUNNING" and ports and ssh_host and ssh_port:
            return pod

        time.sleep(2)

    if last_pod and last_pod.get("desiredStatus") != "RUNNING":
        raise QuadraError(
            f"RunPod pod {pod_id} did not reach RUNNING within {timeout_seconds} seconds."
        )
    raise QuadraError(
        f"RunPod pod {pod_id} did not expose SSH/runtime ports within {timeout_seconds} seconds."
    )


def build_runpod_connection(pod: dict[str, Any]) -> RunpodConnection:
    ports = extract_public_ports(pod)
    ssh_host, ssh_port = extract_ssh_endpoint(ports)
    if not ssh_host or not ssh_port:
        raise QuadraError("RunPod SSH endpoint is unavailable. Run `quadra up` again.")
    return RunpodConnection(
        pod_id=str(pod["id"]),
        pod_name=optional_str(pod.get("name")) or "",
        ssh_host=ssh_host,
        ssh_port=ssh_port,
        public_ports=ports,
    )


def get_runpod_connection(config: ProjectConfig) -> RunpodConnection:
    cleanup_legacy_state_file(config)
    runpod = load_runpod_sdk(config)
    runpod_config = resolve_runtime(config)
    pod = find_runpod_pod(runpod, config)
    if not pod:
        raise QuadraError("No active runtime. Run `quadra up` first.")
    live_pod = wait_for_runpod_pod(runpod, str(pod["id"]), runpod_config.timeout_seconds)
    return build_runpod_connection(live_pod)


def activate_runpod_runtime(config: ProjectConfig) -> tuple[RunpodConnection, bool]:
    cleanup_legacy_state_file(config)
    runpod = load_runpod_sdk(config)
    runpod_config = resolve_runtime(config)
    existing = find_runpod_pod(runpod, config)
    if existing:
        live_pod = wait_for_runpod_pod(
            runpod, str(existing["id"]), runpod_config.timeout_seconds
        )
        return build_runpod_connection(live_pod), True

    volume = find_runpod_volume(runpod, config)
    pod_name = runpod_pod_name(config)

    try:
        created_pod = runpod.create_pod(
            name=pod_name,
            image_name=runpod_config.image or "",
            gpu_type_id=runpod_config.gpu_type,
            cloud_type=runpod_config.cloud_type,
            support_public_ip=runpod_config.support_public_ip,
            start_ssh=runpod_config.start_ssh,
            data_center_id=runpod_config.data_center_id or volume.get("dataCenterId"),
            gpu_count=runpod_config.gpu_count,
            container_disk_in_gb=runpod_config.container_disk_gb,
            min_vcpu_count=runpod_config.min_vcpu_count,
            min_memory_in_gb=runpod_config.min_memory_in_gb,
            ports=runpod_config.ports,
            volume_mount_path=runpod_config.volume_mount_path
            or config.runtime.remote_root,
            template_id=runpod_config.template_id,
            network_volume_id=str(volume["id"]),
            allowed_cuda_versions=list(runpod_config.allowed_cuda_versions) or None,
            instance_id=runpod_config.instance_id,
        )
    except Exception as exc:
        raise QuadraError(f"Failed to create RunPod pod: {exc}") from exc

    live_pod = wait_for_runpod_pod(
        runpod, str(created_pod["id"]), runpod_config.timeout_seconds
    )
    return build_runpod_connection(live_pod), False


def require_command(command: str) -> str:
    resolved = shutil.which(command)
    if not resolved:
        raise QuadraError(f"Required command not found on PATH: {command}")
    return resolved


def runpod_ssh_transport_args(
    connection: RunpodConnection, *, allocate_tty: bool = False
) -> list[str]:
    require_command("ssh")
    args = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ServerAliveInterval=30",
        "-p",
        str(connection.ssh_port),
    ]
    if allocate_tty:
        args.append("-t")
    return args


def runpod_ssh_base_args(
    connection: RunpodConnection, *, allocate_tty: bool = False
) -> list[str]:
    args = runpod_ssh_transport_args(connection, allocate_tty=allocate_tty)
    args.append(f"root@{connection.ssh_host}")
    return args


def runpod_remote_path_exists(
    connection: RunpodConnection, remote_path: str, *, path_kind: str = "e"
) -> bool:
    completed = subprocess.run(
        [
            *runpod_ssh_base_args(connection),
            "sh",
            "-lc",
            f"test -{path_kind} {shlex.quote(remote_path)}",
        ],
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise QuadraError(
        f"Failed to inspect remote path {remote_path}: {completed.stderr.strip() or completed.stdout.strip()}"
    )


def ensure_runpod_synced(config: ProjectConfig, connection: RunpodConnection) -> None:
    remote_config_path = str(PurePosixPath(config.runtime.remote_root) / CONFIG_FILENAME)
    if not runpod_remote_path_exists(connection, remote_config_path):
        raise QuadraError("Runtime has not been synced yet. Run `quadra sync` first.")


def sync_runpod_runtime(config: ProjectConfig, connection: RunpodConnection) -> Path:
    require_command("rsync")
    mkdir_command = f"mkdir -p {shlex.quote(config.runtime.remote_root)}"
    mkdir_result = subprocess.run(
        [*runpod_ssh_base_args(connection), "sh", "-lc", mkdir_command],
        text=True,
        capture_output=True,
    )
    if mkdir_result.returncode != 0:
        raise QuadraError(
            f"Failed to prepare remote project root: {mkdir_result.stderr.strip() or mkdir_result.stdout.strip()}"
        )

    rsync_command = [
        "rsync",
        "-az",
        "--delete",
    ]
    for pattern in sorted(DEFAULT_IGNORES):
        rsync_command.extend(["--exclude", pattern])
    rsync_command.extend(
        [
            "--exclude",
            "*.pyc",
            "-e",
            " ".join(runpod_ssh_transport_args(connection)),
            f"{config.root}/",
            f"root@{connection.ssh_host}:{config.runtime.remote_root}/",
        ]
    )
    completed = subprocess.run(rsync_command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise QuadraError(
            f"Failed to sync project to RunPod: {completed.stderr.strip() or completed.stdout.strip()}"
        )

    return Path(config.runtime.remote_root)


def destroy_runpod_runtime(config: ProjectConfig) -> str | None:
    cleanup_legacy_state_file(config)
    runpod = load_runpod_sdk(config)
    pod = find_runpod_pod(runpod, config)
    if not pod:
        return None
    pod_id = str(pod["id"])
    try:
        runpod.terminate_pod(pod_id)
    except Exception as exc:
        if "not found" not in str(exc).lower():
            raise QuadraError(f"Failed to terminate RunPod pod {pod_id}: {exc}") from exc
    return pod_id


def destroy_runtime(config: ProjectConfig) -> str | None:
    return destroy_runpod_runtime(config)


def resolve_run_command(
    config: ProjectConfig, command_parts: tuple[str, ...], project_root: Path
) -> tuple[str, str]:
    raw_command = " ".join(command_parts).strip()
    if not raw_command:
        raise QuadraError("Missing command. Pass a named command or shell command.")

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


def build_runpod_command_env(
    config: ProjectConfig, connection: RunpodConnection
) -> dict[str, str]:
    remote_root = config.runtime.remote_root
    return {
        "QUADRA_PROJECT_NAME": config.name,
        "QUADRA_PROJECT_ROOT": remote_root,
        "QUADRA_REMOTE_ROOT": remote_root,
        "QUADRA_RUNTIME_ID": connection.pod_id,
        "QUADRA_RUNTIME_ROOT": remote_root,
        "QUADRA_POD_ID": connection.pod_id,
        "QUADRA_PYTHON": "python",
    }


def run_in_runpod_runtime(
    config: ProjectConfig, connection: RunpodConnection, command_parts: tuple[str, ...]
) -> int:
    ensure_runpod_synced(config, connection)
    command, _label = resolve_run_command(config, command_parts, config.root)
    remote_experiment_dir = str(
        PurePosixPath(config.runtime.remote_root) / config.paths.experiment
    )
    exports = " ".join(
        f"{key}={shlex.quote(value)}"
        for key, value in build_runpod_command_env(config, connection).items()
    )
    remote_command = (
        f"cd {shlex.quote(remote_experiment_dir)} && export {exports} && {command}"
    )
    completed = subprocess.run(
        [*runpod_ssh_base_args(connection), "sh", "-lc", remote_command],
        text=True,
        capture_output=True,
    )

    if completed.stdout:
        click.echo(completed.stdout, nl=False)
    if completed.stderr:
        click.echo(completed.stderr, err=True, nl=False)

    return completed.returncode


def run_in_runtime(config: ProjectConfig, command_parts: tuple[str, ...]) -> int:
    return run_in_runpod_runtime(config, get_runpod_connection(config), command_parts)


def open_shell(config: ProjectConfig) -> int:
    connection = get_runpod_connection(config)
    remote_config_path = str(PurePosixPath(config.runtime.remote_root) / CONFIG_FILENAME)
    remote_dir = config.runtime.remote_root
    if runpod_remote_path_exists(connection, remote_config_path):
        remote_dir = str(PurePosixPath(remote_dir) / config.paths.experiment)
    remote_command = (
        f"mkdir -p {shlex.quote(remote_dir)} && "
        f"cd {shlex.quote(remote_dir)} && "
        "exec /bin/sh"
    )
    completed = subprocess.run(
        [
            *runpod_ssh_base_args(connection, allocate_tty=True),
            "sh",
            "-lc",
            remote_command,
        ]
    )
    return completed.returncode


def format_public_endpoints(connection: RunpodConnection) -> list[str]:
    lines: list[str] = []
    for port in connection.public_ports:
        if port.get("privatePort") == 22:
            continue
        host = port.get("ip")
        public_port = port.get("publicPort")
        port_type = str(port.get("type", "tcp")).lower()
        if not host or public_port is None:
            continue
        if port_type in {"http", "https"}:
            target = f"{port_type}://{host}:{public_port}"
        else:
            target = f"{host}:{public_port}/{port_type}"
        lines.append(f"{port_type}: {target}")
    return lines


def format_runtime_summary(
    config: ProjectConfig, connection: RunpodConnection
) -> str:
    lines = [
        f"project: {config.name}",
        f"pod_id: {connection.pod_id}",
        f"pod_name: {connection.pod_name}",
        f"remote_root: {config.runtime.remote_root}",
        f"ssh: ssh -p {connection.ssh_port} root@{connection.ssh_host}",
    ]
    lines.extend(format_public_endpoints(connection))
    return "\n".join(lines)


def bootstrap_runtime(config: ProjectConfig) -> str:
    connection, _ = activate_runpod_runtime(config)
    sync_runpod_runtime(config, connection)
    return format_runtime_summary(config, connection)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="quadra")
def cli() -> None:
    """Quadra owns the project/runtime lifecycle."""


@cli.command()
@click.argument("project_name", required=False)
def init(project_name: str | None) -> None:
    """Create a project scaffold that matches the Quadra contract."""
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
def up() -> None:
    """Create or reuse the active runtime."""
    try:
        config = load_project()
        connection, existed = activate_runpod_runtime(config)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if existed:
        click.echo("runtime already active")
    else:
        click.echo("runtime ready")
    click.echo(format_runtime_summary(config, connection))
    click.echo("")
    click.echo("next:")
    click.echo("quadra sync")
    click.echo("quadra shell")
    click.echo("quadra run")


@cli.command()
def sync() -> None:
    """Sync the project into the active remote root."""
    try:
        config = load_project()
        remote_root = sync_runpod_runtime(config, get_runpod_connection(config))
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"synced {config.name} -> {config.runtime.remote_root}")
    click.echo(remote_root)


@cli.command()
def bootstrap() -> None:
    """Convenience command: create a runtime and sync the project."""
    try:
        config = load_project()
        summary = bootstrap_runtime(config)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("runtime bootstrapped")
    click.echo(summary)


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("command_parts", nargs=-1, required=True, type=click.UNPROCESSED)
def run(command_parts: tuple[str, ...]) -> None:
    """Run a named experiment command or raw shell command."""
    try:
        config = load_project()
        code = run_in_runtime(config, command_parts)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


@cli.command()
def shell() -> None:
    """Open an interactive shell in the synced experiment workspace."""
    try:
        config = load_project()
        code = open_shell(config)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


@cli.command()
def destroy() -> None:
    """Destroy the active runtime."""
    try:
        config = load_project()
        runtime_label = destroy_runtime(config)
        if not runtime_label:
            click.echo("no active runtime")
            return
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"destroyed runtime {runtime_label}")


@cli.command(name="hard-run", context_settings={"ignore_unknown_options": True})
@click.argument("command_parts", nargs=-1, required=True, type=click.UNPROCESSED)
def hard_run(command_parts: tuple[str, ...]) -> None:
    """Run the full create-sync-run-destroy loop."""
    try:
        config = load_project()
        destroy_runtime(config)
        connection, _ = activate_runpod_runtime(config)
        sync_runpod_runtime(config, connection)
        code = run_in_runtime(config, command_parts)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc
    finally:
        try:
            config = load_project()
            destroy_runtime(config)
        except QuadraError:
            pass

    if code != 0:
        raise click.exceptions.Exit(code)
