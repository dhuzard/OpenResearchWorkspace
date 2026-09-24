# GitHub template reference implementation

> **Scope:** this document describes the current GitHub adapter. GitHub is not required by the ORW specification. Provider-neutral core/CLI/browser architecture is defined in [docs/portable-implementations.md](docs/portable-implementations.md), and RO-Crate export is defined in [docs/ro-crate.md](docs/ro-crate.md).

The primary hosted reference implementation is a **self-initializing GitHub template distributed from `dhuzard/OpenResearchWorkspace-template`**, designed for a scientist who has never used Git. The scientific core remains provider-neutral.

The researcher should create an independent project repository from the template. They should not need to fork OpenResearchWorkspace or keep their project synchronized with the ORW development repository.

## Target user journey

### 1. Create project

The researcher selects **Use this template** and creates a new repository owned by themselves, their lab, or their organization.

The newly created repository starts in an uninitialized ORW state.

### 2. First-time setup

The repository presents a clear **Set up this research project** action.

The researcher answers a short form covering project title/description, researcher identity, Study structure, whether an Assays layer is needed, protocol-storage preference, authoritative data location/access, and optional keywords. The form does not require an artificial first Assay.

The setup process writes or updates:

```text
.research/project.yml
.research/workspace.yml
.research/capabilities.yml
README.md
```

The researcher SHOULD NOT need to edit YAML manually.

### 3. Collaborate

The researcher adds project collaborators. GitHub permissions may provide the underlying implementation, but the scientist-facing instructions should describe people as collaborators rather than requiring Git terminology.

### 4. Work

The visible project surface should remain small and recognizable. A simple workspace begins with one Study and exposes only the data/analysis/results/protocol layers the researcher actually needs. Additional Studies and Assays are added later through no-code actions or the same provider-neutral mutation API.

Infrastructure may exist under `.research/`, `.github/`, and capability-specific directories without becoming part of the normal user workflow.

### 5. Publish

The researcher selects **Publish project** or an equivalent intentional action.

The publication workflow should:

1. validate required metadata;
2. warn about secrets and restricted/sensitive data;
3. show what will be published;
4. request explicit confirmation;
5. create a version;
6. send the release to the configured archive when enabled;
7. report the resulting DOI/PID.

Routine edits or merges must not automatically publish permanent scientific records.

## Template lifecycle

The template is an initialization mechanism, not an upstream branch that every research project must track.

At project creation, the workspace records its ORW versions:

```yaml
orw:
  spec_version: "0.1"
  template_version: "0.1.0"
  initialized: true
```

After initialization, the scientific repository evolves independently.

Later ORW improvements should be delivered through explicit workspace/schema migrations rather than asking ordinary researchers to merge changes from the original template.

## What should remain hidden by default

- YAML;
- Git branches;
- commits;
- tags;
- GitHub Actions;
- release internals;
- generated `CITATION.cff`;
- DataCite JSON;
- RO-Crate JSON-LD;
- provider-specific agent instructions.

Advanced users may access all of them.

## Optional lightweight UI

ORW is not intended to become a required central application.

A future lightweight UI MAY make project setup, metadata editing, capability activation or publication easier. Such a UI should operate on the researcher's own ORW repository and should not become the canonical store of project state.

The repository remains the project instance.

## Critical usability metric

A new researcher should be able to create and understand a project, add collaborators, register where data live, and reach a publish-ready state without reading Git documentation.


## Compatibility with the pre-split template

Repositories created before 23 September 2026 may carry ORW development files and historical initialization formats. Current compatibility behavior and migration guidance are documented in [docs/legacy-template-migration.md](docs/legacy-template-migration.md).
