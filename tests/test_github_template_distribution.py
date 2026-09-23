from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from orw import validate_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_github_template.py"
TEST_REVISION = "0123456789abcdef0123456789abcdef01234567"


class GitHubTemplateDistributionTests(unittest.TestCase):
    def _build(self, root: Path) -> Path:
        output = root / "template"
        subprocess.run(
            [
                sys.executable,
                str(BUILD_SCRIPT),
                "--output",
                str(output),
                "--core-revision",
                TEST_REVISION,
                "--force",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return output

    def test_generated_template_uses_canonical_research_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = self._build(Path(tmp))

            for name in (
                "project.yml",
                "workspace.yml",
                "capabilities.yml",
                "layout.yml",
                "profiles.yml",
            ):
                canonical = REPO_ROOT / "src" / "orw" / "templates" / name
                self.assertEqual(
                    canonical.read_bytes(),
                    (generated / ".research" / name).read_bytes(),
                    name,
                )

            workflow = (
                generated / ".github" / "workflows" / "initialize-project.yml"
            ).read_text(encoding="utf-8")
            provenance = (
                generated / ".research" / "template-source.yml"
            ).read_text(encoding="utf-8")
            self.assertIn(TEST_REVISION, workflow)
            self.assertIn(TEST_REVISION, provenance)
            self.assertNotIn("__ORW_CORE_REVISION__", workflow)

    def test_generated_template_stays_researcher_facing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = self._build(Path(tmp))
            top_level = {path.name for path in generated.iterdir()}

            for forbidden in (
                "src",
                "tests",
                "browser",
                "schema",
                "docs",
                "pyproject.toml",
                "MANIFEST.in",
                "SPEC.md",
                "CHANGELOG.md",
            ):
                self.assertNotIn(forbidden, top_level)

            self.assertTrue((generated / "README.md").is_file())
            self.assertTrue((generated / "GETTING_STARTED.md").is_file())
            self.assertTrue(
                (generated / ".github" / "ISSUE_TEMPLATE" / "orw-setup.yml").is_file()
            )

    def test_generated_adapter_initializes_with_local_canonical_core(self) -> None:
        issue_body = """### Project title
Effects of light exposure on mouse activity

### Short project description
Study of how altered light exposure affects spontaneous mouse activity.

### Your name
Jane Researcher

### First study title
Light exposure study

### What will you measure first?
Behaviour

### Where are the authoritative/raw data stored?
Institutional research server

### Data access level
private

### Keywords (optional)
behaviour, circadian rhythm, mouse

### Your ORCID (optional)
0000-0002-1825-0097

### Ready to initialize
- [x] I understand that submitting this form will initialize this repository as my research workspace.
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            generated = self._build(tmp_path)
            event_path = tmp_path / "event.json"
            output_path = tmp_path / "github-output.txt"
            event_path.write_text(
                json.dumps({"issue": {"body": issue_body}}, ensure_ascii=False),
                encoding="utf-8",
            )
            output_path.write_text("", encoding="utf-8")

            parse_env = os.environ.copy()
            parse_env.update(
                {
                    "GITHUB_EVENT_PATH": str(event_path),
                    "GITHUB_OUTPUT": str(output_path),
                }
            )
            subprocess.run(
                [sys.executable, str(generated / "scripts" / "parse_setup_issue.py")],
                cwd=generated,
                env=parse_env,
                check=True,
                capture_output=True,
                text=True,
            )
            output = output_path.read_text(encoding="utf-8").strip()
            self.assertTrue(output.startswith("setup_payload="))
            setup_payload = output.split("=", 1)[1]

            init_env = os.environ.copy()
            existing_pythonpath = init_env.get("PYTHONPATH")
            init_env["PYTHONPATH"] = (
                str(REPO_ROOT / "src")
                if not existing_pythonpath
                else os.pathsep.join((str(REPO_ROOT / "src"), existing_pythonpath))
            )
            init_env.update(
                {
                    "ORW_SETUP_JSON": setup_payload,
                    "ORW_PROVIDER_USER": "jane-researcher",
                }
            )
            subprocess.run(
                [sys.executable, str(generated / "scripts" / "initialize_project.py")],
                cwd=generated,
                env=init_env,
                check=True,
                capture_output=True,
                text=True,
            )

            report = validate_workspace(generated)
            self.assertTrue(report.valid, report.issues)
            self.assertTrue((generated / ".research" / "initialized").is_file())
            self.assertTrue(
                (
                    generated
                    / "studies"
                    / "light-exposure-study"
                    / "assays"
                    / "behaviour"
                    / "README.md"
                ).is_file()
            )
            self.assertTrue(
                (generated / ".research" / "template-readme.md").is_file()
            )
            self.assertTrue(
                (generated / ".research" / "template-project.yml").is_file()
            )
            self.assertTrue(
                (generated / ".research" / "template-workspace.yml").is_file()
            )

    def test_compare_mode_detects_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            generated = self._build(tmp_path)
            published = tmp_path / "published"
            shutil.copytree(generated, published)

            clean = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--output",
                    str(tmp_path / "check"),
                    "--core-revision",
                    TEST_REVISION,
                    "--force",
                    "--check-against",
                    str(published),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(clean.returncode, 0, clean.stderr)

            (published / "README.md").write_text("drift\n", encoding="utf-8")
            drift = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--output",
                    str(tmp_path / "check"),
                    "--core-revision",
                    TEST_REVISION,
                    "--force",
                    "--check-against",
                    str(published),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(drift.returncode, 1)
            self.assertIn("README.md", drift.stderr)


if __name__ == "__main__":
    unittest.main()
