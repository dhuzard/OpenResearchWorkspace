# OpenResearchWorkspace Core Specification v0.1

Status: **Draft**

## 1. Product definition

OpenResearchWorkspace (ORW) is a **workspace format/contract** plus one or more **reference implementations**.

The specification defines what an ORW-compatible workspace is. It does not require a particular hosting provider, user interface, archive service, or AI system.

The primary reference implementation is a self-initializing GitHub template. Other tools MAY generate conforming ORW workspaces directly.

A normal research project created from the GitHub template is an independent repository. It is not expected to remain a fork or synchronized Git child of the ORW development repository.

## 2. Canonical project description

An ORW workspace has exactly one canonical scientific project description:

```text
.research/project.yml
```

Human-facing documents, citation files, repository metadata, archival metadata and agent context SHOULD be generated from or synchronized with this record rather than maintained independently.

Implementation/lifecycle metadata MUST NOT be mixed into the scientific project model. It belongs in `.research/workspace.yml`. Optional capability state SHOULD be represented separately in `.research/capabilities.yml`.

## 3. Canonical workspace layout semantics

ORW defines a small set of stable human-facing folder roles. The default mixed-project skeleton is:

```text
README.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── analysis/
│   ├── notebooks/
│   ├── scripts/
│   └── workflows/
├── results/
│   ├── tables/
│   ├── figures/
│   └── reports/
├── protocols/
├── references/
└── project-docs/
```

The machine-readable declaration of these roles is `.research/layout.yml`.

The semantics are normative even when a project profile omits a folder:

- `data/raw` — authoritative source data, read-only by default;
- `data/processed` — reproducibly derived data;
- `data/external` — references/manifests for authoritative data stored elsewhere;
- `analysis` — computational methods transforming inputs into outputs;
- `results` — derived scientific outputs;
- `protocols` — experimental/acquisition/preprocessing procedures;
- `references` — scholarly context and external scientific resources;
- `project-docs` — project rationale, decisions, notes, data-management context, and history.

The expected provenance direction is:

```text
raw or external data → processed data → analysis → results → publication/archive
```

Raw source evidence SHOULD NOT be silently overwritten. ORW does not require authoritative scientific data to be physically stored in GitHub.

## 4. Project profiles

Profiles are initialization presets, not different ORW standards. Recommended profiles are `experimental`, `computational`, `mixed`, `literature`, and `other`.

Profiles MAY select which canonical folders are initially present but MUST NOT redefine their semantics. Profile declarations are stored in `.research/profiles.yml` in the GitHub reference implementation.

## 5. Core entities

### `spec_version`
Version of this specification.

### `project`
Human-readable project identity. Required fields are `title`, `description`, and `status`. Recommended fields include `keywords`. Allowed status values in v0.1 are `active`, `paused`, `completed`, and `archived`.

### `contributors`
People or organizations contributing to the project. A contributor SHOULD have a name. ORCID and role are optional in Core but strongly recommended where applicable.

### `resources`
Version-controlled or external resources relevant to the project, such as code repositories, protocols, documents or software.

### `data`
Data resources or locations. Core does not require data to live in the workspace. A data entry can point to a local path, external repository, institutional storage, or persistent identifier. Access restrictions SHOULD be stated explicitly.

### `outputs`
Scientific outputs produced by the project: datasets, software, manuscripts, reports, models, workflows, etc.

### `related_identifiers`
Persistent identifiers or canonical URLs connecting the project to external objects or predecessor systems. Existing identifiers from predecessor systems MUST NOT silently disappear during migration.

## 6. Workspace lifecycle metadata

`.research/workspace.yml` describes the ORW implementation state rather than the science itself. A conforming implementation SHOULD record enough version information to support later validation and explicit migrations.

Template-derived projects SHOULD evolve independently after initialization. Future ORW upgrades SHOULD use explicit schema/workspace migrations rather than requiring researchers to merge upstream template history.

## 7. Capabilities

Capabilities are optional and MUST NOT redefine Core semantics. A capability MAY provide FAIR enrichment, archival publication, reproducibility tooling, AI-ready context or agent support.

The implementation of a capability SHOULD be reusable and SHOULD avoid copying unnecessary machinery into every scientist's workspace.

## 8. Reference implementations

A reference implementation is a practical mechanism for creating or emitting a conforming ORW workspace. Examples include the primary GitHub template, an exporter from a scientific application, a future lightweight setup interface, or a future CLI initializer.

Reference implementations MUST preserve the semantics of the ORW specification and MUST NOT redefine core fields for provider-specific convenience.

## 9. GitHub template reference implementation

The intended researcher workflow is:

```text
Use template
→ create independent project repository
→ run first-time setup
→ choose project profile
→ fill short project form
→ repository initializes itself
→ collaborate/work
→ publish intentionally
```

The first-run workflow SHOULD collect core metadata and write `.research/project.yml`, `.research/workspace.yml`, and `.research/capabilities.yml` automatically. It SHOULD also select the project skeleton from the canonical profile declarations.

## 10. Human interface

Implementations SHOULD NOT require ordinary researchers to understand Git commits, branches, pull requests, YAML, CI/CD, tags, or GitHub Actions.

Scientist-facing vocabulary SHOULD prefer project, change, task/discussion, published version, version, and project check over Git-specific terms where possible.

## 11. Publication

Publication MUST be an intentional action. Automated validation MAY determine whether a workspace is ready to publish, but a routine edit or merge SHOULD NOT automatically create a permanent scientific release.

## 12. Extensibility

Extensions MAY add namespaced metadata under `extensions`, but MUST NOT alter the meaning of Core fields or canonical folder roles.

## 13. Agent readiness

Agent-specific instructions and skills are not part of Core v0.1. An agent SHOULD nevertheless be able to inspect the canonical machine-readable files and determine what the project is, where authoritative inputs live, which outputs are derived, what resources exist, and which identifiers connect external objects.

Later capabilities MAY add explicit permissions, authoritative-resource declarations, provenance, quality gates and skills.

## 14. Validation

A conforming Core v0.1 project record MUST validate against `schema/project.schema.json`. The schema is intentionally permissive enough to evolve while the project model is tested with real scientific projects.
