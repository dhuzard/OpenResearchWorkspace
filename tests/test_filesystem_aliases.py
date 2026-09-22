"""Path normalization must support host aliases without hiding payload links."""
from __future__ import annotations
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import SetupConfig, create_workspace, mutate
from orw.export.rocrate import export_rocrate, ROCrateExportError
from orw.fs_safety import absolute_path, inventory


class FilesystemAliasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.config = SetupConfig.from_mapping(json.loads((ROOT / "tests/fixtures/setup/basic.json").read_text(encoding="utf-8")))

    def link(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except OSError:
            self.skipTest("OS account cannot create symlinks")

    def test_parent_alias_resolves_to_same_root(self):
        actual = self.root / "actual"
        actual.mkdir()
        alias = self.root / "alias"
        self.link(alias, actual, directory=True)
        result = create_workspace(self.config, alias / "study")
        self.assertEqual(result.destination, actual / "study")
        self.assertEqual(inventory(alias / "study"), inventory(actual / "study"))

    def test_output_alias_cannot_hide_overlap_with_source(self):
        workspace = self.root / "study"
        create_workspace(self.config, workspace)
        alias = self.root / "alias"
        self.link(alias, workspace, directory=True)
        before = inventory(workspace)
        with self.assertRaises(ROCrateExportError) as caught:
            export_rocrate(workspace, alias / "studies", force=True)
        self.assertEqual(caught.exception.code, "unsafe_output")
        self.assertEqual(inventory(workspace), before)

    def test_final_output_link_is_not_resolved_away(self):
        workspace = self.root / "study"
        create_workspace(self.config, workspace)
        destination = self.root / "elsewhere"
        destination.mkdir()
        alias = self.root / "alias"
        self.link(alias, destination, directory=True)
        self.assertEqual(absolute_path(alias), alias)
        with self.assertRaises(ROCrateExportError):
            export_rocrate(workspace, alias, force=True)
        self.assertEqual(list(destination.iterdir()), [])

    def test_mutations_work_below_a_parent_alias(self):
        """A plan may name a workspace reached through an aliased ancestor."""

        actual = self.root / "actual"
        actual.mkdir()
        alias = self.root / "alias"
        self.link(alias, actual, directory=True)
        create_workspace(self.config, actual / "study")

        planned = mutate.add_contributor(alias / "study", "Ada Lovelace", dry_run=True)
        self.assertFalse(planned.applied)

        applied = mutate.apply_plan(
            replace(planned.plan, workspace=alias / "study")
        )
        self.assertTrue(applied.valid, [issue.message for issue in applied.issues])
        record = (actual / "study/.research/project.yml").read_text(encoding="utf-8")
        self.assertIn("Ada Lovelace", record)

    def test_a_linked_workspace_root_is_still_refused(self):
        workspace = self.root / "study"
        create_workspace(self.config, workspace)
        alias = self.root / "alias"
        self.link(alias, workspace, directory=True)

        planned = mutate.add_contributor(workspace, "Ada Lovelace", dry_run=True)
        with self.assertRaises(mutate.MutationInputError):
            mutate.apply_plan(replace(planned.plan, workspace=alias))
        self.assertNotIn(
            "Ada Lovelace",
            (workspace / ".research/project.yml").read_text(encoding="utf-8"),
        )

    def test_nested_payload_symlink_is_still_rejected(self):
        workspace = self.root / "study"
        create_workspace(self.config, workspace)
        (workspace / "payload").mkdir()
        secret = self.root / "secret.txt"
        secret.write_text("secret", encoding="utf-8")
        self.link(workspace / "payload/reference.txt", secret)
        path = workspace / ".research/project.yml"
        project = yaml.safe_load(path.read_text(encoding="utf-8"))
        project["resources"] = [{"name": "Payload", "path": "payload", "access": "open"}]
        path.write_text(yaml.safe_dump(project), encoding="utf-8")
        output = self.root / "crate"
        with self.assertRaises(ROCrateExportError):
            export_rocrate(workspace, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
