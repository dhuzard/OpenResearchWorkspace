"""Shared readers over the canonical record, used by every FAIR view.

`.research/project.yml` stays canonical. CITATION.cff, DataCite metadata and the
readiness report are generated views over it, so they all read the record the
same way and disagree about nothing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identifiers import Identifier, IdentifierError, parse, parse_orcid

LICENSE_SCOPES = ("project", "data", "code", "documentation")


class FairError(ValueError):
    """A FAIR view could not be produced from the canonical record."""


class FairExportError(FairError):
    """Required metadata are missing, so no export is written."""

    def __init__(self, message: str, gaps: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.gaps = gaps


@dataclass(frozen=True)
class Person:
    """A contributor as the FAIR views need them, with validation already done."""

    name: str
    given_name: str | None
    family_name: str | None
    orcid: Identifier | None
    orcid_problem: str | None
    affiliation: str | None
    email: str | None
    role: str | None

    @property
    def citable_as_person(self) -> bool:
        """CITATION.cff records a person only when a name part is separated out."""

        return bool(self.given_name or self.family_name)


@dataclass(frozen=True)
class Related:
    """A related identifier, kept even when unusable so the report can explain it."""

    raw: str
    relation: str | None
    resource_type: str | None
    title: str | None
    identifier: Identifier | None
    problem: str | None


def investigation(data: Mapping[str, Any]) -> Mapping[str, Any]:
    value = data.get("investigation")
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def keywords(data: Mapping[str, Any]) -> tuple[str, ...]:
    raw = investigation(data).get("keywords")
    if not isinstance(raw, list):
        return ()
    return tuple(word.strip() for word in raw if isinstance(word, str) and word.strip())


def people(data: Mapping[str, Any]) -> tuple[Person, ...]:
    raw = data.get("contributors")
    if not isinstance(raw, list):
        return ()
    result: list[Person] = []
    for entry in raw:
        if not isinstance(entry, Mapping):
            continue
        name = _text(entry.get("name"))
        if not name:
            continue
        orcid: Identifier | None = None
        problem: str | None = None
        declared = _text(entry.get("orcid"))
        if declared:
            try:
                orcid = parse_orcid(declared)
            except IdentifierError as exc:
                problem = str(exc)
        result.append(
            Person(
                name=name,
                given_name=_text(entry.get("given_name")),
                family_name=_text(entry.get("family_name")),
                orcid=orcid,
                orcid_problem=problem,
                affiliation=_text(entry.get("affiliation")),
                email=_text(entry.get("email")),
                role=_text(entry.get("role")),
            )
        )
    return tuple(result)


def licenses(data: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = data.get("licenses")
    if not isinstance(raw, Mapping):
        return {}
    return {
        scope: raw[scope]
        for scope in LICENSE_SCOPES
        if isinstance(raw.get(scope), Mapping) and _text(raw[scope].get("identifier"))
    }


def related(data: Mapping[str, Any]) -> tuple[Related, ...]:
    raw = data.get("related_identifiers")
    if not isinstance(raw, list):
        return ()
    result: list[Related] = []
    for entry in raw:
        if not isinstance(entry, Mapping):
            continue
        value = _text(entry.get("identifier"))
        if not value:
            continue
        scheme = _text(entry.get("scheme"))
        identifier: Identifier | None = None
        problem: str | None = None
        try:
            identifier = parse(value, scheme=scheme)
        except IdentifierError as exc:
            problem = str(exc)
        result.append(
            Related(
                raw=value,
                relation=_text(entry.get("relation")),
                resource_type=_text(entry.get("resource_type")),
                title=_text(entry.get("title")),
                identifier=identifier,
                problem=problem,
            )
        )
    return tuple(result)


def own_doi(data: Mapping[str, Any]) -> Identifier | None:
    """The DOI of this workspace itself, once a publish workflow has recorded one."""

    value = _text(investigation(data).get("doi"))
    if not value:
        return None
    try:
        return parse(value, scheme="doi")
    except IdentifierError:
        return None


def resources(data: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    result: list[Mapping[str, Any]] = []
    for collection in ("resources", "outputs"):
        entries = data.get(collection)
        if isinstance(entries, list):
            result.extend(entry for entry in entries if isinstance(entry, Mapping))
    return tuple(result)
