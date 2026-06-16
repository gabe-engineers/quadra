from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import click
import tomllib

from quadra import __version__

CONFIG_FILENAME = "quadra.toml"
STATE_DIRNAME = ".quadra"
STATE_FILENAME = "state.json"
RUNTIME_DIRNAME = "runtime"
STATE_SCHEMA_VERSION = 1
CONFIG_SCHEMA_VERSION = 1
DEFAULT_REMOTE_ROOT = "/workspace/projects/{project_name}"
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
    backend: str
    remote_root: str


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
    def state_dir(self) -> Path:
        return self.root / STATE_DIRNAME

    @property
    def state_file(self) -> Path:
        return self.state_dir / STATE_FILENAME

    @property
    def runtime_dir(self) -> Path:
        return self.state_dir / RUNTIME_DIRNAME


@dataclass
class RuntimeState:
    schema_version: int = STATE_SCHEMA_VERSION
    active_runtime_id: str | None = None
    last_runtime_id: str | None = None
    created_at: str | None = None
    last_sync_at: str | None = None
    last_command: str | None = None


class QuadraError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


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
            backend=str(runtime.get("backend", "local")),
            remote_root=str(runtime["remote_root"]),
        ),
        commands={str(key): str(value) for key, value in data.get("commands", {}).items()},
    )


def load_state(config: ProjectConfig) -> RuntimeState:
    if not config.state_file.exists():
        return RuntimeState()

    try:
        data = json.loads(config.state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QuadraError(f"Failed to read {config.state_file}: {exc}") from exc

    return RuntimeState(
        schema_version=int(data.get("schema_version", STATE_SCHEMA_VERSION)),
        active_runtime_id=data.get("active_runtime_id"),
        last_runtime_id=data.get("last_runtime_id"),
        created_at=data.get("created_at"),
        last_sync_at=data.get("last_sync_at"),
        last_command=data.get("last_command"),
    )


def save_state(config: ProjectConfig, state: RuntimeState) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    config.state_file.write_text(
        json.dumps(asdict(state), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def current_runtime_root(config: ProjectConfig, state: RuntimeState) -> Path:
    if not state.active_runtime_id:
        raise QuadraError("No active runtime. Run `quadra up` first.")
    return config.runtime_dir / state.active_runtime_id


def current_staging_root(config: ProjectConfig, state: RuntimeState) -> Path:
    runtime_root = current_runtime_root(config, state)
    return runtime_root / config.runtime.remote_root.lstrip("/")


def ensure_runtime_active(config: ProjectConfig) -> RuntimeState:
    state = load_state(config)
    if not state.active_runtime_id:
        raise QuadraError("No active runtime. Run `quadra up` first.")
    if not current_runtime_root(config, state).exists():
        state.active_runtime_id = None
        save_state(config, state)
        raise QuadraError("Runtime state is stale. Run `quadra up` again.")
    return state


def ensure_runtime_synced(config: ProjectConfig, state: RuntimeState) -> Path:
    staging_root = current_staging_root(config, state)
    if not staging_root.exists():
        raise QuadraError("Runtime has not been synced yet. Run `quadra sync` first.")
    return staging_root


def init_project(target_root: Path, project_name: str) -> None:
    if target_root.exists():
        if any(target_root.iterdir()):
            raise QuadraError(f"Target directory already exists and is not empty: {target_root}")
    else:
        target_root.mkdir(parents=True, exist_ok=False)

    directories = [
        target_root / "src" / "libs" / "diffusers",
        target_root / "src" / "libs" / "transformers",
        target_root / "src" / "libs" / "vllm-omni",
        target_root / "src" / "experiment" / "scripts",
        target_root / "models",
        target_root / "caches",
        target_root / "runs",
        target_root / STATE_DIRNAME,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    for keep_dir in directories:
        if keep_dir.name != STATE_DIRNAME:
            (keep_dir / ".gitkeep").write_text("", encoding="utf-8")

    (target_root / CONFIG_FILENAME).write_text(
        render_quadra_config(project_name),
        encoding="utf-8",
    )
    (target_root / "src" / "experiment" / "pyproject.toml").write_text(
        render_experiment_pyproject(project_name),
        encoding="utf-8",
    )
    (target_root / "src" / "experiment" / "main.py").write_text(
        render_main_py(project_name),
        encoding="utf-8",
    )
    (target_root / "src" / "experiment" / "scripts" / "smoke.py").write_text(
        render_smoke_py(project_name),
        encoding="utf-8",
    )
    (target_root / "src" / "experiment" / "scripts" / "bench.py").write_text(
        render_bench_py(project_name),
        encoding="utf-8",
    )


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
        backend = "local"
        remote_root = "{remote_root}"

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


def activate_runtime(config: ProjectConfig) -> RuntimeState:
    state = load_state(config)
    if state.active_runtime_id:
        runtime_root = current_runtime_root(config, state)
        if runtime_root.exists():
            return state
        state.active_runtime_id = None

    new_runtime_id = runtime_id()
    runtime_root = config.runtime_dir / new_runtime_id
    runtime_root.mkdir(parents=True, exist_ok=False)
    state.active_runtime_id = new_runtime_id
    state.last_runtime_id = new_runtime_id
    state.created_at = now_utc()
    state.last_sync_at = None
    save_state(config, state)
    return state


def sync_runtime(config: ProjectConfig, state: RuntimeState) -> Path:
    staging_root = current_staging_root(config, state)
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        config.root,
        staging_root,
        ignore=shutil.ignore_patterns(*sorted(DEFAULT_IGNORES), "*.pyc"),
    )
    state.last_sync_at = now_utc()
    save_state(config, state)
    return staging_root


def destroy_runtime(config: ProjectConfig, state: RuntimeState | None = None) -> RuntimeState:
    state = state or load_state(config)
    if not state.active_runtime_id:
        return state

    runtime_root = current_runtime_root(config, state)
    if runtime_root.exists():
        shutil.rmtree(runtime_root)

    state.active_runtime_id = None
    save_state(config, state)
    return state


def resolve_run_command(
    config: ProjectConfig, command_parts: tuple[str, ...], staging_root: Path
) -> tuple[str, str]:
    raw_command = " ".join(command_parts).strip()
    if not raw_command:
        raise QuadraError("Missing command. Pass a named command or shell command.")

    if len(command_parts) == 1:
        command_name = command_parts[0]
        if command_name in config.commands:
            return config.commands[command_name], command_name

        script_path = staging_root / config.paths.experiment / "scripts" / f"{command_name}.py"
        if script_path.exists():
            return f"python scripts/{command_name}.py", command_name

    return raw_command, raw_command


def build_command_env(config: ProjectConfig, state: RuntimeState, staging_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    python_bin = str(Path(sys.executable).parent)
    env["PATH"] = os.pathsep.join(
        [python_bin, env["PATH"]] if env.get("PATH") else [python_bin]
    )
    env["QUADRA_PROJECT_NAME"] = config.name
    env["QUADRA_PROJECT_ROOT"] = str(config.root)
    env["QUADRA_REMOTE_ROOT"] = config.runtime.remote_root
    env["QUADRA_RUNTIME_ID"] = state.active_runtime_id or ""
    env["QUADRA_RUNTIME_ROOT"] = str(current_runtime_root(config, state))
    env["QUADRA_STAGING_ROOT"] = str(staging_root)
    env["QUADRA_PYTHON"] = sys.executable
    return env


def run_in_runtime(config: ProjectConfig, state: RuntimeState, command_parts: tuple[str, ...]) -> int:
    staging_root = ensure_runtime_synced(config, state)
    command, label = resolve_run_command(config, command_parts, staging_root)
    experiment_dir = staging_root / config.paths.experiment
    env = build_command_env(config, state, staging_root)

    completed = subprocess.run(
        command,
        shell=True,
        cwd=experiment_dir,
        env=env,
        text=True,
        capture_output=True,
    )

    if completed.stdout:
        click.echo(completed.stdout, nl=False)
    if completed.stderr:
        click.echo(completed.stderr, err=True, nl=False)

    state.last_command = label
    save_state(config, state)
    return completed.returncode


def open_shell(config: ProjectConfig, state: RuntimeState) -> int:
    staging_root = ensure_runtime_synced(config, state)
    experiment_dir = staging_root / config.paths.experiment
    env = build_command_env(config, state, staging_root)
    shell = env.get("SHELL") or "/bin/sh"
    completed = subprocess.run([shell], cwd=experiment_dir, env=env)
    return completed.returncode


def format_runtime_summary(config: ProjectConfig, state: RuntimeState) -> str:
    return textwrap.dedent(
        f"""\
        project: {config.name}
        runtime_id: {state.active_runtime_id}
        remote_root: {config.runtime.remote_root}
        runtime_root: {current_runtime_root(config, state)}
        """
    ).strip()


def bootstrap_runtime(config: ProjectConfig) -> RuntimeState:
    state = activate_runtime(config)
    sync_runtime(config, state)
    return state


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="quadra")
def cli() -> None:
    """Quadra owns the project/runtime lifecycle."""


@cli.command()
@click.argument("project_name")
def init(project_name: str) -> None:
    """Create a project scaffold that matches the Quadra contract."""
    target_root = Path.cwd() / project_name
    try:
        init_project(target_root, project_name)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"initialized {project_name}")
    click.echo(target_root)


@cli.command()
def up() -> None:
    """Create or reuse the active runtime."""
    try:
        config = load_project()
        existed = load_state(config).active_runtime_id is not None
        state = activate_runtime(config)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if existed:
        click.echo("runtime already active")
    else:
        click.echo("runtime ready")
    click.echo(format_runtime_summary(config, state))


@cli.command()
def sync() -> None:
    """Sync the project into the active runtime staging root."""
    try:
        config = load_project()
        state = ensure_runtime_active(config)
        staging_root = sync_runtime(config, state)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"synced {config.name} -> {config.runtime.remote_root}")
    click.echo(staging_root)


@cli.command()
def bootstrap() -> None:
    """Convenience command: create a runtime and sync the project."""
    try:
        config = load_project()
        state = bootstrap_runtime(config)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("runtime bootstrapped")
    click.echo(format_runtime_summary(config, state))


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("command_parts", nargs=-1, required=True, type=click.UNPROCESSED)
def run(command_parts: tuple[str, ...]) -> None:
    """Run a named experiment command or raw shell command."""
    try:
        config = load_project()
        state = ensure_runtime_active(config)
        code = run_in_runtime(config, state, command_parts)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


@cli.command()
def shell() -> None:
    """Open an interactive shell in the synced experiment workspace."""
    try:
        config = load_project()
        state = ensure_runtime_active(config)
        code = open_shell(config, state)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    if code != 0:
        raise click.exceptions.Exit(code)


@cli.command()
def destroy() -> None:
    """Destroy the active runtime."""
    try:
        config = load_project()
        state = load_state(config)
        if not state.active_runtime_id:
            click.echo("no active runtime")
            return
        runtime_root = current_runtime_root(config, state)
        destroy_runtime(config, state)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"destroyed runtime {runtime_root.name}")


@cli.command(name="hard-run", context_settings={"ignore_unknown_options": True})
@click.argument("command_parts", nargs=-1, required=True, type=click.UNPROCESSED)
def hard_run(command_parts: tuple[str, ...]) -> None:
    """Run the full create-sync-run-destroy loop."""
    try:
        config = load_project()
        existing_state = load_state(config)
        if existing_state.active_runtime_id:
            destroy_runtime(config, existing_state)

        state = activate_runtime(config)
        sync_runtime(config, state)
        code = run_in_runtime(config, state, command_parts)
        destroy_runtime(config, state)
    except QuadraError as exc:
        raise click.ClickException(str(exc)) from exc
    finally:
        try:
            config = load_project()
            state = load_state(config)
            if state.active_runtime_id:
                destroy_runtime(config, state)
        except QuadraError:
            pass

    if code != 0:
        raise click.exceptions.Exit(code)
