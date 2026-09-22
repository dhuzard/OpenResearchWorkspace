"""FAIR readiness: what is missing, why it matters, and the command that fixes it.

A score would be worse than useless here. "62% FAIR" tells a researcher nothing
they can act on, and invites optimizing the number rather than the metadata. So
every check names a concrete gap and the exact command that closes it.

This reports on metadata ORW can see in the canonical record. It is not a FAIR
certification, and a workspace where every check passes can still be poorly
described science.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from . import citation, datacite
from ._common import investigation, keywords, licenses, own_doi, people, related, resources

REQUIRED = "required"
RECOMMENDED = "recommended"

MET = "met"
UNMET = "unmet"
NOT_APPLICABLE = "not_applicable"

PRINCIPLES = ("findable", "accessible", "interoperable", "reusable")


@dataclass(frozen=True)
class FairCheck:
    code: str
    principle: str
    severity: str
    status: str
    message: str
    remedy: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "principle": self.principle,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            **({"remedy": self.remedy} if self.remedy else {}),
        }


@dataclass(frozen=True)
class FairReport:
    workspace: Path
    checks: tuple[FairCheck, ...]

    @property
    def unmet(self) -> tuple[FairCheck, ...]:
        return tuple(check for check in self.checks if check.status == UNMET)

    @property
    def blocking(self) -> tuple[FairCheck, ...]:
        """Unmet checks that stop a deposit or produce misleading metadata."""

        return tuple(check for check in self.unmet if check.severity == REQUIRED)

    @property
    def ready(self) -> bool:
        return not self.blocking

    def to_mapping(self) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace),
            "ready": self.ready,
            "summary": {
                "met": sum(1 for check in self.checks if check.status == MET),
                "unmet": len(self.unmet),
                "not_applicable": sum(
                    1 for check in self.checks if check.status == NOT_APPLICABLE
                ),
                "blocking": len(self.blocking),
            },
            "checks": [check.to_mapping() for check in self.checks],
        }


def _check(code, principle, severity, condition, met_message, unmet_message, remedy=None):
    return FairCheck(
        code=code,
        principle=principle,
        severity=severity,
        status=MET if condition else UNMET,
        message=met_message if condition else unmet_message,
        remedy=None if condition else remedy,
    )


def _findable(data: Mapping[str, Any]) -> list[FairCheck]:
    record = investigation(data)
    words = keywords(data)
    contributors = people(data)
    with_orcid = [person for person in contributors if person.orcid is not None]
    bad_orcid = [person for person in contributors if person.orcid_problem]

    checks = [
        _check(
            "F1-doi", "findable", RECOMMENDED, own_doi(data) is not None,
            "The Investigation records its own DOI.",
            "No DOI is recorded for this workspace yet.",
            "Deposit the workspace through the publish workflow; the DOI is then "
            "recorded back into .research/project.yml.",
        ),
        _check(
            "F2-keywords", "findable", RECOMMENDED, bool(words),
            f"{len(words)} keyword(s) recorded.",
            "No keywords are recorded, so the workspace is hard to discover.",
            "orw metadata set --keyword <term> --keyword <term>",
        ),
        _check(
            "F3-description", "findable", REQUIRED,
            bool(str(record.get("description") or "").strip()),
            "The Investigation has a description.",
            "The Investigation has no description.",
            'orw metadata set --description "What this project investigates"',
        ),
        _check(
            "F4-contributor-pids", "findable", RECOMMENDED,
            bool(contributors) and len(with_orcid) == len(contributors),
            f"All {len(contributors)} contributor(s) have an ORCID."
            if contributors else "",
            (
                "No contributors are recorded."
                if not contributors
                else "Contributors without an ORCID: "
                + ", ".join(
                    repr(person.name)
                    for person in contributors
                    if person.orcid is None
                )
                + "."
            ),
            "orw contributor add NAME --orcid 0000-0000-0000-0000, or edit the "
            "existing entry in .research/project.yml.",
        ),
    ]

    if bad_orcid:
        checks.append(
            FairCheck(
                "F5-orcid-checksum", "findable", REQUIRED, UNMET,
                "Recorded ORCIDs that fail their check digit: "
                + "; ".join(f"{person.name!r} ({person.orcid_problem})" for person in bad_orcid),
                "Copy each ORCID from the researcher's ORCID record. Workspaces "
                "created by orw init or the browser check an ORCID's shape but "
                "not its check digit.",
            )
        )
    else:
        checks.append(
            FairCheck(
                "F5-orcid-checksum", "findable", REQUIRED, MET,
                "Every recorded ORCID passes its check digit.",
            )
        )
    return checks


def _accessible(data: Mapping[str, Any]) -> list[FairCheck]:
    entries = resources(data)
    undeclared = [
        str(entry.get("name"))
        for entry in entries
        if not str(entry.get("access") or "").strip()
    ]
    unreferenced = [
        str(entry.get("name"))
        for entry in entries
        if not any(
            str(entry.get(key) or "").strip() for key in ("path", "location", "identifier")
        )
    ]

    if not entries:
        access_check = FairCheck(
            "A1-access-levels", "accessible", RECOMMENDED, NOT_APPLICABLE,
            "No resources are registered yet.",
            "orw resource add NAME --location ... --access ...",
        )
    else:
        access_check = _check(
            "A1-access-levels", "accessible", RECOMMENDED, not undeclared,
            f"All {len(entries)} registered resource(s) declare an access level.",
            "Resources with no declared access level: "
            + ", ".join(repr(name) for name in undeclared) + ".",
            "Re-register them with --access open|restricted|embargoed|private, or "
            "edit .research/project.yml.",
        )

    return [
        access_check,
        _check(
            "A2-resource-references", "accessible", REQUIRED, not unreferenced,
            "Every registered resource points at a path, a location or an identifier.",
            "Resources that point nowhere: "
            + ", ".join(repr(name) for name in unreferenced) + ".",
            "Give each one a workspace path, an external location, or a persistent "
            "identifier.",
        ),
    ]


def _interoperable(data: Mapping[str, Any]) -> list[FairCheck]:
    entries = related(data)
    broken = [item for item in entries if item.problem]
    relationless = [item for item in entries if item.identifier and not item.relation]

    if not entries:
        recognized = FairCheck(
            "I1-identifier-syntax", "interoperable", REQUIRED, NOT_APPLICABLE,
            "No related identifiers are recorded.",
            "orw identifier add <DOI or URL> --relation IsSupplementTo",
        )
        relations = FairCheck(
            "I2-identifier-relations", "interoperable", RECOMMENDED, NOT_APPLICABLE,
            "No related identifiers are recorded.",
        )
    else:
        recognized = _check(
            "I1-identifier-syntax", "interoperable", REQUIRED, not broken,
            f"All {len(entries)} related identifier(s) are recognized.",
            "Related identifiers ORW cannot interpret: "
            + "; ".join(f"{item.raw!r} ({item.problem})" for item in broken),
            "Correct them, or record the scheme explicitly with --scheme.",
        )
        relations = _check(
            "I2-identifier-relations", "interoperable", RECOMMENDED, not relationless,
            "Every related identifier states how it relates to this workspace.",
            "Related identifiers with no relation, which a DataCite deposit cannot "
            "carry: " + ", ".join(repr(item.raw) for item in relationless) + ".",
            "Re-add them with --relation, for example IsSupplementTo or Cites.",
        )

    return [
        recognized,
        relations,
        FairCheck(
            "I3-rocrate", "interoperable", RECOMMENDED, MET,
            "The workspace can be exported as an RO-Crate 1.3 package.",
            None,
        ),
    ]


def _reusable(data: Mapping[str, Any], root: Path) -> list[FairCheck]:
    declared = licenses(data)
    contributors = people(data)
    uncitable = [person for person in contributors if not person.citable_as_person]
    gaps = datacite.missing_properties(data)

    checks = [
        _check(
            "R1-project-license", "reusable", REQUIRED, "project" in declared,
            f"Project license: {declared.get('project', {}).get('identifier', '')}.",
            "No project license is declared, so others have no right to reuse this work.",
            "orw license set project CC-BY-4.0",
        )
    ]

    for scope in ("data", "code", "documentation"):
        checks.append(
            _check(
                f"R2-{scope}-license", "reusable", RECOMMENDED, scope in declared,
                f"{scope.capitalize()} license: {declared.get(scope, {}).get('identifier', '')}.",
                f"No {scope} license is declared. An absent license is not an open one.",
                f"orw license set {scope} <SPDX identifier>",
            )
        )

    checks.append(
        _check(
            "R3-datacite-ready", "reusable", REQUIRED, not gaps,
            "DataCite's mandatory properties are all recorded.",
            "DataCite metadata cannot be exported yet: " + " ".join(gaps),
            "Record the properties named above, then run 'orw fair datacite'.",
        )
    )

    checks.append(
        _check(
            "R4-citable-names", "reusable", RECOMMENDED,
            bool(contributors) and not uncitable,
            "Every contributor has separated given and family names.",
            (
                "No contributors are recorded."
                if not contributors
                else "Contributors recorded only as a single name string, which "
                "CITATION.cff must file as an organization rather than a person: "
                + ", ".join(repr(person.name) for person in uncitable) + "."
            ),
            "orw contributor add NAME --given-name ... --family-name ..., or add "
            "given_name/family_name to the existing entry.",
        )
    )

    checks.append(_citation_file_check(data, root))
    return checks


def _citation_file_check(data: Mapping[str, Any], root: Path) -> FairCheck:
    path = root / "CITATION.cff"
    expected = citation.render(data)
    if not path.is_file():
        return FairCheck(
            "R5-citation-file", "reusable", RECOMMENDED, UNMET,
            "No CITATION.cff, so citation tools cannot tell how to cite this work.",
            "orw fair citation",
        )
    try:
        current = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError) as exc:
        return FairCheck(
            "R5-citation-file", "reusable", RECOMMENDED, UNMET,
            f"CITATION.cff could not be read: {exc}",
            "Repair or remove the file, then run 'orw fair citation'.",
        )
    if not citation.is_generated(current):
        return FairCheck(
            "R5-citation-file", "reusable", RECOMMENDED, MET,
            "CITATION.cff is maintained by hand; ORW leaves it alone.",
        )
    if current != expected:
        return FairCheck(
            "R5-citation-file", "reusable", RECOMMENDED, UNMET,
            "CITATION.cff is out of date with the canonical record.",
            "orw fair citation",
        )
    return FairCheck(
        "R5-citation-file", "reusable", RECOMMENDED, MET,
        "CITATION.cff is present and matches the canonical record.",
    )


def build(root: Path, data: Mapping[str, Any]) -> FairReport:
    """Run every readiness check against an already-validated workspace."""

    checks = (
        *_findable(data),
        *_accessible(data),
        *_interoperable(data),
        *_reusable(data, root),
    )
    return FairReport(workspace=root, checks=checks)


__all__ = [
    "FairCheck", "FairReport", "MET", "NOT_APPLICABLE", "PRINCIPLES",
    "RECOMMENDED", "REQUIRED", "UNMET", "build",
]
