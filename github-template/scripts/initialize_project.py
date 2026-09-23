"""Thin GitHub adapter for the canonical ORW initializer.

The scientific scaffold and validation rules live in the OpenResearchWorkspace
package pinned by the GitHub workflow. This repository intentionally contains
no independent ORW generation implementation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from orw import (
    ImplementationContext,
    SetupConfig,
    SetupValidationError,
    WorkspaceAlreadyInitialized,
    initialize_template,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    try:
        config = SetupConfig.from_mapping(
            json.loads(os.environ.get("ORW_SETUP_JSON", ""))
        )
        context = ImplementationContext(
            provider="github",
            provider_user=os.environ.get("ORW_PROVIDER_USER") or None,
        )
        result = initialize_template(config, root, implementation=context)
    except (
        json.JSONDecodeError,
        SetupValidationError,
        WorkspaceAlreadyInitialized,
        OSError,
    ) as exc:
        raise SystemExit(f"Initialization refused: {exc}") from exc

    print(
        f"Initialized {config.project_title}: "
        f"{result.study_identifier} / {result.assay_identifier or 'no-assay'}"
    )


if __name__ == "__main__":
    main()
