#!/usr/bin/env python3
"""Build the GitHub template distribution from canonical ORW sources.

This is a maintainer tool. Scientific generation logic stays in \`\`src/orw\`\`.
The published \`\`OpenResearchWorkspace-template\`\` repository is generated output.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = REPO_ROOT / "github-template"
CORE_REVISION_TOKEN = "__ORW_CORE_REVISION__"

CANONICAL_RESEARCH_FILES = {
    "project.yml": REPO_ROOT / "src" / "orw" / "templates" / "project.yml",
    "workspace.yml": REPO_ROOT / "src" / "orw" / "templates" / "workspace.yml",
    "capabilities.yml": REPO_ROOT / "src" / "orw" / "templates" / "capabilities.yml",
    "layout.yml": REPO_ROOT / "src" / "orw" / "templates" / "layout.yml",
    "profiles.yml": REPO_ROOT / "src" / "orw" / "templates" / "profiles.yml",
}

REQUIRED_FILES = {
    "README.md",
    "GETTING_STARTED.md",
    ".github/ISSUE_TEMPLATE/orw-setup.yml",
    ".github/ISSUE_TEMPLATE/orw-add-study.yml",
    ".github/ISSUE_TEMPLATE/orw-add-assay.yml",
    ".github/ISSUE_TEMPLATE/orw-register-data.yml",
    ".github/ISSUE_TEMPLATE/orw-add-contributor.yml",
    ".github/ISSUE_TEMPLATE/orw-check-workspace.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/initialize-project.yml",
    ".github/workflows/project-actions.yml",
    "scripts/parse_setup_issue.py",
    "scripts/initialize_project.py",
    "scripts/handle_project_action.py",
    ".research/project.yml",
    ".research/workspace.yml",
    ".research/capabilities.yml",
    ".research/layout.yml",
    ".research/profiles.yml",
    ".research/template-source.yml",
}

FORBIDDEN_TOP_LEVEL = {
    "src",
    "tests",
    "browser",
    "schema",
    "docs",
    "dist",
    "build",
    "analysis",
    "data",
    "results",
    "protocols",
    "capabilities",
    "examples",
    "pyproject.toml",
    "MANIFEST.in",
    ".readthedocs.yaml",
    "LICENSE",
    "SPEC.md",
    "CHANGELOG.md",
    "REFERENCE_IMPLEMENTATION.md",
    "TEMPLATE_WORKFLOW.md",
    "PROJECT_STRUCTURE.md",
}


class TemplateBuildError(RuntimeError):
    """The template distribution could not be built safely."""


def _resolve_revision(explicit: str | None) -> str:
    revision = explicit or os.environ.get("GITHUB_SHA")
    if not revision:
        try:
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise TemplateBuildError(
                "Could not determine the canonical ORW commit. "
                "Pass --core-revision explicitly."
            ) from exc

    revision = revision.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise TemplateBuildError(
            f"Core revision must be a full 40-character Git SHA: {revision!r}"
        )
    return revision


def _extract_versions(workspace_text: str) -> tuple[str, str]:
    spec = re.search(
        r'^\s*spec_version:\s*"([^"]+)"\s*$',
        workspace_text,
        re.MULTILINE,
    )
    template = re.search(
        r'^\s*template_version:\s*"([^"]+)"\s*$',
        workspace_text,
        re.MULTILINE,
    )
    if not spec or not template:
        raise TemplateBuildError(
            "Canonical workspace template does not expose spec/template versions."
        )
    return spec.group(1), template.group(1)


def _safe_destination(destination: Path) -> Path:
    resolved = destination.expanduser().resolve()
    forbidden = {
        Path("/").resolve(),
        REPO_ROOT.resolve(),
        REPO_ROOT.parent.resolve(),
        ASSET_ROOT.resolve(),
    }
    if resolved in forbidden:
        raise TemplateBuildError(f"Unsafe template output destination: {resolved}")
    return resolved


def _copy_assets(destination: Path, revision: str) -> None:
    if not ASSET_ROOT.is_dir():
        raise TemplateBuildError(f"Missing template asset directory: {ASSET_ROOT}")

    for source in sorted(path for path in ASSET_ROOT.rglob("*") if path.is_file()):
        relative = source.relative_to(ASSET_ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8")

        if CORE_REVISION_TOKEN in content:
            if not relative.as_posix().startswith(".github/workflows/"):
                raise TemplateBuildError(
                    f"Core revision token is only allowed in generated workflows: {relative}"
                )
            content = content.replace(CORE_REVISION_TOKEN, revision)

        target.write_text(content, encoding="utf-8")


def _write_canonical_research_files(destination: Path, revision: str) -> None:
    research = destination / ".research"
    research.mkdir(parents=True, exist_ok=True)

    for name, source in CANONICAL_RESEARCH_FILES.items():
        if not source.is_file():
            raise TemplateBuildError(f"Missing canonical ORW template: {source}")
        shutil.copyfile(source, research / name)

    workspace_text = CANONICAL_RESEARCH_FILES["workspace.yml"].read_text(
        encoding="utf-8"
    )
    spec_version, template_version = _extract_versions(workspace_text)
    provenance = "\n".join(
        [
            "template:",
            "  adapter: github",
            '  template_repository: "dhuzard/OpenResearchWorkspace-template"',
            '  canonical_repository: "dhuzard/OpenResearchWorkspace"',
            f'  canonical_revision: "{revision}"',
            f'  spec_version: "{spec_version}"',
            f'  template_version: "{template_version}"',
            "",
            "notes:",
            '  - "Generated from the canonical ORW repository; do not maintain scientific rules here."',
            '  - "This file records the immutable core revision used by this template snapshot."',
            "",
        ]
    )
    (research / "template-source.yml").write_text(provenance, encoding="utf-8")


def _relative_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def validate_distribution(destination: Path, revision: str) -> None:
    files = _relative_files(destination)
    missing = sorted(REQUIRED_FILES - files)
    if missing:
        raise TemplateBuildError(
            "Generated template is missing required files: " + ", ".join(missing)
        )

    forbidden = sorted(
        path
        for path in files
        if path.split("/", 1)[0] in FORBIDDEN_TOP_LEVEL
    )
    if forbidden:
        raise TemplateBuildError(
            "Development files leaked into the researcher template: "
            + ", ".join(forbidden)
        )

    for name, source in CANONICAL_RESEARCH_FILES.items():
        generated = destination / ".research" / name
        if generated.read_bytes() != source.read_bytes():
            raise TemplateBuildError(
                f"Generated .research/{name} diverges from canonical source."
            )

    workflows = sorted((destination / ".github" / "workflows").glob("*.yml"))
    provenance = (destination / ".research" / "template-source.yml").read_text(
        encoding="utf-8"
    )
    for workflow_path in workflows:
        workflow = workflow_path.read_text(encoding="utf-8")
        if CORE_REVISION_TOKEN in workflow:
            raise TemplateBuildError(
                f"Unresolved core revision token in generated workflow: {workflow_path.name}"
            )
        if "ORW_CORE_REVISION" in workflow and revision not in workflow:
            raise TemplateBuildError(
                f"Generated workflow does not pin the requested core revision: {workflow_path.name}"
            )
    if revision not in provenance:
        raise TemplateBuildError(
            "Generated provenance does not pin the requested core revision."
        )


def build_template(
    destination: Path,
    *,
    core_revision: str | None = None,
    force: bool = False,
) -> Path:
    revision = _resolve_revision(core_revision)
    destination = _safe_destination(destination)

    if destination.exists():
        if any(destination.iterdir()):
            if not force:
                raise TemplateBuildError(
                    f"Output is not empty: {destination}. Pass --force to replace it."
                )
            shutil.rmtree(destination)
        else:
            destination.rmdir()

    destination.mkdir(parents=True)
    try:
        _copy_assets(destination, revision)
        _write_canonical_research_files(destination, revision)
        validate_distribution(destination, revision)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise

    return destination


def _tree_entries(root: Path) -> Iterable[tuple[str, bytes]]:
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if ".git" in path.relative_to(root).parts:
            continue
        yield path.relative_to(root).as_posix(), path.read_bytes()


def compare_trees(generated: Path, published: Path) -> list[str]:
    generated_entries = dict(_tree_entries(generated))
    published_entries = dict(_tree_entries(published))
    paths = sorted(set(generated_entries) | set(published_entries))
    return [
        path
        for path in paths
        if generated_entries.get(path) != published_entries.get(path)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the minimal GitHub ORW template from canonical sources."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "dist" / "github-template",
        help="Destination directory (default: dist/github-template).",
    )
    parser.add_argument(
        "--core-revision",
        help="Full canonical ORW Git SHA to pin. Defaults to GITHUB_SHA or HEAD.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing non-empty output directory.",
    )
    parser.add_argument(
        "--check-against",
        type=Path,
        help="Optional existing template checkout; fail if generated files differ.",
    )
    args = parser.parse_args()

    try:
        destination = build_template(
            args.output,
            core_revision=args.core_revision,
            force=args.force,
        )
        if args.check_against:
            differences = compare_trees(destination, args.check_against.resolve())
            if differences:
                print(
                    "Generated template differs from published checkout:",
                    file=sys.stderr,
                )
                for path in differences:
                    print(f"  - {path}", file=sys.stderr)
                return 1
    except TemplateBuildError as exc:
        print(f"Template build refused: {exc}", file=sys.stderr)
        return 2

    print(f"Generated GitHub template: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
