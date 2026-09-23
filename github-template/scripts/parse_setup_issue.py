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

# The current GitHub form still asks for an initial Assay. The ORW core itself
# allows first_assay=null so future CLI/browser interfaces can represent
# projects for which an Assay is not scientifically applicable.
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

keywords = [item.strip() for item in values["keywords"].split(",") if item.strip()]

normalized = {
    "project_title": values["project_title"],
    "project_description": values["project_description"],
    "creator": {
        "name": values["researcher_name"],
        "orcid": values["orcid"] or None,
    },
    "first_study": {
        "title": values["study_title"],
    },
    "first_assay": {
        "title": values["assay_title"],
    },
    "data": {
        "location": values["data_location"],
        "access": values["data_access"],
    },
    "keywords": keywords,
}

# Compact JSON stays on one GITHUB_OUTPUT line; embedded newlines in user text
# are escaped by json.dumps and are reconstructed by the initializer.
serialized = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
with OUTPUT_PATH.open("a", encoding="utf-8") as out:
    out.write(f"setup_payload={serialized}\n")

print("Normalized ORW setup form.")
