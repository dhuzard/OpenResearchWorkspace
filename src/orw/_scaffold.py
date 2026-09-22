"""Deterministic ORW workspace generation independent of Git or hosting provider."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .edit import scalar
from .model import SetupConfig

SPEC_VERSION = "0.1"
TEMPLATE_VERSION = "0.1.0"

# Study and Assay folder layouts are shared with the mutation API so that a
# Study added later is scaffolded exactly like the one written at initialization.
STUDY_SUBFOLDERS: tuple[tuple[str, str, str], ...] = (
    (
        "data",
        "Study data",
        "Study-level data and references to authoritative data locations.",
    ),
    (
        "data/raw",
        "Raw data",
        "Authoritative source data when appropriate to keep them in this workspace. Do not silently overwrite raw evidence.",
    ),
    (
        "data/processed",
        "Processed data",
        "Data derived reproducibly from raw or external inputs.",
    ),
    (
        "data/external",
        "External data",
        "Links, identifiers, manifests, checksums, or access notes for data stored elsewhere.",
    ),
    (
        "protocols",
        "Protocols",
        "Study-level procedures, designs, and protocols.",
    ),
    (
        "analysis",
        "Study analysis",
        "Analyses that apply across assays or interpret the Study as a whole.",
    ),
    (
        "results",
        "Study results",
        "Study-level derived outputs and summaries.",
    ),
)

ASSAY_SUBFOLDERS: tuple[tuple[str, str, str], ...] = (
    (
        "data",
        "Assay data",
        "Data belonging specifically to this measurement or assay.",
    ),
    (
        "data/raw",
        "Raw assay data",
        "Authoritative source data for this assay when appropriate to keep them here.",
    ),
    (
        "data/processed",
        "Processed assay data",
        "Data derived reproducibly from this assay's raw or external inputs.",
    ),
    (
        "analysis",
        "Assay analysis",
        "Analysis code, notebooks, and workflows specific to this assay.",
    ),
    (
        "results",
        "Assay results",
        "Derived tables, figures, reports, and outputs specific to this assay.",
    ),
)

# The Assay container README depends on whether an Assay exists yet. Adding one
# later replaces the "none initialized" note only when it is still byte-identical.
NO_ASSAY_FOLDER: tuple[str, str] = (
    "Assays",
    "No Assay was initialized because none was scientifically specified.",
)
ASSAY_CONTAINER_FOLDER: tuple[str, str] = (
    "Assays",
    "Measurements and tests performed on this Study's material or subjects.",
)

INVESTIGATION_FOLDERS: tuple[tuple[str, str, str], ...] = (
    (
        "references",
        "References",
        "Literature, citation exports, and stable identifiers relevant to the Investigation.",
    ),
    (
        "project-docs",
        "Project documentation",
        "Investigation-wide notes, decisions, rationale, history, and data-management context.",
    ),
)


def readme_text(title: str, text: str) -> str:
    """The folder README body used by initialization and by later mutations."""

    return f"# {title}\n\n{text}\n"


def _layout(
    root: Path, entries: tuple[tuple[str, str, str], ...]
) -> dict[Path, tuple[str, str]]:
    return {root / relative: (title, text) for relative, title, text in entries}


def study_folders(study_root: Path) -> dict[Path, tuple[str, str]]:
    """Folders scaffolded inside a Study, keyed by workspace-relative path."""

    return _layout(study_root, STUDY_SUBFOLDERS)


def assay_folders(assay_root: Path) -> dict[Path, tuple[str, str]]:
    """Folders scaffolded inside an Assay, keyed by workspace-relative path."""

    return _layout(assay_root, ASSAY_SUBFOLDERS)


class WorkspaceAlreadyInitialized(RuntimeError):
    """Raised when initialization would overwrite an initialized workspace."""


@dataclass(frozen=True)
class ImplementationContext:
    """Optional adapter metadata kept outside the scientific project record."""

    provider: str | None = None
    provider_user: str | None = None


@dataclass(frozen=True)
class WorkspaceResult:
    destination: Path
    project_identifier: str
    study_identifier: str
    assay_identifier: str | None


def slug(value: str, fallback: str) -> str:
    normalized = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized[:60] or fallback


def yaml_string(value: str) -> str:
    """JSON strings are valid YAML scalars and give deterministic escaping."""

    return scalar(value)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _ensure_readme(root: Path, path: Path, title: str, text: str) -> None:
    directory = root / path
    directory.mkdir(parents=True, exist_ok=True)
    readme = directory / "README.md"
    if not readme.exists():
        _write_text(readme, readme_text(title, text))


def _is_initialized(root: Path) -> bool:
    marker = root / ".research" / "initialized"
    if marker.exists():
        return True

    workspace = root / ".research" / "workspace.yml"
    if workspace.exists():
        text = workspace.read_text(encoding="utf-8")
        if re.search(r"^\s*initialized:\s*true\s*$", text, re.MULTILINE):
            return True

    return False


def _render_keywords(keywords: tuple[str, ...]) -> str:
    if not keywords:
        return "    []"
    return "\n".join(f"    - {yaml_string(keyword)}" for keyword in keywords)


def _render_project_yaml(
    config: SetupConfig,
    project_identifier: str,
    study_identifier: str,
    assay_identifier: str | None,
    study_root: Path,
    assay_root: Path | None,
) -> str:
    orcid_line = (
        f"\n    orcid: {yaml_string(config.creator.orcid)}"
        if config.creator.orcid
        else ""
    )

    if config.first_assay and assay_identifier and assay_root:
        assays = (
            "    assays:\n"
            f"      - identifier: {yaml_string(assay_identifier)}\n"
            f"        title: {yaml_string(config.first_assay.title)}\n"
            f"        path: {yaml_string(assay_root.as_posix())}"
        )
    else:
        assays = "    assays: []"

    return f'''spec_version: "{SPEC_VERSION}"

investigation:
  identifier: {yaml_string(project_identifier)}
  title: {yaml_string(config.project_title)}
  description: {yaml_string(config.project_description)}
  status: active
  keywords:
{_render_keywords(config.keywords)}

contributors:
  - name: {yaml_string(config.creator.name)}
    role: "Project creator"{orcid_line}

studies:
  - identifier: {yaml_string(study_identifier)}
    title: {yaml_string(config.first_study.title)}
    path: {yaml_string(study_root.as_posix())}
{assays}

resources:
  - name: "Authoritative/raw research data"
    type: "dataset"
    location: {yaml_string(config.data.location)}
    access: {yaml_string(config.data.access)}
    description: "Authoritative data location recorded during ORW initialization."

outputs: []
related_identifiers: []
'''


def _render_workspace_yaml(context: ImplementationContext | None) -> str:
    provider = ""
    if context and (context.provider or context.provider_user):
        provider_name = context.provider or "unknown"
        provider = (
            "\n  provider:\n"
            f"    name: {yaml_string(provider_name)}"
        )
        if context.provider_user:
            provider += f"\n    user: {yaml_string(context.provider_user)}"

    return f'''orw:
  spec_version: "{SPEC_VERSION}"
  template_version: "{TEMPLATE_VERSION}"
  initialized: true
  initialized_at: null

implementation:
  generator: "orw-core"
  canonical_project_record: ".research/project.yml"
  capabilities_record: ".research/capabilities.yml"{provider}
'''


def _render_root_readme(
    config: SetupConfig,
    study_identifier: str,
    assay_identifier: str | None,
) -> str:
    study_path = f"studies/{study_identifier}"
    structure = (
        f"- **Investigation:** {config.project_title}\n"
        f"- **Study:** [{config.first_study.title}]({study_path}/)\n"
    )
    if config.first_assay and assay_identifier:
        structure += (
            f"- **Assay:** [{config.first_assay.title}]"
            f"({study_path}/assays/{assay_identifier}/)\n"
        )
    else:
        structure += "- **Assay:** none initialized\n"

    return f'''# {config.project_title}

{config.project_description}

## Research structure

This workspace uses the ISA scientific hierarchy:

{structure}
## Project creator

{config.creator.name}

## Data

Authoritative/raw data location: **{config.data.location}**  
Access: **{config.data.access}**

## Where to work

Use the Study folder above for study-wide protocols and context. Put measurement-specific data, analysis, and results inside the relevant Assay when an Assay exists.

The canonical machine-readable scientific record is `.research/project.yml`. ORW implementation state is kept separately in `.research/workspace.yml`.
'''


def create_workspace(
    config: SetupConfig,
    destination: Path | str,
    *,
    implementation: ImplementationContext | None = None,
) -> WorkspaceResult:
    """Create an ORW workspace at *destination* from normalized setup input.

    The function performs no network, Git, or provider API operations.
    """

    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)

    if _is_initialized(root):
        raise WorkspaceAlreadyInitialized(
            f"Workspace is already initialized: {root}"
        )

    project_identifier = slug(config.project_title, "investigation-01")
    study_identifier = slug(config.first_study.title, "study-01")
    assay_identifier = (
        slug(config.first_assay.title, "assay-01") if config.first_assay else None
    )

    study_root = Path("studies") / study_identifier
    assay_root = (
        study_root / "assays" / assay_identifier if assay_identifier else None
    )

    _ensure_readme(
        root,
        study_root,
        config.first_study.title,
        (
            f"This directory represents an ISA **Study** within the Investigation "
            f"**{config.project_title}**."
        ),
    )

    if assay_root and config.first_assay:
        _ensure_readme(
            root,
            assay_root,
            config.first_assay.title,
            (
                f"This directory represents an ISA **Assay** within "
                f"**{config.first_study.title}**."
            ),
        )
    else:
        _ensure_readme(root, study_root / "assays", *NO_ASSAY_FOLDER)

    folders = study_folders(study_root)
    folders.update(_layout(Path("."), INVESTIGATION_FOLDERS))

    if assay_root:
        folders.update(assay_folders(assay_root))

    for path, (title, text) in folders.items():
        _ensure_readme(root, path, title, text)

    research = root / ".research"
    research.mkdir(parents=True, exist_ok=True)

    _write_text(
        research / "project.yml",
        _render_project_yaml(
            config,
            project_identifier,
            study_identifier,
            assay_identifier,
            study_root,
            assay_root,
        ),
    )
    _write_text(research / "workspace.yml", _render_workspace_yaml(implementation))
    _write_text(research / "initialized", "initialized: true\n")
    _write_text(
        root / "README.md",
        _render_root_readme(config, study_identifier, assay_identifier),
    )

    return WorkspaceResult(
        destination=root,
        project_identifier=project_identifier,
        study_identifier=study_identifier,
        assay_identifier=assay_identifier,
    )
