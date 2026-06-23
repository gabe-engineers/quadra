from __future__ import annotations

import io
import json
import os
import posixpath
import re
import unittest
from contextlib import chdir
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from click.testing import CliRunner
import httpx
from botocore.exceptions import ClientError

from quadra._generated.runpod_rest_client.errors import UnexpectedStatus
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
        self.upload_calls: list[str] = []
        self.put_object_calls: list[str] = []

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        del bucket
        self.upload_calls.append(key)
        self.objects[key] = Path(filename).read_bytes()

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str | None = None,
    ) -> None:
        del Bucket, ContentType
        self.put_object_calls.append(Key)
        self.objects[Key] = Body

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

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        del Bucket
        self.objects.pop(Key, None)

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
        self.volumes: list[dict[str, object]] = [self.volume]
        self.endpoints: list[dict[str, object]] = []
        self.templates: list[dict[str, object]] = []
        self.created_network_volumes: list[dict[str, object]] = []
        self.created_templates: list[dict[str, object]] = []
        self.updated_templates: list[dict[str, object]] = []
        self.created_endpoints: list[dict[str, object]] = []
        self.updated_endpoints: list[dict[str, object]] = []
        self.deleted_endpoints: list[str] = []
        self.jobs: dict[str, dict[str, object]] = {}
        self.submissions: list[dict[str, object]] = []

    def get_network_volumes(self) -> list[dict[str, object]]:
        return list(self.volumes)

    def create_network_volume(
        self, *, name: str, data_center_id: str, size_gb: int
    ) -> dict[str, object]:
        volume = {
            "id": f"nv-{len(self.created_network_volumes) + 1}",
            "name": name,
            "dataCenterId": data_center_id,
            "size": size_gb,
        }
        self.created_network_volumes.append(volume)
        self.volumes.append(volume)
        self.volume = volume
        return volume

    def get_endpoints(self) -> list[dict[str, object]]:
        return list(self.endpoints)

    def get_templates(self) -> list[dict[str, object]]:
        return list(self.templates)

    def create_template(self, **kwargs: object) -> dict[str, object]:
        self.created_templates.append(kwargs)
        template = {
            "id": "tpl-123",
            "name": kwargs["name"],
            "imageName": kwargs["image_name"],
            "ports": list(kwargs["ports"]),
            "dockerEntrypoint": list(kwargs["docker_entrypoint"]),
            "dockerStartCmd": list(kwargs["docker_start_cmd"]),
            "volumeMountPath": kwargs["volume_mount_path"],
            "env": dict(kwargs["env"]),
            "containerDiskInGb": kwargs["container_disk_gb"],
            "readme": kwargs["readme"],
        }
        self.templates.append(template)
        return template

    def get_template(self, template_id: str) -> dict[str, object]:
        for template in self.templates:
            if template["id"] == template_id:
                return dict(template)
        raise KeyError(template_id)

    def update_template(self, template_id: str, **kwargs: object) -> dict[str, object]:
        update = {"template_id": template_id, **kwargs}
        self.updated_templates.append(update)
        for template in self.templates:
            if template["id"] == template_id:
                template.update(
                    {
                        "name": kwargs["name"],
                        "imageName": kwargs["image_name"],
                        "ports": list(kwargs["ports"]),
                        "dockerEntrypoint": list(kwargs["docker_entrypoint"]),
                        "dockerStartCmd": list(kwargs["docker_start_cmd"]),
                        "volumeMountPath": kwargs["volume_mount_path"],
                        "env": dict(kwargs["env"]),
                        "containerDiskInGb": kwargs["container_disk_gb"],
                        "readme": kwargs["readme"],
                    }
                )
                return dict(template)
        raise KeyError(template_id)

    def create_endpoint(self, **kwargs: object) -> dict[str, object]:
        self.created_endpoints.append(kwargs)
        endpoint = {
            "id": "ep-123",
            "name": kwargs["name"],
            "templateId": kwargs["template_id"],
            "networkVolumeId": kwargs["network_volume_id"],
        }
        self.endpoints.append(endpoint)
        return endpoint

    def update_endpoint(self, endpoint_id: str, **kwargs: object) -> dict[str, object]:
        update = {"endpoint_id": endpoint_id, **kwargs}
        self.updated_endpoints.append(update)
        for endpoint in self.endpoints:
            if endpoint["id"] == endpoint_id:
                if "template_id" in kwargs:
                    endpoint["templateId"] = kwargs["template_id"]
                if "network_volume_id" in kwargs:
                    endpoint["networkVolumeId"] = kwargs["network_volume_id"]
                return dict(endpoint)
        raise KeyError(endpoint_id)

    def delete_endpoint(self, endpoint_id: str) -> None:
        self.deleted_endpoints.append(endpoint_id)
        self.endpoints = [
            endpoint for endpoint in self.endpoints if endpoint["id"] != endpoint_id
        ]

    def get_endpoint(
        self, endpoint_id: str, *, include_workers: bool = False
    ) -> dict[str, object]:
        for endpoint in self.endpoints:
            if endpoint["id"] == endpoint_id:
                payload = dict(endpoint)
                if include_workers and "workers" not in payload:
                    payload["workers"] = []
                return payload
        raise KeyError(endpoint_id)

    def run_job(self, endpoint_id: str, request_input: dict[str, object]) -> dict[str, object]:
        payload = request_input["quadra"]
        run_id = str(payload["run_id"])
        workflow = str(payload["workflow"])
        job_id = f"job-{len(self.submissions) + 1}"
        self.submissions.append({"endpoint_id": endpoint_id, "payload": request_input})

        run_prefix = self.remote_key_prefix(str(payload["run_dir"]))
        self.write_run_outputs(run_prefix, run_id=run_id, workflow=workflow)

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

    def write_run_outputs(
        self,
        run_prefix: str,
        *,
        run_id: str,
        workflow: str,
        include_manifest: bool = True,
    ) -> None:
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
        self.s3.objects[posixpath.join(run_prefix, "artifacts", "result.txt")] = (
            f"{workflow} artifact\n".encode("utf-8")
        )
        if include_manifest:
            self.s3.objects[posixpath.join(run_prefix, "run-manifest.json")] = json.dumps(
                {
                    "run_id": run_id,
                    "status": "completed",
                    "files": [
                        "artifacts/result.txt",
                        "status.json",
                        "stderr.log",
                        "stdout.log",
                    ],
                }
            ).encode("utf-8")


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
            self.write_run_outputs(run_prefix, run_id=run_id, workflow=workflow)

        self.jobs[job_id]["status"] = status
        return dict(self.jobs[job_id])


class BootstrapLoggingPollingFakeRunpodClient(PollingFakeRunpodClient):
    def run_job(self, endpoint_id: str, request_input: dict[str, object]) -> dict[str, object]:
        response = super().run_job(endpoint_id, request_input)
        self.s3.objects["projects/bonsai/.quadra/worker-bootstrap.log"] = (
            b"[runpod bootstrap] started 2026-06-19T03:50:54Z\n"
            b"[runpod bootstrap] python package 'runpod' already available\n"
        )
        return response


class RedirectingDeleteFakeS3Client(FakeS3Client):
    def delete_objects(self, *, Bucket: str, Delete: dict[str, object]) -> None:
        del Bucket, Delete
        raise ClientError(
            {
                "Error": {
                    "Code": "307",
                    "Message": "Temporary Redirect",
                }
            },
            "DeleteObjects",
        )


class NoListFakeS3Client(FakeS3Client):
    def list_objects_v2(
        self,
        *,
        Bucket: str,
        Prefix: str,
        MaxKeys: int | None = None,
        ContinuationToken: str | None = None,
    ) -> dict[str, object]:
        del Bucket, Prefix, MaxKeys, ContinuationToken
        raise AssertionError("list_objects_v2 should not be used for run artifact pulls")


class ManifestlessPollingFakeRunpodClient(PollingFakeRunpodClient):
    def write_run_outputs(
        self,
        run_prefix: str,
        *,
        run_id: str,
        workflow: str,
        include_manifest: bool = True,
    ) -> None:
        super().write_run_outputs(
            run_prefix,
            run_id=run_id,
            workflow=workflow,
            include_manifest=False,
        )


class UnhealthyQueuedFakeRunpodClient(FakeRunpodClient):
    def run_job(self, endpoint_id: str, request_input: dict[str, object]) -> dict[str, object]:
        del request_input
        job_id = f"job-{len(self.submissions) + 1}"
        self.submissions.append({"endpoint_id": endpoint_id})
        self.jobs[job_id] = {
            "id": job_id,
            "status": "IN_QUEUE",
        }
        return {"id": job_id}

    def get_job(self, endpoint_id: str, job_id: str, *, source: str = "status") -> dict[str, object]:
        del endpoint_id, source
        return dict(self.jobs[job_id])

    def get_endpoint(
        self, endpoint_id: str, *, include_workers: bool = False
    ) -> dict[str, object]:
        endpoint = super().get_endpoint(endpoint_id, include_workers=include_workers)
        endpoint["workers"] = [
            {
                "id": "worker-1",
                "desiredStatus": "TERMINATED",
                "lastStatusChange": (
                    "IMAGE_AUTH_ERROR: unauthorized: repository is private or does not exist"
                ),
            }
        ]
        return endpoint


class StuckQueuedFakeRunpodClient(FakeRunpodClient):
    def run_job(self, endpoint_id: str, request_input: dict[str, object]) -> dict[str, object]:
        del request_input
        job_id = f"job-{len(self.submissions) + 1}"
        self.submissions.append({"endpoint_id": endpoint_id})
        self.jobs[job_id] = {
            "id": job_id,
            "status": "IN_QUEUE",
        }
        return {"id": job_id}

    def get_job(self, endpoint_id: str, job_id: str, *, source: str = "status") -> dict[str, object]:
        del endpoint_id, source
        return dict(self.jobs[job_id])


class ExitedWorkerPollingFakeRunpodClient(PollingFakeRunpodClient):
    def get_endpoint(
        self, endpoint_id: str, *, include_workers: bool = False
    ) -> dict[str, object]:
        endpoint = super().get_endpoint(endpoint_id, include_workers=include_workers)
        endpoint["workers"] = [
            {
                "id": "worker-1",
                "desiredStatus": "EXITED",
                "lastStatusChange": "Exited by Runpod: Fri Jun 19 2026 03:36:49 GMT+0000",
            }
        ]
        return endpoint


class QuadraCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.env_patcher = patch.dict(
            os.environ,
            {"QUADRA_CONFIG": str(Path.cwd() / ".quadra-test-global.toml")},
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

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
            workers_max=1,
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
                "workersMax": 1,
                "flashboot": False,
                "allowedCudaVersions": ["12.4", "12.5"],
                "gpuCount": 1,
                "executionTimeoutMs": 600000,
            },
        )

    def test_runpod_client_create_endpoint_uses_rest_create_timeout(self) -> None:
        client = RunpodClient("rp-key")
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
                workers_max=1,
                flashboot=False,
                allowed_cuda_versions=("12.4", "12.5"),
                gpu_count=1,
                timeout_seconds=600,
            )

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
                "workersMax": 1,
                "flashboot": False,
                "allowedCudaVersions": ["12.4", "12.5"],
                "gpuCount": 1,
                "executionTimeoutMs": 600000,
            },
        )
        self.assertEqual(endpoint["id"], "ep-rest")
        self.assertEqual(endpoint["executionTimeoutMs"], 600000)

    def test_runpod_client_get_endpoint_uses_raw_json_shape(self) -> None:
        client = RunpodClient("rp-key")
        httpx_client = client.rest_client._client.get_httpx_client()

        with patch.object(
            httpx_client,
            "request",
            return_value=httpx.Response(
                HTTPStatus.OK,
                json={
                    "id": "ep-123",
                    "networkVolumeIds": ["nv-123"],
                    "workers": [{"id": "worker-1", "desiredStatus": "RUNNING"}],
                },
            ),
        ) as request:
            endpoint = client.get_endpoint("ep-123", include_workers=True)

        request.assert_called_once_with(
            "GET",
            "/endpoints/ep-123",
            params={"includeWorkers": True},
        )
        self.assertEqual(endpoint["id"], "ep-123")
        self.assertEqual(endpoint["networkVolumeIds"], ["nv-123"])

    def test_runpod_client_get_endpoints_uses_raw_json_shape(self) -> None:
        client = RunpodClient("rp-key")
        httpx_client = client.rest_client._client.get_httpx_client()

        with patch.object(
            httpx_client,
            "request",
            return_value=httpx.Response(
                HTTPStatus.OK,
                json=[
                    {
                        "id": "ep-123",
                        "name": "quadra-bonsai",
                        "networkVolumeIds": ["nv-123"],
                    }
                ],
            ),
        ) as request:
            endpoints = client.get_endpoints()

        request.assert_called_once_with("GET", "/endpoints", params=None)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0]["networkVolumeIds"], ["nv-123"])

    def test_runpod_client_update_endpoint_uses_rest_shape(self) -> None:
        client = RunpodClient("rp-key")
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
        client = RunpodClient("rp-key")

        response = Response(
            status_code=HTTPStatus.OK,
            content=b"[]",
            headers={},
            parsed=[Template.from_dict({"id": "tpl-rest", "name": "quadra-template"})],
        )
        with patch("quadra.runpod_rest.list_templates_api.sync_detailed", return_value=response):
            templates = client.get_templates()

        self.assertEqual(templates, [{"id": "tpl-rest", "name": "quadra-template"}])

    def test_runpod_client_run_job_uses_endpoint_http_api(self) -> None:
        client = RunpodClient("rp-key")

        def fake_request(
            method: str,
            url: str,
            *,
            headers: dict[str, str],
            json: dict[str, object] | None,
            timeout: int,
        ) -> object:
            self.assertEqual(method, "POST")
            self.assertEqual(url, "https://api.runpod.ai/v2/ep-123/run")
            self.assertEqual(headers["Authorization"], "Bearer rp-key")
            self.assertEqual(json, {"input": {"quadra": {"workflow": "smoke"}}})
            self.assertEqual(timeout, 10)
            return type(
                "Response",
                (),
                {
                    "status_code": HTTPStatus.OK,
                    "text": '{"id":"job-123"}',
                    "reason_phrase": "OK",
                    "json": lambda self: {"id": "job-123"},
                },
            )()

        with patch("quadra.cli.httpx.request", side_effect=fake_request):
            job = client.run_job("ep-123", {"quadra": {"workflow": "smoke"}})

        self.assertEqual(job, {"id": "job-123"})

    def test_runpod_client_get_job_uses_endpoint_http_api(self) -> None:
        client = RunpodClient("rp-key")

        def fake_request(
            method: str,
            url: str,
            *,
            headers: dict[str, str],
            json: dict[str, object] | None,
            timeout: int,
        ) -> object:
            self.assertEqual(method, "GET")
            self.assertEqual(url, "https://api.runpod.ai/v2/ep-123/status/job-123")
            self.assertEqual(headers["Authorization"], "Bearer rp-key")
            self.assertIsNone(json)
            self.assertEqual(timeout, 10)
            return type(
                "Response",
                (),
                {
                    "status_code": HTTPStatus.OK,
                    "text": '{"id":"job-123","status":"IN_QUEUE"}',
                    "reason_phrase": "OK",
                    "json": lambda self: {"id": "job-123", "status": "IN_QUEUE"},
                },
            )()

        with patch("quadra.cli.httpx.request", side_effect=fake_request):
            job = client.get_job("ep-123", "job-123")

        self.assertEqual(job, {"id": "job-123", "status": "IN_QUEUE"})

    def test_runpod_client_uses_rest_template_create(self) -> None:
        client = RunpodClient("rp-key")
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
                image_name="pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                ports=("8080/http",),
                docker_entrypoint=("python",),
                docker_start_cmd=(
                    "python",
                    "-u",
                    "/runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                ),
                volume_mount_path="/runpod-volume",
                env={"FOO": "bar"},
                container_disk_gb=20,
                readme="Managed by Quadra.",
            )

        self.assertEqual(
            captured["payload"],
            {
                "name": "quadra-worker",
                "imageName": "pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                "isServerless": True,
                "containerDiskInGb": 20,
                "ports": ["8080/http"],
                "dockerEntrypoint": ["python"],
                "dockerStartCmd": [
                    "python",
                    "-u",
                    "/runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                ],
                "volumeMountPath": "/runpod-volume",
                "env": {"FOO": "bar"},
                "readme": "Managed by Quadra.",
            },
        )
        self.assertEqual(template["id"], "tpl-rest")

    def test_runpod_client_accepts_http_201_for_template_create(self) -> None:
        client = RunpodClient("rp-key")

        with patch(
            "quadra.runpod_rest.create_template_api.sync_detailed",
            side_effect=UnexpectedStatus(
                HTTPStatus.CREATED,
                json.dumps({"id": "tpl-rest", "name": "quadra-worker"}).encode("utf-8"),
            ),
        ):
            template = client.create_template(
                name="quadra-worker",
                image_name="pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                ports=("8080/http",),
                docker_entrypoint=("python",),
                docker_start_cmd=(
                    "python",
                    "-u",
                    "/runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                ),
                volume_mount_path="/runpod-volume",
                env={"FOO": "bar"},
                container_disk_gb=20,
                readme="Managed by Quadra.",
            )

        self.assertEqual(template["id"], "tpl-rest")

    def test_runpod_client_uses_rest_template_update(self) -> None:
        client = RunpodClient("rp-key")
        captured: dict[str, object] = {}

        with patch.object(client.rest_client, "_request") as request:
            def fake_request(fn: object, *, invalid_response_message: str, **kwargs: object) -> object:
                del fn, invalid_response_message
                body = kwargs["body"]
                captured["template_id"] = kwargs["template_id"]
                captured["payload"] = body.to_dict()
                return Template.from_dict({"id": "tpl-rest", "name": "quadra-worker"})

            request.side_effect = fake_request
            template = client.update_template(
                "tpl-rest",
                name="quadra-worker",
                image_name="pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                ports=("8080/http",),
                docker_entrypoint=("python",),
                docker_start_cmd=(
                    "python",
                    "-u",
                    "/runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                ),
                volume_mount_path="/runpod-volume",
                env={"FOO": "bar"},
                container_disk_gb=20,
                readme="Managed by Quadra.",
            )

        self.assertEqual(captured["template_id"], "tpl-rest")
        self.assertEqual(
            captured["payload"],
            {
                "name": "quadra-worker",
                "imageName": "pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                "containerDiskInGb": 20,
                "ports": ["8080/http"],
                "dockerEntrypoint": ["python"],
                "dockerStartCmd": [
                    "python",
                    "-u",
                    "/runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                ],
                "volumeMountPath": "/runpod-volume",
                "env": {"FOO": "bar"},
                "readme": "Managed by Quadra.",
            },
        )
        self.assertEqual(template["id"], "tpl-rest")

    def test_runpod_client_create_network_volume_uses_rest_shape(self) -> None:
        client = RunpodClient("rp-key")
        captured: dict[str, object] = {}

        with patch.object(client.rest_client, "_request") as request:
            def fake_request(
                fn: object, *, invalid_response_message: str, **kwargs: object
            ) -> object:
                del fn, invalid_response_message
                body = kwargs["body"]
                captured["payload"] = body.to_dict()
                return type(
                    "NetworkVolumeResponse",
                    (),
                    {
                        "to_dict": lambda self: {
                            "id": "nv-rest",
                            "name": "bonsai",
                            "dataCenterId": "US-IL-1",
                            "size": 50,
                        }
                    },
                )()

            request.side_effect = fake_request
            volume = client.create_network_volume(
                name="bonsai",
                data_center_id="US-IL-1",
                size_gb=50,
            )

        self.assertEqual(
            captured["payload"],
            {
                "dataCenterId": "US-IL-1",
                "name": "bonsai",
                "size": 50,
            },
        )
        self.assertEqual(volume["id"], "nv-rest")

    def test_runpod_client_accepts_http_201_for_network_volume_create(self) -> None:
        client = RunpodClient("rp-key")

        with patch(
            "quadra.runpod_rest.create_network_volume_api.sync_detailed",
            side_effect=UnexpectedStatus(
                HTTPStatus.CREATED,
                json.dumps(
                    {
                        "id": "nv-rest",
                        "name": "bonsai",
                        "dataCenterId": "US-IL-1",
                        "size": 50,
                    }
                ).encode("utf-8"),
            ),
        ):
            volume = client.create_network_volume(
                name="bonsai",
                data_center_id="US-IL-1",
                size_gb=50,
            )

        self.assertEqual(volume["id"], "nv-rest")

    def test_runpod_client_accepts_http_201_for_endpoint_create(self) -> None:
        client = RunpodClient("rp-key")

        with patch(
            "quadra.runpod_rest.create_endpoint_api.sync_detailed",
            side_effect=UnexpectedStatus(
                HTTPStatus.CREATED,
                json.dumps(
                    {
                        "id": "ep-rest",
                        "name": "quadra-bonsai",
                        "executionTimeoutMs": 600000,
                    }
                ).encode("utf-8"),
            ),
        ):
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
                workers_max=1,
                flashboot=False,
                allowed_cuda_versions=(),
                gpu_count=1,
                timeout_seconds=600,
            )

        self.assertEqual(endpoint["id"], "ep-rest")

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
            self.assertIn("workers_max = 1", config)
            self.assertIn('[runtime.runpod.template]', config)
            self.assertIn('name = "quadra-bonsai-serverless-worker"', config)
            self.assertIn(
                'setup_command = "uv_runtime_path=\\"{project_dir}/.quadra/uv-runtime\\"',
                config,
            )
            self.assertIn(
                'image_name = "pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime"',
                config,
            )
            self.assertIn(
                'cd \\"{experiment_dir}\\" && \\"$(command -v uv)\\" sync',
                config,
            )
            self.assertIn(
                'cd \\"{experiment_dir}\\" && \\"$uv_python\\" -m uv sync',
                config,
            )
            self.assertIn(
                'PYTHONPATH=\\"$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}\\" python -m uv sync',
                config,
            )
            self.assertIn(
                'docker_start_cmd = ["/bin/sh", "-lc", "worker_path=\\"{worker_path}\\"',
                config,
            )
            self.assertIn(
                'bootstrap_log=\\"{worker_bootstrap_log_path}\\"',
                config,
            )
            self.assertIn(
                'worker_runtime_path=\\"{worker_runtime_path}\\"',
                config,
            )
            self.assertIn(
                "creating isolated worker runtime",
                config,
            )
            self.assertIn(
                "installing python package 'runpod' into isolated worker runtime",
                config,
            )
            self.assertIn(
                'exec \\"$worker_python\\" -u \\"$worker_path\\"',
                config,
            )
            self.assertIn('smoke = "python main.py"', config)
            self.assertIn('main = "python main.py"', config)
            self.assertIn("# Valid serverless gpu_ids pool IDs:", config)
            self.assertIn('#   ADA_24        24 GB    RTX 4090', config)
            self.assertIn(
                '#   ADA_32_PRO    32 GB    RTX 5000 Ada, RTX PRO 4500 Blackwell',
                config,
            )
            self.assertTrue((project_root / ".quadra").exists())
            self.assertTrue((project_root / "quadra_worker.py").exists())
            self.assertFalse((project_root / "src" / "experiment" / "scripts").exists())

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

    def test_global_config_supplies_shared_runpod_backend(self) -> None:
        with self.runner.isolated_filesystem():
            global_config = Path("global-quadra.toml").resolve()
            global_config.write_text(
                "\n".join(
                    [
                        "[runpod]",
                        'api_key_env = "RUNPOD_API_KEY"',
                        'default_data_center_id = "US-IL-1"',
                        "",
                        "[runpod.network_volume]",
                        'name = "quadra-dev"',
                        "size_gb = 80",
                        'mount_path = "/runpod-volume"',
                        "",
                        "[runpod.serverless]",
                        'endpoint_name = "quadra-dev"',
                        'gpu_ids = "ADA_24"',
                        "workers_max = 1",
                        "timeout_seconds = 900",
                        "",
                        "[runpod.template]",
                        'name = "quadra-dev-serverless-worker"',
                        'image_name = "custom/image:latest"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            project_root = Path("bonsai")
            (project_root / "src" / "experiment").mkdir(parents=True)
            (project_root / "quadra.toml").write_text(
                "\n".join(
                    [
                        "[project]",
                        'name = "bonsai"',
                        "",
                        "[commands]",
                        'smoke = "python main.py"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (project_root / "src" / "experiment" / "main.py").write_text(
                "print('ok')\n",
                encoding="utf-8",
            )
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            fake_client.volume["name"] = "quadra-dev"

            with patch.dict(os.environ, {"QUADRA_CONFIG": str(global_config)}):
                with chdir(project_root):
                    config = load_project()
                    self.assertEqual(config.runtime.runpod.network_volume_name, "quadra-dev")
                    self.assertEqual(config.runtime.runpod.endpoint_name, "quadra-dev")
                    self.assertEqual(
                        config.runtime.runpod.template.name,
                        "quadra-dev-serverless-worker",
                    )
                    self.assertEqual(config.runtime.runpod.template.image_name, "custom/image:latest")
                    self.assertEqual(config.runtime.runpod.network_volume_size_gb, 80)

                    with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                        with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                            sync_result = self.runner.invoke(cli, ["sync"])
                            submit_result = self.runner.invoke(cli, ["submit", "smoke"])

            self.assertEqual(sync_result.exit_code, 0, sync_result.output)
            self.assertEqual(submit_result.exit_code, 0, submit_result.output)
            self.assertEqual(fake_client.created_templates[0]["name"], "quadra-dev-serverless-worker")
            self.assertEqual(fake_client.created_templates[0]["image_name"], "custom/image:latest")
            self.assertIn(
                "/runpod-volume/.quadra/quadra_worker.py",
                fake_client.created_templates[0]["docker_start_cmd"][2],
            )
            self.assertEqual(fake_client.created_endpoints[0]["name"], "quadra-dev")
            self.assertIn(".quadra/quadra_worker.py", fake_s3.objects)

    def test_init_uses_lean_project_config_when_global_config_exists(self) -> None:
        with self.runner.isolated_filesystem():
            global_config = Path("global-quadra.toml").resolve()
            global_config.write_text(
                "\n".join(
                    [
                        "[runpod.network_volume]",
                        'name = "quadra-dev"',
                        "",
                        "[runpod.serverless]",
                        'endpoint_name = "quadra-dev"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"QUADRA_CONFIG": str(global_config)}):
                result = self.runner.invoke(cli, ["init", "bonsai"])

            self.assertEqual(result.exit_code, 0, result.output)
            config = Path("bonsai/quadra.toml").read_text(encoding="utf-8")
            self.assertIn("[project]", config)
            self.assertIn("[paths]", config)
            self.assertIn("[commands]", config)
            self.assertNotIn("[runtime.runpod]", config)
            self.assertNotIn("endpoint_name", config)
            self.assertNotIn("network_volume_name", config)

    def test_configure_creates_global_config(self) -> None:
        with self.runner.isolated_filesystem():
            global_config = Path("global-quadra.toml").resolve()

            with patch.dict(os.environ, {"QUADRA_CONFIG": str(global_config)}):
                result = self.runner.invoke(cli, ["configure"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(f"wrote global config: {global_config}", result.output)
            config = global_config.read_text(encoding="utf-8")
            self.assertIn("[runpod]", config)
            self.assertIn('api_key_env = "RUNPOD_API_KEY"', config)
            self.assertIn("[runpod.network_volume]", config)
            self.assertIn('name = "quadra-dev"', config)
            self.assertIn("size_gb = 50", config)
            self.assertIn("[runpod.serverless]", config)
            self.assertIn("workers_max = 1", config)
            self.assertIn("[runpod.template]", config)
            self.assertIn('name = "quadra-dev-serverless-worker"', config)

    def test_configure_refuses_existing_global_config_without_force(self) -> None:
        with self.runner.isolated_filesystem():
            global_config = Path("global-quadra.toml").resolve()
            global_config.write_text("# keep\n", encoding="utf-8")

            with patch.dict(os.environ, {"QUADRA_CONFIG": str(global_config)}):
                result = self.runner.invoke(cli, ["configure"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("already exists", result.output)
            self.assertEqual(global_config.read_text(encoding="utf-8"), "# keep\n")

    def test_configure_force_writes_custom_values(self) -> None:
        with self.runner.isolated_filesystem():
            global_config = Path("global-quadra.toml").resolve()
            global_config.write_text("# old\n", encoding="utf-8")

            result = self.runner.invoke(
                cli,
                [
                    "configure",
                    "--path",
                    str(global_config),
                    "--force",
                    "--volume-name",
                    "quadra-shared",
                    "--endpoint-name",
                    "quadra-shared",
                    "--template-name",
                    "quadra-shared-template",
                    "--gpu-ids",
                    "ADA_24",
                    "--volume-size-gb",
                    "80",
                    "--timeout-seconds",
                    "900",
                    "--image-name",
                    "custom/image:latest",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            config = global_config.read_text(encoding="utf-8")
            self.assertIn('name = "quadra-shared"', config)
            self.assertIn('endpoint_name = "quadra-shared"', config)
            self.assertIn('name = "quadra-shared-template"', config)
            self.assertIn('gpu_ids = "ADA_24"', config)
            self.assertIn("size_gb = 80", config)
            self.assertIn("timeout_seconds = 900", config)
            self.assertIn('image_name = "custom/image:latest"', config)

    def test_init_is_idempotent_and_recreates_missing_scaffold_files(self) -> None:
        with self.runner.isolated_filesystem():
            first = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(first.exit_code, 0, first.output)

            project_root = Path("bonsai")
            config_path = project_root / "quadra.toml"
            config_path.write_text(
                config_path.read_text(encoding="utf-8") + "\n# keep my edits\n",
                encoding="utf-8",
            )
            worker_path = project_root / "quadra_worker.py"
            worker_path.unlink()

            second = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(second.exit_code, 0, second.output)
            self.assertIn("# keep my edits", config_path.read_text(encoding="utf-8"))
            self.assertTrue(worker_path.exists())
            self.assertTrue((project_root / "src" / "libs" / "diffusers").is_dir())

    def test_init_still_rejects_type_conflicts(self) -> None:
        with self.runner.isolated_filesystem():
            project_root = Path("bonsai")
            (project_root / "src" / "libs").mkdir(parents=True)
            (project_root / "src" / "libs" / "diffusers").write_text(
                "not a directory",
                encoding="utf-8",
            )

            result = self.runner.invoke(cli, ["init", "bonsai"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn(
                "Refusing to overwrite existing path:",
                result.output,
            )
            self.assertIn(
                "bonsai/src/libs/diffusers",
                result.output,
            )

    def test_fork_clones_into_lib_and_wires_experiment_dependency(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)

            with chdir("bonsai"):
                project_root = Path.cwd().resolve()
                with patch("quadra.cli.subprocess.run") as run:
                    result = self.runner.invoke(
                        cli,
                        ["fork", "https://github.com/acme/diffusers.git"],
                    )

                self.assertEqual(result.exit_code, 0, result.output)
                run.assert_called_once_with(
                    [
                        "git",
                        "clone",
                        "https://github.com/acme/diffusers.git",
                        str(project_root / "src" / "libs" / "diffusers"),
                    ],
                    cwd=str(project_root),
                    check=True,
                    text=True,
                )
                pyproject = Path("src/experiment/pyproject.toml").read_text(
                    encoding="utf-8"
                )

            self.assertIn('dependencies = [\n    "diffusers",\n]', pyproject)
            self.assertIn("[tool.uv.sources]", pyproject)
            self.assertIn(
                '"diffusers" = { path = "../libs/diffusers", editable = true }',
                pyproject,
            )
            self.assertFalse(
                (project_root / "src" / "libs" / "diffusers" / ".gitkeep").exists()
            )
            self.assertIn("package: diffusers", result.output)

    def test_fork_accepts_package_name_when_repo_name_differs(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)

            with chdir("bonsai"):
                with patch("quadra.cli.subprocess.run"):
                    result = self.runner.invoke(
                        cli,
                        [
                            "fork",
                            "https://github.com/acme/diffusers-experiment.git",
                            "--package",
                            "diffusers",
                        ],
                    )
                pyproject = Path("src/experiment/pyproject.toml").read_text(
                    encoding="utf-8"
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn('    "diffusers",', pyproject)
            self.assertIn(
                '"diffusers" = { path = "../libs/diffusers-experiment", editable = true }',
                pyproject,
            )

    def test_fork_refuses_to_overwrite_existing_lib_checkout(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)

            with chdir("bonsai"):
                lib_dir = Path("src/libs/custom-lib")
                lib_dir.mkdir()
                (lib_dir / "README.md").write_text("keep me\n", encoding="utf-8")
                with patch("quadra.cli.subprocess.run") as run:
                    result = self.runner.invoke(
                        cli,
                        ["fork", "https://github.com/acme/custom-lib.git"],
                    )

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("already exists and is not empty", result.output)
            run.assert_not_called()

    def test_sync_errors_when_volume_datacenter_has_no_s3_support(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_client = FakeRunpodClient(FakeS3Client(), data_center_id="US-KS-1")

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    result = self.runner.invoke(cli, ["sync"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("does not currently support the RunPod S3 API", result.output)

    def test_sync_skips_unchanged_files_when_manifest_matches(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        first_result = self.runner.invoke(cli, ["sync"])
                        first_upload_count = len(fake_s3.upload_calls)
                        first_manifest_count = len(fake_s3.put_object_calls)
                        second_result = self.runner.invoke(cli, ["sync"])

            self.assertEqual(first_result.exit_code, 0, first_result.output)
            self.assertEqual(second_result.exit_code, 0, second_result.output)
            self.assertIn("uploaded: 0, deleted: 0", second_result.output)
            self.assertEqual(len(fake_s3.upload_calls), first_upload_count)
            self.assertEqual(len(fake_s3.put_object_calls), first_manifest_count)
            self.assertIn(
                "projects/bonsai/.quadra/sync-manifest.json",
                "\n".join(sorted(fake_s3.objects)),
            )
            self.assertIn(
                "projects/bonsai/.quadra/quadra_worker.py",
                "\n".join(sorted(fake_s3.objects)),
            )
            self.assertIn(
                ".quadra/quadra_worker.py",
                "\n".join(sorted(fake_s3.objects)),
            )

    def test_sync_uploads_only_changed_files(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        first_result = self.runner.invoke(cli, ["sync"])
                        first_upload_count = len(fake_s3.upload_calls)
                        first_manifest_count = len(fake_s3.put_object_calls)

                        main_path = Path("src/experiment/main.py")
                        main_path.write_text(
                            main_path.read_text(encoding="utf-8") + "\nprint('changed')\n",
                            encoding="utf-8",
                        )
                        second_result = self.runner.invoke(cli, ["sync"])

            self.assertEqual(first_result.exit_code, 0, first_result.output)
            self.assertEqual(second_result.exit_code, 0, second_result.output)
            self.assertIn("uploaded: 1, deleted: 0", second_result.output)
            self.assertEqual(
                fake_s3.upload_calls[first_upload_count:],
                ["projects/bonsai/src/experiment/main.py"],
            )
            self.assertEqual(len(fake_s3.put_object_calls), first_manifest_count + 1)

    def test_sync_falls_back_to_single_delete_when_bulk_delete_redirects(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = RedirectingDeleteFakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        first_result = self.runner.invoke(cli, ["sync"])
                        self.assertEqual(first_result.exit_code, 0, first_result.output)

                        stale_path = Path("stale.txt")
                        stale_path.write_text("stale\n", encoding="utf-8")
                        uploaded_result = self.runner.invoke(cli, ["sync"])
                        self.assertEqual(uploaded_result.exit_code, 0, uploaded_result.output)
                        stale_key = "projects/bonsai/stale.txt"

                        stale_path.unlink()

                        second_result = self.runner.invoke(cli, ["sync"])

            self.assertEqual(second_result.exit_code, 0, second_result.output)
            self.assertIn("deleting 1 stale remote files...", second_result.output)
            self.assertIn("uploaded: 0, deleted: 1", second_result.output)
            self.assertNotIn(stale_key, fake_s3.objects)

    def test_sync_ignores_remote_worker_runtime_artifacts(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        first_result = self.runner.invoke(cli, ["sync"])
                        self.assertEqual(first_result.exit_code, 0, first_result.output)

                        runtime_key = "projects/bonsai/.quadra/worker-runtime/lib64"
                        fake_s3.objects[runtime_key] = b"remote runtime artifact"

                        second_result = self.runner.invoke(cli, ["sync"])

            self.assertEqual(second_result.exit_code, 0, second_result.output)
            self.assertIn("uploaded: 0, deleted: 0", second_result.output)
            self.assertIn(runtime_key, fake_s3.objects)

    def test_submit_normalizes_managed_runtime_defaults_from_older_scaffold(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            old_setup_command = (
                "(command -v uv >/dev/null 2>&1 || "
                "python -m pip install --disable-pip-version-check --no-cache-dir uv) && "
                "uv sync"
            )
            old_bootstrap_command = "\n".join(
                [
                    'worker_path="{worker_path}"',
                    'bootstrap_log="{worker_bootstrap_log_path}"',
                    'mkdir -p "$(dirname "$bootstrap_log")"',
                    ': > "$bootstrap_log"',
                    "{",
                    '  echo "[quadra] bootstrap started $(date -u +%Y-%m-%dT%H:%M:%SZ)"',
                    '  echo "[quadra] python: $(python --version 2>&1)"',
                    '  echo "[quadra] worker path: $worker_path"',
                    '  if [ ! -f "$worker_path" ]; then',
                    '    echo "[quadra] worker script missing"',
                    "    exit 1",
                    "  fi",
                    "  if python -c 'import runpod' >/dev/null 2>&1; then",
                    '    echo "[quadra] python package \'runpod\' already available"',
                    "  else",
                    '    echo "[quadra] installing python package \'runpod\'"',
                    "    python -m pip install --disable-pip-version-check --no-cache-dir runpod || exit 1",
                    "  fi",
                    '  echo "[quadra] launching worker"',
                    '} >>"$bootstrap_log" 2>&1 && exec python -u "$worker_path"',
                ]
            )

            with chdir("bonsai"):
                config_path = Path("quadra.toml")
                config_text = config_path.read_text(encoding="utf-8")
                config_text = re.sub(
                    r'^setup_command = .+$',
                    lambda _: f"setup_command = {json.dumps(old_setup_command)}",
                    config_text,
                    count=1,
                    flags=re.MULTILINE,
                )
                config_text = re.sub(
                    r'^docker_start_cmd = .+$',
                    lambda _: (
                        "docker_start_cmd = "
                        f"{json.dumps(['/bin/sh', '-lc', old_bootstrap_command])}"
                    ),
                    config_text,
                    count=1,
                    flags=re.MULTILINE,
                )
                config_text = re.sub(
                    r'^smoke = .+$',
                    'smoke = "python scripts/smoke.py"',
                    config_text,
                    count=1,
                    flags=re.MULTILINE,
                )
                config_path.write_text(config_text, encoding="utf-8")

                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        sync_result = self.runner.invoke(cli, ["sync"])
                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])

            self.assertEqual(sync_result.exit_code, 0, sync_result.output)
            self.assertEqual(submit_result.exit_code, 0, submit_result.output)
            self.assertIn(
                "[runpod bootstrap] creating isolated worker runtime",
                fake_client.created_templates[0]["docker_start_cmd"][2],
            )
            self.assertIn(
                "/runpod-volume/.quadra/worker-runtime",
                fake_client.created_templates[0]["docker_start_cmd"][2],
            )
            self.assertIn(
                "/runpod-volume/projects/bonsai/.quadra/uv-runtime",
                fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
            )
            self.assertIn(
                'cd "/runpod-volume/projects/bonsai/src/experiment" && "$(command -v uv)" sync',
                fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
            )
            self.assertIn(
                'cd "/runpod-volume/projects/bonsai/src/experiment" && "$uv_python" -m uv sync',
                fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
            )
            self.assertIn(
                'PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv sync',
                fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
            )
            self.assertEqual(
                fake_client.submissions[0]["payload"]["quadra"]["command"],
                "python main.py",
            )

    def test_submit_updates_existing_template_when_mount_path_is_wrong(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            fake_client.templates = [
                {
                    "id": "tpl-123",
                    "name": "quadra-bonsai-serverless-worker",
                    "imageName": "pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                    "ports": [],
                    "dockerEntrypoint": [],
                    "dockerStartCmd": [
                        "/bin/sh",
                        "-lc",
                        "(python -c 'import runpod' >/dev/null 2>&1 || "
                        "python -m pip install --disable-pip-version-check --no-cache-dir runpod) "
                        "&& exec python -u /runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                    ],
                    "volumeMountPath": "/workspace",
                    "env": {},
                    "containerDiskInGb": 20,
                    "readme": "Managed by Quadra. Runs {worker_path} from the synced project volume.",
                }
            ]

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        sync_result = self.runner.invoke(cli, ["sync"])
                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])

            self.assertEqual(sync_result.exit_code, 0, sync_result.output)
            self.assertEqual(submit_result.exit_code, 0, submit_result.output)
            self.assertIn(
                "[quadra] updating RunPod template 'quadra-bonsai-serverless-worker'...",
                submit_result.output,
            )
            self.assertEqual(len(fake_client.created_templates), 0)
            self.assertEqual(len(fake_client.updated_templates), 1)
            self.assertEqual(
                fake_client.updated_templates[0]["volume_mount_path"],
                "/runpod-volume",
            )

    def test_submit_refreshes_existing_endpoint_when_template_changes_in_place(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            fake_client.templates = [
                {
                    "id": "tpl-123",
                    "name": "quadra-bonsai-serverless-worker",
                    "imageName": "pytorch/pytorch:2.12.1-cuda12.6-cudnn9-runtime",
                    "ports": [],
                    "dockerEntrypoint": [],
                    "dockerStartCmd": [
                        "/bin/sh",
                        "-lc",
                        "(python -c 'import runpod' >/dev/null 2>&1 || "
                        "python -m pip install --disable-pip-version-check --no-cache-dir runpod) "
                        "&& exec python -u /runpod-volume/projects/bonsai/.quadra/quadra_worker.py",
                    ],
                    "volumeMountPath": "/runpod-volume",
                    "env": {},
                    "containerDiskInGb": 20,
                    "readme": "Managed by Quadra. Runs {worker_path} from the synced project volume.",
                }
            ]
            fake_client.endpoints = [
                {
                    "id": "ep-123",
                    "name": "quadra-bonsai",
                    "templateId": "tpl-123",
                    "networkVolumeId": "nv-123",
                }
            ]

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        sync_result = self.runner.invoke(cli, ["sync"])
                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])

            self.assertEqual(sync_result.exit_code, 0, sync_result.output)
            self.assertEqual(submit_result.exit_code, 0, submit_result.output)
            self.assertEqual(len(fake_client.updated_templates), 1)
            self.assertEqual(len(fake_client.updated_endpoints), 1)
            self.assertEqual(fake_client.updated_endpoints[0]["endpoint_id"], "ep-123")
            self.assertEqual(fake_client.updated_endpoints[0]["template_id"], "tpl-123")

    def test_submit_recreates_existing_endpoint_when_workers_are_only_exited(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            fake_client.endpoints = [
                {
                    "id": "ep-123",
                    "name": "quadra-bonsai",
                    "templateId": "tpl-123",
                    "networkVolumeId": "nv-123",
                    "workers": [
                        {
                            "id": "worker-1",
                            "desiredStatus": "EXITED",
                            "lastStatusChange": "Exited by Runpod",
                        }
                    ],
                }
            ]

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        sync_result = self.runner.invoke(cli, ["sync"])
                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])

            self.assertEqual(sync_result.exit_code, 0, sync_result.output)
            self.assertEqual(submit_result.exit_code, 0, submit_result.output)
            self.assertEqual(fake_client.deleted_endpoints, ["ep-123"])
            self.assertEqual(len(fake_client.created_endpoints), 1)
            self.assertEqual(len(fake_client.updated_endpoints), 0)

    def test_sync_prompts_to_create_missing_volume(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            fake_client.volumes = []

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch(
                            "quadra.cli.supports_interactive_prompts",
                            return_value=True,
                        ):
                            result = self.runner.invoke(
                                cli,
                                ["sync"],
                                input="y\nUS-IL-1\n50\n",
                            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Create it now?", result.output)
            self.assertIn("created RunPod network volume nv-1", result.output)
            self.assertEqual(
                fake_client.created_network_volumes,
                [
                    {
                        "id": "nv-1",
                        "name": "bonsai",
                        "dataCenterId": "US-IL-1",
                        "size": 50,
                    }
                ],
            )
            self.assertIn(
                "projects/bonsai/quadra.toml",
                "\n".join(sorted(fake_s3.objects)),
            )

    def test_sync_can_link_existing_volume_and_persist_config(self) -> None:
        with self.runner.isolated_filesystem():
            self.assertEqual(self.runner.invoke(cli, ["init", "bonsai"]).exit_code, 0)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            shared_volume = {
                "id": "nv-shared",
                "name": "shared",
                "dataCenterId": "US-IL-1",
                "size": 200,
            }
            fake_client.volume = shared_volume
            fake_client.volumes = [shared_volume]

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch(
                            "quadra.cli.supports_interactive_prompts",
                            return_value=True,
                        ):
                            result = self.runner.invoke(
                                cli,
                                ["sync"],
                                input="link\n1\n",
                            )

                config_text = Path("quadra.toml").read_text(encoding="utf-8")

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("How would you like to continue", result.output)
            self.assertIn("linked bonsai to RunPod network volume nv-shared", result.output)
            self.assertEqual(fake_client.created_network_volumes, [])
            self.assertIn('network_volume_id = "nv-shared"', config_text)

    def test_smoke_links_existing_volume_once_and_reuses_it(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = PollingFakeRunpodClient(fake_s3)
            shared_volume = {
                "id": "nv-shared",
                "name": "shared",
                "dataCenterId": "US-IL-1",
                "size": 200,
            }
            fake_client.volume = shared_volume
            fake_client.volumes = [shared_volume]

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch(
                            "quadra.cli.supports_interactive_prompts",
                            return_value=True,
                        ):
                            with patch("quadra.cli.time.sleep", return_value=None):
                                result = self.runner.invoke(
                                    cli,
                                    ["smoke"],
                                    input="link\n1\n",
                                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.output.count("How would you like to continue"), 1)
            self.assertEqual(
                fake_client.created_endpoints[0]["network_volume_id"],
                "nv-shared",
            )
            self.assertIn(
                "polling RunPod job status and streaming remote worker logs...",
                result.output,
            )

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
                        self.assertIn("[quadra] resolving RunPod network volume...", sync_result.output)
                        self.assertIn("[quadra] scanning local project files...", sync_result.output)
                        self.assertIn("[quadra] uploading", sync_result.output)
                        self.assertIn("[quadra] checking remote project for stale files...", sync_result.output)
                        self.assertIn("projects/bonsai/quadra.toml", "\n".join(sorted(fake_s3.objects)))

                        submit_result = self.runner.invoke(cli, ["submit", "smoke"])
                        self.assertEqual(submit_result.exit_code, 0, submit_result.output)
                        self.assertIn("submitted smoke", submit_result.output)
                        self.assertIn("[quadra] checking remote project sync state...", submit_result.output)
                        self.assertIn("[quadra] resolving RunPod endpoint...", submit_result.output)
                        self.assertIn("[quadra] resolving RunPod template...", submit_result.output)
                        self.assertIn("[quadra] creating RunPod template 'quadra-bonsai-serverless-worker'...", submit_result.output)
                        self.assertIn("[quadra] creating RunPod endpoint 'quadra-bonsai'...", submit_result.output)
                        self.assertIn("[quadra] submitting smoke to RunPod endpoint ep-123...", submit_result.output)
                        self.assertIn("endpoint_id: ep-123", submit_result.output)
                        self.assertTrue(Path(".quadra/last-run.json").exists())
                        self.assertEqual(len(fake_client.created_templates), 1)
                        self.assertEqual(len(fake_client.created_endpoints), 1)
                        self.assertEqual(
                            fake_client.created_templates[0]["docker_start_cmd"][:2],
                            ("/bin/sh", "-lc"),
                        )
                        self.assertIn(
                            "/runpod-volume/projects/bonsai/.quadra/worker-bootstrap.log",
                            fake_client.created_templates[0]["docker_start_cmd"][2],
                        )
                        self.assertIn(
                            "/runpod-volume/.quadra/worker-runtime",
                            fake_client.created_templates[0]["docker_start_cmd"][2],
                        )
                        self.assertIn(
                            "creating isolated worker runtime",
                            fake_client.created_templates[0]["docker_start_cmd"][2],
                        )
                        self.assertIn(
                            "worker script missing",
                            fake_client.created_templates[0]["docker_start_cmd"][2],
                        )
                        self.assertIn(
                            "/runpod-volume/projects/bonsai/.quadra/uv-runtime",
                            fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
                        )
                        self.assertIn(
                            'cd "/runpod-volume/projects/bonsai/src/experiment" && "$(command -v uv)" sync',
                            fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
                        )
                        self.assertIn(
                            'cd "/runpod-volume/projects/bonsai/src/experiment" && "$uv_python" -m uv sync',
                            fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
                        )
                        self.assertIn(
                            'PYTHONPATH="$uv_site_packages${PYTHONPATH:+:$PYTHONPATH}" python -m uv sync',
                            fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
                        )
                        self.assertEqual(
                            fake_client.created_endpoints[0]["timeout_seconds"], 600
                        )

                        logs_result = self.runner.invoke(cli, ["logs", "--no-follow"])
                        self.assertEqual(logs_result.exit_code, 0, logs_result.output)
                        self.assertIn("[quadra] connecting to RunPod S3 volume", logs_result.output)
                        self.assertIn(
                            "[quadra] streaming worker stdout from RunPod...",
                            logs_result.output,
                        )
                        self.assertIn("bonsai smoke remote", logs_result.output)
                        self.assertIn("status: COMPLETED", logs_result.output)

                        pull_result = self.runner.invoke(cli, ["pull"])
                        self.assertEqual(pull_result.exit_code, 0, pull_result.output)
                        self.assertIn("[quadra] downloading remote files for", pull_result.output)
                        pulled_path = Path(pull_result.output.strip().splitlines()[-1])
                        self.assertTrue((pulled_path / "stdout.log").exists())
                        self.assertEqual(
                            (pulled_path / "stdout.log").read_text(encoding="utf-8"),
                            "bonsai smoke remote\n",
                        )
                        self.assertEqual(
                            (pulled_path / "artifacts" / "result.txt").read_text(
                                encoding="utf-8"
                            ),
                            "smoke artifact\n",
                        )

    def test_run_executes_named_workflow_in_quadra_project(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        result = self.runner.invoke(cli, ["run", "smoke"])
                reference = json.loads(
                    Path(".quadra/last-run.json").read_text(encoding="utf-8")
                )
                artifact_path = (
                    Path("runs")
                    / reference["run_id"]
                    / "artifacts"
                    / "result.txt"
                )

                self.assertTrue(artifact_path.exists())

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("syncing bonsai -> /runpod-volume/projects/bonsai", result.output)
            self.assertIn("submitting smoke", result.output)
            self.assertIn("bonsai smoke remote", result.output)

    def test_run_executes_plain_python_directory_with_global_config(self) -> None:
        with self.runner.isolated_filesystem():
            global_config = Path("global-quadra.toml").resolve()
            global_config.write_text(
                "\n".join(
                    [
                        "[runpod.network_volume]",
                        'name = "quadra-dev"',
                        "",
                        "[runpod.serverless]",
                        'endpoint_name = "quadra-dev"',
                        "",
                        "[runpod.template]",
                        'name = "quadra-dev-serverless-worker"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            project_root = Path("gemlite")
            project_root.mkdir()
            (project_root / "pyproject.toml").write_text(
                '[project]\nname = "gemlite"\nversion = "0.1.0"\n',
                encoding="utf-8",
            )
            (project_root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            fake_s3 = FakeS3Client()
            fake_client = FakeRunpodClient(fake_s3)
            fake_client.volume["name"] = "quadra-dev"

            with patch.dict(os.environ, {"QUADRA_CONFIG": str(global_config)}):
                with chdir(project_root):
                    with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                        with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                            result = self.runner.invoke(
                                cli,
                                ["run", "python main.py"],
                            )
                    reference = json.loads(
                        Path(".quadra/last-run.json").read_text(encoding="utf-8")
                    )
                    artifact_path = (
                        Path("runs")
                        / reference["run_id"]
                        / "artifacts"
                        / "result.txt"
                    )
                    self.assertTrue(artifact_path.exists())

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("syncing gemlite -> /runpod-volume/projects/gemlite", result.output)
            self.assertIn("submitting python main.py", result.output)
            self.assertIn("projects/gemlite/pyproject.toml", fake_s3.objects)
            self.assertIn(".quadra/quadra_worker.py", fake_s3.objects)
            self.assertEqual(fake_client.created_endpoints[0]["name"], "quadra-dev")
            self.assertEqual(
                fake_client.submissions[0]["payload"]["quadra"]["command"],
                "python main.py",
            )
            self.assertIn(
                'cd "/runpod-volume/projects/gemlite" && "$(command -v uv)" sync',
                fake_client.submissions[0]["payload"]["quadra"]["setup_command"],
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
            self.assertIn("[quadra] scanning local project files...", result.output)
            self.assertIn("[quadra] resolving RunPod endpoint...", result.output)
            self.assertIn(
                "polling RunPod job status and streaming remote worker logs...",
                result.output,
            )
            self.assertIn("[quadra] smoke: queued on RunPod", result.output)
            self.assertIn(
                "[quadra] smoke: worker running, waiting for remote logs",
                result.output,
            )
            self.assertIn("[quadra] smoke: completed", result.output)
            self.assertIn("pulling artifacts for", result.output)

    def test_smoke_pulls_core_logs_without_listing_when_manifest_is_missing(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = NoListFakeS3Client()
            fake_client = ManifestlessPollingFakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch("quadra.cli.time.sleep", return_value=None):
                            result = self.runner.invoke(cli, ["smoke"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "remote run manifest is missing; downloaded core run logs only",
                result.output,
            )

    def test_smoke_streams_worker_bootstrap_logs_while_queued(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = BootstrapLoggingPollingFakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch("quadra.cli.time.sleep", return_value=None):
                            result = self.runner.invoke(cli, ["smoke"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "[quadra] streaming worker bootstrap log from RunPod...",
                result.output,
            )
            self.assertIn("[runpod bootstrap] started", result.output)
            self.assertIn("python package 'runpod' already available", result.output)

    def test_smoke_fails_fast_when_queued_workers_are_unhealthy(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = UnhealthyQueuedFakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch("quadra.cli.time.sleep", return_value=None):
                            result = self.runner.invoke(cli, ["smoke"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("[quadra] smoke: queued on RunPod", result.output)
            self.assertIn("workers: 1 blocked", result.output)
            self.assertIn("has no viable workers while job", result.output)
            self.assertIn("IMAGE_AUTH_ERROR", result.output)

    def test_smoke_does_not_fail_fast_for_plain_exited_worker(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = ExitedWorkerPollingFakeRunpodClient(fake_s3)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch("quadra.cli.time.sleep", return_value=None):
                            result = self.runner.invoke(cli, ["smoke"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("workers: 1 exited", result.output)
            self.assertNotIn("has no viable workers while job", result.output)
            self.assertIn("[quadra] smoke: completed", result.output)

    def test_smoke_times_out_when_job_stays_queued_without_workers(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            fake_s3 = FakeS3Client()
            fake_client = StuckQueuedFakeRunpodClient(fake_s3)
            queued_since = datetime.now(timezone.utc) - timedelta(seconds=301)

            with chdir("bonsai"):
                with patch("quadra.cli.load_runpod_client", return_value=fake_client):
                    with patch("quadra.cli.build_s3_client", return_value=fake_s3):
                        with patch("quadra.cli.time.sleep", return_value=None):
                            with patch(
                                "quadra.cli.parse_utc_timestamp",
                                return_value=queued_since,
                            ):
                                result = self.runner.invoke(cli, ["smoke"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("has been queued for", result.output)
            self.assertIn("workers: none reported yet", result.output)
            self.assertIn("QUADRA_RUNPOD_QUEUE_TIMEOUT_SECONDS", result.output)


if __name__ == "__main__":
    unittest.main()
