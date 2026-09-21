from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from orw.export.rocrate import (  # noqa: E402
    ROCRATE_CONTEXT,
    ROCRATE_METADATA,
    ROCRATE_SPEC,
    ROCrateExportError,
    export_rocrate,
    validate_rocrate,
)
from orw.initialize import create_workspace  # noqa: E402
from orw.model import SetupConfig  # noqa: E402

SETUP_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "setup"
ROCRATE_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "rocrate"
FIXED_DATE = "2026-09-21"


def load_setup(name: str) -> SetupConfig:
    payload = json.loads((SETUP_FIXTURES / name).read_text(encoding="utf-8"))
    return SetupConfig.from_mapping(payload)


def create_fixture_workspace(root: Path, fixture: str = "basic.json") -> Path:
    workspace = root / "workspace"
    create_workspace(load_setup(fixture), workspace)
    return workspace


def load_project(workspace: Path) -> dict:
    data = yaml.safe_load(
        (workspace / ".research" / "project.yml").read_text(encoding="utf-8")
    )
    assert isinstance(data, dict)
    return data


def write_project(workspace: Path, project: dict) -> None:
    (workspace / ".research" / "project.yml").write_text(
        yaml.safe_dump(
            project,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def load_metadata(crate: Path) -> dict:
    return json.loads((crate / ROCRATE_METADATA).read_text(encoding="utf-8"))


def entity_map(document: dict) -> dict[str, dict]:
    return {
        entity["@id"]: entity
        for entity in document["@graph"]
        if isinstance(entity, dict) and isinstance(entity.get("@id"), str)
    }


def refs(entity: dict, key: str) -> list[str]:
    raw = entity.get(key, [])
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [
        item["@id"]
        for item in raw
        if isinstance(item, dict) and isinstance(item.get("@id"), str)
    ]


def semantic_projection(document: dict) -> dict:
    by_id = entity_map(document)
    root = by_id["./"]
    entities = []
    for entity in document["@graph"]:
        item = {
            "id": entity["@id"],
            "type": entity["@type"],
        }
        if "name" in entity:
            item["name"] = entity["name"]
        if "identifier" in entity:
            item["identifier"] = entity["identifier"]
        if "conditionsOfAccess" in entity:
            item["access"] = entity["conditionsOfAccess"]
        entities.append(item)

    return {
        "context": document["@context"],
        "root": {
            "id": root["@id"],
            "type": root["@type"],
            "name": root["name"],
            "identifier": root.get("identifier"),
            "keywords": root.get("keywords", []),
            "authors": refs(root, "author"),
            "hasPart": refs(root, "hasPart"),
        },
        "entities": entities,
        "relations": {
            identifier: refs(entity, "hasPart")
            for identifier, entity in by_id.items()
            if identifier.startswith("#study-") and refs(entity, "hasPart")
        },
    }


class ROCrateExportTests(unittest.TestCase):
    def test_basic_export_matches_golden_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            crate = root / "crate"

            result = export_rocrate(
                workspace,
                crate,
                date_published=FIXED_DATE,
            )

            self.assertTrue(result.validation.valid)
            self.assertTrue((crate / ROCRATE_METADATA).is_file())
            self.assertTrue((crate / ".research" / "project.yml").is_file())
            self.assertTrue((crate / "README.md").is_file())

            expected = json.loads(
                (ROCRATE_FIXTURES / "basic.mapping.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                semantic_projection(load_metadata(crate)),
                expected,
            )

    def test_metadata_descriptor_and_root_conform_to_13(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)

            document = load_metadata(crate)
            by_id = entity_map(document)
            descriptor = by_id[ROCRATE_METADATA]
            crate_root = by_id["./"]

            self.assertEqual(document["@context"], ROCRATE_CONTEXT)
            self.assertEqual(descriptor["@type"], "CreativeWork")
            self.assertEqual(descriptor["about"], {"@id": "./"})
            self.assertEqual(descriptor["conformsTo"], {"@id": ROCRATE_SPEC})
            self.assertEqual(crate_root["@type"], "Dataset")
            self.assertEqual(crate_root["datePublished"], FIXED_DATE)

    def test_contributor_orcid_becomes_person_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root, "orcid-keywords.json")
            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)

            by_id = entity_map(load_metadata(crate))
            orcid = "https://orcid.org/0000-0002-1825-0097"
            self.assertIn(orcid, by_id)
            self.assertEqual(by_id[orcid]["@type"], "Person")
            self.assertEqual(by_id[orcid]["name"], "Alex Scientist")
            self.assertIn(orcid, refs(by_id["./"], "author"))

    def test_no_assay_project_exports_without_synthetic_assay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root, "no-assay.json")
            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)

            by_id = entity_map(load_metadata(crate))
            assay_ids = [identifier for identifier in by_id if identifier.startswith("#assay-")]
            self.assertEqual(assay_ids, [])
            self.assertIn("#study-protocol-design-study", by_id)

    def test_multiple_studies_and_assays_remain_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            project = load_project(workspace)

            first_study = project["studies"][0]
            first_study["assays"].append(
                {
                    "identifier": "ecg",
                    "title": "ECG",
                    "path": "studies/light-exposure-study/assays/ecg",
                }
            )
            project["studies"].append(
                {
                    "identifier": "follow-up",
                    "title": "Follow-up study",
                    "path": "studies/follow-up",
                    "assays": [
                        {
                            "identifier": "imaging",
                            "title": "Imaging",
                            "path": "studies/follow-up/assays/imaging",
                        }
                    ],
                }
            )

            for relative in [
                "studies/light-exposure-study/assays/ecg",
                "studies/follow-up",
                "studies/follow-up/assays/imaging",
            ]:
                path = workspace / relative
                path.mkdir(parents=True, exist_ok=True)
                (path / "README.md").write_text("# Fixture\n", encoding="utf-8")
            write_project(workspace, project)

            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)
            by_id = entity_map(load_metadata(crate))

            self.assertIn("#study-light-exposure-study", by_id)
            self.assertIn("#study-follow-up", by_id)
            self.assertEqual(
                refs(by_id["#study-light-exposure-study"], "hasPart"),
                [
                    "#assay-light-exposure-study-behaviour",
                    "#assay-light-exposure-study-ecg",
                ],
            )
            self.assertEqual(
                refs(by_id["#study-follow-up"], "hasPart"),
                ["#assay-follow-up-imaging"],
            )

    def test_external_data_is_referenced_without_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            project = load_project(workspace)
            project["resources"] = [
                {
                    "name": "External dataset",
                    "type": "dataset",
                    "location": "https://example.org/datasets/123",
                    "access": "open",
                    "description": "Authoritative data remain in an external repository.",
                }
            ]
            write_project(workspace, project)

            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)
            by_id = entity_map(load_metadata(crate))

            external_id = "https://example.org/datasets/123"
            self.assertIn(external_id, by_id)
            self.assertIn(external_id, refs(by_id["./"], "hasPart"))
            self.assertFalse((crate / "datasets" / "123").exists())

    def test_private_local_resource_is_not_copied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            private_file = workspace / "data" / "private.csv"
            private_file.parent.mkdir(parents=True, exist_ok=True)
            private_file.write_text("subject,value\nA,1\n", encoding="utf-8")

            project = load_project(workspace)
            project["resources"] = [
                {
                    "name": "Private source data",
                    "type": "dataset",
                    "path": "data/private.csv",
                    "access": "private",
                }
            ]
            write_project(workspace, project)

            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)
            by_id = entity_map(load_metadata(crate))

            self.assertFalse((crate / "data" / "private.csv").exists())
            private_entities = [
                entity
                for identifier, entity in by_id.items()
                if identifier.startswith("#resource-")
            ]
            self.assertEqual(len(private_entities), 1)
            self.assertEqual(private_entities[0]["conditionsOfAccess"], "private")
            self.assertEqual(private_entities[0]["identifier"], "data/private.csv")

    def test_open_local_and_external_resources_can_coexist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            local_file = workspace / "results" / "summary.csv"
            local_file.parent.mkdir(parents=True, exist_ok=True)
            local_file.write_text("metric,value\nactivity,3.2\n", encoding="utf-8")

            project = load_project(workspace)
            project["resources"] = [
                {
                    "name": "Open summary",
                    "path": "results/summary.csv",
                    "access": "open",
                },
                {
                    "name": "External raw data",
                    "location": "s3://research-bucket/raw-data",
                    "access": "restricted",
                },
            ]
            write_project(workspace, project)

            crate = root / "crate"
            result = export_rocrate(workspace, crate, date_published=FIXED_DATE)
            by_id = entity_map(load_metadata(crate))

            self.assertTrue((crate / "results" / "summary.csv").is_file())
            self.assertIn("results/summary.csv", result.copied_paths)
            self.assertIn("results/summary.csv", by_id)
            self.assertIn("s3://research-bucket/raw-data", by_id)
            self.assertEqual(
                by_id["s3://research-bucket/raw-data"]["conditionsOfAccess"],
                "restricted",
            )

    def test_local_path_ids_are_uri_encoded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            local_file = workspace / "results" / "almost 50%.csv"
            local_file.parent.mkdir(parents=True, exist_ok=True)
            local_file.write_text("value\n50\n", encoding="utf-8")

            project = load_project(workspace)
            project["resources"] = [
                {
                    "name": "Encoded path fixture",
                    "path": "results/almost 50%.csv",
                    "access": "open",
                }
            ]
            write_project(workspace, project)

            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)
            by_id = entity_map(load_metadata(crate))
            self.assertIn("results/almost%2050%25.csv", by_id)

    def test_invalid_workspace_is_refused_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            shutil.rmtree(workspace / "studies" / "light-exposure-study")
            crate = root / "crate"

            with self.assertRaises(ROCrateExportError) as caught:
                export_rocrate(workspace, crate, date_published=FIXED_DATE)

            self.assertEqual(caught.exception.code, "invalid_workspace")
            self.assertIsNotNone(caught.exception.workspace_report)
            self.assertFalse(crate.exists())

    def test_existing_output_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            crate = root / "crate"
            crate.mkdir()
            (crate / "old.txt").write_text("old\n", encoding="utf-8")

            with self.assertRaises(ROCrateExportError) as caught:
                export_rocrate(workspace, crate, date_published=FIXED_DATE)
            self.assertEqual(caught.exception.code, "output_exists")
            self.assertTrue((crate / "old.txt").is_file())

            result = export_rocrate(
                workspace,
                crate,
                force=True,
                date_published=FIXED_DATE,
            )
            self.assertTrue(result.validation.valid)
            self.assertFalse((crate / "old.txt").exists())

    def test_rocrate_validator_detects_missing_required_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            crate = root / "crate"
            export_rocrate(workspace, crate, date_published=FIXED_DATE)

            metadata_path = crate / ROCRATE_METADATA
            document = json.loads(metadata_path.read_text(encoding="utf-8"))
            by_id = entity_map(document)
            del by_id["./"]["datePublished"]
            metadata_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report = validate_rocrate(crate)
            self.assertFalse(report.valid)
            self.assertTrue(
                any(issue.code == "root_date_published" for issue in report.errors)
            )

    def test_generated_export_validates_with_only_license_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = create_fixture_workspace(root)
            crate = root / "crate"
            result = export_rocrate(workspace, crate, date_published=FIXED_DATE)

            self.assertTrue(result.validation.valid)
            warning_codes = {issue.code for issue in result.validation.warnings}
            self.assertIn("root_license", warning_codes)


if __name__ == "__main__":
    unittest.main()
