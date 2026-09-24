from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from orw.initialize import (  # noqa: E402
    ImplementationContext,
    WorkspaceAlreadyInitialized,
    create_workspace,
    initialize_template,
)
from orw.model import SetupConfig, SetupValidationError  # noqa: E402
from orw.validate import validate_workspace  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "setup"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class SetupModelTests(unittest.TestCase):
    def test_basic_payload_normalizes(self) -> None:
        config = SetupConfig.from_mapping(load_fixture("basic.json"))
        self.assertEqual(config.project_title, "Effects of light exposure on mouse activity")
        self.assertEqual(config.first_study.title, "Light exposure study")
        self.assertEqual(config.first_assay.title if config.first_assay else None, "Behaviour")
        self.assertEqual(
            config.keywords,
            ("behaviour", "circadian rhythm", "mouse"),
        )

    def test_workspace_options_normalize(self) -> None:
        payload = load_fixture("no-assay.json")
        payload["workspace_options"] = {
            "study_structure": "single",
            "assay_structure": "single_or_none",
            "protocol_storage": "elsewhere",
        }
        config = SetupConfig.from_mapping(payload)
        self.assertEqual(config.workspace_options.study_structure, "single")
        self.assertEqual(config.workspace_options.assay_structure, "single_or_none")
        self.assertEqual(config.workspace_options.protocol_storage, "elsewhere")

    def test_invalid_orcid_is_rejected(self) -> None:
        with self.assertRaises(SetupValidationError):
            SetupConfig.from_mapping(load_fixture("invalid-orcid.json"))

    def test_no_assay_is_valid(self) -> None:
        config = SetupConfig.from_mapping(load_fixture("no-assay.json"))
        self.assertIsNone(config.first_assay)


class WorkspaceGenerationTests(unittest.TestCase):
    def _generate(
        self,
        fixture: str,
        root: Path,
        *,
        provider: bool = False,
    ):
        config = SetupConfig.from_mapping(load_fixture(fixture))
        context = (
            ImplementationContext(provider="github", provider_user="jane")
            if provider
            else None
        )
        result = create_workspace(config, root, implementation=context)
        return config, result

    def test_basic_workspace_uses_canonical_schema_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, result = self._generate("basic.json", root, provider=True)

            project = (root / ".research" / "project.yml").read_text(encoding="utf-8")
            workspace = (root / ".research" / "workspace.yml").read_text(encoding="utf-8")

            self.assertIn('spec_version: "0.1"', project)
            self.assertIn("\ninvestigation:\n", project)
            self.assertIn("\nstudies:\n", project)
            self.assertNotIn("\n  studies:\n", project)
            self.assertIn('identifier: "light-exposure-study"', project)
            self.assertIn('identifier: "behaviour"', project)
            self.assertIn('type: "dataset"', project)
            self.assertNotIn("github_login", project)

            self.assertIn('generator: "orw-core"', workspace)
            self.assertIn('name: "github"', workspace)
            self.assertIn('user: "jane"', workspace)

            self.assertEqual(result.study_identifier, "light-exposure-study")
            self.assertEqual(result.assay_identifier, "behaviour")

    def test_orcid_and_keywords_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._generate("orcid-keywords.json", root)
            project = (root / ".research" / "project.yml").read_text(encoding="utf-8")

            self.assertIn('orcid: "0000-0002-1825-0097"', project)
            self.assertIn('- "ECG"', project)
            self.assertIn('- "HRV"', project)
            self.assertIn('- "mouse"', project)

    def test_restricted_external_data_remains_a_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._generate("restricted-external-data.json", root)
            project = (root / ".research" / "project.yml").read_text(encoding="utf-8")

            self.assertIn('location: "s3://institutional-restricted/imaging"', project)
            self.assertIn('access: "restricted"', project)
            self.assertFalse((root / "s3:").exists())

    def test_no_assay_workspace_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, result = self._generate("no-assay.json", root)
            project = (root / ".research" / "project.yml").read_text(encoding="utf-8")

            self.assertIsNone(result.assay_identifier)
            self.assertIn("    assays: []", project)
            self.assertTrue(
                (root / "studies" / result.study_identifier / "assays" / "README.md").is_file()
            )

    def test_simple_workspace_omits_unneeded_assay_and_protocol_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = load_fixture("no-assay.json")
            payload["project_title"] = "Simple observational project"
            payload["first_study"]["title"] = "Simple observational project"
            payload["workspace_options"] = {
                "study_structure": "single",
                "assay_structure": "single_or_none",
                "protocol_storage": "elsewhere",
            }
            config = SetupConfig.from_mapping(payload)
            result = create_workspace(config, root)

            study = root / "studies" / result.study_identifier
            workspace = (root / ".research" / "workspace.yml").read_text(encoding="utf-8")
            readme = (root / "README.md").read_text(encoding="utf-8")

            self.assertIsNone(config.first_assay)
            self.assertFalse((study / "assays").exists())
            self.assertFalse((study / "protocols").exists())
            self.assertTrue((study / "data").is_dir())
            self.assertTrue((study / "analysis").is_dir())
            self.assertTrue((study / "results").is_dir())

            self.assertIn('study_structure: "single"', workspace)
            self.assertIn('assay_structure: "single_or_none"', workspace)
            self.assertIn('protocol_storage: "elsewhere"', workspace)
            self.assertIn("Your OpenResearchWorkspace is initialized", readme)
            self.assertIn("## Start here", readme)
            self.assertIn("No separate Assay layer", readme)

    def test_template_initialization_preserves_legacy_human_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            research = root / ".research"
            research.mkdir()
            project_source = REPO_ROOT / "src" / "orw" / "templates" / "project.yml"
            (research / "project.yml").write_bytes(project_source.read_bytes())
            (research / "workspace.yml").write_text(
                'orw:\n'
                '  spec_version: "0.1"\n'
                '  template_version: "0.1.0"\n'
                '  initialized: false\n'
                '  initialized_at: null\n'
                '\n'
                'implementation:\n'
                '  primary_reference: github-template\n'
                '  canonical_project_record: ".research/project.yml"\n'
                '  capabilities_record: ".research/capabilities.yml"\n',
                encoding="utf-8",
            )

            (root / "README.md").write_text(
                "# Legacy ORW template\n\nResearcher-facing setup overview.\n",
                encoding="utf-8",
            )
            legacy_project_docs = (
                "# Project documentation\n\n"
                "Legacy template guidance that must be preserved, not overwritten.\n"
            )
            legacy_references = (
                "# References\n\n"
                "Legacy reference guidance that must be preserved, not overwritten.\n"
            )
            (root / "project-docs").mkdir()
            (root / "project-docs" / "README.md").write_text(
                legacy_project_docs,
                encoding="utf-8",
            )
            (root / "references").mkdir()
            (root / "references" / "README.md").write_text(
                legacy_references,
                encoding="utf-8",
            )
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"openresearchworkspace\"\n",
                encoding="utf-8",
            )
            legacy_workflow = root / ".github" / "workflows" / "release-checks.yml"
            legacy_workflow.parent.mkdir(parents=True)
            legacy_workflow.write_text(
                "name: Alpha release checks\non:\n  push:\n    branches: [main]\n",
                encoding="utf-8",
            )

            payload = load_fixture("no-assay.json")
            payload["workspace_options"] = {
                "study_structure": "single",
                "assay_structure": "single_or_none",
                "protocol_storage": "workspace",
            }
            config = SetupConfig.from_mapping(payload)
            result = initialize_template(
                config,
                root,
                implementation=ImplementationContext(
                    provider="github",
                    provider_user="legacy-user",
                ),
            )

            self.assertTrue((root / ".research" / "initialized").is_file())
            self.assertTrue((root / "studies" / result.study_identifier).is_dir())
            self.assertEqual(
                (root / "project-docs" / "README.md").read_text(encoding="utf-8"),
                legacy_project_docs,
            )
            self.assertEqual(
                (root / "references" / "README.md").read_text(encoding="utf-8"),
                legacy_references,
            )
            notice = (
                root / ".research" / "legacy-template-notice.md"
            ).read_text(encoding="utf-8")
            self.assertIn("release-checks.yml", notice)
            self.assertIn("root `LICENSE`", notice)
            generated_readme = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("Legacy template detected", generated_readme)
            self.assertNotIn("orw-add-study.yml", generated_readme)
            report = validate_workspace(root)
            self.assertTrue(report.valid, report.issues)

    def test_pre_core_initialized_workspace_is_identified_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            research = root / ".research"
            research.mkdir()
            (research / "project.yml").write_text(
                """spec_version: "0.1"

project:
  title: "Legacy project"
  description: "Created by the early GitHub initializer."
  status: active

investigation:
  title: "Legacy project"
  description: "Created by the early GitHub initializer."
  studies:
    - id: "study-01"
      title: "Study 1"
      path: "studies/study-01"
      assays: []

contributors:
  - name: "Researcher"

data: []
resources: []
outputs: []
related_identifiers: []
""",
                encoding="utf-8",
            )
            (research / "workspace.yml").write_text(
                """orw:
  spec_version: "0.1"
  template_version: "0.1.0"
  initialized: false
  initialized_at: null

implementation:
  primary_reference: github-template
  canonical_project_record: ".research/project.yml"
  capabilities_record: ".research/capabilities.yml"
""",
                encoding="utf-8",
            )
            (research / "initialized").write_text(
                "initialized: true\n",
                encoding="utf-8",
            )

            report = validate_workspace(root)
            self.assertFalse(report.valid)
            self.assertTrue(
                any(issue.code == "legacy_template_format" for issue in report.issues),
                report.issues,
            )

    def test_unicode_metadata_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config, _ = self._generate("unicode.json", root)
            project = (root / ".research" / "project.yml").read_text(encoding="utf-8")
            readme = (root / "README.md").read_text(encoding="utf-8")

            self.assertIn(config.project_title, project)
            self.assertIn("Élodie Müller", project)
            self.assertIn("Montpellier", project)
            self.assertIn(config.project_title, readme)

    def test_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = Path(first_tmp)
            second = Path(second_tmp)
            self._generate("basic.json", first, provider=True)
            self._generate("basic.json", second, provider=True)

            for relative in [
                Path(".research/project.yml"),
                Path(".research/workspace.yml"),
                Path(".research/initialized"),
                Path("README.md"),
            ]:
                self.assertEqual(
                    (first / relative).read_text(encoding="utf-8"),
                    (second / relative).read_text(encoding="utf-8"),
                )

    def test_reinitialization_is_refused_without_modification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._generate("reinitialize.json", root)
            before = (root / ".research" / "project.yml").read_bytes()
            config = SetupConfig.from_mapping(load_fixture("reinitialize.json"))

            with self.assertRaises(WorkspaceAlreadyInitialized):
                create_workspace(config, root)

            after = (root / ".research" / "project.yml").read_bytes()
            self.assertEqual(before, after)

    def test_validation_does_not_depend_on_github_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._generate("basic.json", root)

            github = root / ".github"
            github.mkdir()
            (github / "placeholder").write_text("adapter-only\n", encoding="utf-8")
            shutil.rmtree(github)

            report = validate_workspace(root)
            self.assertTrue(
                report.valid,
                msg="; ".join(issue.message for issue in report.issues),
            )


if __name__ == "__main__":
    unittest.main()
