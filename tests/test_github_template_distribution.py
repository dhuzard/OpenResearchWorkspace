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
            for name in (
                "orw-setup.yml",
                "orw-add-study.yml",
                "orw-add-assay.yml",
                "orw-register-data.yml",
                "orw-add-contributor.yml",
                "orw-check-workspace.yml",
            ):
                self.assertTrue(
                    (generated / ".github" / "ISSUE_TEMPLATE" / name).is_file(),
                    name,
                )
            self.assertTrue(
                (generated / ".github" / "workflows" / "project-actions.yml").is_file()
            )
            self.assertTrue(
                (generated / "scripts" / "handle_project_action.py").is_file()
            )

    def test_generated_adapter_initializes_with_local_canonical_core(self) -> None:
        issue_body = """### Project title
Effects of light exposure on mouse activity

### What is this project about?
Study of how altered light exposure affects spontaneous mouse activity.

### Your name
Jane Researcher

### Your ORCID (optional)
0000-0002-1825-0097

### How is this research organized?
One Study — this project is essentially one Study

### First Study title (optional)
_No response_

### Do your Studies contain several distinct measurement types?
Yes — use an Assays layer for several measurement types

### Do you want to keep protocol documents in this workspace?
Yes — create a protocols folder

### Where are the authoritative or raw data stored?
Institutional research server

### Current data access
private

### Keywords (optional)
behaviour, circadian rhythm, mouse

### Ready to create the workspace
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
            study = (
                generated
                / "studies"
                / "effects-of-light-exposure-on-mouse-activity"
            )
            self.assertTrue((study / "assays" / "README.md").is_file())
            self.assertTrue((study / "protocols" / "README.md").is_file())
            self.assertFalse((study / "assays" / "behaviour").exists())

            project = (generated / ".research" / "project.yml").read_text(
                encoding="utf-8"
            )
            workspace = (generated / ".research" / "workspace.yml").read_text(
                encoding="utf-8"
            )
            self.assertIn("    assays: []", project)
            self.assertIn('study_structure: "single"', workspace)
            self.assertIn('assay_structure: "multiple"', workspace)
            self.assertIn('protocol_storage: "workspace"', workspace)
            self.assertTrue(
                (generated / ".research" / "template-readme.md").is_file()
            )
            self.assertTrue(
                (generated / ".research" / "template-project.yml").is_file()
            )
            self.assertTrue(
                (generated / ".research" / "template-workspace.yml").is_file()
            )

    def test_generated_post_init_actions_use_canonical_mutation_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            generated = self._build(tmp_path)

            setup_payload = {
                "project_title": "Effects of light exposure on mouse activity",
                "project_description": "Synthetic workflow test.",
                "creator": {"name": "Jane Researcher", "orcid": None},
                "first_study": {"title": "Light exposure study"},
                "first_assay": None,
                "data": {
                    "location": "Institutional research server",
                    "access": "private",
                },
                "keywords": ["mouse"],
                "workspace_options": {
                    "study_structure": "multiple",
                    "assay_structure": "multiple",
                    "protocol_storage": "workspace",
                },
            }

            init_env = os.environ.copy()
            existing_pythonpath = init_env.get("PYTHONPATH")
            init_env["PYTHONPATH"] = (
                str(REPO_ROOT / "src")
                if not existing_pythonpath
                else os.pathsep.join((str(REPO_ROOT / "src"), existing_pythonpath))
            )
            init_env["ORW_SETUP_JSON"] = json.dumps(setup_payload)
            init_env["ORW_PROVIDER_USER"] = "jane-researcher"
            subprocess.run(
                [sys.executable, str(generated / "scripts" / "initialize_project.py")],
                cwd=generated,
                env=init_env,
                check=True,
                capture_output=True,
                text=True,
            )

            def action(title: str, body: str):
                event = tmp_path / "action-event.json"
                output = tmp_path / "action-output.txt"
                response = tmp_path / "action-response.md"
                event.write_text(
                    json.dumps({"issue": {"title": title, "body": body}}),
                    encoding="utf-8",
                )
                output.write_text("", encoding="utf-8")
                response.unlink(missing_ok=True)
                env = init_env.copy()
                env.update(
                    {
                        "GITHUB_EVENT_PATH": str(event),
                        "GITHUB_OUTPUT": str(output),
                        "ORW_RESPONSE_PATH": str(response),
                        "GITHUB_REPOSITORY": "example/research-project",
                    }
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        str(generated / "scripts" / "handle_project_action.py"),
                    ],
                    cwd=generated,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                return result, output.read_text(encoding="utf-8"), response.read_text(
                    encoding="utf-8"
                )

            result, output, response = action(
                "[ORW Add Study] Follow-up cohort",
                """### New Study title
Follow-up cohort

### Short Study description (optional)
A distinct follow-up cohort.
""",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("changed=true", output)
            self.assertIn("Study added", response)
            self.assertTrue((generated / "studies" / "follow-up-cohort").is_dir())

            result, output, response = action(
                "[ORW Add Assay] ECG",
                """### Which Study?
Light exposure study

### Measurement / Assay name
ECG

### Short description (optional)
Cardiac recording.
""",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("changed=true", output)
            self.assertIn("Measurement / Assay added", response)
            self.assertTrue(
                (
                    generated
                    / "studies"
                    / "light-exposure-study"
                    / "assays"
                    / "ecg"
                ).is_dir()
            )

            result, output, response = action(
                "[ORW Register Data] Home-cage recordings",
                """### Data source name
Home-cage recordings

### Where are these data stored?
Institutional archive

### Current data access
restricted

### Persistent identifier or public URL (optional)
_No response_

### Short description (optional)
Primary behavioural recordings.
""",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("changed=true", output)
            self.assertIn("Data source registered", response)

            result, output, response = action(
                "[ORW Add Contributor] Ada Lovelace",
                """### Contributor name
Ada Lovelace

### Role (optional)
Data analysis

### ORCID (optional)
0000-0002-1825-0097

### Affiliation (optional)
Example Research Institute
""",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("changed=true", output)
            self.assertIn("Contributor added", response)

            result, output, response = action(
                "[ORW Check] Validate workspace",
                """### Run the check
- [x] Check this workspace now.
""",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("changed=false", output)
            self.assertIn("ok=true", output)
            self.assertIn("Workspace check passed", response)

            report = validate_workspace(generated)
            self.assertTrue(report.valid, report.issues)

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
