"""GitHub setup-form adapter; scientific generation stays in the ORW core."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orw import (ImplementationContext, SetupConfig, SetupValidationError,
                 WorkspaceAlreadyInitialized, create_workspace, initialize_template)


def main() -> None:
    try:
        config = SetupConfig.from_mapping(json.loads(os.environ.get("ORW_SETUP_JSON", "")))
        destination = Path(os.environ.get("ORW_DESTINATION", str(ROOT)))
        context = ImplementationContext(provider=os.environ.get("ORW_PROVIDER") or None,
                                        provider_user=os.environ.get("ORW_PROVIDER_USER") or None)
        # Only the explicit setup-form path on a template checkout takes this route.
        # Custom destinations (including adapter tests) use ordinary safe init.
        if destination.absolute() == ROOT and context.provider == "github":
            result = initialize_template(config, destination, implementation=context)
            print("Previous template overview and placeholder metadata preserved in .research/template-*.")
        else:
            result = create_workspace(config, destination, implementation=context)
    except (json.JSONDecodeError, SetupValidationError, WorkspaceAlreadyInitialized, OSError) as exc:
        raise SystemExit(f"Initialization refused: {exc}") from exc
    print(f"Initialized {config.project_title}: {result.study_identifier} / {result.assay_identifier or 'no-assay'}")


if __name__ == "__main__":
    main()
