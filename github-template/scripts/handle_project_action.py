"""Handle post-initialization GitHub Issue Forms through the canonical ORW core."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

import yaml

from orw import (
    MutationConflict,
    MutationInputError,
    WorkspaceNotValid,
    add_assay,
    add_contributor,
    add_study,
    register_resource,
    validate_workspace,
)

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
EVENT_PATH = Path(os.environ["GITHUB_EVENT_PATH"])
OUTPUT_PATH = Path(os.environ["GITHUB_OUTPUT"])
RESPONSE_PATH = Path(os.environ.get("ORW_RESPONSE_PATH", "/tmp/orw-action-response.md"))


def sections(body: str) -> dict[str, str]:
    result: dict[str, str] = {}
    pattern = re.compile(
        r"^###\s+(.+?)\s*$\n(.*?)(?=^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for heading, value in pattern.findall(body):
        value = value.strip()
        if value in {"_No response_", "No response"}:
            value = ""
        result[heading.strip()] = value
    return result


def read(values: dict[str, str], heading: str, *, required: bool = False) -> str:
    value = values.get(heading, "").strip()
    if required and not value:
        raise MutationInputError(f"Missing required form field: {heading}.")
    return value


def resolve_study(query: str) -> str:
    record = yaml.safe_load((ROOT / ".research" / "project.yml").read_text(encoding="utf-8"))
    studies = record.get("studies", []) if isinstance(record, dict) else []
    needle = " ".join(query.split()).casefold()
    matches: list[str] = []
    available: list[str] = []
    for study in studies:
        if not isinstance(study, dict):
            continue
        identifier = study.get("identifier")
        title = study.get("title")
        if isinstance(identifier, str):
            available.append(identifier)
        for value in (identifier, title):
            if isinstance(value, str) and " ".join(value.split()).casefold() == needle:
                if isinstance(identifier, str):
                    matches.append(identifier)
                break
    matches = list(dict.fromkeys(matches))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise MutationInputError(
            f"Study name {query!r} is ambiguous. Use the folder/identifier instead."
        )
    known = ", ".join(available) or "none"
    raise MutationInputError(
        f"No Study matched {query!r}. Current Study identifiers: {known}."
    )


def write_outputs(*, changed: bool, ok: bool) -> None:
    with OUTPUT_PATH.open("a", encoding="utf-8") as stream:
        stream.write(f"changed={'true' if changed else 'false'}\n")
        stream.write(f"ok={'true' if ok else 'false'}\n")


def write_response(text: str) -> None:
    RESPONSE_PATH.write_text(text.rstrip() + "\n", encoding="utf-8")


def result_message(title: str, summary: str, extra: str = "") -> None:
    body = f"✅ **{title}**\n\n{summary}"
    if extra:
        body += f"\n\n{extra}"
    body += (
        "\n\nThe change was applied through the canonical ORW core and the resulting "
        "workspace was validated before it was kept."
    )
    write_response(body)


def main() -> int:
    event = json.loads(EVENT_PATH.read_text(encoding="utf-8"))
    issue = event.get("issue") or {}
    title = issue.get("title") or ""
    values = sections(issue.get("body") or "")

    try:
        if title.startswith("[ORW Add Study]"):
            study_title = read(values, "New Study title", required=True)
            description = read(values, "Short Study description (optional)") or None
            result = add_study(ROOT, study_title, description=description)
            identifier = result.plan.identifier or ""
            study_url = (
                f"https://github.com/{REPOSITORY}/tree/main/studies/{identifier}"
                if REPOSITORY
                else f"studies/{identifier}/"
            )
            result_message(
                "Study added",
                result.plan.summary + ".",
                f"Open the new Study: [`studies/{identifier}/`]({study_url})",
            )
            write_outputs(changed=True, ok=True)
            return 0

        if title.startswith("[ORW Add Assay]"):
            study_query = read(values, "Which Study?", required=True)
            study_id = resolve_study(study_query)
            assay_title = read(values, "Measurement / Assay name", required=True)
            description = read(values, "Short description (optional)") or None
            result = add_assay(
                ROOT,
                study_id,
                assay_title,
                description=description,
            )
            identifier = result.plan.identifier or ""
            assay_path = f"studies/{study_id}/assays/{identifier}/"
            assay_url = (
                f"https://github.com/{REPOSITORY}/tree/main/{assay_path.rstrip('/')}"
                if REPOSITORY
                else assay_path
            )
            result_message(
                "Measurement / Assay added",
                result.plan.summary + ".",
                f"Open it under [`{assay_path}`]({assay_url})",
            )
            write_outputs(changed=True, ok=True)
            return 0

        if title.startswith("[ORW Register Data]"):
            name = read(values, "Data source name", required=True)
            location = read(values, "Where are these data stored?", required=True)
            access = read(values, "Current data access", required=True)
            identifier = read(values, "Persistent identifier or public URL (optional)") or None
            description = read(values, "Short description (optional)") or None
            result = register_resource(
                ROOT,
                name,
                kind="dataset",
                location=location,
                identifier=identifier,
                access=access,
                description=description,
            )
            result_message(
                "Data source registered",
                result.plan.summary + ".",
                "The data themselves were not copied or uploaded.",
            )
            write_outputs(changed=True, ok=True)
            return 0

        if title.startswith("[ORW Add Contributor]"):
            name = read(values, "Contributor name", required=True)
            role = read(values, "Role (optional)") or None
            orcid = read(values, "ORCID (optional)") or None
            affiliation = read(values, "Affiliation (optional)") or None
            result = add_contributor(
                ROOT,
                name,
                role=role,
                orcid=orcid,
                affiliation=affiliation,
            )
            result_message("Contributor added", result.plan.summary + ".")
            write_outputs(changed=True, ok=True)
            return 0

        if title.startswith("[ORW Check]"):
            report = validate_workspace(ROOT)
            if report.valid:
                write_response(
                    "✅ **Workspace check passed**\n\n"
                    "The ORW project record, declared paths, and initialization state are valid."
                )
                write_outputs(changed=False, ok=True)
            else:
                lines = ["⚠️ **Workspace check found problems**", ""]
                for issue in report.issues:
                    location = f" — `{issue.path}`" if issue.path else ""
                    lines.append(f"- **{issue.code}**{location}: {issue.message}")
                lines.extend(
                    [
                        "",
                        "No files were changed. Keep this issue open while the problems are corrected.",
                    ]
                )
                write_response("\n".join(lines))
                write_outputs(changed=False, ok=False)
            return 0

        raise MutationInputError("This issue is not a recognized ORW no-code action.")

    except (MutationInputError, MutationConflict, WorkspaceNotValid, OSError, yaml.YAMLError) as exc:
        write_response(
            "❌ **ORW could not apply this request.**\n\n"
            f"{exc}\n\n"
            "No intended scientific change was kept. Review the form values or ask for help."
        )
        write_outputs(changed=False, ok=False)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
