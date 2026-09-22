"""The structural YAML editor must change only the lines an operation targets."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import edit  # noqa: E402

DOCUMENT = """spec_version: "0.1"

investigation:
  title: "Example"
  status: active
  keywords:
    - "one"

contributors:
  - name: "Ada"

studies:
  - identifier: "a"
    title: "A"
    assays: []

outputs: []
"""


class ScalarTests(unittest.TestCase):
    def test_quotes_deterministically(self) -> None:
        self.assertEqual(edit.scalar("plain"), '"plain"')
        self.assertEqual(edit.scalar('say "hi"'), '"say \\"hi\\""')
        self.assertEqual(edit.scalar("héllo 日本"), '"héllo 日本"')
        self.assertEqual(edit.scalar(None), "null")
        self.assertEqual(edit.scalar(True), "true")

    def test_rejects_unsupported_types(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.scalar(1.5)


class AppendTests(unittest.TestCase):
    def assert_only_added(self, before: str, after: str, added: list[str]) -> None:
        """Every original line survives in order; only *added* lines are new."""

        before_lines = before.splitlines()
        after_lines = after.splitlines()
        remaining = list(after_lines)
        for line in before_lines:
            self.assertIn(line, remaining, f"original line lost: {line!r}")
            remaining.remove(line)
        self.assertEqual(remaining, added)

    def test_appends_to_block_sequence(self) -> None:
        after = edit.append_item(DOCUMENT, ("studies",), {"identifier": "b", "title": "B"})
        self.assert_only_added(
            DOCUMENT, after, ['  - identifier: "b"', '    title: "B"']
        )
        self.assertEqual(len(yaml.safe_load(after)["studies"]), 2)

    def test_expands_an_empty_flow_sequence(self) -> None:
        after = edit.append_item(DOCUMENT, ("studies", 0, "assays"), {"identifier": "x"})
        self.assertIn('    assays:\n      - identifier: "x"\n', after)
        self.assertEqual(yaml.safe_load(after)["studies"][0]["assays"], [{"identifier": "x"}])

    def test_expands_a_top_level_empty_sequence(self) -> None:
        after = edit.append_item(DOCUMENT, ("outputs",), {"name": "figure"})
        self.assertIn('outputs:\n  - name: "figure"\n', after)

    def test_creates_a_missing_top_level_key(self) -> None:
        document = DOCUMENT.replace("contributors:\n  - name: \"Ada\"\n\n", "")
        after = edit.append_item(document, ("contributors",), {"name": "Ada"})
        self.assertEqual(yaml.safe_load(after)["contributors"], [{"name": "Ada"}])

    def test_creates_a_missing_nested_key(self) -> None:
        document = DOCUMENT.replace("    assays: []\n", "")
        after = edit.append_item(document, ("studies", 0, "assays"), {"identifier": "x"})
        self.assertEqual(yaml.safe_load(after)["studies"][0]["assays"], [{"identifier": "x"}])

    def test_keeps_a_comment_attached_to_the_following_key(self) -> None:
        document = (
            'studies:\n  - identifier: "a"\n\n'
            "# Outputs are reviewed before release.\noutputs: []\n"
        )
        after = edit.append_item(document, ("studies",), {"identifier": "b"})
        self.assertIn(
            '  - identifier: "b"\n\n# Outputs are reviewed before release.\noutputs: []\n',
            after,
        )

    def test_keeps_an_inline_comment(self) -> None:
        document = 'studies:\n  - identifier: "a"  # legacy identifier\n'
        after = edit.append_item(document, ("studies",), {"identifier": "b"})
        self.assertIn('  - identifier: "a"  # legacy identifier\n', after)

    def test_omits_keys_whose_value_is_absent(self) -> None:
        after = edit.append_item(
            DOCUMENT, ("contributors",), {"name": "Grace", "role": None, "orcid": None}
        )
        self.assertEqual(yaml.safe_load(after)["contributors"][1], {"name": "Grace"})

    def test_refuses_populated_flow_sequences(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.append_item("studies: [1, 2]\n", ("studies",), {"identifier": "x"})

    def test_refuses_a_non_sequence_target(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.append_item(DOCUMENT, ("investigation",), {"a": "b"})


class SetValueTests(unittest.TestCase):
    def test_replaces_a_quoted_scalar(self) -> None:
        after = edit.set_value(DOCUMENT, ("investigation", "title"), "Renamed")
        self.assertIn('  title: "Renamed"\n', after)
        self.assertNotIn("Example", after)

    def test_replaces_a_plain_scalar(self) -> None:
        after = edit.set_value(DOCUMENT, ("investigation", "status"), "completed")
        self.assertIn('  status: "completed"\n', after)

    def test_replaces_a_whole_sequence(self) -> None:
        after = edit.set_value(DOCUMENT, ("investigation", "keywords"), ["x", "y"])
        self.assertIn('  keywords:\n    - "x"\n    - "y"\n', after)

    def test_clears_a_sequence(self) -> None:
        after = edit.set_value(DOCUMENT, ("investigation", "keywords"), [])
        self.assertIn("  keywords: []\n", after)
        self.assertEqual(yaml.safe_load(after)["investigation"]["keywords"], [])

    def test_inserts_a_missing_key(self) -> None:
        after = edit.set_value(DOCUMENT, ("investigation", "description"), "New")
        self.assertEqual(yaml.safe_load(after)["investigation"]["description"], "New")

    def test_refuses_to_overwrite_a_collection_with_a_scalar(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.set_value(DOCUMENT, ("investigation", "keywords"), "one")


class DocumentTests(unittest.TestCase):
    def test_refuses_multiple_documents(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.compose("a: 1\n---\nb: 2\n")

    def test_refuses_a_non_mapping_root(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.compose("- 1\n- 2\n")

    def test_refuses_invalid_yaml(self) -> None:
        with self.assertRaises(edit.YamlEditError):
            edit.compose("a: [1,\n")


if __name__ == "__main__":
    unittest.main()
