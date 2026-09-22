"""Deterministic, provider-neutral evolution of an existing ORW workspace.

Creating a workspace is only the first scientific act; Studies, measurements,
people and data references accumulate afterwards. These operations are the one
supported way to record that, so the CLI, the browser and any agent apply the
same conflict rules instead of each editing YAML their own way.

Every operation:

* refuses to start from a workspace that does not already validate;
* detects conflicts (duplicate identifiers, overlapping paths, declared paths
  that do not exist) before touching the filesystem;
* produces a reviewable plan, so ``--dry-run`` shows the exact diff that
  applying would write;
* writes the canonical record atomically and rolls the whole operation back if
  the resulting workspace would not validate.

No Git, network or hosting-provider operation happens here.
"""
from __future__ import annotations

from dataclasses import dataclass
import difflib
import os
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import yaml

from . import edit
from ._scaffold import (
    ASSAY_CONTAINER_FOLDER, NO_ASSAY_FOLDER, assay_folders, readme_text, slug,
    study_folders,
)
from .fs_safety import UnsafePathError, absolute_path, assert_no_links, overlaps, relative_path
from .model import ACCESS_LEVELS, ORCID_RE
from .validate import ValidationReport, validate_workspace

PROJECT_RECORD = ".research/project.yml"
RESEARCH_DIRECTORY = ".research"
STATUSES = ("active", "paused", "completed", "archived")
RESOURCE_COLLECTIONS = ("resources", "outputs")


class MutationError(ValueError):
    """A workspace mutation was refused; nothing on disk was modified."""


class MutationInputError(MutationError):
    """The requested mutation is not well formed."""


class MutationConflict(MutationError):
    """The mutation conflicts with what the workspace already records."""


class WorkspaceNotValid(MutationError):
    """The workspace did not validate before, or would not validate after."""

    def __init__(self, message: str, report: ValidationReport, stage: str) -> None:
        super().__init__(message)
        self.report = report
        self.stage = stage


@dataclass(frozen=True)
class MutationPlan:
    """Everything an operation would write, reviewable before it is applied."""

    workspace: Path
    operation: str
    summary: str
    identifier: str | None
    record_before: str
    record_after: str
    new_directories: tuple[str, ...] = ()
    new_files: tuple[tuple[str, str], ...] = ()
    replaced_files: tuple[tuple[str, str, str], ...] = ()

    @property
    def record(self) -> str:
        """The canonical record this plan rewrites."""

        return PROJECT_RECORD

    def diff(self) -> str:
        """A unified diff of the canonical record, as a reviewer would read it."""

        return "".join(
            difflib.unified_diff(
                self.record_before.splitlines(keepends=True),
                self.record_after.splitlines(keepends=True),
                fromfile=f"a/{PROJECT_RECORD}",
                tofile=f"b/{PROJECT_RECORD}",
            )
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "summary": self.summary,
            "workspace": str(self.workspace),
            "identifier": self.identifier,
            "record": PROJECT_RECORD,
            "diff": self.diff(),
            "new_directories": list(self.new_directories),
            "new_files": [name for name, _ in self.new_files],
            "replaced_files": [name for name, _, _ in self.replaced_files],
        }


@dataclass(frozen=True)
class MutationResult:
    plan: MutationPlan
    applied: bool
    validation: ValidationReport | None = None

    def to_mapping(self) -> dict[str, Any]:
        return {"applied": self.applied, **self.plan.to_mapping()}


# --- reading and checking the workspace -------------------------------------


def _record_path(root: Path) -> Path:
    return root / RESEARCH_DIRECTORY / "project.yml"


def _read_record(path: Path) -> tuple[str, str]:
    """Return the record with LF endings plus the convention to write back.

    Workspaces created on Windows hold CRLF. Normalizing them would turn a
    one-line addition into a whole-file diff, so the original ending is kept.
    """

    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def _open(workspace: Path | str) -> tuple[Path, str, Mapping[str, Any]]:
    try:
        root = absolute_path(workspace)
        assert_no_links(root)
    except UnsafePathError as exc:
        raise MutationInputError(str(exc)) from exc
    if not root.is_dir():
        raise MutationInputError(f"Workspace folder does not exist: {root}")

    report = validate_workspace(root)
    if not report.valid:
        raise WorkspaceNotValid(
            f"Refusing to modify a workspace that does not validate: {root}",
            report,
            "before",
        )

    text, _ = _read_record(_record_path(root))
    data = yaml.safe_load(text)
    if not isinstance(data, Mapping):
        raise MutationInputError(f"{PROJECT_RECORD} must contain a YAML object.")
    return root, text, data


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MutationInputError(f"{label} must be a non-empty string.")
    return value.strip()


def _optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _identifier(value: str, label: str) -> str:
    """Identifiers double as folder names, so only the slug form is accepted."""

    candidate = _text(value, label)
    if slug(candidate, "") != candidate:
        raise MutationInputError(
            f"{label} must be lowercase letters, digits and single hyphens "
            f"(for example {slug(candidate, 'study-01')!r}), not {candidate!r}."
        )
    return candidate


def _derive_identifier(title: str, label: str) -> str:
    candidate = slug(title, "")
    if not candidate:
        raise MutationInputError(
            f"{label} could not be derived from {title!r}; supply one explicitly."
        )
    return candidate


def _workspace_relative(raw: str, label: str) -> PurePosixPath:
    try:
        path = PurePosixPath(relative_path(raw).as_posix())
    except UnsafePathError as exc:
        raise MutationInputError(f"{label}: {exc}") from exc
    if path.parts[0] == RESEARCH_DIRECTORY:
        raise MutationInputError(
            f"{label} must not point inside {RESEARCH_DIRECTORY}/, which ORW owns."
        )
    return path


def _studies(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    studies = data.get("studies")
    if studies is None:
        return []
    if not isinstance(studies, list):
        raise MutationInputError("studies must be a sequence in the project record.")
    return [study for study in studies if isinstance(study, Mapping)]


def _study_index(data: Mapping[str, Any], identifier: str) -> int | None:
    """Index into the record's own sequence, which is what the editor addresses."""

    studies = data.get("studies")
    if not isinstance(studies, list):
        return None
    for position, study in enumerate(studies):
        if isinstance(study, Mapping) and study.get("identifier") == identifier:
            return position
    return None


def _assays(study: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    assays = study.get("assays")
    if not isinstance(assays, list):
        return []
    return [assay for assay in assays if isinstance(assay, Mapping)]


def _declared_paths(data: Mapping[str, Any]) -> list[tuple[str, PurePosixPath]]:
    """Every workspace-relative path the record already claims."""

    declared: list[tuple[str, PurePosixPath]] = []

    def record(label: str, raw: Any) -> None:
        if isinstance(raw, str) and raw.strip():
            declared.append((label, PurePosixPath(raw.strip().replace("\\", "/"))))

    for study in _studies(data):
        record(f"Study {study.get('identifier')!r}", study.get("path"))
        for assay in _assays(study):
            record(f"Assay {assay.get('identifier')!r}", assay.get("path"))
    return declared


def _reject_path_overlap(
    candidate: PurePosixPath,
    data: Mapping[str, Any],
    label: str,
    *,
    contained_by: PurePosixPath | None = None,
) -> None:
    """Refuse a path that would collide with one the record already declares.

    An Assay is expected to sit inside its own Study, so that one containment is
    the single permitted overlap.
    """

    for owner, existing in _declared_paths(data):
        if contained_by is not None and existing == contained_by:
            continue
        if overlaps(Path(candidate), Path(existing)):
            raise MutationConflict(
                f"{label} path {candidate.as_posix()!r} overlaps the path already "
                f"declared by {owner}: {existing.as_posix()!r}."
            )


def _require_empty_directory(root: Path, relative: PurePosixPath, label: str) -> None:
    directory = root / Path(*relative.parts)
    try:
        assert_no_links(directory)
    except UnsafePathError as exc:
        raise MutationInputError(str(exc)) from exc
    if directory.exists():
        if not directory.is_dir():
            raise MutationConflict(
                f"{label} path already exists as a file: {relative.as_posix()}"
            )
        if any(directory.iterdir()):
            raise MutationConflict(
                f"{label} path already exists and is not empty: {relative.as_posix()}. "
                "Choose another identifier or path; existing content was not modified."
            )


def _missing_directories(root: Path, targets: Iterable[PurePosixPath]) -> tuple[str, ...]:
    """Directories to create, parents first, each tracked for rollback."""

    needed: list[str] = []
    seen: set[str] = set()
    for target in targets:
        parts: list[str] = []
        for part in target.parts:
            parts.append(part)
            relative = PurePosixPath(*parts)
            name = relative.as_posix()
            if name in seen:
                continue
            seen.add(name)
            if not (root / Path(*parts)).exists():
                needed.append(name)
    return tuple(needed)


def _scaffold_files(
    layout: Mapping[Path, tuple[str, str]],
) -> tuple[tuple[PurePosixPath, ...], tuple[tuple[str, str], ...]]:
    directories = tuple(PurePosixPath(path.as_posix()) for path in layout)
    files = tuple(
        (f"{path.as_posix()}/README.md", readme_text(title, body))
        for path, (title, body) in layout.items()
    )
    return directories, files


def _plan(
    root: Path,
    operation: str,
    summary: str,
    identifier: str | None,
    before: str,
    after: str,
    *,
    directories: Sequence[PurePosixPath] = (),
    files: Sequence[tuple[str, str]] = (),
    replaced: Sequence[tuple[str, str, str]] = (),
) -> MutationPlan:
    new_directories = _missing_directories(root, directories)
    new_files = tuple(
        (name, content) for name, content in files if not (root / Path(name)).exists()
    )
    return MutationPlan(
        workspace=root,
        operation=operation,
        summary=summary,
        identifier=identifier,
        record_before=before,
        record_after=after,
        new_directories=new_directories,
        new_files=new_files,
        replaced_files=tuple(replaced),
    )


# --- applying ---------------------------------------------------------------


def _atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".orw-mutate-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_plan(plan: MutationPlan) -> ValidationReport:
    """Apply *plan*, or restore the workspace and raise.

    This assumes exclusive access to the workspace for the duration of the
    call. It is a rollback on ordinary failure, not a filesystem transaction
    against another process writing concurrently.
    """

    # A plan can arrive from another process, so normalize its root here rather
    # than trusting the caller to have done it. Ancestors below a host alias
    # such as macOS /var -> /private/var are resolved; a link at the workspace
    # root itself is still refused.
    try:
        root = absolute_path(plan.workspace)
        assert_no_links(root)
    except UnsafePathError as exc:
        raise MutationInputError(str(exc)) from exc

    record = _record_path(root)
    try:
        assert_no_links(record)
    except UnsafePathError as exc:
        raise MutationInputError(str(exc)) from exc

    current, newline = _read_record(record)
    if current != plan.record_before:
        raise MutationConflict(
            f"{PROJECT_RECORD} changed after this operation was planned; nothing was written."
        )

    created_directories: list[Path] = []
    created_files: list[Path] = []
    restored_files: list[tuple[Path, bytes]] = []
    try:
        for name in plan.new_directories:
            path = root / Path(name)
            assert_no_links(path)
            path.mkdir()
            created_directories.append(path)

        for name, content in plan.new_files:
            path = root / Path(name)
            assert_no_links(path)
            with path.open("x", encoding="utf-8") as stream:
                created_files.append(path)
                stream.write(content)

        for name, expected, replacement in plan.replaced_files:
            path = root / Path(name)
            assert_no_links(path)
            original = path.read_bytes()
            if original.decode("utf-8").replace("\r\n", "\n") != expected:
                raise MutationConflict(
                    f"Refusing to replace an edited file: {name}"
                )
            restored_files.append((path, original))
            _atomic_write(path, replacement.replace("\n", newline).encode("utf-8"))

        _atomic_write(record, plan.record_after.replace("\n", newline).encode("utf-8"))

        report = validate_workspace(root)
        if not report.valid:
            raise WorkspaceNotValid(
                "The resulting workspace would not validate; the change was rolled back.",
                report,
                "after",
            )
        return report
    except BaseException:
        _atomic_write(record, current.replace("\n", newline).encode("utf-8"))
        for path, original in reversed(restored_files):
            _atomic_write(path, original)
        for path in reversed(created_files):
            path.unlink(missing_ok=True)
        for path in reversed(created_directories):
            try:
                path.rmdir()
            except OSError:
                pass
        raise


def _finish(plan: MutationPlan, dry_run: bool) -> MutationResult:
    if dry_run:
        return MutationResult(plan=plan, applied=False)
    return MutationResult(plan=plan, applied=True, validation=apply_plan(plan))


# --- operations -------------------------------------------------------------


def add_study(
    workspace: Path | str,
    title: str,
    *,
    identifier: str | None = None,
    description: str | None = None,
    path: str | None = None,
    dry_run: bool = False,
) -> MutationResult:
    """Record a new ISA Study and scaffold its folders."""

    root, text, data = _open(workspace)
    title = _text(title, "Study title")
    description = _optional_text(description, "Study description")
    study_id = (
        _identifier(identifier, "Study identifier")
        if identifier is not None
        else _derive_identifier(title, "Study identifier")
    )

    for study in _studies(data):
        if study.get("identifier") == study_id:
            raise MutationConflict(f"A Study with identifier {study_id!r} already exists.")

    relative = (
        _workspace_relative(path, "Study path")
        if path is not None
        else PurePosixPath("studies") / study_id
    )
    _reject_path_overlap(relative, data, "Study")
    _require_empty_directory(root, relative, "Study")

    item = {
        "identifier": study_id,
        "title": title,
        "description": description,
        "path": relative.as_posix(),
        "assays": [],
    }
    after = edit.append_item(text, ("studies",), item)

    study_root = Path(*relative.parts)
    layout = {study_root: (title, _study_readme(data))}
    layout.update(study_folders(study_root))
    layout[study_root / "assays"] = NO_ASSAY_FOLDER
    directories, files = _scaffold_files(layout)

    return _finish(
        _plan(
            root,
            "study.add",
            f"Added Study {study_id!r} at {relative.as_posix()}",
            study_id,
            text,
            after,
            directories=directories,
            files=files,
        ),
        dry_run,
    )


def _study_readme(data: Mapping[str, Any]) -> str:
    investigation = data.get("investigation")
    name = ""
    if isinstance(investigation, Mapping) and isinstance(investigation.get("title"), str):
        name = investigation["title"]
    return (
        f"This directory represents an ISA **Study** within the Investigation **{name}**."
        if name
        else "This directory represents an ISA **Study** within this Investigation."
    )


def add_assay(
    workspace: Path | str,
    study: str,
    title: str,
    *,
    identifier: str | None = None,
    description: str | None = None,
    path: str | None = None,
    dry_run: bool = False,
) -> MutationResult:
    """Record a new ISA Assay inside an existing Study and scaffold its folders."""

    root, text, data = _open(workspace)
    study_id = _text(study, "Study identifier")
    title = _text(title, "Assay title")
    description = _optional_text(description, "Assay description")
    assay_id = (
        _identifier(identifier, "Assay identifier")
        if identifier is not None
        else _derive_identifier(title, "Assay identifier")
    )

    index = _study_index(data, study_id)
    if index is None:
        known = ", ".join(
            repr(item.get("identifier")) for item in _studies(data)
        ) or "none"
        raise MutationInputError(
            f"No Study with identifier {study_id!r}. Known Studies: {known}."
        )
    parent = data["studies"][index]

    for assay in _assays(parent):
        if assay.get("identifier") == assay_id:
            raise MutationConflict(
                f"Study {study_id!r} already records an Assay {assay_id!r}."
            )

    study_path_raw = parent.get("path")
    study_path = (
        _workspace_relative(study_path_raw, f"Study {study_id!r} path")
        if isinstance(study_path_raw, str) and study_path_raw.strip()
        else None
    )
    if path is not None:
        relative = _workspace_relative(path, "Assay path")
        if study_path is not None and not _inside(relative, study_path):
            raise MutationInputError(
                f"Assay path {relative.as_posix()!r} must be inside its Study path "
                f"{study_path.as_posix()!r}."
            )
    elif study_path is not None:
        relative = study_path / "assays" / assay_id
    else:
        raise MutationInputError(
            f"Study {study_id!r} declares no path, so an Assay path must be given explicitly."
        )

    _reject_path_overlap(relative, data, "Assay", contained_by=study_path)
    _require_empty_directory(root, relative, "Assay")

    item = {
        "identifier": assay_id,
        "title": title,
        "description": description,
        "path": relative.as_posix(),
    }
    after = edit.append_item(text, ("studies", index, "assays"), item)

    assay_root = Path(*relative.parts)
    layout = {assay_root: (title, _assay_readme(parent))}
    layout.update(assay_folders(assay_root))
    directories, files = _scaffold_files(layout)

    replaced = ()
    container = assay_root.parent / "README.md"
    stale = readme_text(*NO_ASSAY_FOLDER)
    if (root / container).is_file():
        existing = (root / container).read_bytes().decode("utf-8").replace("\r\n", "\n")
        if existing == stale:
            replaced = (
                (container.as_posix(), stale, readme_text(*ASSAY_CONTAINER_FOLDER)),
            )

    return _finish(
        _plan(
            root,
            "assay.add",
            f"Added Assay {assay_id!r} to Study {study_id!r} at {relative.as_posix()}",
            assay_id,
            text,
            after,
            directories=directories,
            files=files,
            replaced=replaced,
        ),
        dry_run,
    )


def _inside(candidate: PurePosixPath, parent: PurePosixPath) -> bool:
    return candidate != parent and parent in candidate.parents


def _assay_readme(study: Mapping[str, Any]) -> str:
    title = study.get("title")
    if isinstance(title, str) and title.strip():
        return f"This directory represents an ISA **Assay** within **{title.strip()}**."
    return "This directory represents an ISA **Assay** within this Study."


def register_resource(
    workspace: Path | str,
    name: str,
    *,
    collection: str = "resources",
    kind: str | None = None,
    path: str | None = None,
    location: str | None = None,
    identifier: str | None = None,
    access: str | None = None,
    description: str | None = None,
    dry_run: bool = False,
) -> MutationResult:
    """Register a dataset, document or other resource, in place or elsewhere."""

    root, text, data = _open(workspace)
    name = _text(name, "Resource name")
    if collection not in RESOURCE_COLLECTIONS:
        allowed = ", ".join(RESOURCE_COLLECTIONS)
        raise MutationInputError(f"Resource collection must be one of: {allowed}.")

    kind = _optional_text(kind, "Resource type")
    location = _optional_text(location, "Resource location")
    identifier = _optional_text(identifier, "Resource identifier")
    description = _optional_text(description, "Resource description")
    access = _optional_text(access, "Resource access")
    if access is not None and access not in ACCESS_LEVELS:
        allowed = ", ".join(sorted(ACCESS_LEVELS))
        raise MutationInputError(f"Resource access must be one of: {allowed}.")

    relative = _workspace_relative(path, "Resource path") if path is not None else None
    if relative is None and location is None and identifier is None:
        raise MutationInputError(
            "A resource needs at least one of a workspace path, an external location, "
            "or a persistent identifier."
        )
    if relative is not None:
        target = root / Path(*relative.parts)
        try:
            assert_no_links(target)
        except UnsafePathError as exc:
            raise MutationInputError(str(exc)) from exc
        if not target.exists():
            raise MutationConflict(
                f"Resource path does not exist in the workspace: {relative.as_posix()}. "
                "Add the file or folder first, or record it as an external location."
            )

    existing = data.get(collection)
    if isinstance(existing, list):
        for item in existing:
            if isinstance(item, Mapping) and item.get("name") == name:
                raise MutationConflict(
                    f"{collection} already records a resource named {name!r}."
                )

    item = {
        "name": name,
        "type": kind,
        "path": relative.as_posix() if relative else None,
        "identifier": identifier,
        "location": location,
        "access": access,
        "description": description,
    }
    after = edit.append_item(text, (collection,), item)

    return _finish(
        _plan(
            root,
            f"{collection[:-1]}.add",
            f"Registered {collection[:-1]} {name!r}",
            name,
            text,
            after,
        ),
        dry_run,
    )


def add_contributor(
    workspace: Path | str,
    name: str,
    *,
    role: str | None = None,
    orcid: str | None = None,
    dry_run: bool = False,
) -> MutationResult:
    """Record a person who contributes to the Investigation."""

    root, text, data = _open(workspace)
    name = _text(name, "Contributor name")
    role = _optional_text(role, "Contributor role")
    orcid = _optional_text(orcid, "ORCID")
    if orcid is not None and not ORCID_RE.fullmatch(orcid):
        raise MutationInputError(
            "ORCID must look like 0000-0000-0000-0000 (final character may be X), "
            "optionally prefixed by https://orcid.org/."
        )

    contributors = data.get("contributors")
    if isinstance(contributors, list):
        for item in contributors:
            if not isinstance(item, Mapping):
                continue
            if isinstance(item.get("name"), str) and _same_person(item["name"], name):
                raise MutationConflict(f"A contributor named {name!r} is already recorded.")
            if orcid and _same_orcid(item.get("orcid"), orcid):
                raise MutationConflict(f"ORCID {orcid} is already recorded for this project.")

    item = {"name": name, "role": role, "orcid": orcid}
    after = edit.append_item(text, ("contributors",), item)

    return _finish(
        _plan(root, "contributor.add", f"Added contributor {name!r}", name, text, after),
        dry_run,
    )


def _same_person(left: str, right: str) -> bool:
    return " ".join(left.split()).casefold() == " ".join(right.split()).casefold()


def _same_orcid(existing: Any, orcid: str) -> bool:
    if not isinstance(existing, str):
        return False
    prefix = "https://orcid.org/"
    return existing.strip().removeprefix(prefix) == orcid.removeprefix(prefix)


def update_project_metadata(
    workspace: Path | str,
    *,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    keywords: Sequence[str] | None = None,
    dry_run: bool = False,
) -> MutationResult:
    """Update Investigation-level metadata, replacing only the fields given."""

    root, text, data = _open(workspace)
    title = _optional_text(title, "Investigation title")
    description = _optional_text(description, "Investigation description")
    status = _optional_text(status, "Investigation status")
    if status is not None and status not in STATUSES:
        raise MutationInputError(
            f"Investigation status must be one of: {', '.join(STATUSES)}."
        )
    if keywords is not None:
        keywords = _keywords(keywords)
    if title is None and description is None and status is None and keywords is None:
        raise MutationInputError("Give at least one metadata field to update.")

    investigation = data.get("investigation")
    if not isinstance(investigation, Mapping):
        raise MutationInputError("The project record has no investigation object.")

    changed: list[str] = []
    after = text
    for field, value in (
        ("title", title),
        ("description", description),
        ("status", status),
        ("keywords", list(keywords) if keywords is not None else None),
    ):
        if value is None:
            continue
        if investigation.get(field) == value:
            continue
        after = edit.set_value(after, ("investigation", field), value)
        changed.append(field)

    summary = (
        f"Updated Investigation {', '.join(changed)}" if changed else "No metadata changed"
    )
    return _finish(
        _plan(root, "metadata.set", summary, None, text, after),
        dry_run or not changed,
    )


def _keywords(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise MutationInputError("Keywords must be given as a sequence of strings.")
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        keyword = _text(raw, "Keyword")
        if keyword in seen:
            raise MutationInputError(f"Duplicate keyword: {keyword}.")
        seen.add(keyword)
        result.append(keyword)
    return tuple(result)
