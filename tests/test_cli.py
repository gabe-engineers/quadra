from __future__ import annotations

import io
import json
import posixpath
import unittest
from contextlib import chdir
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from click.testing import CliRunner

from quadra.cli import cli, load_banner_text


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
        self.created_endpoints: list[dict[str, object]] = []
        self.jobs: dict[str, dict[str, object]] = {}
        self.submissions: list[dict[str, object]] = []

    def get_user(self) -> dict[str, object]:
        return {"networkVolumes": [self.volume]}

    def get_endpoints(self) -> list[dict[str, object]]:
        return list(self.endpoints)

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


class QuadraCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

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
            self.assertIn('template_id = ""', config)
            self.assertIn("# Valid serverless gpu_ids pool IDs:", config)
            self.assertIn('#   ADA_24        24 GB    RTX 4090', config)
            self.assertTrue((project_root / ".quadra").exists())
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
                self.write_template_id(Path("quadra.toml"))
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
                self.write_template_id(Path("quadra.toml"))
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
                        self.assertEqual(len(fake_client.created_endpoints), 1)

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

    def write_template_id(self, config_path: Path) -> None:
        config = config_path.read_text(encoding="utf-8")
        config_path.write_text(
            config.replace('template_id = ""', 'template_id = "tpl-123"'),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
