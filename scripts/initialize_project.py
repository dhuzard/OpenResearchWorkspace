"""Initialize an ORW project from GitHub Actions form inputs.

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


project_title = env("PROJECT_TITLE")
description = env("PROJECT_DESCRIPTION")
study_title = env("STUDY_TITLE")
assay_title = env("ASSAY_TITLE")
data_location = env("DATA_LOCATION")
data_access = env("DATA_ACCESS")
keywords = [x.strip() for x in env("KEYWORDS", False).split(",") if x.strip()]
orcid = env("ORCID", False)
actor = env("ACTOR")
validate_orcid(orcid)

study_slug = slug(study_title, "study-01")
assay_slug = slug(assay_title, "assay-01")
study_root = Path("studies") / study_slug
assay_root = study_root / "assays" / assay_slug

for path in [
    study_root / "data" / "raw",
    study_root / "data" / "processed",
    study_root / "data" / "external",
    study_root / "protocols",
    study_root / "analysis",
    study_root / "results",
    assay_root / "data" / "raw",
    assay_root / "data" / "processed",
    assay_root / "analysis",
    assay_root / "results",
    Path("references"),
    Path("project-docs"),
    Path(".research"),
]:
    (ROOT / path).mkdir(parents=True, exist_ok=True)

# Git does not retain empty directories, so add small explanatory READMEs.
(ROOT / study_root / "README.md").write_text(
    f"# {study_title}\n\nThis directory represents an ISA **Study** within the investigation **{project_title}**.\n",
    encoding="utf-8",
)
(ROOT / assay_root / "README.md").write_text(
    f"# {assay_title}\n\nThis directory represents an ISA **Assay** within **{study_title}**.\n",
    encoding="utf-8",
)
for path in [study_root / "data", study_root / "protocols", study_root / "analysis", study_root / "results",
             assay_root / "data", assay_root / "analysis", assay_root / "results", Path("references"), Path("project-docs")]:
    p = ROOT / path / "README.md"
    if not p.exists():
        p.write_text(f"# {path.name.replace('-', ' ').title()}\n\nAdd or document project material belonging to this area here.\n", encoding="utf-8")

kw_lines = "\n".join(f"    - {yaml_string(k)}" for k in keywords) if keywords else "    []"
orcid_line = f"\n    orcid: {yaml_string(orcid)}" if orcid else ""
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
  - name: {yaml_string(actor)}
    role: "Project creator"{orcid_line}

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

## Data

Authoritative/raw data location: **{data_location}**  
Access: **{data_access}**

## Where to work

Open the Study folder above. Put study-wide protocols and context at Study level; put measurement-specific data, analysis and results inside the relevant Assay.

The machine-readable project description is maintained in `.research/project.yml`. You normally do not need to edit it directly.
'''
(ROOT / "README.md").write_text(readme, encoding="utf-8")
print(f"Initialized {project_title}: {study_slug} / {assay_slug}")
