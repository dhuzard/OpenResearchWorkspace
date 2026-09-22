"""Regression tests for the public filesystem mutation boundaries."""
from __future__ import annotations

from dataclasses import replace
from importlib.resources import files
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import SetupConfig, create_workspace, initialize_template, SetupValidationError
from orw.export.rocrate import export_rocrate, ROCrateExportError, MARKER
from orw.fs_safety import inventory


class ReleaseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = SetupConfig.from_mapping(json.loads((ROOT / "tests/fixtures/setup/basic.json").read_text(encoding="utf-8")))
        self.workspace = self.root / "study"
        self.output = self.root / "crate"

    def create(self):
        create_workspace(self.config, self.workspace)
        return self.workspace

    def export(self, **kwargs):
        return export_rocrate(self.workspace, self.output, date_published="2026-09-22", **kwargs)

    def resource(self, path, access):
        target = self.workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("scientific evidence\n", encoding="utf-8")
        return {"name": path, "path": path, "access": access}

    def project(self, resources):
        path = self.workspace / ".research/project.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["resources"] = resources
        path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    def test_existing_readme_is_preserved(self):
        self.workspace.mkdir()
        (self.workspace / "README.md").write_text("Irreplaceable original overview", encoding="utf-8")
        before = inventory(self.workspace)
        with self.assertRaises(SetupValidationError):
            create_workspace(self.config, self.workspace)
        self.assertEqual(inventory(self.workspace), before)

    def test_any_nonempty_unmarked_directory_is_preserved(self):
        self.workspace.mkdir()
        (self.workspace / "notes.txt").write_text("notes", encoding="utf-8")
        with self.assertRaises(SetupValidationError):
            create_workspace(self.config, self.workspace)
        self.assertEqual(sorted(p.name for p in self.workspace.iterdir()), ["notes.txt"])

    def test_directly_constructed_invalid_config_does_not_write(self):
        with self.assertRaises(SetupValidationError):
            create_workspace(replace(self.config, project_title=""), self.workspace)
        self.assertFalse(self.workspace.exists())

    def template(self):
        self.workspace.mkdir()
        (self.workspace / ".research").mkdir()
        for name in ("project.yml", "workspace.yml"):
            (self.workspace / ".research" / name).write_bytes(files("orw").joinpath("templates", name).read_bytes())
        (self.workspace / "README.md").write_text("Original template overview", encoding="utf-8")

    def test_template_originals_are_preserved(self):
        self.template()
        before = (self.workspace / ".research/project.yml").read_bytes()
        initialize_template(self.config, self.workspace)
        self.assertEqual((self.workspace / ".research/template-project.yml").read_bytes(), before)
        self.assertEqual((self.workspace / ".research/template-readme.md").read_text(encoding="utf-8"), "Original template overview")
        self.assertTrue((self.workspace / ".research/initialized").is_file())

    def test_edited_template_metadata_are_refused(self):
        self.template()
        path = self.workspace / ".research/project.yml"
        path.write_text(path.read_text(encoding="utf-8") + "\n# real project edit\n", encoding="utf-8")
        before = inventory(self.workspace)
        with self.assertRaises(SetupValidationError):
            initialize_template(self.config, self.workspace)
        self.assertEqual(inventory(self.workspace), before)

    def test_force_cannot_replace_any_source_subdirectory(self):
        self.create()
        before = inventory(self.workspace)
        for path in (self.workspace, self.workspace / "studies", self.workspace / "results", self.workspace / ".research"):
            with self.subTest(path=path), self.assertRaises(ROCrateExportError):
                export_rocrate(self.workspace, path, force=True)
        self.assertEqual(inventory(self.workspace), before)

    def test_force_cannot_replace_source_parent(self):
        self.create()
        with self.assertRaises(ROCrateExportError):
            export_rocrate(self.workspace, self.root, force=True)
        self.assertTrue((self.workspace / "README.md").is_file())

    def test_force_cannot_replace_unrelated_directory(self):
        self.create()
        self.output.mkdir()
        (self.output / "keep.txt").write_text("keep", encoding="utf-8")
        before = inventory(self.output)
        with self.assertRaises(ROCrateExportError):
            self.export(force=True)
        self.assertEqual(inventory(self.output), before)

    def test_force_replaces_unchanged_marked_export(self):
        self.create()
        self.export()
        self.assertTrue((self.output / MARKER).is_file())
        self.assertTrue(self.export(force=True).validation.valid)

    def test_added_or_edited_export_content_is_never_deleted(self):
        self.create()
        for mutation in ("added", "edited", "deleted"):
            with self.subTest(mutation=mutation):
                if self.output.exists():
                    shutil.rmtree(self.output)
                self.export()
                if mutation == "added":
                    (self.output / "notes.txt").write_text("new notes", encoding="utf-8")
                elif mutation == "edited":
                    (self.output / "README.md").write_text("new notes", encoding="utf-8")
                else:
                    (self.output / "README.md").unlink()
                before = inventory(self.output)
                with self.assertRaises(ROCrateExportError):
                    self.export(force=True)
                self.assertEqual(inventory(self.output), before)

    def test_failed_final_rename_restores_previous_export(self):
        self.create()
        self.export()
        before = inventory(self.output)
        rename = Path.rename
        def fail_stage(path, target):
            if path.name == "crate" and path.parent.name.startswith(".orw-export-"):
                raise OSError("injected final promotion failure")
            return rename(path, target)
        with patch.object(Path, "rename", fail_stage), self.assertRaises(OSError):
            self.export(force=True)
        self.assertEqual(inventory(self.output), before)

    def test_private_child_of_open_directory_is_refused(self):
        self.create()
        for access in ("private", "restricted", "embargoed", "unknown"):
            with self.subTest(access=access):
                child = self.resource("data/private.csv", access)
                self.project([{"name": "Open folder", "path": "data", "access": "open"}, child])
                before = inventory(self.workspace)
                with self.assertRaises(ROCrateExportError) as caught:
                    self.export()
                self.assertEqual(caught.exception.code, "conflicting_access")
                self.assertFalse(self.output.exists())
                self.assertEqual(inventory(self.workspace), before)

    def test_open_child_cannot_override_private_parent(self):
        self.create()
        child = self.resource("data/open.csv", "open")
        self.project([{"name": "Private folder", "path": "data", "access": "private"}, child])
        with self.assertRaises(ROCrateExportError):
            self.export()
        self.assertFalse(self.output.exists())

    def test_symlinked_readme_is_not_copied(self):
        self.create()
        secret = self.root / "secret.txt"
        secret.write_text("secret", encoding="utf-8")
        (self.workspace / "README.md").unlink()
        try:
            (self.workspace / "README.md").symlink_to(secret)
        except OSError:
            self.skipTest("OS account cannot create symlinks")
        with self.assertRaises(ROCrateExportError):
            self.export()
        self.assertFalse(self.output.exists())

    def test_init_symlink_destination_is_refused(self):
        other = self.root / "other"
        other.mkdir()
        try:
            self.workspace.symlink_to(other, target_is_directory=True)
        except OSError:
            self.skipTest("OS account cannot create symlinks")
        with self.assertRaises(SetupValidationError):
            create_workspace(self.config, self.workspace)
        self.assertEqual(list(other.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
