"""Initialize an ORW project from the beginner setup form.

Uses only Python's standard library so initialization has no package-install step.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def env(name: str, required: bool = True) -> str:
    value = os.environ.get(name, "").strip()
    if required and not value:
        raise SystemExit(f"Missing required initialization value: {name}")
    return value


def yaml_string(value: str) -> str:
    # JSON-style quoted strings are valid YAML scalars.
    import json
    return json.dumps(value, ensure_ascii=False)


def slug(value: str, fallback: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:60] or fallback


def validate_orcid(value: str) -> None:
    if not value:
        return
    normalized = value.removeprefix("https://orcid.org/")
    if not re.fullmatch(r"\d{4}-\d{4}-\d{4}-[\dX]{4}", normalized):
        raise SystemExit("ORCID must look like 0000-0000-0000-0000 (final character may be X).")


def ensure_readme(path: Path, title: str, text: str) -> None:
    directory = ROOT / path
    directory.mkdir(parents=True, exist_ok=True)
    readme = directory / "README.md"
    if not readme.exists():
        readme.write_text(f"# {title}\n\n{text}\n", encoding="utf-8")


project_title = env("PROJECT_TITLE")
description = env("PROJECT_DESCRIPTION")
creator_name = env("CREATOR_NAME")
study_title = env("STUDY_TITLE")
assay_title = env("ASSAY_TITLE")
data_location = env("DATA_LOCATION")
data_access = env("DATA_ACCESS")
keywords = [x.strip() for x in env("KEYWORDS", False).split(",") if x.strip()]
orcid = env("ORCID", False)
github_login = env("GITHUB_LOGIN", False)
validate_orcid(orcid)

study_slug = slug(study_title, "study-01")
assay_slug = slug(assay_title, "assay-01")
study_root = Path("studies") / study_slug
assay_root = study_root / "assays" / assay_slug

# Create the ISA-aligned tree. Each visible leaf gets a README because Git does
# not retain empty directories.
(ROOT / study_root).mkdir(parents=True, exist_ok=True)
(ROOT / assay_root).mkdir(parents=True, exist_ok=True)
(ROOT / ".research").mkdir(parents=True, exist_ok=True)

(ROOT / study_root / "README.md").write_text(
    f"# {study_title}\n\nThis directory represents an ISA **Study** within the Investigation **{project_title}**.\n",
    encoding="utf-8",
)
(ROOT / assay_root / "README.md").write_text(
    f"# {assay_title}\n\nThis directory represents an ISA **Assay** within **{study_title}**.\n",
    encoding="utf-8",
)

folders = {
    study_root / "data": ("Study data", "Study-level data and references to authoritative data locations."),
    study_root / "data" / "raw": ("Raw data", "Authoritative source data when appropriate to store them in GitHub. Do not silently overwrite raw evidence."),
    study_root / "data" / "processed": ("Processed data", "Data derived reproducibly from raw or external inputs."),
    study_root / "data" / "external": ("External data", "Links, identifiers, manifests, checksums, or access notes for data stored elsewhere."),
    study_root / "protocols": ("Protocols", "Study-level procedures, designs, and protocols."),
    study_root / "analysis": ("Study analysis", "Analyses that apply across assays or interpret the Study as a whole."),
    study_root / "results": ("Study results", "Study-level derived outputs and summaries."),
    assay_root / "data": ("Assay data", "Data belonging specifically to this measurement or assay."),
    assay_root / "data" / "raw": ("Raw assay data", "Authoritative source data for this assay when appropriate to store them here."),
    assay_root / "data" / "processed": ("Processed assay data", "Data derived reproducibly from this assay's raw or external inputs."),
    assay_root / "analysis": ("Assay analysis", "Analysis code, notebooks, and workflows specific to this assay."),
    assay_root / "results": ("Assay results", "Derived tables, figures, reports, and outputs specific to this assay."),
    Path("references"): ("References", "Literature, citation exports, and stable identifiers relevant to the Investigation."),
    Path("project-docs"): ("Project documentation", "Investigation-wide notes, decisions, rationale, history, and data-management context."),
}
for path, (title, text) in folders.items():
    ensure_readme(path, title, text)

kw_lines = "\n".join(f"    - {yaml_string(k)}" for k in keywords) if keywords else "    []"
orcid_line = f"\n    orcid: {yaml_string(orcid)}" if orcid else ""
github_line = f"\n    github_login: {yaml_string(github_login)}" if github_login else ""
project_yml = f'''spec_version: "0.1"

project:
  title: {yaml_string(project_title)}
  description: {yaml_string(description)}
  status: active
  keywords:
{kw_lines}

investigation:
  title: {yaml_string(project_title)}
  description: {yaml_string(description)}
  studies:
    - id: {yaml_string(study_slug)}
      title: {yaml_string(study_title)}
      path: {yaml_string(str(study_root))}
      assays:
        - id: {yaml_string(assay_slug)}
          title: {yaml_string(assay_title)}
          path: {yaml_string(str(assay_root))}

contributors:
  - name: {yaml_string(creator_name)}
    role: "Project creator"{orcid_line}{github_line}

data:
  - name: "Authoritative/raw research data"
    location: {yaml_string(data_location)}
    access: {yaml_string(data_access)}
    description: "Authoritative data location recorded during ORW initialization."

resources: []
outputs: []
related_identifiers: []
'''
(ROOT / ".research" / "project.yml").write_text(project_yml, encoding="utf-8")
(ROOT / ".research" / "initialized").write_text("initialized: true\n", encoding="utf-8")

readme = f'''# {project_title}

{description}

## Research structure

This workspace uses the ISA scientific hierarchy:

- **Investigation:** {project_title}
- **Study:** [{study_title}]({study_root.as_posix()}/)
- **Assay:** [{assay_title}]({assay_root.as_posix()}/)

## Project creator

{creator_name}

## Data

Authoritative/raw data location: **{data_location}**  
Access: **{data_access}**

## Where to work

Open the Study folder above. Put study-wide protocols and context at Study level; put measurement-specific data, analysis, and results inside the relevant Assay.

The machine-readable project description is maintained in `.research/project.yml`. You normally do not need to edit it directly.

## ORW help

- [Getting started](docs/getting-started.md)
- [Project structure](docs/project-structure.md)
- [Why ORW uses ISA](docs/isa.md)
'''
(ROOT / "README.md").write_text(readme, encoding="utf-8")
print(f"Initialized {project_title}: {study_slug} / {assay_slug}")
