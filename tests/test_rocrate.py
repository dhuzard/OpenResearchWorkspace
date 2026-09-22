from __future__ import annotations
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import SetupConfig, create_workspace
from orw.export.rocrate import (ROCRATE_CONTEXT, ROCRATE_SPEC, ROCRATE_METADATA,
                               ROCrateExportError, export_rocrate, validate_rocrate)


def refs(entity, key):
    values = entity.get(key, [])
    if isinstance(values, dict):
        values = [values]
    return [value["@id"] for value in values]


class ROCrateExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace, self.crate = self.root / "workspace", self.root / "crate"

    def create(self, fixture="basic.json"):
        payload = json.loads((ROOT / "tests/fixtures/setup" / fixture).read_text(encoding="utf-8"))
        create_workspace(SetupConfig.from_mapping(payload), self.workspace)

    def project(self):
        return yaml.safe_load((self.workspace / ".research/project.yml").read_text(encoding="utf-8"))

    def save(self, project):
        (self.workspace / ".research/project.yml").write_text(yaml.safe_dump(project, allow_unicode=True), encoding="utf-8")

    def export(self, **kwargs):
        result = export_rocrate(self.workspace, self.crate, date_published="2026-09-21", **kwargs)
        self.document = json.loads((self.crate / ROCRATE_METADATA).read_text(encoding="utf-8"))
        self.entities = {e["@id"]: e for e in self.document["@graph"]}
        return result

    def test_basic_export_matches_golden_mapping(self):
        self.create()
        self.assertTrue(self.export().validation.valid)
        entities = []
        for entity in self.document["@graph"]:
            item = {"id": entity["@id"], "type": entity["@type"]}
            for key in ("name", "identifier"):
                if key in entity:
                    item[key] = entity[key]
            if "conditionsOfAccess" in entity:
                item["access"] = entity["conditionsOfAccess"]
            entities.append(item)
        root = self.entities["./"]
        actual = {"context": self.document["@context"], "root": {
            "id": "./", "type": root["@type"], "name": root["name"],
            "identifier": root["identifier"], "keywords": root["keywords"],
            "authors": refs(root, "author"), "hasPart": refs(root, "hasPart")},
            "entities": entities, "relations": {key: refs(value, "hasPart")
            for key, value in self.entities.items() if key.startswith("#study-") and refs(value, "hasPart")}}
        expected = json.loads((ROOT / "tests/fixtures/rocrate/basic.mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)
        self.assertEqual((self.workspace / ".research/project.yml").read_bytes(), (self.crate / ".research/project.yml").read_bytes())

    def test_metadata_descriptor_and_root_conform_to_13(self):
        self.create()
        self.export()
        self.assertEqual(self.document["@context"], ROCRATE_CONTEXT)
        descriptor = self.entities[ROCRATE_METADATA]
        self.assertEqual(descriptor["@type"], "CreativeWork")
        self.assertEqual(descriptor["about"], {"@id": "./"})
        self.assertEqual(descriptor["conformsTo"], {"@id": ROCRATE_SPEC})
        self.assertEqual(self.entities["./"]["@type"], "Dataset")
        self.assertEqual(self.entities["./"]["datePublished"], "2026-09-21")

    def test_contributor_orcid_becomes_person_identifier(self):
        self.create("orcid-keywords.json")
        self.export()
        identifier = "https://orcid.org/0000-0002-1825-0097"
        self.assertEqual(self.entities[identifier]["@type"], "Person")
        self.assertEqual(self.entities[identifier]["name"], "Alex Scientist")
        self.assertIn(identifier, refs(self.entities["./"], "author"))

    def test_no_assay_project_exports_without_synthetic_assay(self):
        self.create("no-assay.json")
        self.export()
        self.assertFalse(any(key.startswith("#assay-") for key in self.entities))
        self.assertIn("#study-protocol-design-study", self.entities)

    def test_multiple_studies_and_assays_remain_explicit(self):
        self.create()
        project = self.project()
        project["studies"][0]["assays"].append({"identifier": "ecg", "title": "ECG", "path": "studies/light-exposure-study/assays/ecg"})
        project["studies"].append({"identifier": "follow-up", "title": "Follow-up study", "path": "studies/follow-up",
                                   "assays": [{"identifier": "imaging", "title": "Imaging", "path": "studies/follow-up/assays/imaging"}]})
        for path in ("studies/light-exposure-study/assays/ecg", "studies/follow-up/assays/imaging"):
            (self.workspace / path).mkdir(parents=True)
        self.save(project)
        self.export()
        self.assertEqual(refs(self.entities["#study-light-exposure-study"], "hasPart"),
                         ["#assay-light-exposure-study-behaviour", "#assay-light-exposure-study-ecg"])
        self.assertEqual(refs(self.entities["#study-follow-up"], "hasPart"), ["#assay-follow-up-imaging"])

    def test_external_data_is_referenced_without_copy(self):
        self.create()
        project = self.project()
        identifier = "https://example.org/datasets/123"
        project["resources"] = [{"name": "External dataset", "location": identifier, "access": "open"}]
        self.save(project)
        self.export()
        self.assertIn(identifier, refs(self.entities["./"], "hasPart"))
        self.assertFalse((self.crate / "datasets/123").exists())

    def test_private_local_resource_is_not_copied(self):
        self.create()
        (self.workspace / "private.csv").write_text("private", encoding="utf-8")
        project = self.project()
        project["resources"] = [{"name": "Private source data", "path": "private.csv", "access": "private"}]
        self.save(project)
        self.export()
        self.assertFalse((self.crate / "private.csv").exists())
        self.assertEqual(self.entities["#resource-1"]["conditionsOfAccess"], "private")
        self.assertEqual(self.entities["#resource-1"]["identifier"], "private.csv")

    def test_open_local_and_external_resources_can_coexist(self):
        self.create()
        (self.workspace / "summary.csv").write_text("value\n3.2\n", encoding="utf-8")
        project = self.project()
        project["resources"] = [{"name": "Open summary", "path": "summary.csv", "access": "open"},
                                {"name": "External raw data", "location": "s3://research-bucket/raw-data", "access": "restricted"}]
        self.save(project)
        result = self.export()
        self.assertIn("summary.csv", result.copied_paths)
        self.assertTrue((self.crate / "summary.csv").is_file())
        self.assertEqual(self.entities["s3://research-bucket/raw-data"]["conditionsOfAccess"], "restricted")

    def test_local_path_ids_are_uri_encoded(self):
        self.create()
        (self.workspace / "almost 50%.csv").write_text("50", encoding="utf-8")
        project = self.project()
        project["resources"] = [{"name": "Encoded path", "path": "almost 50%.csv", "access": "open"}]
        self.save(project)
        self.export()
        self.assertIn("almost%2050%25.csv", self.entities)

    def test_invalid_workspace_is_refused_before_output(self):
        self.create()
        shutil.rmtree(self.workspace / "studies")
        with self.assertRaises(ROCrateExportError) as caught:
            self.export()
        self.assertEqual(caught.exception.code, "invalid_workspace")
        self.assertIsNotNone(caught.exception.workspace_report)
        self.assertFalse(self.crate.exists())

    def test_existing_output_requires_force(self):
        # Arbitrary old directories are NOT replaceable any more; regression
        # tests in test_release_safety exercise that intentional behavior change.
        self.create()
        self.export()
        with self.assertRaises(ROCrateExportError) as caught:
            self.export()
        self.assertEqual(caught.exception.code, "output_exists")
        self.assertTrue(self.export(force=True).validation.valid)

    def test_rocrate_validator_detects_missing_required_date(self):
        self.create()
        self.export()
        del self.entities["./"]["datePublished"]
        (self.crate / ROCRATE_METADATA).write_text(json.dumps(self.document), encoding="utf-8")
        report = validate_rocrate(self.crate)
        self.assertFalse(report.valid)
        self.assertIn("root_date_published", {issue.code for issue in report.errors})

    def test_generated_export_validates_with_only_license_warning(self):
        self.create()
        report = self.export().validation
        self.assertTrue(report.valid)
        self.assertEqual({item.code for item in report.warnings}, {"root_license"})


if __name__ == "__main__":
    unittest.main()
