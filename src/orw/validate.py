"""Minimal provider-neutral structural validation for ORW workspaces.

Full JSON-Schema/YAML validation is intentionally left for the dedicated
validation CLI milestone. This module establishes the core invariant that
scientific workspace validity does not depend on a forge such as GitHub.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]


def validate_workspace(destination: Path | str) -> ValidationReport:
    root = Path(destination)
    issues: list[ValidationIssue] = []

    project = root / ".research" / "project.yml"
    workspace = root / ".research" / "workspace.yml"
    marker = root / ".research" / "initialized"

    if not project.is_file():
        issues.append(
            ValidationIssue("missing_project", "Missing .research/project.yml.")
        )
    if not workspace.is_file():
        issues.append(
            ValidationIssue("missing_workspace", "Missing .research/workspace.yml.")
        )
    if not marker.is_file():
        issues.append(
            ValidationIssue("missing_initialized", "Missing .research/initialized.")
        )

    if project.is_file():
        text = project.read_text(encoding="utf-8")
        required_markers = {
            'spec_version: "0.1"': "missing_spec_version",
            "investigation:": "missing_investigation",
            "contributors:": "missing_contributors",
            "studies:": "missing_studies",
        }
        for needle, code in required_markers.items():
            if needle not in text:
                issues.append(
                    ValidationIssue(code, f"Canonical project record lacks {needle!r}.")
                )

        for raw_path in re.findall(
            r'^\s+path:\s+"([^"]+)"\s*$', text, re.MULTILINE
        ):
            target = root / Path(raw_path)
            if not target.exists():
                issues.append(
                    ValidationIssue(
                        "missing_declared_path",
                        f"Declared workspace path does not exist: {raw_path}",
                    )
                )

    if workspace.is_file():
        text = workspace.read_text(encoding="utf-8")
        if not re.search(r"^\s*initialized:\s*true\s*$", text, re.MULTILINE):
            issues.append(
                ValidationIssue(
                    "workspace_not_initialized",
                    ".research/workspace.yml does not record initialized: true.",
                )
            )

    if marker.is_file() and "initialized: true" not in marker.read_text(
        encoding="utf-8"
    ):
        issues.append(
            ValidationIssue(
                "invalid_initialized_marker",
                ".research/initialized does not contain initialized: true.",
            )
        )

    return ValidationReport(valid=not issues, issues=tuple(issues))
