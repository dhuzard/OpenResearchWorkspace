"""Normalized, provider-neutral input model for creating ORW workspaces."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

ACCESS_LEVELS = frozenset({"private", "restricted", "embargoed", "open", "unknown"})
STUDY_STRUCTURES = frozenset({"single", "multiple", "undecided"})
ASSAY_STRUCTURES = frozenset({"single_or_none", "multiple", "undecided"})
PROTOCOL_STORAGE = frozenset({"workspace", "elsewhere", "undecided"})
ORCID_RE = re.compile(r"^(https://orcid\.org/)?\d{4}-\d{4}-\d{4}-[\dX]{4}$")


class SetupValidationError(ValueError):
    """Raised when normalized ORW setup input is invalid."""


def _reject_unknown_keys(
    mapping: Mapping[str, Any], allowed: set[str], label: str
) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise SetupValidationError(f"Unexpected {label} field(s): {names}.")


def _required_text(mapping: Mapping[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SetupValidationError(f"{label} must be a non-empty string.")
    return value.strip()


def _optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SetupValidationError(f"{label} must be a string when provided.")
    value = value.strip()
    return value or None


@dataclass(frozen=True)
class Creator:
    name: str
    orcid: str | None = None


@dataclass(frozen=True)
class StudySeed:
    title: str


@dataclass(frozen=True)
class AssaySeed:
    title: str


@dataclass(frozen=True)
class DataSource:
    location: str
    access: str


@dataclass(frozen=True)
class WorkspaceOptions:
    """Researcher-facing choices that shape the initial workspace, not the science."""

    study_structure: str = "single"
    assay_structure: str = "multiple"
    protocol_storage: str = "workspace"


@dataclass(frozen=True)
class SetupConfig:
    """Normalized scientific setup payload shared by every ORW adapter."""

    project_title: str
    project_description: str
    creator: Creator
    first_study: StudySeed
    first_assay: AssaySeed | None
    data: DataSource
    keywords: tuple[str, ...] = ()
    workspace_options: WorkspaceOptions = field(default_factory=WorkspaceOptions)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SetupConfig":
        if not isinstance(payload, Mapping):
            raise SetupValidationError("Setup payload must be an object.")

        _reject_unknown_keys(
            payload,
            {
                "project_title",
                "project_description",
                "creator",
                "first_study",
                "first_assay",
                "data",
                "keywords",
                "workspace_options",
            },
            "setup",
        )

        project_title = _required_text(payload, "project_title", "Project title")
        project_description = _required_text(
            payload, "project_description", "Project description"
        )

        creator_raw = payload.get("creator")
        if not isinstance(creator_raw, Mapping):
            raise SetupValidationError("creator must be an object.")
        _reject_unknown_keys(creator_raw, {"name", "orcid"}, "creator")
        creator_name = _required_text(creator_raw, "name", "Creator name")
        orcid = _optional_text(creator_raw.get("orcid"), "ORCID")
        if orcid and not ORCID_RE.fullmatch(orcid):
            raise SetupValidationError(
                "ORCID must look like 0000-0000-0000-0000 "
                "(final character may be X), optionally prefixed by https://orcid.org/."
            )

        study_raw = payload.get("first_study")
        if not isinstance(study_raw, Mapping):
            raise SetupValidationError("first_study must be an object.")
        _reject_unknown_keys(study_raw, {"title"}, "first_study")
        study_title = _required_text(study_raw, "title", "First study title")

        assay_raw = payload.get("first_assay")
        first_assay: AssaySeed | None
        if assay_raw is None:
            first_assay = None
        elif isinstance(assay_raw, Mapping):
            _reject_unknown_keys(assay_raw, {"title"}, "first_assay")
            assay_title = _optional_text(assay_raw.get("title"), "First assay title")
            first_assay = AssaySeed(assay_title) if assay_title else None
        else:
            raise SetupValidationError("first_assay must be an object or null.")

        data_raw = payload.get("data")
        if not isinstance(data_raw, Mapping):
            raise SetupValidationError("data must be an object.")
        _reject_unknown_keys(data_raw, {"location", "access"}, "data")
        data_location = _required_text(data_raw, "location", "Data location")
        data_access = _required_text(data_raw, "access", "Data access")
        if data_access not in ACCESS_LEVELS:
            allowed = ", ".join(sorted(ACCESS_LEVELS))
            raise SetupValidationError(
                f"Data access must be one of: {allowed}."
            )

        keywords_raw = payload.get("keywords", [])
        if not isinstance(keywords_raw, (list, tuple)):
            raise SetupValidationError("keywords must be an array of strings.")

        keywords: list[str] = []
        seen: set[str] = set()
        for raw in keywords_raw:
            if not isinstance(raw, str):
                raise SetupValidationError("Each keyword must be a string.")
            keyword = raw.strip()
            if not keyword:
                raise SetupValidationError("Keywords must not be empty strings.")
            if keyword in seen:
                raise SetupValidationError(f"Duplicate keyword: {keyword}.")
            keywords.append(keyword)
            seen.add(keyword)

        options_raw = payload.get("workspace_options")
        if options_raw is None:
            workspace_options = WorkspaceOptions()
        elif isinstance(options_raw, Mapping):
            _reject_unknown_keys(
                options_raw,
                {"study_structure", "assay_structure", "protocol_storage"},
                "workspace_options",
            )
            study_structure = (
                _optional_text(
                    options_raw.get("study_structure"),
                    "Study structure",
                )
                or "single"
            )
            assay_structure = (
                _optional_text(
                    options_raw.get("assay_structure"),
                    "Assay structure",
                )
                or "multiple"
            )
            protocol_storage = (
                _optional_text(
                    options_raw.get("protocol_storage"),
                    "Protocol storage",
                )
                or "workspace"
            )
            if study_structure not in STUDY_STRUCTURES:
                raise SetupValidationError(
                    "Study structure must be one of: "
                    + ", ".join(sorted(STUDY_STRUCTURES))
                    + "."
                )
            if assay_structure not in ASSAY_STRUCTURES:
                raise SetupValidationError(
                    "Assay structure must be one of: "
                    + ", ".join(sorted(ASSAY_STRUCTURES))
                    + "."
                )
            if protocol_storage not in PROTOCOL_STORAGE:
                raise SetupValidationError(
                    "Protocol storage must be one of: "
                    + ", ".join(sorted(PROTOCOL_STORAGE))
                    + "."
                )
            workspace_options = WorkspaceOptions(
                study_structure=study_structure,
                assay_structure=assay_structure,
                protocol_storage=protocol_storage,
            )
        else:
            raise SetupValidationError("workspace_options must be an object.")

        return cls(
            project_title=project_title,
            project_description=project_description,
            creator=Creator(creator_name, orcid),
            first_study=StudySeed(study_title),
            first_assay=first_assay,
            data=DataSource(data_location, data_access),
            keywords=tuple(keywords),
            workspace_options=workspace_options,
        )

    def to_mapping(self) -> dict[str, Any]:
        """Return the normalized payload as JSON-serializable data."""

        return {
            "project_title": self.project_title,
            "project_description": self.project_description,
            "creator": {
                "name": self.creator.name,
                "orcid": self.creator.orcid,
            },
            "first_study": {"title": self.first_study.title},
            "first_assay": (
                {"title": self.first_assay.title} if self.first_assay else None
            ),
            "data": {
                "location": self.data.location,
                "access": self.data.access,
            },
            "keywords": list(self.keywords),
            "workspace_options": {
                "study_structure": self.workspace_options.study_structure,
                "assay_structure": self.workspace_options.assay_structure,
                "protocol_storage": self.workspace_options.protocol_storage,
            },
        }
