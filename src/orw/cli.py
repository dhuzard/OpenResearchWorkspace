"""Command-line interface for OpenResearchWorkspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from . import __version__
from .initialize import WorkspaceAlreadyInitialized, create_workspace
from .model import ACCESS_LEVELS, SetupConfig, SetupValidationError
from .validate import validate_workspace

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_INPUT = 2
EXIT_ALREADY_INITIALIZED = 3


def _nonempty(prompt: str) -> str:
    while True:
        try:
            value = input(prompt).strip()
        except EOFError as exc:
            raise SetupValidationError(
                "Interactive input is unavailable. Use --config FILE (or --config - for stdin)."
            ) from exc
        if value:
            return value
        print("A value is required.", file=sys.stderr)


def _optional(prompt: str) -> str | None:
    try:
        value = input(prompt).strip()
    except EOFError as exc:
        raise SetupValidationError(
            "Interactive input is unavailable. Use --config FILE (or --config - for stdin)."
        ) from exc
    return value or None


def _prompt_access() -> str:
    choices = ("private", "restricted", "embargoed", "open", "unknown")
    while True:
        value = _optional(
            "Data access [private/restricted/embargoed/open/unknown] (private): "
        )
        access = value or "private"
        if access in ACCESS_LEVELS:
            return access
        print(
            f"Choose one of: {', '.join(choices)}.",
            file=sys.stderr,
        )


def _interactive_payload() -> dict[str, Any]:
    assay = _optional(
        "First measurement/assay (optional; leave blank if not applicable): "
    )
    keywords_text = _optional("Keywords (comma-separated, optional): ")
    keywords = (
        [item.strip() for item in keywords_text.split(",") if item.strip()]
        if keywords_text
        else []
    )

    return {
        "project_title": _nonempty("Project title: "),
        "project_description": _nonempty("Short description: "),
        "creator": {
            "name": _nonempty("Your name: "),
            "orcid": _optional("ORCID (optional): "),
        },
        "first_study": {
            "title": _nonempty("First study title: "),
        },
        "first_assay": {"title": assay} if assay else None,
        "data": {
            "location": _nonempty("Authoritative data location: "),
            "access": _prompt_access(),
        },
        "keywords": keywords,
    }


def _load_config(source: str) -> dict[str, Any]:
    try:
        if source == "-":
            text = sys.stdin.read()
            label = "stdin"
        else:
            path = Path(source)
            text = path.read_text(encoding="utf-8")
            label = str(path)
    except OSError as exc:
        raise SetupValidationError(f"Could not read setup config {source!r}: {exc}") from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SetupValidationError(
            f"Setup config {label} is not valid JSON: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})."
        ) from exc

    if not isinstance(payload, dict):
        raise SetupValidationError("Setup config must contain one JSON object.")
    return payload


def _cmd_init(args: argparse.Namespace) -> int:
    try:
        payload = _load_config(args.config) if args.config else _interactive_payload()
        config = SetupConfig.from_mapping(payload)
        result = create_workspace(config, args.destination)
    except SetupValidationError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return EXIT_INPUT
    except WorkspaceAlreadyInitialized as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_ALREADY_INITIALIZED
    except OSError as exc:
        print(f"Could not create workspace: {exc}", file=sys.stderr)
        return EXIT_INPUT

    print(f"Created ORW workspace: {result.destination}")
    print(f"Investigation: {result.project_identifier}")
    print(f"Study: {result.study_identifier}")
    if result.assay_identifier:
        print(f"Assay: {result.assay_identifier}")
    else:
        print("Assay: none initialized")
    return EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    report = validate_workspace(args.destination)
    root = str(Path(args.destination).resolve())

    if args.json:
        print(
            json.dumps(
                {
                    "valid": report.valid,
                    "workspace": root,
                    "issues": [
                        {
                            "code": issue.code,
                            "message": issue.message,
                            **({"path": issue.path} if issue.path else {}),
                        }
                        for issue in report.issues
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif report.valid:
        print(f"Valid ORW workspace: {root}")
    else:
        print(f"Invalid ORW workspace: {root}", file=sys.stderr)
        for issue in report.issues:
            location = f" ({issue.path})" if issue.path else ""
            print(
                f"- [{issue.code}]{location} {issue.message}",
                file=sys.stderr,
            )

    return EXIT_OK if report.valid else EXIT_INVALID


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orw",
        description=(
            "Create and validate portable OpenResearchWorkspace projects "
            "without requiring a hosted forge."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Create a new research workspace.",
        description=(
            "Create a new ORW research workspace interactively or from a "
            "normalized JSON setup file."
        ),
    )
    init_parser.add_argument(
        "destination",
        help="Folder to create or initialize.",
    )
    init_parser.add_argument(
        "--config",
        metavar="FILE",
        help=(
            "Read normalized setup JSON from FILE. Use '-' to read JSON from stdin. "
            "Without --config, ORW asks the setup questions interactively."
        ),
    )
    init_parser.set_defaults(func=_cmd_init)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an existing research workspace.",
        description=(
            "Validate canonical ORW metadata, declared workspace paths, and "
            "initialization state."
        ),
    )
    validate_parser.add_argument(
        "destination",
        nargs="?",
        default=".",
        help="Workspace folder to validate (default: current folder).",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON validation report.",
    )
    validate_parser.set_defaults(func=_cmd_validate)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
