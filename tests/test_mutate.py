"""Workspace mutations must be conflict-checked, reviewable and reversible."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import mutate  # noqa: E402
from orw.initialize import create_workspace  # noqa: E402
from orw.model import SetupConfig  # noqa: E402
from orw.validate import validate_workspace  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "setup"


def setup(name: str = "basic") -> SetupConfig:
    return SetupConfig.from_mapping(
        json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    )


class WorkspaceCase(unittest.TestCase):
    fixture = "basic"

    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="orw-mutate-test-")
        self.addCleanup(self._temporary.cleanup)
        self.workspace = Path(self._temporary.name) / "workspace"
        self.result = create_workspace(setup(self.fixture), self.workspace)

    @property
    def record(self) -> Path:
        return self.workspace / ".research" / "project.yml"

    def project(self) -> dict:
        return yaml.safe_load(self.record.read_text(encoding="utf-8"))

    def assert_valid(self) -> None:
        report = validate_workspace(self.workspace)
        self.assertTrue(report.valid, [issue.message for issue in report.issues])


class AddStudyTests(WorkspaceCase):
    def test_records_and_scaffolds_a_study(self) -> None:
        result = mutate.add_study(self.workspace, "Sleep deprivation")
        self.assertTrue(result.applied)
        self.assertEqual(result.plan.identifier, "sleep-deprivation")

        identifiers = [study["identifier"] for study in self.project()["studies"]]
        self.assertIn("sleep-deprivation", identifiers)

        folder = self.workspace / "studies" / "sleep-deprivation"
        for expected in ("README.md", "data/raw", "protocols", "analysis", "results"):
            self.assertTrue((folder / expected).exists(), expected)
        self.assert_valid()

    def test_added_study_matches_the_layout_initialization_writes(self) -> None:
        """A Study added later must not be a second-class citizen."""

        mutate.add_study(self.workspace, "Sleep deprivation")
        initial = self.workspace / "studies" / self.result.study_identifier
        added = self.workspace / "studies" / "sleep-deprivation"
        expected = {
            path.relative_to(initial).as_posix()
            for path in initial.rglob("*")
            if "assays" not in path.relative_to(initial).parts
        }
        actual = {
            path.relative_to(added).as_posix()
            for path in added.rglob("*")
            if "assays" not in path.relative_to(added).parts
        }
        self.assertEqual(expected, actual)

    def test_dry_run_writes_nothing(self) -> None:
        before = self.record.read_bytes()
        result = mutate.add_study(self.workspace, "Sleep deprivation", dry_run=True)

        self.assertFalse(result.applied)
        self.assertEqual(self.record.read_bytes(), before)
        self.assertFalse((self.workspace / "studies" / "sleep-deprivation").exists())
        self.assertIn('+  - identifier: "sleep-deprivation"', result.plan.diff())
        self.assertIn(
            "studies/sleep-deprivation/data/raw", result.plan.new_directories
        )

    def test_dry_run_plan_matches_what_applying_writes(self) -> None:
        planned = mutate.add_study(self.workspace, "Sleep deprivation", dry_run=True)
        applied = mutate.add_study(self.workspace, "Sleep deprivation")
        self.assertEqual(planned.plan.record_after, applied.plan.record_after)
        self.assertEqual(planned.plan.new_directories, applied.plan.new_directories)
        self.assertEqual(
            self.record.read_text(encoding="utf-8").replace("\r\n", "\n"),
            planned.plan.record_after,
        )

    def test_only_the_new_lines_change(self) -> None:
        before = self.record.read_text(encoding="utf-8")
        mutate.add_study(self.workspace, "Sleep deprivation")
        after = self.record.read_text(encoding="utf-8")
        removed = [
            line for line in before.splitlines() if line not in after.splitlines()
        ]
        self.assertEqual(removed, [])

    def test_refuses_a_duplicate_identifier(self) -> None:
        mutate.add_study(self.workspace, "Sleep deprivation")
        before = self.record.read_bytes()
        with self.assertRaises(mutate.MutationConflict):
            mutate.add_study(self.workspace, "Sleep Deprivation")
        self.assertEqual(self.record.read_bytes(), before)

    def test_refuses_a_non_empty_target_folder(self) -> None:
        folder = self.workspace / "studies" / "sleep-deprivation"
        folder.mkdir(parents=True)
        (folder / "existing.csv").write_text("keep me", encoding="utf-8")

        with self.assertRaises(mutate.MutationConflict):
            mutate.add_study(self.workspace, "Sleep deprivation")
        self.assertEqual((folder / "existing.csv").read_text(encoding="utf-8"), "keep me")

    def test_refuses_a_path_that_overlaps_an_existing_study(self) -> None:
        with self.assertRaises(mutate.MutationConflict):
            mutate.add_study(
                self.workspace,
                "Nested",
                path=f"studies/{self.result.study_identifier}/inner",
            )

    def test_refuses_an_identifier_that_is_not_a_slug(self) -> None:
        for bad in ("Sleep Deprivation", "sleep_deprivation", "../escape"):
            with self.subTest(bad=bad):
                with self.assertRaises(mutate.MutationInputError):
                    mutate.add_study(self.workspace, "Sleep", identifier=bad)

    def test_refuses_a_path_inside_the_research_folder(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_study(self.workspace, "Sneaky", path=".research/studies/x")

    def test_refuses_an_escaping_path(self) -> None:
        for bad in ("../outside", "/absolute", "studies/../../escape"):
            with self.subTest(bad=bad):
                with self.assertRaises(mutate.MutationInputError):
                    mutate.add_study(self.workspace, "Sneaky", path=bad)

    def test_refuses_a_title_without_usable_characters(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_study(self.workspace, "???")


class AddAssayTests(WorkspaceCase):
    def test_records_and_scaffolds_an_assay(self) -> None:
        result = mutate.add_assay(
            self.workspace, self.result.study_identifier, "Open field"
        )
        self.assertTrue(result.applied)

        study = self.project()["studies"][0]
        self.assertIn("open-field", [assay["identifier"] for assay in study["assays"]])
        folder = self.workspace / study["path"] / "assays" / "open-field"
        for expected in ("README.md", "data/raw", "analysis", "results"):
            self.assertTrue((folder / expected).exists(), expected)
        self.assert_valid()

    def test_refuses_an_unknown_study(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_assay(self.workspace, "no-such-study", "Open field")

    def test_refuses_a_duplicate_assay_within_the_study(self) -> None:
        mutate.add_assay(self.workspace, self.result.study_identifier, "Open field")
        with self.assertRaises(mutate.MutationConflict):
            mutate.add_assay(self.workspace, self.result.study_identifier, "Open field")

    def test_allows_the_same_assay_identifier_in_a_different_study(self) -> None:
        mutate.add_assay(self.workspace, self.result.study_identifier, "Open field")
        mutate.add_study(self.workspace, "Second study")
        mutate.add_assay(self.workspace, "second-study", "Open field")
        self.assert_valid()

    def test_refuses_an_assay_path_outside_its_study(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_assay(
                self.workspace,
                self.result.study_identifier,
                "Elsewhere",
                path="studies/elsewhere",
            )

    def test_replaces_only_the_untouched_no_assay_note(self) -> None:
        mutate.add_study(self.workspace, "Second study")
        note = self.workspace / "studies" / "second-study" / "assays" / "README.md"
        self.assertIn("No Assay was initialized", note.read_text(encoding="utf-8"))

        mutate.add_assay(self.workspace, "second-study", "Open field")
        self.assertNotIn("No Assay was initialized", note.read_text(encoding="utf-8"))

    def test_keeps_an_edited_note(self) -> None:
        mutate.add_study(self.workspace, "Second study")
        note = self.workspace / "studies" / "second-study" / "assays" / "README.md"
        note.write_text("# Assays\n\nOur lab's own notes.\n", encoding="utf-8")

        mutate.add_assay(self.workspace, "second-study", "Open field")
        self.assertIn("Our lab's own notes.", note.read_text(encoding="utf-8"))


class AddAssayWithoutStudyPathTests(unittest.TestCase):
    def test_requires_an_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            create_workspace(setup(), workspace)
            record = workspace / ".research" / "project.yml"
            text = record.read_text(encoding="utf-8")
            record.write_text(
                text.replace('    path: "studies/light-exposure-study"\n', ""),
                encoding="utf-8",
            )

            with self.assertRaises(mutate.MutationInputError):
                mutate.add_assay(workspace, "light-exposure-study", "Open field")

            result = mutate.add_assay(
                workspace,
                "light-exposure-study",
                "Open field",
                path="studies/light-exposure-study/assays/open-field",
            )
            self.assertTrue(result.applied)


class RegisterResourceTests(WorkspaceCase):
    def test_registers_an_external_resource(self) -> None:
        mutate.register_resource(
            self.workspace,
            "Imaging archive",
            kind="dataset",
            location="https://example.org/archive",
            access="restricted",
        )
        names = [item["name"] for item in self.project()["resources"]]
        self.assertIn("Imaging archive", names)
        self.assert_valid()

    def test_registers_an_output(self) -> None:
        mutate.register_resource(
            self.workspace,
            "Protocols",
            collection="outputs",
            path=f"studies/{self.result.study_identifier}/protocols",
        )
        self.assertEqual(self.project()["outputs"][0]["name"], "Protocols")
        self.assert_valid()

    def test_refuses_a_path_that_does_not_exist(self) -> None:
        with self.assertRaises(mutate.MutationConflict):
            mutate.register_resource(self.workspace, "Missing", path="studies/nothing")

    def test_refuses_a_resource_with_no_reference(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.register_resource(self.workspace, "Vague", kind="dataset")

    def test_refuses_a_duplicate_name(self) -> None:
        with self.assertRaises(mutate.MutationConflict):
            mutate.register_resource(
                self.workspace,
                "Authoritative/raw research data",
                location="somewhere else",
            )

    def test_refuses_an_unknown_access_level(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.register_resource(
                self.workspace, "Archive", location="elsewhere", access="secret"
            )

    def test_refuses_an_unknown_collection(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.register_resource(
                self.workspace, "Archive", collection="inputs", location="elsewhere"
            )


class AddContributorTests(WorkspaceCase):
    def test_records_a_contributor(self) -> None:
        mutate.add_contributor(
            self.workspace, "Ada Lovelace", role="Analyst", orcid="0000-0002-1825-0097"
        )
        contributors = self.project()["contributors"]
        self.assertEqual(contributors[-1]["name"], "Ada Lovelace")
        self.assertEqual(contributors[-1]["orcid"], "0000-0002-1825-0097")
        self.assert_valid()

    def test_refuses_a_duplicate_name(self) -> None:
        mutate.add_contributor(self.workspace, "Ada Lovelace")
        with self.assertRaises(mutate.MutationConflict):
            mutate.add_contributor(self.workspace, "  ada   lovelace ")

    def test_refuses_a_duplicate_orcid_under_another_name(self) -> None:
        mutate.add_contributor(self.workspace, "Ada Lovelace", orcid="0000-0002-1825-0097")
        with self.assertRaises(mutate.MutationConflict):
            mutate.add_contributor(
                self.workspace, "A. Lovelace", orcid="https://orcid.org/0000-0002-1825-0097"
            )

    def test_refuses_a_malformed_orcid(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_contributor(self.workspace, "Ada", orcid="0000-0002-1825")


class UpdateMetadataTests(WorkspaceCase):
    def test_updates_only_the_fields_given(self) -> None:
        before = self.project()["investigation"]
        mutate.update_project_metadata(self.workspace, status="completed")
        after = self.project()["investigation"]

        self.assertEqual(after["status"], "completed")
        self.assertEqual(after["title"], before["title"])
        self.assertEqual(after["keywords"], before["keywords"])
        self.assert_valid()

    def test_replaces_the_keyword_list(self) -> None:
        mutate.update_project_metadata(self.workspace, keywords=["sleep", "mouse"])
        self.assertEqual(self.project()["investigation"]["keywords"], ["sleep", "mouse"])

    def test_clears_the_keyword_list(self) -> None:
        mutate.update_project_metadata(self.workspace, keywords=[])
        self.assertEqual(self.project()["investigation"]["keywords"], [])
        self.assert_valid()

    def test_reports_no_change_without_writing(self) -> None:
        current = self.project()["investigation"]["title"]
        before = self.record.read_bytes()
        result = mutate.update_project_metadata(self.workspace, title=current)

        self.assertFalse(result.applied)
        self.assertEqual(self.record.read_bytes(), before)

    def test_refuses_an_unknown_status(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.update_project_metadata(self.workspace, status="finished")

    def test_refuses_an_empty_request(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.update_project_metadata(self.workspace)

    def test_refuses_duplicate_keywords(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.update_project_metadata(self.workspace, keywords=["a", "a"])


class PreconditionTests(WorkspaceCase):
    def test_refuses_an_invalid_workspace(self) -> None:
        (self.workspace / ".research" / "initialized").unlink()
        with self.assertRaises(mutate.WorkspaceNotValid) as caught:
            mutate.add_contributor(self.workspace, "Ada")
        self.assertEqual(caught.exception.stage, "before")

    def test_refuses_a_missing_workspace(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_contributor(self.workspace / "nowhere", "Ada")


class RollbackTests(WorkspaceCase):
    def test_restores_everything_when_the_result_would_be_invalid(self) -> None:
        """A plan that would break validation must leave no trace behind."""

        before = self.record.read_text(encoding="utf-8")
        broken = mutate.MutationPlan(
            workspace=self.workspace,
            operation="test.invalid",
            summary="declares a path that will not exist",
            identifier=None,
            record_before=before,
            record_after=before.replace(
                "outputs: []",
                'outputs:\n  - name: "Ghost"\n    path: "studies/ghost"',
            ),
            new_directories=("scratch", "scratch/inner"),
            new_files=(("scratch/inner/README.md", "# Scratch\n"),),
        )

        with self.assertRaises(mutate.WorkspaceNotValid) as caught:
            mutate.apply_plan(broken)

        self.assertEqual(caught.exception.stage, "after")
        self.assertEqual(self.record.read_text(encoding="utf-8"), before)
        self.assertFalse((self.workspace / "scratch").exists())
        self.assert_valid()

    def test_refuses_a_plan_built_from_a_stale_record(self) -> None:
        planned = mutate.add_study(self.workspace, "Sleep deprivation", dry_run=True)
        mutate.add_contributor(self.workspace, "Ada Lovelace")

        with self.assertRaises(mutate.MutationConflict):
            mutate.apply_plan(planned.plan)
        self.assertNotIn("sleep-deprivation", self.record.read_text(encoding="utf-8"))


class FormattingTests(WorkspaceCase):
    def test_preserves_comments_and_key_order(self) -> None:
        text = self.record.read_text(encoding="utf-8")
        self.record.write_text(
            "# Curated by the data steward. Do not reorder.\n" + text, encoding="utf-8"
        )
        mutate.add_contributor(self.workspace, "Ada Lovelace")

        updated = self.record.read_text(encoding="utf-8")
        self.assertTrue(updated.startswith("# Curated by the data steward."))
        self.assertIn('  role: "Project creator"', updated)

    def test_preserves_carriage_returns(self) -> None:
        text = self.record.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.record.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

        mutate.add_contributor(self.workspace, "Ada Lovelace")

        raw = self.record.read_bytes()
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        self.assertIn("Ada Lovelace", self.project()["contributors"][-1]["name"])

    def test_writes_unicode_faithfully(self) -> None:
        mutate.add_contributor(self.workspace, "Émilie du Châtelet — 日本")
        self.assertEqual(
            self.project()["contributors"][-1]["name"], "Émilie du Châtelet — 日本"
        )
        self.assert_valid()


if __name__ == "__main__":
    unittest.main()
