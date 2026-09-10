# Research Workspace Core Specification v0.1

Status: **Draft**

## 1. Principle

A Research Workspace has exactly one canonical project description:

```text
.research/project.yml
```

Human-facing documents, citation files, repository metadata, archival metadata and agent context SHOULD be generated from or synchronized with this record rather than maintained independently.

## 2. Core entities

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

This is particularly important when migrating from OSF: existing OSF URLs/DOIs must not silently disappear.

## 3. Capabilities

Capabilities are optional and MUST NOT redefine Core semantics.

Examples:

```yaml
capabilities:
  archive:
    provider: zenodo
    enabled: true
  reproducibility:
    enabled: false
  ro_crate:
    enabled: false
  agents:
    enabled: false
```

The implementation of a capability SHOULD live outside the scientist's project whenever practical.

## 4. Human interface

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

## 5. Publication

Publication MUST be an intentional action.

Automated validation MAY determine whether a workspace is ready to publish, but a routine edit or merge SHOULD NOT automatically create a permanent scientific release.

## 6. Extensibility

Extensions MAY add namespaced metadata under `extensions`.

Example:

```yaml
extensions:
  ro_crate:
    profile: "..."
  hmco:
    ontology_version: "..."
```

Extensions MUST NOT alter the meaning of Core fields.

## 7. Agent readiness

Agent-specific instructions and skills are not part of Core v0.1.

An agent SHOULD nevertheless be able to inspect `.research/project.yml` and determine:

- what the project is;
- who contributes;
- what resources/data exist;
- where those resources are;
- what outputs exist;
- which identifiers connect external objects.

Later specifications can add explicit permissions, authoritative-resource declarations, provenance and skills.

## 8. Validation

A conforming Core v0.1 record MUST validate against:

```text
schema/project.schema.json
```

The schema is intentionally permissive enough to evolve while the project model is tested with real scientific projects.
