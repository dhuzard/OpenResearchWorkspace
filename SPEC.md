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

Implementation/lifecycle metadata MUST NOT be mixed into the scientific project model. It belongs in:

```text
.research/workspace.yml
```

Optional capability state SHOULD be represented separately in:

```text
.research/capabilities.yml
```

## 3. Core entities

### `spec_version`
Version of this specification.

### `project`
Human-readable project identity.

Required:
- `title`
- `description`
- `status`

Recommended:
- `keywords`

Allowed status values in v0.1:
- `active`
- `paused`
- `completed`
- `archived`

### `contributors`
People or organizations contributing to the project.

A contributor SHOULD have a name. ORCID and role are optional in Core but strongly recommended where applicable.

### `resources`
Version-controlled or external resources relevant to the project, such as code repositories, protocols, documents or software.

### `data`
Data resources or locations. Core does not require data to live in the workspace.

A data entry can therefore point to:
- a local path;
- an external repository;
- institutional storage;
- a persistent identifier.

Access restrictions SHOULD be stated explicitly.

### `outputs`
Scientific outputs produced by the project: datasets, software, manuscripts, reports, models, workflows, etc.

### `related_identifiers`
Persistent identifiers or canonical URLs connecting the project to external objects or predecessor systems.

Existing identifiers from predecessor systems MUST NOT silently disappear during migration.

## 4. Workspace lifecycle metadata

`.research/workspace.yml` describes the ORW implementation state rather than the science itself.

Recommended fields include:

```yaml
orw:
  spec_version: "0.1"
  template_version: "0.1.0"
  initialized: false
  initialized_at: null
```

A conforming implementation SHOULD record enough version information to support later validation and explicit migrations.

Template-derived projects SHOULD evolve independently after initialization. Future ORW upgrades SHOULD use explicit schema/workspace migrations rather than requiring researchers to merge upstream template history.

## 5. Capabilities

Capabilities are optional and MUST NOT redefine Core semantics.

A capability MAY provide FAIR enrichment, archival publication, reproducibility tooling, AI-ready context or agent support.

Example `.research/capabilities.yml`:

```yaml
capabilities:
  fair:
    enabled: true
  archive:
    enabled: false
    provider: null
  reproducibility:
    enabled: false
  agent_ready:
    enabled: false
```

The implementation of a capability SHOULD be reusable and SHOULD avoid copying unnecessary machinery into every scientist's workspace.

## 6. Reference implementations

A reference implementation is a practical mechanism for creating or emitting a conforming ORW workspace.

Examples include:

- the primary GitHub template;
- an exporter from a scientific application;
- a future lightweight setup interface;
- a future CLI initializer.

Reference implementations MUST preserve the semantics of the ORW specification and MUST NOT redefine core fields for provider-specific convenience.

## 7. GitHub template reference implementation

The primary v0 implementation is a GitHub template repository.

The intended researcher workflow is:

```text
Use template
→ create independent project repository
→ run first-time setup
→ fill short project form
→ repository initializes itself
→ collaborate/work
→ publish intentionally
```

The template SHOULD hide Git-specific concepts from ordinary researchers wherever practical.

The first-run workflow SHOULD collect core metadata and write `.research/project.yml`, `.research/workspace.yml`, and `.research/capabilities.yml` automatically.

## 8. Human interface

Implementations SHOULD NOT require ordinary researchers to understand:

- Git commits;
- branches;
- pull requests;
- YAML;
- CI/CD;
- tags;
- GitHub Actions.

Those concepts may remain available to advanced users.

Scientist-facing vocabulary SHOULD prefer:

| Infrastructure | Scientist-facing concept |
|---|---|
| repository | project |
| commit | change |
| issue | task/discussion |
| release | published version |
| tag | version |
| CI check | project check |

## 9. Publication

Publication MUST be an intentional action.

Automated validation MAY determine whether a workspace is ready to publish, but a routine edit or merge SHOULD NOT automatically create a permanent scientific release.

## 10. Extensibility

Extensions MAY add namespaced metadata under `extensions`.

Example:

```yaml
extensions:
  ro_crate:
    profile: "..."
```

Extensions MUST NOT alter the meaning of Core fields.

## 11. Agent readiness

Agent-specific instructions and skills are not part of Core v0.1.

An agent SHOULD nevertheless be able to inspect `.research/project.yml` and determine:

- what the project is;
- who contributes;
- what resources/data exist;
- where those resources are;
- what outputs exist;
- which identifiers connect external objects.

Later capabilities MAY add explicit permissions, authoritative-resource declarations, provenance, quality gates and skills.

## 12. Validation

A conforming Core v0.1 project record MUST validate against:

```text
schema/project.schema.json
```

The schema is intentionally permissive enough to evolve while the project model is tested with real scientific projects.
