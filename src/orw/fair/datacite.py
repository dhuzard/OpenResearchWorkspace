"""DataCite-compatible metadata generated from the canonical record.

This is the payload a deposition workflow would submit, prepared *before*
anyone asks for a DOI. Preparing it early is the point: DataCite's mandatory
properties become visible as concrete gaps while the research is still open,
instead of as a form to improvise at publication time.

Missing mandatory properties are refused, not invented. ORW does not guess a
publisher, guess a publication year, or file the creator as "Anonymous".

Generating this payload is not depositing it. No network call happens here, and
a DOI is minted only by an explicit publish workflow.
"""
from __future__ import annotations

from typing import Any, Mapping

from ._common import (
    FairExportError, investigation, keywords, licenses, own_doi, people, related,
)

SCHEMA_VERSION = "http://datacite.org/schema/kernel-4"
RESOURCE_TYPE_GENERAL = "Dataset"
RESOURCE_TYPE = "Research workspace"

# Everyone ORW records is credited as a DataCite creator. Splitting the list into
# creators and contributors would mean inferring seniority from a free-text role,
# which silently demotes people; a workspace's contributor list is its author list.


def _creator(person) -> dict[str, Any]:
    entry: dict[str, Any] = {"name": person.name}
    if person.citable_as_person:
        entry["nameType"] = "Personal"
        if person.given_name:
            entry["givenName"] = person.given_name
        if person.family_name:
            entry["familyName"] = person.family_name
    if person.orcid is not None:
        entry["nameIdentifiers"] = [
            {
                "nameIdentifier": person.orcid.url,
                "nameIdentifierScheme": "ORCID",
                "schemeUri": "https://orcid.org",
            }
        ]
    if person.affiliation:
        entry["affiliation"] = [{"name": person.affiliation}]
    return entry


def _rights(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for scope, license_record in licenses(data).items():
        entry: dict[str, Any] = {
            "rights": str(license_record.get("name") or license_record["identifier"]),
            "rightsIdentifier": str(license_record["identifier"]),
            "rightsIdentifierScheme": "SPDX",
        }
        url = license_record.get("url")
        if isinstance(url, str) and url.strip():
            entry["rightsUri"] = url.strip()
        # The scope is not part of DataCite, so it is carried in the free text.
        entry["rights"] = f"{entry['rights']} ({scope})"
        entries.append(entry)
    return entries


def _related(data: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    skipped: list[str] = []
    for item in related(data):
        if item.identifier is None:
            skipped.append(f"{item.raw}: {item.problem}")
            continue
        datacite_type = item.identifier.datacite_type
        if datacite_type is None:
            skipped.append(
                f"{item.raw}: the {item.identifier.scheme!r} scheme has no DataCite equivalent."
            )
            continue
        if not item.relation:
            skipped.append(f"{item.raw}: no relation was recorded.")
            continue
        entry = {
            "relatedIdentifier": (
                item.identifier.url
                if item.identifier.scheme == "url"
                else item.identifier.value
            ),
            "relatedIdentifierType": datacite_type,
            "relationType": item.relation,
        }
        if item.resource_type:
            entry["resourceTypeGeneral"] = item.resource_type
        entries.append(entry)
    return entries, skipped


def missing_properties(data: Mapping[str, Any]) -> tuple[str, ...]:
    """DataCite's mandatory properties that the canonical record cannot supply."""

    record = investigation(data)
    gaps: list[str] = []
    if not people(data):
        gaps.append(
            "creators: no contributors are recorded. Add one with "
            "'orw contributor add NAME'."
        )
    if not str(record.get("title") or "").strip():
        gaps.append("titles: the Investigation has no title.")
    if not str(record.get("publisher") or "").strip():
        gaps.append(
            "publisher: not recorded. Set it with "
            "'orw metadata set --publisher \"Your institution or repository\"'."
        )
    if not str(record.get("publication_year") or "").strip():
        gaps.append(
            "publicationYear: not recorded. Set it with "
            "'orw metadata set --publication-year YYYY'."
        )
    return tuple(gaps)


def build(data: Mapping[str, Any]) -> dict[str, Any]:
    """The DataCite payload, or a refusal naming every mandatory gap."""

    gaps = missing_properties(data)
    if gaps:
        raise FairExportError(
            "DataCite metadata are incomplete, so nothing was exported.", gaps
        )

    record = investigation(data)
    payload: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "creators": [_creator(person) for person in people(data)],
        "titles": [{"title": str(record["title"]).strip()}],
        "publisher": str(record["publisher"]).strip(),
        "publicationYear": str(record["publication_year"]).strip(),
        "types": {
            "resourceTypeGeneral": RESOURCE_TYPE_GENERAL,
            "resourceType": RESOURCE_TYPE,
        },
    }

    doi = own_doi(data)
    if doi is not None:
        payload["doi"] = doi.value
        payload["identifiers"] = [
            {"identifier": doi.url, "identifierType": "DOI"}
        ]

    description = str(record.get("description") or "").strip()
    if description:
        payload["descriptions"] = [
            {"description": description, "descriptionType": "Abstract"}
        ]

    words = keywords(data)
    if words:
        payload["subjects"] = [{"subject": word} for word in words]

    rights = _rights(data)
    if rights:
        payload["rightsList"] = rights

    entries, _ = _related(data)
    if entries:
        payload["relatedIdentifiers"] = entries

    version = str(record.get("version") or "").strip()
    if version:
        payload["version"] = version

    return payload


def skipped_identifiers(data: Mapping[str, Any]) -> tuple[str, ...]:
    """Related identifiers a DataCite deposit could not carry, and why."""

    _, skipped = _related(data)
    return tuple(skipped)
