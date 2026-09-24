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


LEGACY_TEMPLATE_PLACEHOLDERS: dict[str, tuple[bytes, ...]] = {
    "workspace.yml": (
        b'orw:\n'
        b'  spec_version: "0.1"\n'
        b'  template_version: "0.1.0"\n'
        b'  initialized: false\n'
        b'  initialized_at: null\n'
        b'\n'
        b'implementation:\n'
        b'  primary_reference: github-template\n'
        b'  canonical_project_record: ".research/project.yml"\n'
        b'  capabilities_record: ".research/capabilities.yml"\n'
    ),
}


def _recognized_template_placeholder(name: str, actual: bytes, expected: bytes) -> bool:
    """Accept current placeholders plus exact historical self-initializing templates."""

    if actual == expected:
        return True
    return actual in LEGACY_TEMPLATE_PLACEHOLDERS.get(name, ())

LEGACY_DEVELOPMENT_MARKERS = (
    "pyproject.toml",
    "src/orw",
    "tests",
    ".github/workflows/release-checks.yml",
    ".github/workflows/test-core.yml",
    ".github/workflows/test-browser.yml",
    ".github/workflows/release-alpha.yml",
)


def _legacy_development_artifacts(root: Path) -> tuple[str, ...]:
    """Detect the pre-split development repository when used as a project template."""

    return tuple(marker for marker in LEGACY_DEVELOPMENT_MARKERS if (root / marker).exists())


def _write_legacy_template_notice(stage: Path, artifacts: tuple[str, ...]) -> None:
    if not artifacts:
        return
    notice = [
        "# Legacy ORW template migration notice",
        "",
        "This research repository was created from the old combined ORW development/template repository.",
        "Initialization preserved potentially user-edited legacy files instead of deleting them automatically.",
        "",
        "Detected legacy development artifacts:",
        "",
    ]
    notice.extend(f"- `{item}`" for item in artifacts)
    notice.extend(
        [
            "",
            "## What to review",
            "",
            "- Old ORW development workflows such as `release-checks.yml`, `test-core.yml`, and `test-browser.yml` may run on pushes and are not needed for a research project.",
            "- Development folders such as `src/`, `tests/`, `browser/`, `docs/`, and package files are not part of the researcher-facing ORW workspace.",
            "- A copied root `LICENSE` is the license of ORW software; it does **not** automatically define the license of your research data, documentation, or project outputs.",
            "- Old root-level `data/`, `analysis/`, `results/`, or `protocols/` folders may coexist with the new Study structure. Prefer the Study folders created by ORW unless you intentionally migrate content.",
            "",
            "Review and remove legacy development artifacts only after confirming they contain no project-specific edits.",
            "",
        ]
    )
    (stage / ".research" / "legacy-template-notice.md").write_text(
        "\n".join(notice), encoding="utf-8"
    )
    readme = stage / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n## Legacy template detected\n\n"
        + "This repository was created from the old combined ORW development/template repository. "
        + "Review [`.research/legacy-template-notice.md`](.research/legacy-template-notice.md) "
        + "for inherited development files and workflows that may be safe to remove.\n",
        encoding="utf-8",
    )

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


def _install_new_files(
    stage: Path,
    root: Path,
    *,
    replaceable: dict[str, bytes] | None = None,
    preserve_existing: set[str] | None = None,
) -> None:
    """Install staged files without overwriting unrecognized existing content.

    replaceable is reserved for exact template placeholders whose original
    bytes were verified before initialization. preserve_existing names
    human-facing files that are allowed to pre-exist and are deliberately left
    untouched; this supports older ORW template snapshots without weakening the
    safety boundary around machine-readable metadata or scientific paths.
    """
    replaceable = replaceable or {}
    preserve_existing = preserve_existing or set()
    staged = sorted(p for p in stage.rglob("*") if p.is_file())
    for source in staged:
        rel = source.relative_to(stage).as_posix()
        target = root / rel
        assert_no_links(target)
        if target.exists() and rel in preserve_existing:
            continue
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
            if target.exists() and rel in preserve_existing:
                continue
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
        if not _recognized_template_placeholder(name, actual, expected):
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
    legacy_artifacts = _legacy_development_artifacts(root)
    with tempfile.TemporaryDirectory(prefix="orw-template-") as temporary:
        stage = Path(temporary) / "workspace"
        result = _scaffold.create_workspace(config, stage, implementation=implementation)
        _write_legacy_template_notice(stage, legacy_artifacts)
        for source, backup in backups.items():
            (stage / backup).write_bytes(original[source])
        _install_new_files(
            stage,
            root,
            replaceable=original,
            preserve_existing={
                "project-docs/README.md",
                "references/README.md",
            },
        )
    return replace(result, destination=root)
