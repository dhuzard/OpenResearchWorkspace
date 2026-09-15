"""Parse the GitHub Issue Form used to initialize an ORW workspace.

GitHub renders Issue Form fields into Markdown sections. This script reads the
issue body from the Actions event payload and exposes validated values as step
outputs for the trusted initializer.
"""

from __future__ import annotations

import json
import os
import re
import secrets
from pathlib import Path

EVENT_PATH = Path(os.environ["GITHUB_EVENT_PATH"])
OUTPUT_PATH = Path(os.environ["GITHUB_OUTPUT"])

payload = json.loads(EVENT_PATH.read_text(encoding="utf-8"))
body = payload.get("issue", {}).get("body") or ""

sections: dict[str, str] = {}
pattern = re.compile(r"^###\s+(.+?)\s*$\n(.*?)(?=^###\s+|\Z)", re.MULTILINE | re.DOTALL)
for heading, value in pattern.findall(body):
    sections[heading.strip()] = value.strip()

mapping = {
    "project_title": "Project title",
    "project_description": "Short project description",
    "researcher_name": "Your name",
    "study_title": "First study title",
    "assay_title": "What will you measure first?",
    "data_location": "Where are the authoritative/raw data stored?",
    "data_access": "Data access level",
    "keywords": "Keywords (optional)",
    "orcid": "Your ORCID (optional)",
}

required = {
    "project_title",
    "project_description",
    "researcher_name",
    "study_title",
    "assay_title",
    "data_location",
    "data_access",
}

values: dict[str, str] = {}
for key, heading in mapping.items():
    value = sections.get(heading, "").strip()
    if value in {"_No response_", "No response"}:
        value = ""
    if key in required and not value:
        raise SystemExit(f"Missing required setup field: {heading}")
    values[key] = value

allowed_access = {"private", "restricted", "embargoed", "open", "unknown"}
if values["data_access"] not in allowed_access:
    raise SystemExit(f"Unexpected data access level: {values['data_access']}")

# Write multiline-safe GitHub Actions outputs.
with OUTPUT_PATH.open("a", encoding="utf-8") as out:
    for key, value in values.items():
        delimiter = f"ORW_{secrets.token_hex(12)}"
        out.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")

print("Validated ORW setup form.")
