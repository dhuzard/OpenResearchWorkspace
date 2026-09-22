"""FAIR views must be generated from the canonical record, and never invented."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import fair, mutate  # noqa: E402
from orw.fair import citation, datacite, identifiers, report  # noqa: E402
from orw.initialize import create_workspace  # noqa: E402
from orw.model import SetupConfig  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "setup"
VALID_ORCID = "0000-0002-1825-0097"


class IdentifierTests(unittest.TestCase):
    def test_normalizes_every_accepted_form(self) -> None:
        for raw, scheme, value, url in (
            (VALID_ORCID, "orcid", VALID_ORCID, f"https://orcid.org/{VALID_ORCID}"),
            (f"https://orcid.org/{VALID_ORCID}", "orcid", VALID_ORCID, f"https://orcid.org/{VALID_ORCID}"),
            ("10.5281/zenodo.1", "doi", "10.5281/zenodo.1", "https://doi.org/10.5281/zenodo.1"),
            ("doi:10.5281/zenodo.1", "doi", "10.5281/zenodo.1", "https://doi.org/10.5281/zenodo.1"),
            ("https://doi.org/10.5281/zenodo.1", "doi", "10.5281/zenodo.1", "https://doi.org/10.5281/zenodo.1"),
            ("arXiv:2401.01234", "arxiv", "arXiv:2401.01234", "https://arxiv.org/abs/2401.01234"),
            ("urn:nbn:de:bvb:19-146642", "urn", "urn:nbn:de:bvb:19-146642", None),
            ("https://example.org/a", "url", "https://example.org/a", "https://example.org/a"),
            ("20.500.12345/abc", "handle", "20.500.12345/abc", "https://hdl.handle.net/20.500.12345/abc"),
        ):
            with self.subTest(raw=raw):
                parsed = identifiers.parse_identifier(raw)
                self.assertEqual((parsed.scheme, parsed.value, parsed.url), (scheme, value, url))

    def test_rejects_an_orcid_that_fails_its_check_digit(self) -> None:
        with self.assertRaises(identifiers.IdentifierError) as caught:
            identifiers.parse_orcid("0000-0002-1825-0098")
        self.assertIn("check digit", str(caught.exception))

    def test_accepts_the_x_check_character(self) -> None:
        """A check digit of 10 is written X, and must not be rejected as a typo."""

        self.assertEqual(identifiers.orcid_check_digit("000000021694233"), "X")
        self.assertEqual(
            identifiers.parse_orcid("0000-0002-1694-233X").value, "0000-0002-1694-233X"
        )
        self.assertEqual(
            identifiers.parse_orcid("0000-0002-1694-233x").value, "0000-0002-1694-233X"
        )

    def test_rejects_an_isbn_that_fails_its_check_digit(self) -> None:
        identifiers.parse_identifier("978-3-16-148410-0", scheme="isbn")
        with self.assertRaises(identifiers.IdentifierError):
            identifiers.parse_identifier("978-3-16-148410-1", scheme="isbn")

    def test_requires_a_scheme_when_detection_is_ambiguous(self) -> None:
        with self.assertRaises(identifiers.IdentifierError) as caught:
            identifiers.parse_identifier("12345678")
        self.assertIn("--scheme", str(caught.exception))
        self.assertEqual(
            identifiers.parse_identifier("12345678", scheme="pmid").value, "PMID:12345678"
        )

    def test_a_doi_is_not_mistaken_for_a_handle(self) -> None:
        self.assertEqual(identifiers.detect_scheme("10.5281/zenodo.1"), "doi")

    def test_unverifiable_schemes_are_kept_verbatim(self) -> None:
        parsed = identifiers.parse_identifier("GSE12345", scheme="accession")
        self.assertEqual((parsed.scheme, parsed.value, parsed.url), ("accession", "GSE12345", None))
        self.assertIsNone(parsed.datacite_type)


class WorkspaceCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="orw-fair-test-")
        self.addCleanup(self._temporary.cleanup)
        self.workspace = Path(self._temporary.name) / "workspace"
        payload = json.loads((FIXTURES / "basic.json").read_text(encoding="utf-8"))
        create_workspace(SetupConfig.from_mapping(payload), self.workspace)

    def data(self) -> dict:
        return yaml.safe_load(
            (self.workspace / ".research" / "project.yml").read_text(encoding="utf-8")
        )

    def make_depositable(self) -> None:
        mutate.set_license(self.workspace, "project", "CC-BY-4.0")
        mutate.update_project_metadata(
            self.workspace, publisher="Institute of Example Research", publication_year="2026"
        )


class LicenseMutationTests(WorkspaceCase):
    def test_declares_each_scope_independently(self) -> None:
        mutate.set_license(self.workspace, "project", "CC-BY-4.0")
        mutate.set_license(self.workspace, "code", "MIT")
        self.assertEqual(
            self.data()["licenses"],
            {"project": {"identifier": "CC-BY-4.0"}, "code": {"identifier": "MIT"}},
        )

    def test_replaces_a_declared_scope(self) -> None:
        mutate.set_license(self.workspace, "data", "CC-BY-4.0", url="https://example.org/a")
        result = mutate.set_license(self.workspace, "data", "CC0-1.0")
        self.assertTrue(result.applied)
        self.assertEqual(self.data()["licenses"]["data"], {"identifier": "CC0-1.0"})

    def test_reports_an_unchanged_declaration_without_writing(self) -> None:
        mutate.set_license(self.workspace, "project", "MIT")
        record = self.workspace / ".research" / "project.yml"
        before = record.read_bytes()
        result = mutate.set_license(self.workspace, "project", "MIT")
        self.assertFalse(result.applied)
        self.assertEqual(record.read_bytes(), before)

    def test_refuses_an_unknown_scope(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.set_license(self.workspace, "figures", "MIT")


class RelatedIdentifierMutationTests(WorkspaceCase):
    def test_normalizes_before_writing(self) -> None:
        mutate.add_related_identifier(
            self.workspace, "https://doi.org/10.5281/zenodo.1", relation="IsSupplementTo"
        )
        entry = self.data()["related_identifiers"][0]
        self.assertEqual(entry["identifier"], "10.5281/zenodo.1")
        self.assertEqual(entry["scheme"], "doi")

    def test_refuses_a_malformed_identifier(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.add_related_identifier(self.workspace, "10.x/y", scheme="doi")

    def test_refuses_an_unknown_relation(self) -> None:
        with self.assertRaises(mutate.MutationInputError) as caught:
            mutate.add_related_identifier(self.workspace, "10.5281/zenodo.1", relation="Supplements")
        self.assertIn("IsSupplementTo", str(caught.exception))

    def test_refuses_an_orcid_as_a_related_work(self) -> None:
        with self.assertRaises(mutate.MutationInputError) as caught:
            mutate.add_related_identifier(self.workspace, VALID_ORCID)
        self.assertIn("contributor add", str(caught.exception))

    def test_refuses_a_duplicate_however_it_is_written(self) -> None:
        mutate.add_related_identifier(self.workspace, "10.5281/zenodo.1", relation="Cites")
        with self.assertRaises(mutate.MutationConflict):
            mutate.add_related_identifier(
                self.workspace, "https://doi.org/10.5281/zenodo.1", relation="Cites"
            )


class MetadataMutationTests(WorkspaceCase):
    def test_records_datacite_properties(self) -> None:
        mutate.update_project_metadata(
            self.workspace, publisher="Example Institute", publication_year="2026",
            version="1.0.0", doi="https://doi.org/10.5281/zenodo.42",
        )
        record = self.data()["investigation"]
        self.assertEqual(record["publisher"], "Example Institute")
        self.assertEqual(record["publication_year"], "2026")
        self.assertEqual(record["version"], "1.0.0")
        self.assertEqual(record["doi"], "10.5281/zenodo.42")

    def test_refuses_a_malformed_year(self) -> None:
        for bad in ("26", "twenty twenty-six", "2026-01"):
            with self.subTest(bad=bad):
                with self.assertRaises(mutate.MutationInputError):
                    mutate.update_project_metadata(self.workspace, publication_year=bad)

    def test_refuses_a_malformed_doi(self) -> None:
        with self.assertRaises(mutate.MutationInputError):
            mutate.update_project_metadata(self.workspace, doi="not-a-doi")


class ContributorMutationTests(WorkspaceCase):
    def test_records_name_parts_and_affiliation(self) -> None:
        mutate.add_contributor(
            self.workspace, "Ada Lovelace", given_name="Ada", family_name="Lovelace",
            orcid=f"https://orcid.org/{VALID_ORCID}", affiliation="Example Institute",
            email="ada@example.org",
        )
        entry = self.data()["contributors"][-1]
        self.assertEqual(entry["given_name"], "Ada")
        self.assertEqual(entry["family_name"], "Lovelace")
        self.assertEqual(entry["orcid"], VALID_ORCID)
        self.assertEqual(entry["affiliation"], "Example Institute")

    def test_refuses_an_orcid_that_fails_its_check_digit(self) -> None:
        with self.assertRaises(mutate.MutationInputError) as caught:
            mutate.add_contributor(self.workspace, "Typo", orcid="0000-0002-1825-0098")
        self.assertIn("check digit", str(caught.exception))


class CitationTests(WorkspaceCase):
    def test_renders_a_parsable_citation_file(self) -> None:
        mutate.set_license(self.workspace, "project", "CC-BY-4.0", url="https://example.org/l")
        text = citation.render(self.data())
        document = yaml.safe_load(text)

        self.assertEqual(document["cff-version"], "1.2.0")
        self.assertEqual(document["type"], "dataset")
        self.assertEqual(document["title"], "Effects of light exposure on mouse activity")
        self.assertEqual(document["license"], "CC-BY-4.0")
        self.assertEqual(document["license-url"], "https://example.org/l")
        self.assertTrue(citation.is_generated(text))

    def test_omits_a_license_that_was_never_declared(self) -> None:
        document = yaml.safe_load(citation.render(self.data()))
        self.assertNotIn("license", document)
        self.assertNotIn("license-url", document)

    def test_falls_back_to_a_url_for_an_unrecognized_spdx_identifier(self) -> None:
        mutate.set_license(
            self.workspace, "project", "Lab-Internal-1.0", url="https://example.org/terms"
        )
        document = yaml.safe_load(citation.render(self.data()))
        self.assertNotIn("license", document)
        self.assertEqual(document["license-url"], "https://example.org/terms")

    def test_records_a_person_only_when_name_parts_exist(self) -> None:
        mutate.add_contributor(
            self.workspace, "Ada Lovelace", given_name="Ada", family_name="Lovelace"
        )
        authors = yaml.safe_load(citation.render(self.data()))["authors"]
        self.assertEqual(authors[0], {"name": "Jane Researcher"})
        self.assertEqual(
            authors[1], {"family-names": "Lovelace", "given-names": "Ada"}
        )

    def test_maps_related_identifiers_to_cff_types(self) -> None:
        mutate.add_related_identifier(self.workspace, "10.5281/zenodo.1", relation="Cites")
        mutate.add_related_identifier(self.workspace, "https://example.org/p", relation="References")
        mutate.add_related_identifier(self.workspace, "GSE1", scheme="accession", relation="Cites")
        entries = yaml.safe_load(citation.render(self.data()))["identifiers"]
        self.assertEqual([entry["type"] for entry in entries], ["doi", "url", "other"])

    def test_is_deterministic(self) -> None:
        self.assertEqual(citation.render(self.data()), citation.render(self.data()))

    def test_a_hand_written_file_is_not_recognized_as_generated(self) -> None:
        self.assertFalse(citation.is_generated("cff-version: 1.2.0\ntitle: Mine\n"))


class DataCiteTests(WorkspaceCase):
    def test_refuses_to_export_without_mandatory_properties(self) -> None:
        with self.assertRaises(fair.FairExportError) as caught:
            datacite.build(self.data())
        gaps = " ".join(caught.exception.gaps)
        self.assertIn("publisher", gaps)
        self.assertIn("publicationYear", gaps)

    def test_exports_once_the_gaps_are_closed(self) -> None:
        self.make_depositable()
        payload = datacite.build(self.data())

        self.assertEqual(payload["publisher"], "Institute of Example Research")
        self.assertEqual(payload["publicationYear"], "2026")
        self.assertEqual(payload["types"]["resourceTypeGeneral"], "Dataset")
        self.assertEqual(payload["titles"], [{"title": "Effects of light exposure on mouse activity"}])
        self.assertEqual(payload["rightsList"][0]["rightsIdentifier"], "CC-BY-4.0")
        self.assertNotIn("doi", payload)

    def test_includes_the_orcid_as_a_name_identifier(self) -> None:
        self.make_depositable()
        mutate.add_contributor(self.workspace, "Ada Lovelace", orcid=VALID_ORCID)
        creator = datacite.build(self.data())["creators"][-1]
        self.assertEqual(
            creator["nameIdentifiers"][0]["nameIdentifier"], f"https://orcid.org/{VALID_ORCID}"
        )

    def test_reports_identifiers_a_deposit_cannot_carry(self) -> None:
        self.make_depositable()
        mutate.add_related_identifier(self.workspace, "GSE1", scheme="accession", relation="Cites")
        mutate.add_related_identifier(self.workspace, "10.5281/zenodo.1")

        payload = datacite.build(self.data())
        self.assertNotIn("relatedIdentifiers", payload)
        skipped = " ".join(datacite.skipped_identifiers(self.data()))
        self.assertIn("no DataCite equivalent", skipped)
        self.assertIn("no relation was recorded", skipped)

    def test_is_serializable_json(self) -> None:
        self.make_depositable()
        json.dumps(datacite.build(self.data()))


class ReportTests(WorkspaceCase):
    def build(self) -> report.FairReport:
        return report.build(self.workspace, self.data())

    def status(self, result: report.FairReport, code: str) -> str:
        return next(check.status for check in result.checks if check.code == code)

    def test_a_fresh_workspace_has_actionable_gaps(self) -> None:
        result = self.build()
        self.assertFalse(result.ready)
        self.assertEqual(self.status(result, "R1-project-license"), report.UNMET)
        self.assertEqual(self.status(result, "R3-datacite-ready"), report.UNMET)
        self.assertEqual(self.status(result, "F3-description"), report.MET)
        for check in result.unmet:
            self.assertTrue(check.remedy, f"{check.code} has no remedy")

    def test_becomes_ready_once_required_gaps_are_closed(self) -> None:
        self.make_depositable()
        result = self.build()
        self.assertTrue(result.ready, [check.message for check in result.blocking])
        self.assertTrue(result.unmet, "recommended gaps should still be reported")

    def test_flags_an_orcid_that_fails_its_check_digit(self) -> None:
        """orw init and the browser check an ORCID's shape but not its check digit."""

        record = self.workspace / ".research" / "project.yml"
        record.write_text(
            record.read_text(encoding="utf-8").replace(
                '    role: "Project creator"',
                '    role: "Project creator"\n    orcid: "0000-0002-1825-0098"',
            ),
            encoding="utf-8",
        )
        result = self.build()
        self.assertEqual(self.status(result, "F5-orcid-checksum"), report.UNMET)
        self.assertFalse(result.ready)

    def test_tracks_the_citation_file(self) -> None:
        self.assertEqual(self.status(self.build(), "R5-citation-file"), report.UNMET)

        path = self.workspace / "CITATION.cff"
        path.write_text(citation.render(self.data()), encoding="utf-8")
        self.assertEqual(self.status(self.build(), "R5-citation-file"), report.MET)

        mutate.update_project_metadata(self.workspace, title="Renamed project")
        self.assertEqual(self.status(self.build(), "R5-citation-file"), report.UNMET)

    def test_leaves_a_hand_written_citation_file_alone(self) -> None:
        (self.workspace / "CITATION.cff").write_text(
            "cff-version: 1.2.0\ntitle: Maintained by hand\n", encoding="utf-8"
        )
        result = self.build()
        self.assertEqual(self.status(result, "R5-citation-file"), report.MET)
        self.assertIn("by hand", next(
            check.message for check in result.checks if check.code == "R5-citation-file"
        ))

    def test_is_serializable_and_covers_every_principle(self) -> None:
        payload = self.build().to_mapping()
        json.dumps(payload)
        self.assertEqual(
            {check["principle"] for check in payload["checks"]}, set(report.PRINCIPLES)
        )
        self.assertEqual(
            len(payload["checks"]),
            payload["summary"]["met"] + payload["summary"]["unmet"]
            + payload["summary"]["not_applicable"],
        )

    def test_every_check_code_is_unique(self) -> None:
        codes = [check.code for check in self.build().checks]
        self.assertEqual(len(codes), len(set(codes)))


class CanonicalSourceTests(WorkspaceCase):
    def test_relations_come_from_the_bundled_schema(self) -> None:
        schema = json.loads(
            (ROOT / "schema" / "project.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            list(mutate.RELATIONS),
            schema["$defs"]["relatedIdentifier"]["properties"]["relation"]["enum"],
        )

    def test_fair_views_refuse_an_invalid_workspace(self) -> None:
        (self.workspace / ".research" / "initialized").unlink()
        with self.assertRaises(mutate.WorkspaceNotValid):
            mutate.load_workspace(self.workspace)

    def test_a_fully_described_workspace_still_validates(self) -> None:
        self.make_depositable()
        mutate.set_license(self.workspace, "data", "CC0-1.0")
        mutate.add_contributor(
            self.workspace, "Ada Lovelace", given_name="Ada", family_name="Lovelace",
            orcid=VALID_ORCID, affiliation="Example Institute",
        )
        mutate.add_related_identifier(
            self.workspace, "10.5281/zenodo.1", relation="IsSupplementTo"
        )
        mutate.update_project_metadata(self.workspace, doi="10.5281/zenodo.99")

        from orw.validate import validate_workspace

        result = validate_workspace(self.workspace)
        self.assertTrue(result.valid, [issue.message for issue in result.issues])


if __name__ == "__main__":
    unittest.main()
