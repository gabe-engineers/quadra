from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Generator


WORKER_BOOTSTRAP_LOG_PATH = Path(__file__).resolve().parent / ".quadra" / "worker-bootstrap.log"
RUN_MANIFEST_FILENAME = "run-manifest.json"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_bootstrap_log(message: str) -> None:
    WORKER_BOOTSTRAP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"[runpod worker] {_now()} {message}\n"
    with WORKER_BOOTSTRAP_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)
    sys.stdout.write(line)
    sys.stdout.flush()


def _use_project_bootstrap_log(project_dir: Path) -> None:
    global WORKER_BOOTSTRAP_LOG_PATH
    WORKER_BOOTSTRAP_LOG_PATH = project_dir / ".quadra" / "worker-bootstrap.log"


def _write_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_run_manifest(path: Path, *, run_dir: Path, run_id: str, status: str) -> None:
    files = sorted(
        file_path.relative_to(run_dir).as_posix()
        for file_path in run_dir.rglob("*")
        if file_path.is_file() and file_path.name != RUN_MANIFEST_FILENAME
    )
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": status,
                "files": files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _persist_run_state(
    *,
    run_dir: Path,
    run_id: str,
    status_path: Path,
    manifest_path: Path,
    status_payload: dict[str, Any],
) -> None:
    _write_status(status_path, status_payload)
    _write_run_manifest(
        manifest_path,
        run_dir=run_dir,
        run_id=run_id,
        status=str(status_payload.get("status", "unknown")),
    )


def _run_streaming(
    command: str,
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
) -> Generator[dict[str, str], None, int]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        ["/bin/sh", "-lc", command],
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout_fd = proc.stdout.fileno()
    stderr_fd = proc.stderr.fileno()
    with stdout_path.open("a", encoding="utf-8") as stdout_file:
        with stderr_path.open("a", encoding="utf-8") as stderr_file:
            while True:
                reads, _, _ = select.select([stdout_fd, stderr_fd], [], [])
                for fd in reads:
                    if fd == stdout_fd:
                        line = proc.stdout.readline()
                        if line:
                            stdout_file.write(line)
                            stdout_file.flush()
                            sys.stdout.write(line)
                            sys.stdout.flush()
                            yield {"stream": "stdout", "text": line}
                    elif fd == stderr_fd:
                        line = proc.stderr.readline()
                        if line:
                            stderr_file.write(line)
                            stderr_file.flush()
                            sys.stderr.write(line)
                            sys.stderr.flush()
                            yield {"stream": "stderr", "text": line}
                if proc.poll() is not None:
                    for line in proc.stdout:
                        stdout_file.write(line)
                        sys.stdout.write(line)
                        yield {"stream": "stdout", "text": line}
                    for line in proc.stderr:
                        stderr_file.write(line)
                        sys.stderr.write(line)
                        yield {"stream": "stderr", "text": line}
                    break
    return proc.returncode


def _fail(
    *,
    run_dir: Path,
    run_id: str,
    status_path: Path,
    manifest_path: Path,
    status_payload: dict[str, Any],
    step: str,
    exit_code: int | None,
    error: str,
) -> dict[str, Any]:
    status_payload.update(
        {
            "status": "failed",
            "step": step,
            "finished_at": _now(),
            "exit_code": exit_code,
            "error": error,
        }
    )
    _persist_run_state(
        run_dir=run_dir,
        run_id=run_id,
        status_path=status_path,
        manifest_path=manifest_path,
        status_payload=status_payload,
    )
    return {
        "run_id": run_id,
        "status": "failed",
        "error": error,
        "exit_code": exit_code,
    }


def handler(job: dict[str, Any]) -> Generator[dict[str, str], None, dict[str, Any]]:
    payload = (job or {}).get("input") or {}
    spec = payload.get("quadra") if isinstance(payload.get("quadra"), dict) else payload

    required = ["project_name", "run_id", "project_dir", "experiment_dir", "run_dir", "command"]
    missing = [key for key in required if not spec.get(key)]
    if missing:
        raise ValueError(f"Missing required Quadra payload fields: {', '.join(missing)}")

    project_name = str(spec["project_name"])
    run_id = str(spec["run_id"])
    workflow = str(spec.get("workflow", spec["command"]))
    project_dir = Path(str(spec["project_dir"]))
    _use_project_bootstrap_log(project_dir)
    _append_bootstrap_log("handler invoked")
    experiment_dir = Path(str(spec["experiment_dir"]))
    run_dir = Path(str(spec["run_dir"]))
    artifacts_dir = Path(str(spec.get("artifacts_dir", run_dir / "artifacts")))
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    status_path = run_dir / "status.json"
    manifest_path = run_dir / RUN_MANIFEST_FILENAME

    run_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    stdout_path.touch()
    stderr_path.touch()

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
    _persist_run_state(
        run_dir=run_dir,
        run_id=run_id,
        status_path=status_path,
        manifest_path=manifest_path,
        status_payload=status_payload,
    )

    if not project_dir.exists():
        return _fail(
            run_dir=run_dir,
            run_id=run_id,
            status_path=status_path,
            manifest_path=manifest_path,
            status_payload=status_payload,
            step="prepare",
            exit_code=None,
            error=f"Project directory does not exist: {project_dir}",
        )

    if not experiment_dir.exists():
        return _fail(
            run_dir=run_dir,
            run_id=run_id,
            status_path=status_path,
            manifest_path=manifest_path,
            status_payload=status_payload,
            step="prepare",
            exit_code=None,
            error=f"Experiment directory does not exist: {experiment_dir}",
        )

    setup_command = spec.get("setup_command")
    if setup_command:
        setup_rc = yield from _run_streaming(
            str(setup_command),
            cwd=project_dir,
            env=env,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        if setup_rc != 0:
            return _fail(
                run_dir=run_dir,
                run_id=run_id,
                status_path=status_path,
                manifest_path=manifest_path,
                status_payload=status_payload,
                step="setup",
                exit_code=setup_rc,
                error=f"Setup command failed with exit code {setup_rc}",
            )

    command_rc = yield from _run_streaming(
        str(spec["command"]),
        cwd=experiment_dir,
        env=env,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    if command_rc != 0:
        return _fail(
            run_dir=run_dir,
            run_id=run_id,
            status_path=status_path,
            manifest_path=manifest_path,
            status_payload=status_payload,
            step="command",
            exit_code=command_rc,
            error=f"Command failed with exit code {command_rc}",
        )

    status_payload.update(
        {
            "status": "completed",
            "finished_at": _now(),
            "exit_code": 0,
        }
    )
    _persist_run_state(
        run_dir=run_dir,
        run_id=run_id,
        status_path=status_path,
        manifest_path=manifest_path,
        status_payload=status_payload,
    )
    return {
        "run_id": run_id,
        "status": "completed",
        "run_dir": str(run_dir),
        "artifacts_dir": str(artifacts_dir),
    }


def main() -> None:
    _append_bootstrap_log("worker process starting")
    runpod_env_keys = sorted(key for key in os.environ if key.startswith("RUNPOD"))
    _append_bootstrap_log(f"runpod env keys: {', '.join(runpod_env_keys) or '<none>'}")
    try:
        import runpod
    except ImportError as exc:
        _append_bootstrap_log("failed to import runpod")
        raise RuntimeError(
            "The worker image is missing the `runpod` package required for serverless startup."
        ) from exc

    _append_bootstrap_log("imported runpod")
    _append_bootstrap_log("starting runpod.serverless.start")
    runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})


if __name__ == "__main__":
    main()
