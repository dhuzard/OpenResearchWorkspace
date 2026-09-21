from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "setup"


def cli_env() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("PYTHONPATH", "")
    source = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = source + (os.pathsep + current if current else "")
    return env


def run_cli(*args: str, cwd: Path | None = None, input_text: str | None = None):
    return subprocess.run(
        [sys.executable, "-m", "orw.cli", *args],
        cwd=cwd or REPO_ROOT,
        env=cli_env(),
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_help_is_researcher_facing(self) -> None:
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Create and validate portable OpenResearchWorkspace projects", result.stdout)
        self.assertIn("init", result.stdout)
        self.assertIn("validate", result.stdout)

    def test_init_from_config_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            result = run_cli(
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
                cwd=root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Created ORW workspace:", result.stdout)

            validation = run_cli("validate", str(workspace), cwd=root)
            self.assertEqual(validation.returncode, 0, msg=validation.stderr)
            self.assertIn("Valid ORW workspace:", validation.stdout)

    def test_init_accepts_config_from_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "stdin-study"
            payload = (FIXTURES / "no-assay.json").read_text(encoding="utf-8")
            result = run_cli(
                "init",
                str(workspace),
                "--config",
                "-",
                cwd=root,
                input_text=payload,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Assay: none initialized", result.stdout)

    def test_reinitialization_has_distinct_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            args = (
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
            )
            first = run_cli(*args, cwd=root)
            second = run_cli(*args, cwd=root)

            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertEqual(second.returncode, 3)
            self.assertIn("already initialized", second.stderr.lower())

    def test_invalid_config_returns_input_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_cli(
                "init",
                str(root / "bad"),
                "--config",
                str(FIXTURES / "invalid-orcid.json"),
                cwd=root,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Input error:", result.stderr)

    def test_validate_json_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            created = run_cli(
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
                cwd=root,
            )
            self.assertEqual(created.returncode, 0, msg=created.stderr)

            result = run_cli("validate", str(workspace), "--json", cwd=root)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["valid"])
            self.assertEqual(payload["issues"], [])

    def test_schema_failure_returns_validation_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            created = run_cli(
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
                cwd=root,
            )
            self.assertEqual(created.returncode, 0, msg=created.stderr)

            project_path = workspace / ".research" / "project.yml"
            project_text = project_path.read_text(encoding="utf-8")
            project_path.write_text(
                project_text.replace(
                    '  title: "Effects of light exposure on mouse activity"',
                    '  title: ""',
                    1,
                ),
                encoding="utf-8",
            )

            result = run_cli("validate", str(workspace), "--json", cwd=root)
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["valid"])
            self.assertTrue(
                any(issue["code"] == "schema_validation" for issue in payload["issues"])
            )

    def test_missing_declared_path_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            created = run_cli(
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
                cwd=root,
            )
            self.assertEqual(created.returncode, 0, msg=created.stderr)

            shutil.rmtree(workspace / "studies" / "light-exposure-study")

            result = run_cli("validate", str(workspace), "--json", cwd=root)
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertTrue(
                any(
                    issue["code"] == "missing_declared_path"
                    for issue in payload["issues"]
                )
            )

    def test_missing_workspace_root_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_cli("validate", str(root / "does-not-exist"), "--json", cwd=root)
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["issues"][0]["code"], "missing_workspace_root")


class PackagingTests(unittest.TestCase):
    def test_packaged_project_schema_matches_canonical_schema(self) -> None:
        canonical = (REPO_ROOT / "schema" / "project.schema.json").read_text(
            encoding="utf-8"
        )
        packaged = (
            REPO_ROOT / "src" / "orw" / "schemas" / "project.schema.json"
        ).read_text(encoding="utf-8")
        self.assertEqual(canonical, packaged)


if __name__ == "__main__":
    unittest.main()
