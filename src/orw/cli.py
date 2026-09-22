"""Command-line interface for OpenResearchWorkspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from . import __version__
from .edit import YamlEditError
from .export.rocrate import ROCrateExportError, export_rocrate
from .initialize import WorkspaceAlreadyInitialized, create_workspace
from .model import ACCESS_LEVELS, SetupConfig, SetupValidationError
from .mutate import (
    MutationConflict, MutationInputError, MutationResult, RESOURCE_COLLECTIONS,
    STATUSES, WorkspaceNotValid, add_assay, add_contributor, add_study,
    register_resource, update_project_metadata,
)
from .validate import validate_workspace

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_INPUT = 2
EXIT_ALREADY_INITIALIZED = 3
EXIT_EXPORT = 4
EXIT_CONFLICT = 5


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
    project_title = _nonempty("Project title: ")
    project_description = _nonempty("Short description: ")
    creator_name = _nonempty("Your name: ")
    orcid = _optional("ORCID (optional): ")
    study_title = _nonempty("First study title: ")
    assay = _optional(
        "First measurement/assay (optional; leave blank if not applicable): "
    )
    data_location = _nonempty("Authoritative data location: ")
    data_access = _prompt_access()
    keywords_text = _optional("Keywords (comma-separated, optional): ")
    keywords = (
        [item.strip() for item in keywords_text.split(",") if item.strip()]
        if keywords_text
        else []
    )

    return {
        "project_title": project_title,
        "project_description": project_description,
        "creator": {
            "name": creator_name,
            "orcid": orcid,
        },
        "first_study": {
            "title": study_title,
        },
        "first_assay": {"title": assay} if assay else None,
        "data": {
            "location": data_location,
            "access": data_access,
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


def _cmd_export(args: argparse.Namespace) -> int:
    try:
        result = export_rocrate(
            args.workspace,
            args.output,
            force=args.force,
        )
    except ROCrateExportError as exc:
        print(f"Export error: {exc}", file=sys.stderr)
        if exc.workspace_report is not None:
            for issue in exc.workspace_report.issues:
                location = f" ({issue.path})" if issue.path else ""
                print(
                    f"- [{issue.code}]{location} {issue.message}",
                    file=sys.stderr,
                )
            return EXIT_INVALID
        return EXIT_EXPORT
    except OSError as exc:
        print(f"Export error: {exc}", file=sys.stderr)
        return EXIT_EXPORT

    print(f"Created RO-Crate 1.3 export: {result.output}")
    print(f"Metadata: {result.metadata_path}")
    print(f"Entities: {result.entity_count}")
    if result.copied_paths:
        print(f"Packaged paths: {len(result.copied_paths)}")
    if result.validation.warnings:
        print(
            f"Validation warnings: {len(result.validation.warnings)}",
            file=sys.stderr,
        )
        for warning in result.validation.warnings:
            location = f" ({warning.path})" if warning.path else ""
            print(
                f"- [{warning.code}]{location} {warning.message}",
                file=sys.stderr,
            )
    return EXIT_OK


def _report_mutation(result: MutationResult, as_json: bool) -> int:
    plan = result.plan
    if as_json:
        print(json.dumps(result.to_mapping(), ensure_ascii=False, indent=2))
        return EXIT_OK

    print(plan.summary)
    diff = plan.diff()
    if diff:
        print(diff, end="" if diff.endswith("\n") else "\n")
    else:
        print(f"No change to {plan.record}.")

    if result.applied:
        if diff:
            print(f"Updated {plan.record}")
        for name in plan.replaced_files:
            print(f"Replaced {name[0]}")
        if plan.new_directories or plan.new_files:
            print(
                f"Created {len(plan.new_directories)} folder(s) "
                f"and {len(plan.new_files)} file(s)."
            )
    else:
        print("Dry run: nothing was written.")
        for name in plan.new_directories:
            print(f"Would create folder: {name}")
        for name, _ in plan.new_files:
            print(f"Would create file: {name}")
        for name, _, _ in plan.replaced_files:
            print(f"Would replace file: {name}")
    return EXIT_OK


def _run_mutation(args: argparse.Namespace, operation) -> int:
    try:
        result = operation()
    except MutationInputError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return EXIT_INPUT
    except MutationConflict as exc:
        print(f"Conflict: {exc}", file=sys.stderr)
        return EXIT_CONFLICT
    except WorkspaceNotValid as exc:
        print(str(exc), file=sys.stderr)
        for issue in exc.report.issues:
            location = f" ({issue.path})" if issue.path else ""
            print(f"- [{issue.code}]{location} {issue.message}", file=sys.stderr)
        return EXIT_INVALID
    except YamlEditError as exc:
        print(f"Record error: {exc}", file=sys.stderr)
        return EXIT_INPUT
    except OSError as exc:
        print(f"Could not update workspace: {exc}", file=sys.stderr)
        return EXIT_INPUT
    return _report_mutation(result, args.json)


def _cmd_study_add(args: argparse.Namespace) -> int:
    return _run_mutation(
        args,
        lambda: add_study(
            args.workspace,
            args.title,
            identifier=args.id,
            description=args.description,
            path=args.path,
            dry_run=args.dry_run,
        ),
    )


def _cmd_assay_add(args: argparse.Namespace) -> int:
    return _run_mutation(
        args,
        lambda: add_assay(
            args.workspace,
            args.study,
            args.title,
            identifier=args.id,
            description=args.description,
            path=args.path,
            dry_run=args.dry_run,
        ),
    )


def _cmd_resource_add(args: argparse.Namespace) -> int:
    return _run_mutation(
        args,
        lambda: register_resource(
            args.workspace,
            args.name,
            collection=args.collection,
            kind=args.type,
            path=args.path,
            location=args.location,
            identifier=args.identifier,
            access=args.access,
            description=args.description,
            dry_run=args.dry_run,
        ),
    )


def _cmd_contributor_add(args: argparse.Namespace) -> int:
    return _run_mutation(
        args,
        lambda: add_contributor(
            args.workspace,
            args.name,
            role=args.role,
            orcid=args.orcid,
            dry_run=args.dry_run,
        ),
    )


def _cmd_metadata_set(args: argparse.Namespace) -> int:
    if args.keyword and args.clear_keywords:
        print(
            "Input error: use either --keyword or --clear-keywords, not both.",
            file=sys.stderr,
        )
        return EXIT_INPUT
    keywords = [] if args.clear_keywords else (args.keyword or None)
    return _run_mutation(
        args,
        lambda: update_project_metadata(
            args.workspace,
            title=args.title,
            description=args.description,
            status=args.status,
            keywords=keywords,
            dry_run=args.dry_run,
        ),
    )


def _mutation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        default=".",
        metavar="DIR",
        help="Workspace folder to update (default: current folder).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the diff and the folders that would be created, without writing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON plan instead of human-readable output.",
    )


def _add_mutation_commands(subparsers: argparse._SubParsersAction) -> None:
    """Commands that evolve an already-initialized workspace."""

    study = subparsers.add_parser(
        "study",
        help="Work with the Studies of an existing workspace.",
        description="Record additional ISA Studies in an existing workspace.",
    )
    study_actions = study.add_subparsers(dest="action", required=True)
    study_add = study_actions.add_parser(
        "add",
        help="Record a new Study and scaffold its folders.",
        description=(
            "Record a new ISA Study in .research/project.yml and scaffold the same "
            "folder layout initialization creates. Refused if the identifier or the "
            "folder is already taken."
        ),
    )
    study_add.add_argument("title", help="Human-readable Study title.")
    study_add.add_argument(
        "--id",
        metavar="IDENTIFIER",
        help="Study identifier and folder name (default: derived from the title).",
    )
    study_add.add_argument("--description", help="Optional Study description.")
    study_add.add_argument(
        "--path",
        metavar="RELATIVE",
        help="Workspace-relative Study folder (default: studies/<identifier>).",
    )
    _mutation_options(study_add)
    study_add.set_defaults(func=_cmd_study_add)

    assay = subparsers.add_parser(
        "assay",
        help="Work with the Assays of an existing Study.",
        description="Record additional ISA Assays inside an existing Study.",
    )
    assay_actions = assay.add_subparsers(dest="action", required=True)
    assay_add = assay_actions.add_parser(
        "add",
        help="Record a new Assay inside a Study and scaffold its folders.",
        description=(
            "Record a new ISA Assay under an existing Study. The Assay folder is "
            "created inside the Study folder, which the ORW validator requires."
        ),
    )
    assay_add.add_argument("title", help="Human-readable Assay title.")
    assay_add.add_argument(
        "--study",
        required=True,
        metavar="IDENTIFIER",
        help="Identifier of the Study this measurement belongs to.",
    )
    assay_add.add_argument(
        "--id",
        metavar="IDENTIFIER",
        help="Assay identifier and folder name (default: derived from the title).",
    )
    assay_add.add_argument("--description", help="Optional Assay description.")
    assay_add.add_argument(
        "--path",
        metavar="RELATIVE",
        help=(
            "Workspace-relative Assay folder inside the Study "
            "(default: <study path>/assays/<identifier>)."
        ),
    )
    _mutation_options(assay_add)
    assay_add.set_defaults(func=_cmd_assay_add)

    resource = subparsers.add_parser(
        "resource",
        help="Register data, documents and other resources.",
        description=(
            "Register resources the Investigation depends on or produces. ORW records "
            "references; it does not copy or move research data."
        ),
    )
    resource_actions = resource.add_subparsers(dest="action", required=True)
    resource_add = resource_actions.add_parser(
        "add",
        help="Register a resource in the canonical project record.",
        description=(
            "Register a dataset, document or other resource. Give a workspace path "
            "for content kept here, or a location/identifier for data held elsewhere."
        ),
    )
    resource_add.add_argument("name", help="Human-readable resource name.")
    resource_add.add_argument(
        "--type",
        metavar="TYPE",
        help="Resource type, for example dataset, documentation, software or schema.",
    )
    resource_add.add_argument(
        "--path",
        metavar="RELATIVE",
        help="Workspace-relative path of an existing file or folder.",
    )
    resource_add.add_argument(
        "--location",
        help="Authoritative location when the data live outside this workspace.",
    )
    resource_add.add_argument(
        "--identifier",
        help="Persistent identifier, for example a DOI or accession number.",
    )
    resource_add.add_argument(
        "--access",
        choices=sorted(ACCESS_LEVELS),
        help="Access level recorded for this resource.",
    )
    resource_add.add_argument("--description", help="Optional resource description.")
    resource_add.add_argument(
        "--collection",
        choices=RESOURCE_COLLECTIONS,
        default="resources",
        help=(
            "Record the entry as an input resource or as a project output "
            "(default: resources)."
        ),
    )
    _mutation_options(resource_add)
    resource_add.set_defaults(func=_cmd_resource_add)

    contributor = subparsers.add_parser(
        "contributor",
        help="Record the people working on the Investigation.",
        description="Record contributors in the canonical project record.",
    )
    contributor_actions = contributor.add_subparsers(dest="action", required=True)
    contributor_add = contributor_actions.add_parser(
        "add",
        help="Record a contributor.",
        description=(
            "Record a contributor. Duplicate names and duplicate ORCIDs are refused "
            "so that the credit record stays unambiguous."
        ),
    )
    contributor_add.add_argument("name", help="Contributor name.")
    contributor_add.add_argument("--role", help="Role in the Investigation.")
    contributor_add.add_argument("--orcid", help="ORCID, for example 0000-0002-1825-0097.")
    _mutation_options(contributor_add)
    contributor_add.set_defaults(func=_cmd_contributor_add)

    metadata = subparsers.add_parser(
        "metadata",
        help="Update Investigation-level metadata.",
        description="Update the Investigation title, description, status or keywords.",
    )
    metadata_actions = metadata.add_subparsers(dest="action", required=True)
    metadata_set = metadata_actions.add_parser(
        "set",
        help="Set Investigation metadata fields.",
        description=(
            "Set Investigation metadata. Only the fields given are changed; the "
            "workspace README is left to its authors."
        ),
    )
    metadata_set.add_argument("--title", help="New Investigation title.")
    metadata_set.add_argument("--description", help="New Investigation description.")
    metadata_set.add_argument(
        "--status",
        choices=STATUSES,
        help="New Investigation status.",
    )
    metadata_set.add_argument(
        "--keyword",
        action="append",
        metavar="KEYWORD",
        help="Keyword to record; repeat the option to replace the whole keyword list.",
    )
    metadata_set.add_argument(
        "--clear-keywords",
        action="store_true",
        help="Record an empty keyword list.",
    )
    _mutation_options(metadata_set)
    metadata_set.set_defaults(func=_cmd_metadata_set)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orw",
        description=(
            "Create and validate portable OpenResearchWorkspace projects, and record "
            "Studies, Assays, resources, contributors and metadata as the research "
            "grows, without requiring a hosted forge."
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

    export_parser = subparsers.add_parser(
        "export",
        help="Export a validated workspace to an interoperability package.",
        description=(
            "Export canonical ORW metadata and eligible resources as a validated "
            "interoperability package. RO-Crate export never replaces the "
            "canonical .research/project.yml source record."
        ),
    )
    export_parser.add_argument(
        "workspace",
        nargs="?",
        default=".",
        help="Workspace folder to export (default: current folder).",
    )
    export_parser.add_argument(
        "--format",
        choices=("ro-crate",),
        default="ro-crate",
        help="Export format (currently: ro-crate).",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Destination directory for the generated package.",
    )
    export_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output directory after the new crate validates.",
    )
    export_parser.set_defaults(func=_cmd_export)

    _add_mutation_commands(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
