from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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

    required = ["project_name", "run_id", "project_dir", "experiment_dir", "run_dir", "command"]
    missing = [key for key in required if not spec.get(key)]
    if missing:
        raise ValueError(f"Missing required Quadra payload fields: {', '.join(missing)}")

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
                    "error": f"Setup command failed with exit code {setup_result.returncode}",
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
                "error": f"Command failed with exit code {command_result.returncode}",
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


def main() -> None:
    try:
        import runpod
    except ImportError as exc:
        raise RuntimeError(
            "The worker image is missing the `runpod` package required for serverless startup."
        ) from exc

    runpod.serverless.start({"handler": handler})


if __name__ == "__main__":
    main()
