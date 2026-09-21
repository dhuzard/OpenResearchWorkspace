"""GitHub adapter for provider-neutral ORW workspace initialization.

Scientific workspace generation lives in src/orw/. This script only translates
GitHub Actions environment input into the core API.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orw.initialize import (  # noqa: E402
    ImplementationContext,
    WorkspaceAlreadyInitialized,
    create_workspace,
)
from orw.model import SetupConfig, SetupValidationError  # noqa: E402


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required initialization value: {name}")
    return value


try:
    raw_payload = json.loads(required_env("ORW_SETUP_JSON"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"ORW_SETUP_JSON is not valid JSON: {exc}") from exc

try:
    config = SetupConfig.from_mapping(raw_payload)
except SetupValidationError as exc:
    raise SystemExit(f"Invalid ORW setup payload: {exc}") from exc

context = ImplementationContext(
    provider=os.environ.get("ORW_PROVIDER", "").strip() or None,
    provider_user=os.environ.get("ORW_PROVIDER_USER", "").strip() or None,
)

destination = Path(os.environ.get("ORW_DESTINATION", str(ROOT)))

try:
    result = create_workspace(
        config,
        destination,
        implementation=context,
    )
except WorkspaceAlreadyInitialized as exc:
    raise SystemExit(str(exc)) from exc

assay = result.assay_identifier or "no-assay"
print(
    f"Initialized {config.project_title}: "
    f"{result.study_identifier} / {assay}"
)
