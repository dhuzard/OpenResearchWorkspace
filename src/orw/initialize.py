"""Safe public initialization boundary around the unchanged scientific scaffold.

The internal renderer only writes into a fresh staging directory. Normal CLI/API
initialization never overwrites existing content. The optional GitHub template
adapter has a separate, narrowly checked entry point with preserved originals.
"""
from __future__ import annotations

from dataclasses import replace
from importlib.resources import files
import os
from pathlib import Path
import shutil
import tempfile

from . import _scaffold
from ._scaffold import (
    ImplementationContext, WorkspaceAlreadyInitialized, WorkspaceResult,
    SPEC_VERSION, TEMPLATE_VERSION, slug, yaml_string,
)
from .fs_safety import absolute_path, assert_no_links, UnsafePathError
from .model import SetupConfig, SetupValidationError


class WorkspaceConflict(SetupValidationError):
    """Initialization refused without modifying existing workspace content."""


def _preflight(destination: Path | str) -> Path:
    root = absolute_path(destination)
    try:
        assert_no_links(root)
        if root.exists() and not root.is_dir():
            raise WorkspaceConflict(f"Destination is not a directory: {root}")
        if _scaffold._is_initialized(root):
            raise WorkspaceAlreadyInitialized(f"Workspace is already initialized: {root}")
    except UnsafePathError as exc:
        raise WorkspaceConflict(str(exc)) from exc
    return root


def _config(config: SetupConfig) -> SetupConfig:
    if not isinstance(config, SetupConfig):
        raise SetupValidationError("config must be a SetupConfig.")
    # Frozen dataclasses can still be constructed directly; validate before writes.
    return SetupConfig.from_mapping(config.to_mapping())


def _install_new_files(stage: Path, root: Path, *, replaceable: dict[str, bytes] | None = None) -> None:
    """Exclusive-create new files; template replacements have preserved originals."""
    replaceable = replaceable or {}
    staged = sorted(p for p in stage.rglob("*") if p.is_file())
    for source in staged:
        rel = source.relative_to(stage).as_posix()
        target = root / rel
        assert_no_links(target)
        if target.exists() and rel not in replaceable:
            raise WorkspaceConflict(f"Refusing to overwrite existing file: {target}")
        if rel in replaceable and target.read_bytes() != replaceable[rel]:
            raise WorkspaceConflict(f"Template changed during initialization: {target}")
    created: list[Path] = []
    changed: list[Path] = []
    try:
        for source in staged:
            rel = source.relative_to(stage).as_posix()
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            assert_no_links(target)
            if rel in replaceable:
                if target.read_bytes() != replaceable[rel]:
                    raise WorkspaceConflict(f"Template changed during initialization: {target}")
                # Write a sibling first, then replace only a verified placeholder.
                descriptor, temporary = tempfile.mkstemp(prefix=".orw-init-", dir=target.parent)
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(source.read_bytes())
                    os.replace(temporary, target)
                    changed.append(target)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
            else:
                with target.open("xb") as stream:
                    created.append(target)
                    stream.write(source.read_bytes())
    except Exception:
        # Restore originals on ordinary I/O failure. Exclusive workspace access
        # is required; do not use this as a concurrent filesystem transaction.
        for target in reversed(changed):
            target.write_bytes(replaceable[target.relative_to(root).as_posix()])
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise


def create_workspace(config: SetupConfig, destination: Path | str, *,
                     implementation: ImplementationContext | None = None) -> WorkspaceResult:
    config = _config(config)
    root = _preflight(destination)
    if root.exists() and any(root.iterdir()):
        raise WorkspaceConflict(
            f"Destination must be empty: {root}. Choose a new directory; existing files were not modified."
        )
    with tempfile.TemporaryDirectory(prefix="orw-initialize-") as temporary:
        stage = Path(temporary) / "workspace"
        result = _scaffold.create_workspace(config, stage, implementation=implementation)
        root.parent.mkdir(parents=True, exist_ok=True)
        assert_no_links(root)
        if root.exists():
            if any(root.iterdir()):
                raise WorkspaceConflict(f"Destination is no longer empty: {root}")
        else:
            root.mkdir()  # Exclusive creation rejects an intervening destination.
        _install_new_files(stage, root)
    return replace(result, destination=root)


def initialize_template(config: SetupConfig, destination: Path | str, *,
                        implementation: ImplementationContext | None = None) -> WorkspaceResult:
    """Initialize a recognized ORW template; preserve overview and placeholders.

Not exposed as a general CLI --force flag. The setup-form adapter invokes it
only for its explicit template initialization request. Edited scientific
metadata fail the exact-byte check rather than being overwritten.
"""
    config = _config(config)
    root = _preflight(destination)
    original: dict[str, bytes] = {}
    for name in ("project.yml", "workspace.yml"):
        relative = f".research/{name}"
        target = root / relative
        try:
            assert_no_links(target)
            expected = files("orw").joinpath("templates", name).read_bytes()
            actual = target.read_bytes()
        except (OSError, UnsafePathError) as exc:
            raise WorkspaceConflict(f"Not a recognized ORW template: {target}") from exc
        if actual != expected:
            raise WorkspaceConflict(f"Template metadata are edited or unrecognized: {target}")
        original[relative] = actual
    overview = root / "README.md"
    assert_no_links(overview)
    if not overview.is_file():
        raise WorkspaceConflict("Recognized templates require an existing README.md.")
    original["README.md"] = overview.read_bytes()
    backups = {
        "README.md": ".research/template-readme.md",
        ".research/project.yml": ".research/template-project.yml",
        ".research/workspace.yml": ".research/template-workspace.yml",
    }
    for backup in backups.values():
        if (root / backup).exists():
            raise WorkspaceConflict(f"Template backup already exists: {backup}")
    with tempfile.TemporaryDirectory(prefix="orw-template-") as temporary:
        stage = Path(temporary) / "workspace"
        result = _scaffold.create_workspace(config, stage, implementation=implementation)
        for source, backup in backups.items():
            (stage / backup).write_bytes(original[source])
        _install_new_files(stage, root, replaceable=original)
    return replace(result, destination=root)
