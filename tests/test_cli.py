from __future__ import annotations

import io
import json
import posixpath
import unittest
from contextlib import chdir
from http import HTTPStatus
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from click.testing import CliRunner

from quadra._generated.runpod_rest_client.models.endpoint import Endpoint
from quadra._generated.runpod_rest_client.models.template import Template
from quadra._generated.runpod_rest_client.types import Response
from quadra.cli import (
    RunpodClient,
    cli,
    load_banner_text,
    load_project,
    resolve_runpod_volume,
)
from quadra.runpod_rest import build_endpoint_create_body


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        del bucket
        self.objects[key] = Path(filename).read_bytes()

    def list_objects_v2(
        self,
        *,
        Bucket: str,
        Prefix: str,
        MaxKeys: int | None = None,
        ContinuationToken: str | None = None,
    ) -> dict[str, object]:
        del Bucket, MaxKeys, ContinuationToken
        keys = sorted(key for key in self.objects if key.startswith(Prefix))
        return {
            "Contents": [{"Key": key} for key in keys],
            "IsTruncated": False,
        }

    def delete_objects(self, *, Bucket: str, Delete: dict[str, object]) -> None:
        del Bucket
        for item in Delete.get("Objects", []):
            key = str(item["Key"])
            self.objects.pop(key, None)

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        del Bucket
        if Key not in self.objects:
            raise KeyError(Key)
        return {}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        del Bucket
        if Key not in self.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self.objects[Key])}

    def download_file(self, bucket: str, key: str, filename: str) -> None:
        del bucket
        Path(filename).write_bytes(self.objects[key])


class FakeRunpodClient:
    def __init__(self, s3: FakeS3Client, *, data_center_id: str = "US-IL-1") -> None:
        self.s3 = s3
        self.volume = {
            "id": "nv-123",
            "name": "bonsai",
            "dataCenterId": data_center_id,
        }
        self.endpoints: list[dict[str, object]] = []
        self.templates: list[dict[str, object]] = []
        self.created_templates: list[dict[str, object]] = []
        self.created_endpoints: list[dict[str, object]] = []
        self.jobs: dict[str, dict[str, object]] = {}
        self.submissions: list[dict[str, object]] = []

    def get_network_volumes(self) -> list[dict[str, object]]:
        return [self.volume]

    def get_endpoints(self) -> list[dict[str, object]]:
        return list(self.endpoints)

    def get_templates(self) -> list[dict[str, object]]:
        return list(self.templates)

    def create_template(self, **kwargs: object) -> dict[str, object]:
        self.created_templates.append(kwargs)
        template = {"id": "tpl-123", "name": kwargs["name"]}
        self.templates.append(template)
        return template

    def create_endpoint(self, **kwargs: object) -> dict[str, object]:
        self.created_endpoints.append(kwargs)
        endpoint = {"id": "ep-123", "name": kwargs["name"]}
        self.endpoints.append(endpoint)
        return endpoint

    def run_job(self, endpoint_id: str, request_input: dict[str, object]) -> dict[str, object]:
        payload = request_input["quadra"]
        run_id = str(payload["run_id"])
        workflow = str(payload["workflow"])
        job_id = f"job-{len(self.submissions) + 1}"
        self.submissions.append({"endpoint_id": endpoint_id, "payload": request_input})

        run_prefix = self.remote_key_prefix(str(payload["run_dir"]))
        self.s3.objects[posixpath.join(run_prefix, "stdout.log")] = (
            f"bonsai {workflow} remote\n".encode("utf-8")
        )
        self.s3.objects[posixpath.join(run_prefix, "stderr.log")] = b""
        self.s3.objects[posixpath.join(run_prefix, "status.json")] = json.dumps(
            {
                "run_id": run_id,
                "status": "completed",
                "exit_code": 0,
            }
        ).encode("utf-8")

        self.jobs[job_id] = {
            "id": job_id,
            "status": "COMPLETED",
            "output": {"run_id": run_id},
        }
        return {"id": job_id}

    def get_job(self, endpoint_id: str, job_id: str, *, source: str = "status") -> dict[str, object]:
        del endpoint_id, source
        return dict(self.jobs[job_id])

    @staticmethod
    def remote_key_prefix(run_dir: str) -> str:
        return str(PurePosixPath(run_dir).relative_to("/runpod-volume"))


class PollingFakeRunpodClient(FakeRunpodClient):
    def __init__(self, s3: FakeS3Client, *, data_center_id: str = "US-IL-1") -> None:
        super().__init__(s3, data_center_id=data_center_id)
        self.job_poll_counts: dict[str, int] = {}
        self.job_run_prefixes: dict[str, str] = {}
        self.job_workflows: dict[str, str] = {}
        self.job_run_ids: dict[str, str] = {}

    def run_job(self, endpoint_id: str, request_input: dict[str, object]) -> dict[str, object]:
        payload = request_input["quadra"]
        run_id = str(payload["run_id"])
        workflow = str(payload["workflow"])
        job_id = f"job-{len(self.submissions) + 1}"
        self.submissions.append({"endpoint_id": endpoint_id, "payload": request_input})

        self.job_poll_counts[job_id] = 0
        self.job_run_ids[job_id] = run_id
        self.job_workflows[job_id] = workflow
        self.job_run_prefixes[job_id] = self.remote_key_prefix(str(payload["run_dir"]))
        self.jobs[job_id] = {
            "id": job_id,
            "status": "IN_QUEUE",
            "output": {"run_id": run_id},
        }
        return {"id": job_id}

    def get_job(self, endpoint_id: str, job_id: str, *, source: str = "status") -> dict[str, object]:
        del endpoint_id, source
        poll_count = self.job_poll_counts[job_id]
        self.job_poll_counts[job_id] = poll_count + 1

        if poll_count == 0:
            status = "IN_QUEUE"
        elif poll_count == 1:
            status = "IN_PROGRESS"
        else:
            status = "COMPLETED"
            run_prefix = self.job_run_prefixes[job_id]
            workflow = self.job_workflows[job_id]
            run_id = self.job_run_ids[job_id]
            self.s3.objects[posixpath.join(run_prefix, "stdout.log")] = (
                f"bonsai {workflow} remote\n".encode("utf-8")
            )
            self.s3.objects[posixpath.join(run_prefix, "stderr.log")] = b""
            self.s3.objects[posixpath.join(run_prefix, "status.json")] = json.dumps(
                {
                    "run_id": run_id,
                    "status": "completed",
                    "exit_code": 0,
                }
            ).encode("utf-8")

        self.jobs[job_id]["status"] = status
        return dict(self.jobs[job_id])


class QuadraCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_build_endpoint_create_body_maps_quadra_fields_to_rest(self) -> None:
        body = build_endpoint_create_body(
            name="quadra-bonsai",
            template_id="tpl-123",
            gpu_ids="AMPERE_16",
            network_volume_id="nv-123",
            locations="US-IL-1",
            idle_timeout=5,
            scaler_type="QUEUE_DELAY",
            scaler_value=4,
            workers_min=0,
            workers_max=3,
            flashboot=False,
            allowed_cuda_versions=("12.4", "12.5"),
            gpu_count=1,
            timeout_seconds=600,
        )

        self.assertEqual(
            body.to_dict(),
            {
                "name": "quadra-bonsai",
                "templateId": "tpl-123",
                "gpuTypeIds": [
                    "NVIDIA RTX A4000",
                    "NVIDIA  RTX A4500",
                    "NVIDIA RTX 4000 Ada Generation",
                    "NVIDIA RTX 2000 Ada Generation",
                ],
                "networkVolumeId": "nv-123",
                "dataCenterIds": ["US-IL-1"],
                "idleTimeout": 5,
                "scalerType": "QUEUE_DELAY",
                "scalerValue": 4,
                "workersMin": 0,
                "workersMax": 3,
                "flashboot": False,
                "allowedCudaVersions": ["12.4", "12.5"],
                "gpuCount": 1,
                "executionTimeoutMs": 600000,
            },
        )

    def test_runpod_client_create_endpoint_uses_rest_create_timeout(self) -> None:
        class FakeRunpodModule:
            def __init__(self) -> None:
                self.api_key: str | None = None

        fake_runpod = FakeRunpodModule()
        client = RunpodClient(fake_runpod, "rp-key")
        captured: dict[str, object] = {}

        with patch.object(
            client.rest_client,
            "_request",
        ) as request:
            def fake_request(fn: object, *, invalid_response_message: str, **kwargs: object) -> object:
                del fn, invalid_response_message
                body = kwargs["body"]
                captured["payload"] = body.to_dict()
                return Endpoint.from_dict(
                    {
                        "id": "ep-rest",
                        "name": "quadra-bonsai",
                        "executionTimeoutMs": 600000,
                    }
                )

            request.side_effect = fake_request
            endpoint = client.create_endpoint(
                name="quadra-bonsai",
                template_id="tpl-123",
                gpu_ids="AMPERE_16",
                network_volume_id="nv-123",
                locations="US-IL-1",
                idle_timeout=5,
                scaler_type="QUEUE_DELAY",
                scaler_value=4,
                workers_min=0,
                workers_max=3,
                flashboot=False,
                allowed_cuda_versions=("12.4", "12.5"),
                gpu_count=1,
                timeout_seconds=600,
            )

        self.assertEqual(fake_runpod.api_key, "rp-key")
        self.assertEqual(
            captured["payload"],
            {
                "name": "quadra-bonsai",
                "templateId": "tpl-123",
                "gpuTypeIds": [
                    "NVIDIA RTX A4000",
                    "NVIDIA  RTX A4500",
                    "NVIDIA RTX 4000 Ada Generation",
                    "NVIDIA RTX 2000 Ada Generation",
                ],
                "networkVolumeId": "nv-123",
                "dataCenterIds": ["US-IL-1"],
                "idleTimeout": 5,
                "scalerType": "QUEUE_DELAY",
                "scalerValue": 4,
                "workersMin": 0,
                "workersMax": 3,
                "flashboot": False,
                "allowedCudaVersions": ["12.4", "12.5"],
                "gpuCount": 1,
                "executionTimeoutMs": 600000,
            },
        )
        self.assertEqual(endpoint["id"], "ep-rest")
        self.assertEqual(endpoint["executionTimeoutMs"], 600000)

    def test_runpod_client_update_endpoint_uses_rest_shape(self) -> None:
        class FakeRunpodModule:
            def __init__(self) -> None:
                self.api_key: str | None = None

        fake_runpod = FakeRunpodModule()
        client = RunpodClient(fake_runpod, "rp-key")
        captured: dict[str, object] = {}

        with patch.object(client.rest_client, "_request") as request:
            def fake_request(fn: object, *, invalid_response_message: str, **kwargs: object) -> object:
                del fn, invalid_response_message
                body = kwargs["body"]
                captured["payload"] = body.to_dict()
                return Endpoint.from_dict(
                    {
                        "id": "ep-rest",
                        "name": "quadra-bonsai",
                        "executionTimeoutMs": 90000,
                    }
                )

            request.side_effect = fake_request
            endpoint = client.update_endpoint(
                "ep-rest",
                gpu_ids="ADA_24",
                locations="US-IL-1,US-NC-1",
                timeout_seconds=90,
            )

        self.assertEqual(fake_runpod.api_key, "rp-key")
        self.assertEqual(
            captured["payload"],
            {
                "gpuTypeIds": ["NVIDIA GeForce RTX 4090"],
                "dataCenterIds": ["US-IL-1", "US-NC-1"],
                "executionTimeoutMs": 90000,
            },
        )
        self.assertEqual(endpoint["executionTimeoutMs"], 90000)

    def test_runpod_client_uses_rest_template_list(self) -> None:
        class FakeRunpodModule:
            def __init__(self) -> None:
                self.api_key: str | None = None

        fake_runpod = FakeRunpodModule()
        client = RunpodClient(fake_runpod, "rp-key")

        response = Response(
            status_code=HTTPStatus.OK,
            content=b"[]",
            headers={},
            parsed=[Template.from_dict({"id": "tpl-rest", "name": "quadra-template"})],
        )
        with patch("quadra.runpod_rest.list_templates_api.sync_detailed", return_value=response):
            templates = client.get_templates()

        self.assertEqual(fake_runpod.api_key, "rp-key")
        self.assertEqual(templates, [{"id": "tpl-rest", "name": "quadra-template"}])

    def test_runpod_client_uses_rest_template_create(self) -> None:
        class FakeRunpodModule:
            def __init__(self) -> None:
                self.api_key: str | None = None

        fake_runpod = FakeRunpodModule()
        client = RunpodClient(fake_runpod, "rp-key")
        captured: dict[str, object] = {}

        with patch.object(client.rest_client, "_request") as request:
            def fake_request(fn: object, *, invalid_response_message: str, **kwargs: object) -> object:
                del fn, invalid_response_message
                body = kwargs["body"]
                captured["payload"] = body.to_dict()
                return Template.from_dict({"id": "tpl-rest", "name": "quadra-worker"})

            request.side_effect = fake_request
            template = client.create_template(
                name="quadra-worker",
                image_name="runpod/base:0.6.1-cuda12.4.1",
                ports=("8080/http",),
                docker_entrypoint=("python",),
                docker_start_cmd=("python", "-u", "/runpod-volume/projects/bonsai/quadra_worker.py"),
                env={"FOO": "bar"},
                container_disk_gb=20,
                readme="Managed by Quadra.",
            )

        self.assertEqual(fake_runpod.api_key, "rp-key")
        self.assertEqual(
            captured["payload"],
            {
                "name": "quadra-worker",
                "imageName": "runpod/base:0.6.1-cuda12.4.1",
                "isServerless": True,
                "containerDiskInGb": 20,
                "ports": ["8080/http"],
                "dockerEntrypoint": ["python"],
                "dockerStartCmd": [
                    "python",
                    "-u",
                    "/runpod-volume/projects/bonsai/quadra_worker.py",
                ],
                "env": {"FOO": "bar"},
                "readme": "Managed by Quadra.",
            },
        )
        self.assertEqual(template["id"], "tpl-rest")

    def test_resolve_runpod_volume_uses_rest_network_volume_list(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(result.exit_code, 0, result.output)

            with chdir("bonsai"):
                config = load_project()
                volume = resolve_runpod_volume(config, FakeRunpodClient(FakeS3Client()))

        self.assertEqual(volume.id, "nv-123")
        self.assertEqual(volume.name, "bonsai")
        self.assertEqual(volume.data_center_id, "US-IL-1")

    def test_no_args_prints_plain_banner_before_help(self) -> None:
        result = self.runner.invoke(cli, [])

        self.assertEqual(result.exit_code, 2)
        self.assertNotIn("\033[", result.output)
        self.assertTrue(result.output.startswith(load_banner_text(color=False)))
        self.assertIn("        QUADRA", result.output)
        self.assertIn("        accelerate remote GPU development", result.output)
        self.assertIn("Usage:", result.output)
        self.assertIn("Commands:", result.output)

    def test_explicit_help_does_not_print_banner(self) -> None:
        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.output.startswith(load_banner_text(color=False)))
        self.assertIn("Usage:", result.output)

    def test_init_creates_serverless_contract(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(result.exit_code, 0, result.output)

            project_root = Path("bonsai")
            config = (project_root / "quadra.toml").read_text(encoding="utf-8")
            self.assertIn('project_dir = "/runpod-volume/projects/bonsai"', config)
            self.assertIn('endpoint_name = "quadra-bonsai"', config)
            self.assertIn('[runtime.runpod.template]', config)
            self.assertIn('name = "quadra-bonsai-worker"', config)
            self.assertIn(
                'docker_start_cmd = ["python", "-u", "{worker_path}"]',
                config,
            )
            self.assertIn("# Valid serverless gpu_ids pool IDs:", config)
            self.assertIn('#   ADA_24        24 GB    RTX 4090', config)
            self.assertIn(
                '#   ADA_32_PRO    32 GB    RTX 5000 Ada, RTX PRO 4500 Blackwell',
                config,
            )
            self.assertTrue((project_root / ".quadra").exists())
            self.assertTrue((project_root / "quadra_worker.py").exists())
            self.assertTrue((project_root / "src" / "experiment" / "scripts" / "smoke.py").exists())

    def test_init_without_name_uses_current_directory_name(self) -> None:
        with self.runner.isolated_filesystem():
            project_root = Path("bonsai")
            project_root.mkdir()
            (project_root / "README.md").write_text("# bonsai\n", encoding="utf-8")

            with chdir(project_root):
                result = self.runner.invoke(cli, ["init"])
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("initialized bonsai", result.output)
                self.assertIn('name = "bonsai"', Path("quadra.toml").read_text(encoding="utf-8"))
                self.assertEqual(Path("README.md").read_text(encoding="utf-8"), "# bonsai\n")

    def test_sync_errors_when_volume_datacenter_has_no_s3_support(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_client = FakeRunpodClient(FakeS3Client(), data_center_id="US-KS-1")

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    result = self.runner.invoke(cli, ["sync"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("does not currently support the RunPod S3 API", result.output)

    def test_submit_requires_sync_first(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        result = self.runner.invoke(cli, ["submit", "smoke"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Run `quadra sync` first", result.output)

    def test_sync_submit_logs_and_pull_flow(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        sync_result = self.runner.invoke(cli, ["sync"])
                        self.assertEqual(sync_result.exit_code, 0, sync_result.output)
                        self.assertIn("synced bonsai -> /runpod-volume/projects/bonsai", sync_result.output)
                        self.assertIn("projects/bonsai/quadra.toml", "\n".join(sorted(fake_s3.objects)))

                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])
                        self.assertEqual(submit_result.exit_code, 0, submit_result.output)
                        self.assertIn("submitted smoke", submit_result.output)
                        self.assertIn("endpoint_id: ep-123", submit_result.output)
                        self.assertTrue(Path(".quadra/last-run.json").exists())
                        self.assertEqual(len(fake_client.created_templates), 1)
                        self.assertEqual(len(fake_client.created_endpoints), 1)
                        self.assertEqual(
                            fake_client.created_templates[0]["docker_start_cmd"],
                            (
                                "python",
                                "-u",
                                "/runpod-volume/projects/bonsai/quadra_worker.py",
                            ),
                        )
                        self.assertEqual(
                            fake_client.created_endpoints[0]["timeout_seconds"], 600
                        )

                        logs_result = self.runner.invoke(cli, ["logs", "--no-follow"])
                        self.assertEqual(logs_result.exit_code, 0, logs_result.output)
                        self.assertIn("bonsai smoke remote", logs_result.output)
                        self.assertIn("status: COMPLETED", logs_result.output)

                        pull_result = self.runner.invoke(cli, ["pull"])
                        self.assertEqual(pull_result.exit_code, 0, pull_result.output)
                        pulled_path = Path(pull_result.output.strip().splitlines()[-1])
                        self.assertTrue((pulled_path / "stdout.log").exists())
                        self.assertEqual(
                            (pulled_path / "stdout.log").read_text(encoding="utf-8"),
                            "bonsai smoke remote\n",
                        )

    def test_smoke_reports_polling_progress(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = PollingFakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch("quadra.cli.time.sleep", return_value=None):
                            result = self.runner.invoke(cli, ["smoke"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("polling RunPod job status and remote logs...", result.output)
            self.assertIn("[quadra] smoke: queued on RunPod", result.output)
            self.assertIn(
                "[quadra] smoke: worker running, waiting for remote logs",
                result.output,
            )
            self.assertIn("[quadra] smoke: completed", result.output)
            self.assertIn("pulling artifacts for", result.output)

    def test_submit_accepts_legacy_top_level_template_id(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                config_path = Path("quadra.toml")
                config = config_path.read_text(encoding="utf-8")
                config_path.write_text(
                    config.replace(
                        'endpoint_name = "quadra-bonsai"',
                        'endpoint_name = "quadra-bonsai"\ntemplate_id = "tpl-existing"',
                    ),
                    encoding="utf-8",
                )

                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        sync_result = self.runner.invoke(cli, ["sync"])
                        self.assertEqual(sync_result.exit_code, 0, sync_result.output)

                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])
                        self.assertEqual(submit_result.exit_code, 0, submit_result.output)
                        self.assertEqual(len(fake_client.created_templates), 0)
                        self.assertEqual(
                            fake_client.created_endpoints[0]["template_id"],
                            "tpl-existing",
                        )

if __name__ == "__main__":
    unittest.main()
