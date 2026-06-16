from __future__ import annotations

import subprocess
import sys
import types
import unittest
from contextlib import chdir
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from quadra.cli import cli


class QuadraCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_init_creates_project_contract(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(result.exit_code, 0, result.output)

            project_root = Path("bonsai")
            self.assertTrue((project_root / "quadra.toml").exists())
            self.assertTrue((project_root / ".quadra").exists())
            self.assertTrue((project_root / "src" / "libs" / "diffusers").exists())
            self.assertTrue((project_root / "src" / "libs" / "transformers").exists())
            self.assertTrue((project_root / "src" / "libs" / "vllm-omni").exists())
            self.assertTrue((project_root / "src" / "experiment" / "scripts" / "smoke.py").exists())
            self.assertTrue((project_root / "models").exists())
            self.assertTrue((project_root / "caches").exists())
            self.assertTrue((project_root / "runs").exists())

    def test_init_without_name_uses_current_directory_name(self) -> None:
        with self.runner.isolated_filesystem():
            project_root = Path("bonsai")
            project_root.mkdir()
            (project_root / "README.md").write_text("# bonsai\n", encoding="utf-8")

            with chdir(project_root):
                result = self.runner.invoke(cli, ["init"])
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("initialized bonsai", result.output)

                config = Path("quadra.toml").read_text(encoding="utf-8")
                self.assertIn('name = "bonsai"', config)

                self.assertTrue(Path(".quadra").exists())
                self.assertTrue(Path("src/experiment/scripts/smoke.py").exists())
                self.assertTrue(Path("models").exists())
                self.assertTrue(Path("caches").exists())
                self.assertTrue(Path("runs").exists())
                self.assertEqual(Path("README.md").read_text(encoding="utf-8"), "# bonsai\n")

    def test_sync_stages_runtime_and_hard_run_cleans_up(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            runpod = self.make_fake_runpod_module()
            remote = self.make_fake_remote_runner()

            with chdir("bonsai"):
                with patch.dict(sys.modules, {"runpod": runpod}):
                    with patch.dict("os.environ", {"RUNPOD_API_KEY": "test-key"}):
                        with patch("quadra.cli.shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"):
                            with patch("quadra.cli.subprocess.run", side_effect=remote.run):
                                up_result = self.runner.invoke(cli, ["up"])
                                self.assertEqual(up_result.exit_code, 0, up_result.output)

                                pre_sync_run = self.runner.invoke(cli, ["run", "smoke"])
                                self.assertNotEqual(pre_sync_run.exit_code, 0)
                                self.assertIn("Run `quadra sync` first", pre_sync_run.output)

                                sync_result = self.runner.invoke(cli, ["sync"])
                                self.assertEqual(sync_result.exit_code, 0, sync_result.output)
                                self.assertTrue(remote.synced)

                                run_result = self.runner.invoke(cli, ["run", "smoke"])
                                self.assertEqual(run_result.exit_code, 0, run_result.output)
                                self.assertIn("bonsai smoke remote", run_result.output)

                                hard_run_result = self.runner.invoke(cli, ["hard-run", "smoke"])
                                self.assertEqual(hard_run_result.exit_code, 0, hard_run_result.output)
                                self.assertIn("bonsai smoke remote", hard_run_result.output)

                                self.assertEqual(remote.sync_runs, 2)
                                self.assertEqual(len(runpod.create_calls), 2)
                                self.assertEqual(runpod.terminated_pods, ["pod-123", "pod-123"])
                                self.assertFalse(Path(".quadra/state.json").exists())

    def test_runpod_up_discovers_pod_by_name_and_destroy_terminates_it(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            runpod = self.make_fake_runpod_module()

            with chdir("bonsai"):
                with patch.dict(sys.modules, {"runpod": runpod}):
                    with patch.dict("os.environ", {"RUNPOD_API_KEY": "test-key"}):
                        up_result = self.runner.invoke(cli, ["up"])
                        self.assertEqual(up_result.exit_code, 0, up_result.output)
                        self.assertIn("runtime ready", up_result.output)
                        self.assertIn("pod_id: pod-123", up_result.output)
                        self.assertIn("pod_name: quadra-bonsai", up_result.output)
                        self.assertIn("ssh: ssh -p 22022 root@1.2.3.4", up_result.output)
                        self.assertIn("quadra sync", up_result.output)

                        self.assertEqual(len(runpod.create_calls), 1)
                        create_call = runpod.create_calls[0]
                        self.assertEqual(create_call["name"], "quadra-bonsai")
                        self.assertEqual(create_call["network_volume_id"], "nv-123")
                        self.assertEqual(
                            create_call["volume_mount_path"],
                            "/workspace/bonsai",
                        )
                        self.assertFalse(Path(".quadra/state.json").exists())

                        destroy_result = self.runner.invoke(cli, ["destroy"])
                        self.assertEqual(destroy_result.exit_code, 0, destroy_result.output)
                        self.assertIn("destroyed runtime pod-123", destroy_result.output)
                        self.assertEqual(runpod.terminated_pods, ["pod-123"])
                        self.assertEqual(runpod.get_pods(), [])

    def make_fake_runpod_module(self) -> types.ModuleType:
        module = types.ModuleType("runpod")
        module.api_key = None
        module.create_calls = []
        module.terminated_pods = []
        module._pods = []
        module._volume = {
            "id": "nv-123",
            "name": "bonsai",
            "size": 100,
            "dataCenterId": "US-KS-1",
        }
        module._pod = {
            "id": "pod-123",
            "name": "quadra-bonsai",
            "desiredStatus": "RUNNING",
            "runtime": {
                "ports": [
                    {
                        "ip": "1.2.3.4",
                        "isIpPublic": True,
                        "privatePort": 22,
                        "publicPort": 22022,
                        "type": "tcp",
                    },
                    {
                        "ip": "1.2.3.4",
                        "isIpPublic": True,
                        "privatePort": 8888,
                        "publicPort": 28888,
                        "type": "http",
                    },
                ]
            },
        }

        def get_user() -> dict[str, object]:
            return {"networkVolumes": [module._volume]}

        def get_pods() -> list[dict[str, object]]:
            return list(module._pods)

        def create_pod(**kwargs: object) -> dict[str, object]:
            module.create_calls.append(kwargs)
            module._pod["name"] = kwargs["name"]
            module._pods = [{"id": "pod-123", "name": kwargs["name"]}]
            return {
                "id": "pod-123",
                "name": kwargs["name"],
                "desiredStatus": "PENDING",
            }

        def get_pod(pod_id: str) -> dict[str, object]:
            self.assertEqual(pod_id, "pod-123")
            return dict(module._pod)

        def terminate_pod(pod_id: str) -> None:
            module.terminated_pods.append(pod_id)
            module._pods = []

        module.get_user = get_user
        module.get_pods = get_pods
        module.create_pod = create_pod
        module.get_pod = get_pod
        module.terminate_pod = terminate_pod
        return module

    def make_fake_remote_runner(self):
        class FakeRemoteRunner:
            def __init__(self):
                self.synced = False
                self.sync_runs = 0

            def run(self, args, **kwargs):
                if args[0] == "ssh":
                    remote_command = args[-1]
                    if remote_command.startswith("test -e "):
                        return subprocess.CompletedProcess(
                            args,
                            0 if self.synced else 1,
                            stdout="",
                            stderr="",
                        )
                    if remote_command.startswith("mkdir -p "):
                        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
                    if "python scripts/smoke.py" in remote_command:
                        return subprocess.CompletedProcess(
                            args,
                            0,
                            stdout="bonsai smoke remote\n",
                            stderr="",
                        )
                    return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

                if args[0] == "rsync":
                    self.synced = True
                    self.sync_runs += 1
                    return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

                raise AssertionError(f"unexpected subprocess args: {args}")

        return FakeRemoteRunner()


if __name__ == "__main__":
    unittest.main()
