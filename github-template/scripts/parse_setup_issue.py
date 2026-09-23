"""Parse the GitHub Issue Form into the provider-neutral ORW setup payload.

GitHub renders Issue Form fields into Markdown sections. This adapter reads the
issue body from the Actions event payload and emits one normalized JSON payload
consumed by the provider-neutral ORW core.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

EVENT_PATH = Path(os.environ["GITHUB_EVENT_PATH"])
OUTPUT_PATH = Path(os.environ["GITHUB_OUTPUT"])

payload = json.loads(EVENT_PATH.read_text(encoding="utf-8"))
body = payload.get("issue", {}).get("body") or ""

sections: dict[str, str] = {}
pattern = re.compile(r"^###\s+(.+?)\s*$\n(.*?)(?=^###\s+|\Z)", re.MULTILINE | re.DOTALL)
for heading, value in pattern.findall(body):
    sections[heading.strip()] = value.strip()


def read(heading: str, *, required: bool = False) -> str:
    value = sections.get(heading, "").strip()
    if value in {"_No response_", "No response"}:
        value = ""
    if required and not value:
        raise SystemExit(f"Missing required setup field: {heading}")
    return value


def choice(value: str, options: tuple[tuple[str, str], ...], label: str) -> str:
    for prefix, normalized in options:
        if value.startswith(prefix):
            return normalized
    raise SystemExit(f"Unsupported {label} choice: {value!r}")


project_title = read("Project title", required=True)
project_description = read("What is this project about?", required=True)
researcher_name = read("Your name", required=True)
orcid = read("Your ORCID (optional)")
study_structure = choice(
    read("How is this research organized?", required=True),
    (
        ("One Study", "single"),
        ("Several Studies", "multiple"),
        ("Not sure yet", "undecided"),
    ),
    "study structure",
)

study_title = read("First Study title (optional)")
if not study_title:
    study_title = (
        f"{project_title} — Study 1"
        if study_structure == "multiple"
        else project_title
    )

assay_structure = choice(
    read("Do your Studies contain several distinct measurement types?", required=True),
    (
        ("No", "single_or_none"),
        ("Yes", "multiple"),
        ("Not sure yet", "undecided"),
    ),
    "measurement structure",
)

protocol_storage = choice(
    read("Do you want to keep protocol documents in this workspace?", required=True),
    (
        ("Yes", "workspace"),
        ("No", "elsewhere"),
        ("Not sure yet", "undecided"),
    ),
    "protocol storage",
)

data_location = read("Where are the authoritative or raw data stored?", required=True)
data_access = read("Current data access", required=True)
keywords_raw = read("Keywords (optional)")
keywords = [item.strip() for item in keywords_raw.split(",") if item.strip()]

normalized = {
    "project_title": project_title,
    "project_description": project_description,
    "creator": {
        "name": researcher_name,
        "orcid": orcid or None,
    },
    "first_study": {
        "title": study_title,
    },
    # Beginner setup deliberately does not invent or request an Assay name.
    "first_assay": None,
    "data": {
        "location": data_location,
        "access": data_access,
    },
    "keywords": keywords,
    "workspace_options": {
        "study_structure": study_structure,
        "assay_structure": assay_structure,
        "protocol_storage": protocol_storage,
    },
}

# Compact JSON stays on one GITHUB_OUTPUT line; embedded newlines in user text
# are escaped by json.dumps and are reconstructed by the initializer.
serialized = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
with OUTPUT_PATH.open("a", encoding="utf-8") as out:
    out.write(f"setup_payload={serialized}\n")

print("Normalized ORW setup form.")
