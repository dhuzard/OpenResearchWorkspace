"""The one networked path in ORW, exercised without a network.

Every test here injects a transport. A test that reached pub.orcid.org would
make the suite depend on a third party being up, and would leak the fact that
the suite ran; the module takes an opener precisely so that never happens.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from orw import SetupConfig, cli, create_workspace  # noqa: E402
from orw.orcid_lookup import (  # noqa: E402
    OrcidLookupError,
    OrcidNotFound,
    OrcidPerson,
    OrcidUnavailable,
    fetch_person,
)

VALID = "0000-0002-1825-0097"
MISTYPED = "0000-0001-7938-4051"


class _Response(io.BytesIO):
    """The subset of an HTTPResponse that the module actually touches."""

    def __init__(self, payload: bytes, status: int = 200) -> None:
        super().__init__(payload)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def responder(payload, status=200):
    captured = {}

    def opener(request, timeout=None):
        captured["url"] = request.full_url
        captured["headers"] = request.headers
        captured["timeout"] = timeout
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return _Response(body, status)

    opener.captured = captured
    return opener


def raiser(exc):
    def opener(request, timeout=None):
        raise exc

    return opener


def name_payload(given, family):
    def part(value):
        return None if value is None else {"value": value}

    return {"name": {"given-names": part(given), "family-name": part(family)}}


class FetchTests(unittest.TestCase):
    def test_reads_the_public_name(self):
        person = fetch_person(VALID, opener=responder(name_payload("Josiah", "Carberry")))
        self.assertEqual((person.given_name, person.family_name), ("Josiah", "Carberry"))
        self.assertEqual(person.orcid, VALID)

    def test_requests_the_public_api_as_json(self):
        opener = responder(name_payload("Josiah", "Carberry"))
        fetch_person(VALID, opener=opener)
        self.assertEqual(opener.captured["url"], f"https://pub.orcid.org/v3.0/{VALID}/person")
        self.assertEqual(opener.captured["headers"]["Accept"], "application/json")
        self.assertIn("orw/", opener.captured["headers"]["User-agent"])

    def test_normalizes_a_url_form_identifier(self):
        opener = responder(name_payload("Josiah", "Carberry"))
        person = fetch_person(f"https://orcid.org/{VALID}", opener=opener)
        self.assertEqual(person.orcid, VALID)
        self.assertIn(VALID, opener.captured["url"])

    def test_a_mistyped_orcid_never_reaches_the_network(self):
        def forbidden(request, timeout=None):
            raise AssertionError("a mistyped ORCID must not be looked up")

        with self.assertRaises(OrcidLookupError):
            fetch_person(MISTYPED, opener=forbidden)

    def test_a_private_name_is_still_a_successful_lookup(self):
        """The record exists; its owner simply withheld the name."""
        person = fetch_person(VALID, opener=responder({"name": None}))
        self.assertEqual((person.given_name, person.family_name), (None, None))
        self.assertEqual(person.orcid, VALID)

    def test_a_half_private_name_fills_only_what_is_public(self):
        person = fetch_person(VALID, opener=responder(name_payload("Josiah", None)))
        self.assertEqual((person.given_name, person.family_name), ("Josiah", None))

    def test_blank_name_parts_are_not_recorded(self):
        person = fetch_person(VALID, opener=responder(name_payload("  ", "Carberry")))
        self.assertEqual((person.given_name, person.family_name), (None, "Carberry"))

    def test_unknown_record_is_not_found(self):
        error = urllib.error.HTTPError("https://pub.orcid.org", 404, "Not Found", {}, None)
        with self.assertRaises(OrcidNotFound):
            fetch_person(VALID, opener=raiser(error))

    def test_server_error_is_unavailable_not_not_found(self):
        """A broken registry says nothing about whether the ORCID is real."""
        error = urllib.error.HTTPError("https://pub.orcid.org", 503, "Down", {}, None)
        with self.assertRaises(OrcidUnavailable):
            fetch_person(VALID, opener=raiser(error))

    def test_offline_is_unavailable(self):
        with self.assertRaises(OrcidUnavailable):
            fetch_person(VALID, opener=raiser(urllib.error.URLError("offline")))

    def test_timeout_is_unavailable(self):
        with self.assertRaises(OrcidUnavailable):
            fetch_person(VALID, opener=raiser(TimeoutError("timed out")))

    def test_non_json_is_unavailable(self):
        with self.assertRaises(OrcidUnavailable):
            fetch_person(VALID, opener=responder(b"<html>portal login</html>"))


class CommandTests(unittest.TestCase):
    """--fetch wiring, with the lookup replaced so no test reaches the network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "study"
        create_workspace(
            SetupConfig.from_mapping(
                {
                    "project_title": "Fetch",
                    "project_description": "Fetch test.",
                    "creator": {"name": "Creator"},
                    "first_study": {"title": "Study"},
                    "first_assay": {"title": "Assay"},
                    "data": {"location": "Local", "access": "private"},
                    "keywords": [],
                }
            ),
            self.workspace,
        )
        self.calls = []

    def patch(self, outcome):
        def fake(orcid, **kwargs):
            self.calls.append(orcid)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        original = cli.fetch_person
        cli.fetch_person = fake
        self.addCleanup(setattr, cli, "fetch_person", original)

    def record(self):
        return (self.workspace / ".research/project.yml").read_text(encoding="utf-8")

    def add(self, *extra):
        return cli.main(
            ["contributor", "add", "Josiah Carberry", "--workspace", str(self.workspace), *extra]
        )

    def test_fetch_fills_the_name_parts(self):
        self.patch(OrcidPerson(VALID, "Josiah", "Carberry"))
        self.assertEqual(self.add("--orcid", VALID, "--fetch"), 0)
        record = self.record()
        self.assertIn("given_name", record)
        self.assertIn("Josiah", record)
        self.assertIn("Carberry", record)
        self.assertEqual(self.calls, [VALID])

    def test_explicit_names_win_over_the_registry(self):
        self.patch(OrcidPerson(VALID, "Josiah", "Carberry"))
        self.assertEqual(self.add("--orcid", VALID, "--fetch", "--given-name", "Jo"), 0)
        record = self.record()
        self.assertIn('given_name: "Jo"', record)
        self.assertIn("Carberry", record)

    def test_unknown_orcid_is_refused(self):
        self.patch(OrcidNotFound("ORCID is not in the registry."))
        self.assertEqual(self.add("--orcid", VALID, "--fetch"), cli.EXIT_INPUT)
        self.assertNotIn("Josiah Carberry", self.record())

    def test_unreachable_registry_still_records_the_contributor(self):
        """Being offline must not stop work; this is the degradation promise."""
        self.patch(OrcidUnavailable("ORCID registry could not be reached."))
        self.assertEqual(self.add("--orcid", VALID, "--fetch"), 0)
        self.assertIn("Josiah Carberry", self.record())

    def test_fetch_without_orcid_is_refused_before_looking_anything_up(self):
        self.patch(OrcidNotFound("unused"))
        self.assertEqual(self.add("--fetch"), cli.EXIT_INPUT)
        self.assertEqual(self.calls, [])

    def test_no_fetch_makes_no_lookup(self):
        self.patch(OrcidNotFound("unused"))
        self.assertEqual(self.add("--orcid", VALID), 0)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
