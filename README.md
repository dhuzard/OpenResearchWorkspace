# OpenResearchWorkspace

**A research workspace specification with a GitHub template as its primary reference implementation.**

OpenResearchWorkspace (ORW) defines a portable format/contract for research workspaces that are human usable, FAIR-oriented, machine readable, reproducible, and able to evolve toward agent-ready science.

The normal researcher does **not** fork ORW and does not use a central ORW application.

The intended workflow is:

> **Use template → initialize project → collaborate → work → publish**

Each researcher or lab creates an independent repository from the ORW GitHub template. That repository becomes the canonical project workspace and remains owned by the researcher/lab.

GitHub is infrastructure, not the user model. Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or release mechanics to use the workspace.

## What ORW is

ORW has two distinct layers:

1. **Specification / contract** — defines what an ORW-compatible research workspace must expose and how core concepts are represented.
2. **Reference implementations** — practical ways to create or emit a conforming workspace.

The primary reference implementation is this GitHub template. Other software can produce ORW-compatible workspaces without using the template.

```text
ORW specification
      │
      ├── GitHub template
      ├── external exporters/adapters
      ├── future lightweight setup UI
      └── future CLI/tools
              │
              ▼
        ORW-compatible workspace
```

## Researcher-facing workflow

For an ordinary scientist, the experience should be:

```text
Use this template
      ↓
Create my research repository
      ↓
Run first-time setup
      ↓
Fill a short project form
      ↓
Repository initializes itself
      ↓
Project overview / files / data / analysis / results
      ↓
Publish when ready
```

The setup workflow should write the machine-readable files behind the scenes. Researchers should not need to edit `.research/*.yml` directly unless they want to.

## Core design principles

Every ORW-compatible workspace should be:

- **Human usable** — understandable without learning repository internals.
- **FAIR-oriented** — metadata, identifiers and licensing are captured during the project, not reconstructed only at publication.
- **Machine readable** — one canonical structured project description.
- **Reproducible** — optional capabilities can describe environments, workflows and provenance.
- **Agent ready** — AI systems can discover project context without reverse-engineering filenames or repository history.

## Canonical project model

The canonical machine-readable project record is:

```text
.research/project.yml
```

Human-facing documents, citation files, archival metadata and agent context should be generated from or synchronized with that record rather than maintained independently.

Workspace-level implementation/version information is separate from project metadata:

```text
.research/workspace.yml
```

Optional feature activation is recorded in:

```text
.research/capabilities.yml
```

This separation allows a workspace to be upgraded without confusing ORW implementation metadata with the scientific project description.

## Template lifecycle

The GitHub template is primarily an **initialization mechanism**, not a long-term upstream dependency.

A project created from the template records the ORW specification and template versions it started from. Future upgrades should be explicit workspace/schema migrations rather than asking scientists to merge changes from the original template repository.

```text
Template creates workspace
        ↓
workspace records ORW versions
        ↓
project evolves independently
        ↓
optional explicit ORW migration later
```

See [`TEMPLATE_WORKFLOW.md`](TEMPLATE_WORKFLOW.md).

## Architecture

The project separates four concepts:

1. **Core specification** — what the research project *is*.
2. **Reference implementation** — how the GitHub template instantiates and initializes it.
3. **Optional capabilities** — what the workspace *can do* (archival publication, FAIR enrichment, reproducibility, agent-readiness, etc.).
4. **Agent skills/adapters** — what AI systems can safely do with the project and how provider-specific tools discover those rules.

## v0 goal

The first usable version is deliberately narrow:

```text
Create project
↓
Describe project
↓
Invite collaborators
↓
Add files and/or data links
↓
Work
↓
Publish a permanent citable version
```

The critical usability test is:

> Can a scientist unfamiliar with Git create, understand, collaborate on, and publish a research project without reading Git documentation?

## Repository contents

- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable project schema.
- [`examples/minimal.project.yml`](examples/minimal.project.yml) — minimal example project record.
- [`REFERENCE_IMPLEMENTATION.md`](REFERENCE_IMPLEMENTATION.md) — scientist-facing GitHub template requirements.
- [`TEMPLATE_WORKFLOW.md`](TEMPLATE_WORKFLOW.md) — template initialization and lifecycle model.
- [`docs/AI_READY_WORKSPACE.md`](docs/AI_READY_WORKSPACE.md) — generic AI-ready workspace capability.

## Roadmap

**v0 — Self-initializing GitHub template:** create, setup form, collaboration, files/data references, metadata, publish/DOI.

**v1 — FAIR capability:** persistent identifiers, richer metadata, DataCite export, RO-Crate, FAIR Signposting.

**v2 — Reproducible workspace:** environments, workflows, provenance and automated QA.

**v3 — AI-ready workspace:** semantic project context, schemas, ontology mappings and explicit policies.

**v4 — Agentic workspace:** reusable provider-neutral skills plus thin Codex/Claude/Copilot adapters operating against the same project model.

## Non-goals

OpenResearchWorkspace is not intended to:

- become a required central hosted application;
- require scientists to fork the ORW development repository;
- replace repositories designed for large scientific datasets;
- store sensitive research data on GitHub by default;
- prescribe a single archival provider;
- prescribe a single AI provider;
- require researchers to maintain redundant metadata formats.

## Status

Early specification and GitHub-template reference implementation design. Feedback and real-world research use cases are welcome.

## License

Licensing of the ORW software/specification and licensing of scientific projects created with ORW are separate concerns. A project created from the template must explicitly choose licenses appropriate for its own code, data, documentation and other research outputs.
