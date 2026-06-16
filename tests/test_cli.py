from __future__ import annotations

import json
import unittest
from contextlib import chdir
from pathlib import Path

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

    def test_sync_stages_runtime_and_hard_run_cleans_up(self) -> None:
        with self.runner.isolated_filesystem():
            init_result = self.runner.invoke(cli, ["init", "bonsai"])
            self.assertEqual(init_result.exit_code, 0, init_result.output)

            with chdir("bonsai"):
                up_result = self.runner.invoke(cli, ["up"])
                self.assertEqual(up_result.exit_code, 0, up_result.output)

                sync_result = self.runner.invoke(cli, ["sync"])
                self.assertEqual(sync_result.exit_code, 0, sync_result.output)

                source_smoke = Path("src/experiment/scripts/smoke.py")
                source_smoke.write_text(
                    "def main() -> None:\n    print('source changed')\n\n\nif __name__ == '__main__':\n    main()\n",
                    encoding="utf-8",
                )

                run_result = self.runner.invoke(cli, ["run", "smoke"])
                self.assertEqual(run_result.exit_code, 0, run_result.output)
                self.assertIn("bonsai smoke ok", run_result.output)
                self.assertNotIn("source changed", run_result.output)

                resync_result = self.runner.invoke(cli, ["sync"])
                self.assertEqual(resync_result.exit_code, 0, resync_result.output)

                rerun_result = self.runner.invoke(cli, ["run", "smoke"])
                self.assertEqual(rerun_result.exit_code, 0, rerun_result.output)
                self.assertIn("source changed", rerun_result.output)

                hard_run_result = self.runner.invoke(cli, ["hard-run", "smoke"])
                self.assertEqual(hard_run_result.exit_code, 0, hard_run_result.output)
                self.assertIn("source changed", hard_run_result.output)

                state = json.loads(Path(".quadra/state.json").read_text(encoding="utf-8"))
                self.assertIsNone(state["active_runtime_id"])


if __name__ == "__main__":
    unittest.main()
