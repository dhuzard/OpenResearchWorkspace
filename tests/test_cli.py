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
        self.assertIn("export", result.stdout)

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

    def test_export_rocrate_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            crate = root / "crate"

            created = run_cli(
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
                cwd=root,
            )
            self.assertEqual(created.returncode, 0, msg=created.stderr)

            exported = run_cli(
                "export",
                str(workspace),
                "--format",
                "ro-crate",
                "--output",
                str(crate),
                cwd=root,
            )
            self.assertEqual(exported.returncode, 0, msg=exported.stderr)
            self.assertIn("Created RO-Crate 1.3 export:", exported.stdout)
            self.assertTrue((crate / "ro-crate-metadata.json").is_file())
            self.assertTrue((crate / ".research" / "project.yml").is_file())

    def test_export_invalid_workspace_returns_validation_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exported = run_cli(
                "export",
                str(root / "not-a-workspace"),
                "--format",
                "ro-crate",
                "--output",
                str(root / "crate"),
                cwd=root,
            )
            self.assertEqual(exported.returncode, 1)
            self.assertIn("Export error:", exported.stderr)
            self.assertFalse((root / "crate").exists())

    def test_export_existing_output_returns_export_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "study"
            crate = root / "crate"
            created = run_cli(
                "init",
                str(workspace),
                "--config",
                str(FIXTURES / "basic.json"),
                cwd=root,
            )
            self.assertEqual(created.returncode, 0, msg=created.stderr)
            crate.mkdir()

            exported = run_cli(
                "export",
                str(workspace),
                "--output",
                str(crate),
                cwd=root,
            )
            self.assertEqual(exported.returncode, 4)
            self.assertIn("Use --force", exported.stderr)

    def test_missing_workspace_root_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_cli("validate", str(root / "does-not-exist"), "--json", cwd=root)
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["issues"][0]["code"], "missing_workspace_root")


class MutationCliTests(unittest.TestCase):
    """The mutation commands are the researcher-facing half of the mutation API."""

    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="orw-cli-mutate-")
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)
        self.workspace = self.root / "study"
        created = run_cli(
            "init", str(self.workspace), "--config", str(FIXTURES / "basic.json"),
            cwd=self.root,
        )
        self.assertEqual(created.returncode, 0, msg=created.stderr)

    def mutate(self, *args: str):
        return run_cli(*args, "--workspace", str(self.workspace), cwd=self.root)

    def record(self) -> str:
        return (self.workspace / ".research" / "project.yml").read_text(encoding="utf-8")

    def test_help_lists_the_mutation_commands(self) -> None:
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        for command in ("study", "assay", "resource", "contributor", "metadata"):
            self.assertIn(command, result.stdout)

    def test_study_and_assay_round_trip(self) -> None:
        study = self.mutate("study", "add", "Sleep deprivation")
        self.assertEqual(study.returncode, 0, msg=study.stderr)
        self.assertIn("sleep-deprivation", study.stdout)

        assay = self.mutate("assay", "add", "Open field", "--study", "sleep-deprivation")
        self.assertEqual(assay.returncode, 0, msg=assay.stderr)

        validated = run_cli("validate", str(self.workspace), cwd=self.root)
        self.assertEqual(validated.returncode, 0, msg=validated.stderr)
        self.assertTrue(
            (self.workspace / "studies/sleep-deprivation/assays/open-field").is_dir()
        )

    def test_dry_run_leaves_the_workspace_untouched(self) -> None:
        before = self.record()
        result = self.mutate("study", "add", "Sleep deprivation", "--dry-run")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Dry run: nothing was written.", result.stdout)
        self.assertIn('+  - identifier: "sleep-deprivation"', result.stdout)
        self.assertEqual(self.record(), before)
        self.assertFalse((self.workspace / "studies" / "sleep-deprivation").exists())

    def test_json_plan_is_machine_readable(self) -> None:
        result = self.mutate("study", "add", "Sleep deprivation", "--dry-run", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        payload = json.loads(result.stdout)
        self.assertFalse(payload["applied"])
        self.assertEqual(payload["operation"], "study.add")
        self.assertEqual(payload["identifier"], "sleep-deprivation")
        self.assertEqual(payload["record"], ".research/project.yml")
        self.assertIn("studies/sleep-deprivation", payload["new_directories"])

    def test_conflicts_have_their_own_exit_code(self) -> None:
        first = self.mutate("study", "add", "Sleep deprivation")
        self.assertEqual(first.returncode, 0, msg=first.stderr)

        second = self.mutate("study", "add", "Sleep deprivation")
        self.assertEqual(second.returncode, 5)
        self.assertIn("Conflict:", second.stderr)

    def test_input_errors_have_the_input_exit_code(self) -> None:
        result = self.mutate("study", "add", "Sleep", "--id", "Not A Slug")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input error:", result.stderr)

    def test_an_invalid_workspace_is_refused_before_any_write(self) -> None:
        (self.workspace / ".research" / "initialized").unlink()
        before = self.record()

        result = self.mutate("contributor", "add", "Ada Lovelace")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not validate", result.stderr)
        self.assertIn("missing_initialized", result.stderr)
        self.assertEqual(self.record(), before)

    def test_contributor_resource_and_metadata_commands(self) -> None:
        contributor = self.mutate(
            "contributor", "add", "Ada Lovelace",
            "--role", "Analyst", "--orcid", "0000-0002-1825-0097",
        )
        self.assertEqual(contributor.returncode, 0, msg=contributor.stderr)

        resource = self.mutate(
            "resource", "add", "Imaging archive",
            "--type", "dataset", "--location", "https://example.org/a", "--access", "restricted",
        )
        self.assertEqual(resource.returncode, 0, msg=resource.stderr)

        metadata = self.mutate(
            "metadata", "set", "--status", "paused", "--keyword", "sleep", "--keyword", "mouse",
        )
        self.assertEqual(metadata.returncode, 0, msg=metadata.stderr)

        validated = run_cli("validate", str(self.workspace), cwd=self.root)
        self.assertEqual(validated.returncode, 0, msg=validated.stderr)

        record = self.record()
        self.assertIn("Ada Lovelace", record)
        self.assertIn("Imaging archive", record)
        self.assertIn('status: "paused"', record)

    def test_metadata_requires_a_field(self) -> None:
        result = self.mutate("metadata", "set")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input error:", result.stderr)

    def test_metadata_refuses_contradictory_keyword_options(self) -> None:
        result = self.mutate("metadata", "set", "--keyword", "sleep", "--clear-keywords")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not both", result.stderr)

    def test_a_subcommand_group_requires_an_action(self) -> None:
        result = run_cli("study", cwd=self.root)
        self.assertEqual(result.returncode, 2)


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
