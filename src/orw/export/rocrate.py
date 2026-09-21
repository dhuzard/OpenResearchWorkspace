"""Deterministic RO-Crate 1.3 export derived from canonical ORW metadata.

RO-Crate is an interoperability/package representation. The canonical editable
scientific record remains .research/project.yml.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from typing import Any, Iterable, Mapping
from urllib.parse import quote, unquote

import yaml

from ..validate import ValidationReport, validate_workspace

ROCRATE_CONTEXT = "https://w3id.org/ro/crate/1.3/context"
ROCRATE_SPEC = "https://w3id.org/ro/crate/1.3"
ROCRATE_METADATA = "ro-crate-metadata.json"


class ROCrateExportError(RuntimeError):
    """Raised when an ORW workspace cannot be exported safely."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "export_error",
        workspace_report: ValidationReport | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.workspace_report = workspace_report


@dataclass(frozen=True)
class ROCrateValidationIssue:
    code: str
    message: str
    severity: str = "error"
    path: str | None = None


@dataclass(frozen=True)
class ROCrateValidationReport:
    valid: bool
    issues: tuple[ROCrateValidationIssue, ...]

    @property
    def errors(self) -> tuple[ROCrateValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[ROCrateValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")


@dataclass(frozen=True)
class ExportResult:
    output: Path
    metadata_path: Path
    entity_count: int
    copied_paths: tuple[str, ...]
    validation: ROCrateValidationReport


def _as_mapping(path: Path) -> Mapping[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ROCrateExportError(
            f"Could not read canonical ORW metadata: {exc}",
            code="project_read_error",
        ) from exc
    if not isinstance(data, Mapping):
        raise ROCrateExportError(
            ".research/project.yml must contain a YAML object.",
            code="project_read_error",
        )
    return data


def _types(entity: Mapping[str, Any]) -> set[str]:
    raw = entity.get("@type")
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {item for item in raw if isinstance(item, str)}
    return set()


def _absolute_uri(value: Any) -> bool:
    return (
        isinstance(value, str)
        and "\\" not in value
        and re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value) is not None
    )


def _encoded_path(path: PurePosixPath, *, directory: bool = False) -> str:
    # Keep URI path separators and native UTF-8 characters while escaping
    # characters such as spaces and percent signs as required by RO-Crate.
    encoded = quote(path.as_posix(), safe="/:@-._~", encoding="utf-8")
    if directory and not encoded.endswith("/"):
        encoded += "/"
    return encoded


def _fragment(kind: str, *parts: Any) -> str:
    material = "-".join(str(part) for part in parts if part is not None)
    encoded = quote(material, safe="-._~", encoding="utf-8")
    return f"#{kind}-{encoded or 'unknown'}"


def _ref(identifier: str) -> dict[str, str]:
    return {"@id": identifier}


def _append_ref(entity: dict[str, Any], property_name: str, identifier: str) -> None:
    current = entity.setdefault(property_name, [])
    if not isinstance(current, list):
        current = [current]
        entity[property_name] = current
    candidate = _ref(identifier)
    if candidate not in current:
        current.append(candidate)


def _normalize_orcid(value: str) -> str:
    value = value.strip()
    if value.startswith("https://orcid.org/"):
        return value
    return f"https://orcid.org/{value}"


def _validate_date_published(value: str) -> str:
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
    except ValueError as exc:
        raise ROCrateExportError(
            f"datePublished must be ISO 8601; got {value!r}.",
            code="invalid_date_published",
        ) from exc
    return value


def _default_date_published() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_source(workspace: Path, raw_path: str, output: Path) -> tuple[Path, PurePosixPath]:
    value = raw_path.strip().replace("\\", "/")
    relative = PurePosixPath(value)
    if (
        not value
        or value.startswith("/")
        or re.match(r"^[A-Za-z]:/", value)
        or ".." in relative.parts
        or relative == PurePosixPath(".")
    ):
        raise ROCrateExportError(
            f"Unsafe local resource path: {raw_path!r}.",
            code="unsafe_resource_path",
        )

    source = workspace.joinpath(*relative.parts)
    if not source.exists():
        raise ROCrateExportError(
            f"Declared local resource does not exist: {relative.as_posix()}",
            code="missing_resource",
        )

    # Reject symlinks in any path component and recursively within directories.
    cursor = workspace
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ROCrateExportError(
                f"Symlinked resources are not packaged automatically: {relative.as_posix()}",
                code="symlink_resource",
            )

    resolved_workspace = workspace.resolve()
    resolved_source = source.resolve()
    if resolved_source != resolved_workspace and resolved_workspace not in resolved_source.parents:
        raise ROCrateExportError(
            f"Resource escapes workspace: {relative.as_posix()}",
            code="unsafe_resource_path",
        )

    resolved_output = output.resolve(strict=False)
    if source.is_dir() and (
        resolved_output == resolved_source or resolved_source in resolved_output.parents
    ):
        raise ROCrateExportError(
            (
                f"Export destination is inside packaged resource directory "
                f"{relative.as_posix()!r}."
            ),
            code="recursive_export",
        )

    if source.is_dir():
        for dirpath, dirnames, filenames in os.walk(source):
            base = Path(dirpath)
            for name in [*dirnames, *filenames]:
                candidate = base / name
                if candidate.is_symlink():
                    raise ROCrateExportError(
                        (
                            "Symlinked resources are not packaged automatically: "
                            f"{candidate.relative_to(workspace).as_posix()}"
                        ),
                        code="symlink_resource",
                    )

    return source, relative


def _copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, copy_function=shutil.copy2)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _entity_name(resource: Mapping[str, Any], fallback: str) -> str:
    name = resource.get("name")
    return name.strip() if isinstance(name, str) and name.strip() else fallback


def _resource_description(
    resource: Mapping[str, Any],
    *,
    fallback: str,
) -> str:
    description = resource.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()
    return fallback


class _GraphBuilder:
    def __init__(
        self,
        workspace: Path,
        crate_root: Path,
        final_output: Path,
        project: Mapping[str, Any],
        date_published: str,
    ) -> None:
        self.workspace = workspace
        self.crate_root = crate_root
        self.final_output = final_output
        self.project = project
        self.date_published = date_published
        self.entities: list[dict[str, Any]] = []
        self.by_id: dict[str, dict[str, Any]] = {}
        self.copied_paths: list[str] = []
        self.resource_counter = 0

    def add(self, entity: dict[str, Any]) -> dict[str, Any]:
        identifier = entity["@id"]
        existing = self.by_id.get(identifier)
        if existing is not None:
            return existing
        self.by_id[identifier] = entity
        self.entities.append(entity)
        return entity

    def add_canonical_file(
        self,
        relative: PurePosixPath,
        *,
        name: str,
        description: str,
        encoding_format: str,
    ) -> str | None:
        source = self.workspace.joinpath(*relative.parts)
        if not source.is_file():
            return None
        destination = self.crate_root.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

        identifier = _encoded_path(relative)
        self.add(
            {
                "@id": identifier,
                "@type": "File",
                "name": name,
                "description": description,
                "encodingFormat": encoding_format,
                "contentSize": str(source.stat().st_size),
            }
        )
        self.copied_paths.append(relative.as_posix())
        return identifier

    def add_person(self, contributor: Mapping[str, Any], index: int) -> str:
        name = contributor.get("name")
        name_text = name.strip() if isinstance(name, str) and name.strip() else f"Contributor {index + 1}"
        orcid = contributor.get("orcid")
        if isinstance(orcid, str) and orcid.strip():
            identifier = _normalize_orcid(orcid)
        else:
            identifier = _fragment("person", index + 1)

        entity: dict[str, Any] = {
            "@id": identifier,
            "@type": "Person",
            "name": name_text,
        }
        role = contributor.get("role")
        if isinstance(role, str) and role.strip():
            entity["description"] = f"ORW contributor role: {role.strip()}"
        self.add(entity)
        return identifier

    def add_resource(
        self,
        resource: Mapping[str, Any],
        parent: dict[str, Any],
        *,
        scope: str,
    ) -> str:
        self.resource_counter += 1
        access = resource.get("access")
        access_text = access.strip() if isinstance(access, str) and access.strip() else "unknown"
        raw_path = resource.get("path")
        location = resource.get("location")
        external_identifier = resource.get("identifier")

        if isinstance(raw_path, str) and raw_path.strip() and access_text == "open":
            source, relative = _safe_source(
                self.workspace,
                raw_path,
                self.final_output,
            )
            destination = self.crate_root.joinpath(*relative.parts)
            _copy_path(source, destination)

            is_directory = source.is_dir()
            identifier = _encoded_path(relative, directory=is_directory)
            entity: dict[str, Any] = {
                "@id": identifier,
                "@type": "Dataset" if is_directory else "File",
                "name": _entity_name(resource, relative.name or relative.as_posix()),
                "description": _resource_description(
                    resource,
                    fallback=f"Open ORW resource from {scope}.",
                ),
                "conditionsOfAccess": "open",
            }
            if not is_directory:
                entity["contentSize"] = str(source.stat().st_size)
                media_type, _ = mimetypes.guess_type(source.name)
                if media_type:
                    entity["encodingFormat"] = media_type
            if isinstance(external_identifier, str) and external_identifier.strip():
                entity["identifier"] = external_identifier.strip()
            if isinstance(location, str) and _absolute_uri(location.strip()):
                entity["contentUrl"] = location.strip()

            self.add(entity)
            self.copied_paths.append(relative.as_posix())
            _append_ref(parent, "hasPart", identifier)
            return identifier

        if isinstance(location, str) and _absolute_uri(location.strip()):
            identifier = location.strip()
            entity = {
                "@id": identifier,
                "@type": "Dataset",
                "name": _entity_name(resource, identifier),
                "description": _resource_description(
                    resource,
                    fallback=f"Externally managed ORW resource from {scope}; content is not copied into this crate.",
                ),
                "conditionsOfAccess": access_text,
            }
            if isinstance(external_identifier, str) and external_identifier.strip():
                entity["identifier"] = external_identifier.strip()
            self.add(entity)
            _append_ref(parent, "hasPart", identifier)
            return identifier

        identifier = _fragment("resource", self.resource_counter)
        description = _resource_description(
            resource,
            fallback=f"ORW resource from {scope}; content is not packaged automatically.",
        )
        details: list[str] = []
        if isinstance(raw_path, str) and raw_path.strip():
            details.append(f"workspace path: {raw_path.strip()}")
        if isinstance(location, str) and location.strip():
            details.append(f"location: {location.strip()}")
        if details:
            description = f"{description} ({'; '.join(details)}.)"

        entity = {
            "@id": identifier,
            "@type": "Dataset",
            "name": _entity_name(resource, f"ORW resource {self.resource_counter}"),
            "description": description,
            "conditionsOfAccess": access_text,
        }
        if isinstance(external_identifier, str) and external_identifier.strip():
            entity["identifier"] = external_identifier.strip()
        elif isinstance(raw_path, str) and raw_path.strip():
            entity["identifier"] = raw_path.strip()
        elif isinstance(location, str) and location.strip():
            entity["identifier"] = location.strip()

        self.add(entity)
        _append_ref(parent, "hasPart", identifier)
        return identifier

    def add_assay(
        self,
        assay: Mapping[str, Any],
        study_identifier: str,
        study_entity: dict[str, Any],
        assay_index: int,
    ) -> str:
        assay_id = assay.get("identifier")
        assay_id_text = (
            assay_id.strip()
            if isinstance(assay_id, str) and assay_id.strip()
            else f"assay-{assay_index + 1}"
        )
        identifier = _fragment("assay", study_identifier, assay_id_text)
        name = assay.get("title")
        name_text = name.strip() if isinstance(name, str) and name.strip() else assay_id_text
        entity: dict[str, Any] = {
            "@id": identifier,
            "@type": "Dataset",
            "identifier": assay_id_text,
            "name": name_text,
            "description": (
                assay.get("description").strip()
                if isinstance(assay.get("description"), str)
                and assay.get("description").strip()
                else f"ORW Assay within Study {study_identifier}."
            ),
        }
        self.add(entity)
        _append_ref(study_entity, "hasPart", identifier)

        data = assay.get("data")
        if isinstance(data, list):
            for resource in data:
                if isinstance(resource, Mapping):
                    self.add_resource(
                        resource,
                        entity,
                        scope=f"Assay {assay_id_text}",
                    )
        return identifier

    def add_study(
        self,
        study: Mapping[str, Any],
        root_entity: dict[str, Any],
        study_index: int,
    ) -> str:
        study_id = study.get("identifier")
        study_id_text = (
            study_id.strip()
            if isinstance(study_id, str) and study_id.strip()
            else f"study-{study_index + 1}"
        )
        identifier = _fragment("study", study_id_text)
        title = study.get("title")
        title_text = title.strip() if isinstance(title, str) and title.strip() else study_id_text
        entity: dict[str, Any] = {
            "@id": identifier,
            "@type": "Dataset",
            "identifier": study_id_text,
            "name": title_text,
            "description": (
                study.get("description").strip()
                if isinstance(study.get("description"), str)
                and study.get("description").strip()
                else "ORW Study represented as an explicit contextual entity."
            ),
        }
        self.add(entity)
        _append_ref(root_entity, "hasPart", identifier)

        assays = study.get("assays")
        if isinstance(assays, list):
            for assay_index, assay in enumerate(assays):
                if isinstance(assay, Mapping):
                    self.add_assay(
                        assay,
                        study_id_text,
                        entity,
                        assay_index,
                    )
        return identifier

    def build(self) -> dict[str, Any]:
        descriptor = self.add(
            {
                "@id": ROCRATE_METADATA,
                "@type": "CreativeWork",
                "about": _ref("./"),
                "conformsTo": _ref(ROCRATE_SPEC),
            }
        )

        investigation = self.project.get("investigation")
        if not isinstance(investigation, Mapping):
            raise ROCrateExportError(
                "Canonical project has no valid investigation object.",
                code="invalid_project",
            )

        root_entity: dict[str, Any] = {
            "@id": "./",
            "@type": "Dataset",
            "name": str(investigation.get("title", "")).strip(),
            "description": str(investigation.get("description", "")).strip(),
            "datePublished": self.date_published,
        }
        investigation_identifier = investigation.get("identifier")
        if isinstance(investigation_identifier, str) and investigation_identifier.strip():
            root_entity["identifier"] = investigation_identifier.strip()
        keywords = investigation.get("keywords")
        if isinstance(keywords, list):
            clean_keywords = [
                value.strip()
                for value in keywords
                if isinstance(value, str) and value.strip()
            ]
            if clean_keywords:
                root_entity["keywords"] = clean_keywords

        license_value = investigation.get("license")
        if not license_value:
            license_value = self.project.get("license")
        if isinstance(license_value, str) and license_value.strip():
            license_text = license_value.strip()
            if _absolute_uri(license_text):
                root_entity["license"] = _ref(license_text)
                self.add(
                    {
                        "@id": license_text,
                        "@type": "CreativeWork",
                        "name": license_text,
                        "description": "License declared by the canonical ORW project metadata.",
                    }
                )
            else:
                root_entity["license"] = license_text

        self.add(root_entity)

        project_file_id = self.add_canonical_file(
            PurePosixPath(".research/project.yml"),
            name="Canonical ORW project record",
            description=(
                "Canonical ISA-aligned OpenResearchWorkspace metadata from which "
                "this RO-Crate export was generated."
            ),
            encoding_format="application/yaml",
        )
        if project_file_id:
            _append_ref(root_entity, "hasPart", project_file_id)

        readme_id = self.add_canonical_file(
            PurePosixPath("README.md"),
            name="ORW project overview",
            description="Human-readable project overview from the ORW workspace.",
            encoding_format="text/markdown",
        )
        if readme_id:
            _append_ref(root_entity, "hasPart", readme_id)

        contributors = self.project.get("contributors")
        if isinstance(contributors, list):
            for index, contributor in enumerate(contributors):
                if isinstance(contributor, Mapping):
                    person_id = self.add_person(contributor, index)
                    _append_ref(root_entity, "author", person_id)

        studies = self.project.get("studies")
        if isinstance(studies, list):
            for study_index, study in enumerate(studies):
                if isinstance(study, Mapping):
                    self.add_study(study, root_entity, study_index)

        for collection_name in ("resources", "outputs"):
            collection = self.project.get(collection_name)
            if isinstance(collection, list):
                for resource in collection:
                    if isinstance(resource, Mapping):
                        self.add_resource(
                            resource,
                            root_entity,
                            scope=collection_name,
                        )

        return {
            "@context": ROCRATE_CONTEXT,
            "@graph": self.entities,
        }


def _reference_ids(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        if set(value) == {"@id"} and isinstance(value.get("@id"), str):
            yield value["@id"]
        else:
            for nested in value.values():
                yield from _reference_ids(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _reference_ids(nested)


def _iso8601(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_rocrate(crate: Path | str) -> ROCrateValidationReport:
    """Validate base RO-Crate 1.3 requirements used by the ORW exporter.

    This validator targets the normative base requirements needed by ORW's
    attached-directory export. It is intentionally not an ORW RO-Crate profile.
    """

    root = Path(crate).expanduser().resolve()
    issues: list[ROCrateValidationIssue] = []

    def issue(
        code: str,
        message: str,
        *,
        severity: str = "error",
        path: str | None = None,
    ) -> None:
        issues.append(ROCrateValidationIssue(code, message, severity, path))

    if not root.is_dir():
        issue("missing_crate", f"RO-Crate directory does not exist: {root}", path=str(root))
        return ROCrateValidationReport(False, tuple(issues))

    metadata_path = root / ROCRATE_METADATA
    if not metadata_path.is_file():
        issue(
            "missing_metadata",
            f"Missing {ROCRATE_METADATA}.",
            path=ROCRATE_METADATA,
        )
        return ROCrateValidationReport(False, tuple(issues))

    try:
        document = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issue("invalid_json", f"RO-Crate metadata is not valid JSON: {exc}", path=ROCRATE_METADATA)
        return ROCrateValidationReport(False, tuple(issues))

    if not isinstance(document, Mapping):
        issue("invalid_document", "RO-Crate metadata root must be a JSON object.", path=ROCRATE_METADATA)
        return ROCrateValidationReport(False, tuple(issues))

    if document.get("@context") != ROCRATE_CONTEXT:
        issue(
            "wrong_context",
            f"@context must be {ROCRATE_CONTEXT!r}.",
            path="@context",
        )

    graph = document.get("@graph")
    if not isinstance(graph, list):
        issue("missing_graph", "@graph must be a JSON array.", path="@graph")
        return ROCrateValidationReport(False, tuple(issues))

    by_id: dict[str, Mapping[str, Any]] = {}
    for index, raw_entity in enumerate(graph):
        entity_path = f"@graph[{index}]"
        if not isinstance(raw_entity, Mapping):
            issue("invalid_entity", "Every @graph item must be an object.", path=entity_path)
            continue
        identifier = raw_entity.get("@id")
        if not isinstance(identifier, str) or not identifier:
            issue("missing_id", "Every RO-Crate entity MUST have @id.", path=entity_path)
            continue
        if identifier in by_id:
            issue("duplicate_id", f"Duplicate entity @id: {identifier}", path=entity_path)
        else:
            by_id[identifier] = raw_entity

        entity_types = _types(raw_entity)
        if not entity_types:
            issue(
                "missing_type",
                "Every RO-Crate entity MUST have @type.",
                path=f"{entity_path}.@type",
            )

        # RO-Crate metadata must be flattened. Nested entity descriptions are
        # not allowed; nested objects are entity references and therefore only
        # contain @id.
        for key, value in raw_entity.items():
            if key.startswith("@"):
                continue

            def check_nested(item: Any, nested_path: str) -> None:
                if isinstance(item, Mapping):
                    if set(item) != {"@id"} or not isinstance(item.get("@id"), str):
                        issue(
                            "not_flattened",
                            "Nested entity objects must be represented as {'@id': ...} references.",
                            path=nested_path,
                        )
                elif isinstance(item, list):
                    for nested_index, child in enumerate(item):
                        check_nested(child, f"{nested_path}[{nested_index}]")

            check_nested(value, f"{entity_path}.{key}")

    descriptor = by_id.get(ROCRATE_METADATA)
    if descriptor is None:
        issue(
            "missing_descriptor",
            f"@graph MUST describe {ROCRATE_METADATA}.",
            path="@graph",
        )
        root_entity = None
    else:
        if "CreativeWork" not in _types(descriptor):
            issue(
                "descriptor_type",
                "RO-Crate Metadata Descriptor MUST have @type CreativeWork.",
                path=f"{ROCRATE_METADATA}.@type",
            )
        about = descriptor.get("about")
        if not (
            isinstance(about, Mapping)
            and isinstance(about.get("@id"), str)
        ):
            issue(
                "descriptor_about",
                "RO-Crate Metadata Descriptor MUST reference the Root Data Entity using about.",
                path=f"{ROCRATE_METADATA}.about",
            )
            root_entity = None
        else:
            root_id = about["@id"]
            root_entity = by_id.get(root_id)
            if root_entity is None:
                issue(
                    "missing_root",
                    f"Descriptor about reference does not resolve: {root_id}",
                    path=f"{ROCRATE_METADATA}.about",
                )

        conforms = descriptor.get("conformsTo")
        if not (
            isinstance(conforms, Mapping)
            and conforms.get("@id") == ROCRATE_SPEC
        ):
            issue(
                "descriptor_conformance",
                f"Metadata Descriptor SHOULD conformTo {ROCRATE_SPEC}.",
                severity="warning",
                path=f"{ROCRATE_METADATA}.conformsTo",
            )

    if root_entity is not None:
        root_id = str(root_entity.get("@id"))
        if "Dataset" not in _types(root_entity):
            issue(
                "root_type",
                "Root Data Entity MUST have @type Dataset.",
                path=f"{root_id}.@type",
            )
        if not _iso8601(root_entity.get("datePublished")):
            issue(
                "root_date_published",
                "Root Data Entity MUST have a single ISO 8601 datePublished value.",
                path=f"{root_id}.datePublished",
            )
        if not isinstance(root_entity.get("name"), str) or not root_entity.get("name", "").strip():
            issue(
                "root_name",
                "Root Data Entity SHOULD have a human-readable name.",
                severity="warning",
                path=f"{root_id}.name",
            )
        if not isinstance(root_entity.get("description"), str) or not root_entity.get("description", "").strip():
            issue(
                "root_description",
                "Root Data Entity SHOULD have a description.",
                severity="warning",
                path=f"{root_id}.description",
            )
        if "license" not in root_entity:
            issue(
                "root_license",
                "Root Data Entity SHOULD declare a license when known.",
                severity="warning",
                path=f"{root_id}.license",
            )

    # Local and fragment references should resolve to graph entities. Absolute
    # external references MAY be described elsewhere and are therefore not
    # required in the local graph.
    for entity_id, entity in by_id.items():
        for key, value in entity.items():
            if key.startswith("@"):
                continue
            for referenced_id in _reference_ids(value):
                if (
                    referenced_id.startswith("#")
                    or referenced_id == "./"
                    or not _absolute_uri(referenced_id)
                ) and referenced_id not in by_id:
                    issue(
                        "unresolved_reference",
                        f"Reference does not resolve in @graph: {referenced_id}",
                        path=f"{entity_id}.{key}",
                    )

    # Attached local Data Entities must exist in the crate and be reachable
    # from the root through hasPart, directly or indirectly.
    reachable: set[str] = set()
    if root_entity is not None:
        pending = [str(root_entity.get("@id"))]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            entity = by_id.get(current)
            if entity is None:
                continue
            has_part = entity.get("hasPart")
            if not isinstance(has_part, list):
                has_part = [has_part] if has_part is not None else []
            for child in has_part:
                if isinstance(child, Mapping) and isinstance(child.get("@id"), str):
                    pending.append(child["@id"])

    for entity_id, entity in by_id.items():
        if (
            entity_id in {ROCRATE_METADATA, "./"}
            or entity_id.startswith("#")
            or _absolute_uri(entity_id)
        ):
            continue
        entity_types = _types(entity)
        if "File" not in entity_types and "Dataset" not in entity_types:
            continue

        decoded = unquote(entity_id.rstrip("/"))
        relative = PurePosixPath(decoded)
        if (
            not decoded
            or decoded.startswith("/")
            or ".." in relative.parts
        ):
            issue(
                "unsafe_data_entity_id",
                f"Local Data Entity @id is not a safe relative URI: {entity_id}",
                path=f"{entity_id}.@id",
            )
            continue

        target = root.joinpath(*relative.parts)
        if "File" in entity_types and not target.is_file():
            issue(
                "missing_file_entity",
                f"Attached File Data Entity is absent: {entity_id}",
                path=entity_id,
            )
        if "Dataset" in entity_types and not target.is_dir():
            issue(
                "missing_dataset_entity",
                f"Attached Dataset Data Entity is absent: {entity_id}",
                path=entity_id,
            )
        if entity_id not in reachable:
            issue(
                "unreachable_data_entity",
                f"Data Entity is not reachable from the Root Data Entity via hasPart: {entity_id}",
                path=entity_id,
            )

    valid = not any(item.severity == "error" for item in issues)
    return ROCrateValidationReport(valid, tuple(issues))


def export_rocrate(
    workspace: Path | str,
    output: Path | str,
    *,
    force: bool = False,
    date_published: str | None = None,
) -> ExportResult:
    """Export a validated ORW workspace as an attached RO-Crate 1.3 directory."""

    workspace_root = Path(workspace).expanduser().resolve()
    output_path = Path(output).expanduser().resolve(strict=False)

    workspace_report = validate_workspace(workspace_root)
    if not workspace_report.valid:
        raise ROCrateExportError(
            "ORW workspace validation failed; refusing RO-Crate export.",
            code="invalid_workspace",
            workspace_report=workspace_report,
        )

    if output_path == workspace_root or output_path in workspace_root.parents:
        raise ROCrateExportError(
            "RO-Crate output must not replace the source workspace or one of its parents.",
            code="unsafe_output",
        )
    if output_path.exists() and not force:
        raise ROCrateExportError(
            f"Output already exists: {output_path}. Use --force to replace it.",
            code="output_exists",
        )
    if output_path.exists() and not output_path.is_dir():
        raise ROCrateExportError(
            f"RO-Crate directory output path is an existing file: {output_path}",
            code="output_not_directory",
        )

    date_value = _validate_date_published(date_published or _default_date_published())
    project = _as_mapping(workspace_root / ".research" / "project.yml")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = Path(
        tempfile.mkdtemp(
            prefix=f".{output_path.name}.orw-rocrate-",
            dir=output_path.parent,
        )
    )

    try:
        builder = _GraphBuilder(
            workspace_root,
            temp_path,
            output_path,
            project,
            date_value,
        )
        document = builder.build()
        metadata_path = temp_path / ROCRATE_METADATA
        metadata_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        crate_report = validate_rocrate(temp_path)
        if not crate_report.valid:
            details = "; ".join(
                f"{item.code}: {item.message}" for item in crate_report.errors
            )
            raise ROCrateExportError(
                f"Generated RO-Crate failed RO-Crate 1.3 validation: {details}",
                code="invalid_generated_crate",
            )

        if output_path.exists():
            shutil.rmtree(output_path)
        temp_path.replace(output_path)

        final_report = validate_rocrate(output_path)
        return ExportResult(
            output=output_path,
            metadata_path=output_path / ROCRATE_METADATA,
            entity_count=len(document["@graph"]),
            copied_paths=tuple(builder.copied_paths),
            validation=final_report,
        )
    except Exception:
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
        raise
