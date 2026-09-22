"""Safe public RO-Crate export boundary.

Graph mapping/base validation live in _rocrate_model. Its writer is only called
with force=False and a new private staging directory, never a user destination.
The alpha requires disjoint source/output trees and exclusive workspace access.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Mapping
from uuid import uuid4

from . import _rocrate_model as model
from ._rocrate_model import (
    ROCRATE_CONTEXT, ROCRATE_SPEC, ROCRATE_METADATA, ExportResult,
    ROCrateExportError, ROCrateValidationIssue, ROCrateValidationReport,
    validate_rocrate,
)
from ..fs_safety import (
    absolute_path, assert_no_links, inventory, overlaps, relative_path, UnsafePathError,
)
from ..validate import validate_workspace
from .._version import __version__

MARKER = ".orw-export.json"
MARKER_FORMAT = "orw-ro-crate-export"


def _records(project: Mapping):
    for key in ("resources", "outputs"):
        yield from project.get(key, [])
    for study in project.get("studies", []):
        for assay in study.get("assays", []):
            yield from assay.get("data", [])


def _authorize_sources(root: Path, project: Mapping) -> dict:
    """Reject conflicting access declarations before any payload is copied."""
    declared = []
    snapshots = {}
    for record in _records(project):
        if "path" not in record:
            continue
        relative = relative_path(record["path"])
        source = root / relative
        assert_no_links(source)
        declared.append((source, record.get("access", "unknown")))
    for index, (source, access) in enumerate(declared):
        if access != "open":
            continue
        rel = source.relative_to(root)
        if (rel.parts[0] in {".research", ".git", ".github", ".venv"}
                or rel.as_posix() in {"README.md", ROCRATE_METADATA, MARKER}):
            raise ROCrateExportError(f"Reserved metadata/infrastructure payload: {rel}", code="reserved_payload")
        for other_index, (other, other_access) in enumerate(declared):
            if other_index == index or not overlaps(source, other):
                continue
            if other_access != "open":
                raise ROCrateExportError(
                    f"Conflicting access declarations: open {rel} overlaps "
                    f"{other_access} {other.relative_to(root)}. Nothing was exported.",
                    code="conflicting_access",
                )
            if source != other and (source.is_dir() or other.is_dir()):
                raise ROCrateExportError(
                    "Overlapping attached directories are unsupported in this alpha; "
                    "declare non-overlapping payload paths.", code="overlapping_payloads",
                )
        if source.is_dir():
            snapshots[rel.as_posix()] = inventory(source)
        elif source.is_file():
            with source.open("rb") as stream:
                digest = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            snapshots[rel.as_posix()] = digest.hexdigest()
        else:
            raise ROCrateExportError(f"Not a regular file/directory: {rel}", code="unsafe_resource")
    return snapshots


def _recognized_export(path: Path) -> dict:
    try:
        assert_no_links(path / MARKER)
        saved = json.loads((path / MARKER).read_text(encoding="utf-8"))
        actual = inventory(path, exclude=frozenset({MARKER}))
    except (OSError, ValueError) as exc:
        raise ROCrateExportError(
            f"--force only replaces an identifiable ORW export. Choose a new output directory: {path}",
            code="unrecognized_output",
        ) from exc
    if (not isinstance(saved, dict) or saved.get("format") != MARKER_FORMAT
            or saved.get("marker_version") != 1 or saved.get("inventory") != actual):
        raise ROCrateExportError(
            f"Output is unrecognized or contains changed/added files: {path}. "
            "Those files are protected even with --force; choose a new output directory.",
            code="modified_output",
        )
    return actual


def _commit(stage: Path, output: Path, previous: dict | None) -> None:
    assert_no_links(output)
    if previous is None:
        if output.exists():
            raise ROCrateExportError("Output appeared during export; refusing replacement.", code="output_exists")
        stage.rename(output)
        return
    if _recognized_export(output) != previous:
        raise ROCrateExportError("Output changed during export.", code="modified_output")
    backup = output.with_name(f".{output.name}.orw-previous-{uuid4().hex}")
    output.rename(backup)
    try:
        stage.rename(output)
    except Exception:
        # The existing export has not been deleted. Restore it on commit failure.
        if not output.exists():
            backup.rename(output)
        raise
    # Never delete an unexpected file added to the old export during the operation.
    if inventory(backup, exclude=frozenset({MARKER})) != previous:
        raise ROCrateExportError(f"Previous export changed; preserved backup at {backup}", code="preserved_backup")
    shutil.rmtree(backup)


def export_rocrate(workspace: Path | str, output: Path | str, *,
                   force: bool = False, date_published: str | None = None) -> ExportResult:
    root, target = absolute_path(workspace), absolute_path(output)
    try:
        assert_no_links(root)
        assert_no_links(target)
        if overlaps(root, target):
            raise ROCrateExportError(
                "Source and output trees must be disjoint, even with --force. "
                "Select a sibling directory outside the source workspace.", code="unsafe_output",
            )
        for relative in (".research/project.yml", ".research/workspace.yml", ".research/initialized", "README.md"):
            assert_no_links(root / relative)
        report = validate_workspace(root)
        if not report.valid:
            raise ROCrateExportError("ORW workspace validation failed; refusing export.",
                                    code="invalid_workspace", workspace_report=report)
        if target.exists() and not force:
            raise ROCrateExportError(f"Output already exists: {target}. Use --force only for an unchanged ORW export.",
                                    code="output_exists")
        previous = _recognized_export(target) if target.exists() else None
        source_metadata = (root / ".research/project.yml").read_bytes()
        source_readme = (root / "README.md").read_bytes() if (root / "README.md").exists() else None
        project = model._as_mapping(root / ".research/project.yml")
        snapshots = _authorize_sources(root, project)
        target.parent.mkdir(parents=True, exist_ok=True)
        assert_no_links(target.parent)
        with tempfile.TemporaryDirectory(prefix=".orw-export-", dir=target.parent) as temporary:
            stage = Path(temporary) / "crate"
            result = model.export_rocrate(root, stage, force=False, date_published=date_published)
            if ((root / ".research/project.yml").read_bytes() != source_metadata
                    or (stage / ".research/project.yml").read_bytes() != source_metadata
                    or ((root / "README.md").read_bytes() if (root / "README.md").exists() else None) != source_readme
                    or _authorize_sources(root, project) != snapshots):
                raise ROCrateExportError("Source changed during export; rerun with exclusive workspace access.",
                                        code="source_changed")
            manifest = {"format": MARKER_FORMAT, "marker_version": 1, "software_version": __version__,
                        "inventory": inventory(stage)}
            (stage / MARKER).write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            _commit(stage, target, previous)
        return replace(result, output=target, metadata_path=target / ROCRATE_METADATA,
                       validation=validate_rocrate(target))
    except UnsafePathError as exc:
        raise ROCrateExportError(str(exc), code="unsafe_path") from exc
