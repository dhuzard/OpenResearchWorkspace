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


def study_folders(
    study_root: Path,
    *,
    include_protocols: bool = True,
) -> dict[Path, tuple[str, str]]:
    """Folders scaffolded inside a Study, keyed by workspace-relative path."""

    entries = STUDY_SUBFOLDERS
    if not include_protocols:
        entries = tuple(entry for entry in entries if entry[0] != "protocols")
    return _layout(study_root, entries)


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
    no_code_actions: bool = False


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


def _render_workspace_yaml(
    context: ImplementationContext | None,
    config: SetupConfig,
) -> str:
    provider = ""
    if context and (context.provider or context.provider_user):
        provider_name = context.provider or "unknown"
        provider = (
            "\n  provider:\n"
            f"    name: {yaml_string(provider_name)}"
        )
        if context.provider_user:
            provider += f"\n    user: {yaml_string(context.provider_user)}"

    options = config.workspace_options
    return f'''orw:
  spec_version: "{SPEC_VERSION}"
  template_version: "{TEMPLATE_VERSION}"
  initialized: true
  initialized_at: null

implementation:
  generator: "orw-core"
  canonical_project_record: ".research/project.yml"
  capabilities_record: ".research/capabilities.yml"{provider}

preferences:
  study_structure: {yaml_string(options.study_structure)}
  assay_structure: {yaml_string(options.assay_structure)}
  protocol_storage: {yaml_string(options.protocol_storage)}
'''


def _render_root_readme(
    config: SetupConfig,
    study_identifier: str,
    assay_identifier: str | None,
    implementation: ImplementationContext | None = None,
) -> str:
    study_path = f"studies/{study_identifier}"
    options = config.workspace_options

    if options.study_structure == "multiple":
        study_note = (
            "This Investigation is configured to contain **several Studies**. "
            "The Study below is the first one."
        )
    elif options.study_structure == "undecided":
        study_note = (
            "The Study structure is **not fixed yet**. You can start with the Study "
            "below and add more later if the research requires it."
        )
    else:
        study_note = (
            "This project starts as **one Study inside one Investigation**. "
            "You do not need to create additional Study levels unless the project grows."
        )

    if config.first_assay and assay_identifier:
        measurement_note = (
            f"An initial Assay is already recorded: **{config.first_assay.title}**."
        )
        measurement_path = f"{study_path}/assays/{assay_identifier}/"
    elif options.assay_structure == "multiple":
        measurement_note = (
            "This Study may contain **several measurement types / Assays**. "
            "An `assays/` container is ready, but no Assay name was invented during setup."
        )
        measurement_path = f"{study_path}/assays/"
    elif options.assay_structure == "undecided":
        measurement_note = (
            "The project has **not committed to an Assay layer yet**. "
            "Keep Study-wide material at Study level until distinct measurements need "
            "their own structure."
        )
        measurement_path = None
    else:
        measurement_note = (
            "No separate Assay layer is used at initialization. "
            "For a simple project, keep data, analysis and results directly in the Study."
        )
        measurement_path = None

    if options.protocol_storage == "workspace":
        protocol_note = (
            f"Protocol documents are intended to live in "
            f"[`{study_path}/protocols/`]({study_path}/protocols/)."
        )
        protocol_action = (
            f"4. Add or update protocol documents in "
            f"[`{study_path}/protocols/`]({study_path}/protocols/)."
        )
    elif options.protocol_storage == "elsewhere":
        protocol_note = (
            "Protocols are managed elsewhere. Record stable links or identifiers when "
            "available rather than duplicating controlled documents."
        )
        protocol_action = ""
    else:
        protocol_note = (
            "Protocol storage was left undecided. Add a protocol folder later only if "
            "it becomes useful."
        )
        protocol_action = ""

    measurement_action = ""
    if measurement_path:
        measurement_action = (
            f" If you later separate measurement-specific work, use "
            f"[`{measurement_path}`]({measurement_path})."
        )

    protocol_line = f"\n{protocol_action}" if protocol_action else ""

    no_code_actions = ""
    if (
        implementation
        and implementation.provider == "github"
        and implementation.no_code_actions
    ):
        no_code_actions = """
{no_code_actions}"""

    return f'''# {config.project_title}

{config.project_description}

> ✅ **Your OpenResearchWorkspace is initialized.**
> Start with the scientific folders below. You normally do not need to edit `.research/` or `.github/`.

## Start here

1. Add or reference the data used by the Study in [`{study_path}/data/`]({study_path}/data/).
2. Put analysis code, notebooks or workflows in [`{study_path}/analysis/`]({study_path}/analysis/).
3. Put derived tables, figures and reports in [`{study_path}/results/`]({study_path}/results/).{protocol_line}

This workspace does **not** need to contain your authoritative raw data. If they live on institutional storage or in a domain repository, keep them there and record the authoritative location instead.

## A good working sequence

1. **Work in the existing Study first.** Put ordinary research files in the Study folders above.
2. **Register authoritative data early.** If important data live elsewhere, record their location rather than copying them into GitHub.
3. **Add another Study only when the design really branches** — for example a distinct cohort, intervention, experiment, or study design.
4. **Add a measurement / Assay only when a distinct modality needs its own structure** — for example ECG, imaging, behaviour, or RNA-seq within the same Study.
5. **Add contributors as they join the project** so attribution is not reconstructed at the end.
6. **Run a workspace check periodically**, especially before sharing, archiving, or publishing.

The default rule is: **keep the structure simple until the science requires another layer.**

## No-code ORW actions

You can perform the common structural and metadata actions through GitHub forms:

| What you need | Use this action |
| --- | --- |
| A distinct new Study | [**Add another Study**](../../issues/new?template=orw-add-study.yml) |
| A distinct measurement type inside a Study | [**Add a measurement / Assay**](../../issues/new?template=orw-add-assay.yml) |
| Record where another authoritative dataset lives | [**Register a data source**](../../issues/new?template=orw-register-data.yml) |
| Record another project contributor | [**Add a contributor**](../../issues/new?template=orw-add-contributor.yml) |
| Check that ORW metadata and paths are consistent | [**Check my workspace**](../../issues/new?template=orw-check-workspace.yml) |

These forms call the same validated ORW core used by the command-line tools. You do not need to edit `.research/project.yml` yourself.

## Your initial research structure

- **Investigation:** {config.project_title}
- **Study:** [{config.first_study.title}]({study_path}/)
{f"- **Initial Assay:** [{config.first_assay.title}]({measurement_path})" if config.first_assay and measurement_path else ""}

{study_note}

{measurement_note}{measurement_action}

## Protocols

{protocol_note}

## Data

Authoritative/raw data location: **{config.data.location}**  
Access: **{config.data.access}**

## Where things go

| What you are adding | Suggested place |
| --- | --- |
| Study-wide data or data references | [`{study_path}/data/`]({study_path}/data/) |
| Analysis code / notebooks / workflows | [`{study_path}/analysis/`]({study_path}/analysis/) |
| Derived tables / figures / reports | [`{study_path}/results/`]({study_path}/results/) |
| Project-wide notes and decisions | [`project-docs/`](project-docs/) |
| Literature and references | [`references/`](references/) |

## ORW infrastructure

You can normally ignore these folders during everyday research:

- `.research/` — machine-readable ORW metadata and workspace state;
- `.github/` — GitHub forms and automation.

The canonical scientific record is `.research/project.yml`. ORW implementation state and the workspace-shaping choices made during setup are stored separately in `.research/workspace.yml`.
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
        _ensure_readme(root, study_root / "assays", *ASSAY_CONTAINER_FOLDER)
        _ensure_readme(
            root,
            assay_root,
            config.first_assay.title,
            (
                f"This directory represents an ISA **Assay** within "
                f"**{config.first_study.title}**."
            ),
        )
    elif config.workspace_options.assay_structure == "multiple":
        _ensure_readme(root, study_root / "assays", *ASSAY_CONTAINER_FOLDER)

    folders = study_folders(
        study_root,
        include_protocols=config.workspace_options.protocol_storage == "workspace",
    )
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
    _write_text(
        research / "workspace.yml",
        _render_workspace_yaml(implementation, config),
    )
    _write_text(research / "initialized", "initialized: true\n")
    _write_text(
        root / "README.md",
        _render_root_readme(
            config,
            study_identifier,
            assay_identifier,
            implementation,
        ),
    )

    return WorkspaceResult(
        destination=root,
        project_identifier=project_identifier,
        study_identifier=study_identifier,
        assay_identifier=assay_identifier,
    )
