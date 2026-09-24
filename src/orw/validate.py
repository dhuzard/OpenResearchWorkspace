"""Provider-neutral validation for OpenResearchWorkspace projects."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources as importlib_resources
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterator, Mapping

from jsonschema import Draft202012Validator
import yaml


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]


def _yaml_mapping(
    path: Path,
    *,
    label: str,
    issues: list[ValidationIssue],
) -> Mapping[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(
            ValidationIssue(
                "read_error",
                f"Could not read {label}: {exc}",
                path.as_posix(),
            )
        )
        return None

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        issues.append(
            ValidationIssue(
                "invalid_yaml",
                f"{label} is not valid YAML: {exc}",
                path.as_posix(),
            )
        )
        return None

    if not isinstance(data, Mapping):
        issues.append(
            ValidationIssue(
                "invalid_document",
                f"{label} must contain a YAML object at its root.",
                path.as_posix(),
            )
        )
        return None
    return data


def _schema_path(parts: Any) -> str:
    result = ""
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        elif result:
            result += f".{part}"
        else:
            result = str(part)
    return result


def _load_project_schema() -> Mapping[str, Any]:
    schema_file = importlib_resources.files("orw.schemas").joinpath(
        "project.schema.json"
    )
    return json.loads(schema_file.read_text(encoding="utf-8"))


def _validate_schema(
    project_data: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    try:
        schema = _load_project_schema()
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        issues.append(
            ValidationIssue(
                "schema_unavailable",
                f"Installed ORW project schema could not be loaded: {exc}",
                "orw.schemas/project.schema.json",
            )
        )
        return

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(project_data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    for error in errors:
        location = _schema_path(error.absolute_path)
        issues.append(
            ValidationIssue(
                "schema_validation",
                error.message,
                (
                    f".research/project.yml:{location}"
                    if location
                    else ".research/project.yml"
                ),
            )
        )


def _safe_relative_path(raw: Any) -> PurePosixPath | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip().replace("\\", "/")
    if value.startswith("/") or re.match(r"^[A-Za-z]:/", value):
        return None
    path = PurePosixPath(value)
    if ".." in path.parts:
        return None
    return path


def _declared_paths(
    project: Mapping[str, Any],
) -> Iterator[tuple[str, Any, PurePosixPath | None]]:
    studies = project.get("studies")
    if isinstance(studies, list):
        for study_index, study in enumerate(studies):
            if not isinstance(study, Mapping):
                continue

            study_path_raw = study.get("path")
            study_path = _safe_relative_path(study_path_raw)
            if "path" in study:
                yield (
                    f"studies[{study_index}].path",
                    study_path_raw,
                    None,
                )

            assays = study.get("assays")
            if isinstance(assays, list):
                for assay_index, assay in enumerate(assays):
                    if not isinstance(assay, Mapping):
                        continue
                    if "path" in assay:
                        yield (
                            f"studies[{study_index}].assays[{assay_index}].path",
                            assay.get("path"),
                            study_path,
                        )

                    assay_data = assay.get("data")
                    if isinstance(assay_data, list):
                        for data_index, datum in enumerate(assay_data):
                            if isinstance(datum, Mapping) and "path" in datum:
                                yield (
                                    (
                                        f"studies[{study_index}].assays[{assay_index}]"
                                        f".data[{data_index}].path"
                                    ),
                                    datum.get("path"),
                                    None,
                                )

    for collection_name in ("resources", "outputs"):
        collection = project.get(collection_name)
        if not isinstance(collection, list):
            continue
        for index, item in enumerate(collection):
            if isinstance(item, Mapping) and "path" in item:
                yield (
                    f"{collection_name}[{index}].path",
                    item.get("path"),
                    None,
                )


def _validate_declared_paths(
    root: Path,
    project: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    for location, raw, expected_parent in _declared_paths(project):
        relative = _safe_relative_path(raw)
        if relative is None:
            issues.append(
                ValidationIssue(
                    "unsafe_declared_path",
                    (
                        "Declared workspace paths must be non-empty relative paths "
                        "and must not contain '..'."
                    ),
                    f".research/project.yml:{location}",
                )
            )
            continue

        if expected_parent is not None:
            try:
                relative.relative_to(expected_parent)
            except ValueError:
                issues.append(
                    ValidationIssue(
                        "assay_path_outside_study",
                        (
                            f"Assay path {relative.as_posix()!r} is not inside "
                            f"its Study path {expected_parent.as_posix()!r}."
                        ),
                        f".research/project.yml:{location}",
                    )
                )

        target = root.joinpath(*relative.parts)
        if not target.exists():
            issues.append(
                ValidationIssue(
                    "missing_declared_path",
                    f"Declared workspace path does not exist: {relative.as_posix()}",
                    f".research/project.yml:{location}",
                )
            )


def _validate_identifiers(
    project: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    studies = project.get("studies")
    if not isinstance(studies, list):
        return

    study_ids: set[str] = set()
    for study_index, study in enumerate(studies):
        if not isinstance(study, Mapping):
            continue
        study_id = study.get("identifier")
        if isinstance(study_id, str):
            if study_id in study_ids:
                issues.append(
                    ValidationIssue(
                        "duplicate_identifier",
                        f"Duplicate Study identifier: {study_id}",
                        f".research/project.yml:studies[{study_index}].identifier",
                    )
                )
            study_ids.add(study_id)

        assay_ids: set[str] = set()
        assays = study.get("assays")
        if not isinstance(assays, list):
            continue
        for assay_index, assay in enumerate(assays):
            if not isinstance(assay, Mapping):
                continue
            assay_id = assay.get("identifier")
            if isinstance(assay_id, str):
                if assay_id in assay_ids:
                    issues.append(
                        ValidationIssue(
                            "duplicate_identifier",
                            f"Duplicate Assay identifier within Study: {assay_id}",
                            (
                                f".research/project.yml:studies[{study_index}]"
                                f".assays[{assay_index}].identifier"
                            ),
                        )
                    )
                assay_ids.add(assay_id)


def _looks_like_pre_core_github_workspace(project: Mapping[str, Any]) -> bool:
    """Recognize the September 2026 pre-core GitHub initializer shape."""

    legacy_project = project.get("project")
    legacy_investigation = project.get("investigation")
    return (
        isinstance(legacy_project, Mapping)
        and isinstance(legacy_investigation, Mapping)
        and isinstance(legacy_investigation.get("studies"), list)
        and "studies" not in project
    )


def _validate_workspace_state(
    root: Path,
    project_data: Mapping[str, Any] | None,
    issues: list[ValidationIssue],
) -> None:
    workspace_path = root / ".research" / "workspace.yml"
    marker_path = root / ".research" / "initialized"

    if not workspace_path.is_file():
        issues.append(
            ValidationIssue(
                "missing_workspace",
                "Missing .research/workspace.yml.",
                ".research/workspace.yml",
            )
        )
        workspace_data = None
    else:
        workspace_data = _yaml_mapping(
            workspace_path,
            label=".research/workspace.yml",
            issues=issues,
        )

    if not marker_path.is_file():
        issues.append(
            ValidationIssue(
                "missing_initialized",
                "Missing .research/initialized.",
                ".research/initialized",
            )
        )
        marker_data = None
    else:
        marker_data = _yaml_mapping(
            marker_path,
            label=".research/initialized",
            issues=issues,
        )

    if workspace_data is not None:
        orw_state = workspace_data.get("orw")
        if not isinstance(orw_state, Mapping):
            issues.append(
                ValidationIssue(
                    "missing_workspace_state",
                    ".research/workspace.yml must contain an 'orw' object.",
                    ".research/workspace.yml:orw",
                )
            )
        else:
            if orw_state.get("initialized") is not True:
                issues.append(
                    ValidationIssue(
                        "workspace_not_initialized",
                        ".research/workspace.yml must record orw.initialized: true.",
                        ".research/workspace.yml:orw.initialized",
                    )
                )

            if project_data is not None:
                project_version = project_data.get("spec_version")
                workspace_version = orw_state.get("spec_version")
                if (
                    project_version is not None
                    and workspace_version is not None
                    and project_version != workspace_version
                ):
                    issues.append(
                        ValidationIssue(
                            "spec_version_mismatch",
                            (
                                "Project and workspace specification versions differ: "
                                f"{project_version!r} != {workspace_version!r}."
                            ),
                            ".research/workspace.yml:orw.spec_version",
                        )
                    )

        implementation = workspace_data.get("implementation")
        if isinstance(implementation, Mapping):
            canonical = implementation.get("canonical_project_record")
            if canonical is not None and canonical != ".research/project.yml":
                issues.append(
                    ValidationIssue(
                        "canonical_record_mismatch",
                        (
                            "implementation.canonical_project_record must be "
                            "'.research/project.yml'."
                        ),
                        (
                            ".research/workspace.yml:"
                            "implementation.canonical_project_record"
                        ),
                    )
                )

    if marker_data is not None and marker_data.get("initialized") is not True:
        issues.append(
            ValidationIssue(
                "invalid_initialized_marker",
                ".research/initialized must record initialized: true.",
                ".research/initialized:initialized",
            )
        )


def validate_workspace(destination: Path | str) -> ValidationReport:
    """Validate an ORW workspace without requiring Git or a hosting provider."""

    root = Path(destination).expanduser().resolve()
    issues: list[ValidationIssue] = []

    if not root.exists():
        return ValidationReport(
            valid=False,
            issues=(
                ValidationIssue(
                    "missing_workspace_root",
                    f"Workspace folder does not exist: {root}",
                    str(root),
                ),
            ),
        )
    if not root.is_dir():
        return ValidationReport(
            valid=False,
            issues=(
                ValidationIssue(
                    "invalid_workspace_root",
                    f"Workspace path is not a directory: {root}",
                    str(root),
                ),
            ),
        )

    project_path = root / ".research" / "project.yml"
    if not project_path.is_file():
        issues.append(
            ValidationIssue(
                "missing_project",
                "Missing canonical .research/project.yml.",
                ".research/project.yml",
            )
        )
        project_data = None
    else:
        project_data = _yaml_mapping(
            project_path,
            label=".research/project.yml",
            issues=issues,
        )

    if project_data is not None:
        if _looks_like_pre_core_github_workspace(project_data):
            issues.append(
                ValidationIssue(
                    "legacy_template_format",
                    (
                        "This workspace appears to have been initialized by the "
                        "pre-core GitHub template used before 21 September 2026. "
                        "Its metadata shape requires an explicit migration; do not "
                        "repair it by hand. See docs/legacy-template-migration.md."
                    ),
                    ".research/project.yml",
                )
            )
        _validate_schema(project_data, issues)
        _validate_identifiers(project_data, issues)
        _validate_declared_paths(root, project_data, issues)

    _validate_workspace_state(root, project_data, issues)

    return ValidationReport(valid=not issues, issues=tuple(issues))
