# OpenResearchWorkspace

**A research workspace specification with a GitHub template as its primary reference implementation.**

OpenResearchWorkspace (ORW) defines a portable format/contract for research workspaces that are **human usable, FAIR-oriented, machine readable, reproducible, and agent ready**.

The normal researcher does **not** fork ORW and does not use a central ORW application.

> **Use template → initialize project → collaborate → work → publish**

Each researcher or lab creates an independent repository from the ORW GitHub template. That repository becomes the canonical project workspace and remains owned by the researcher/lab.

GitHub is infrastructure, not the user model. Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or release mechanics to use the workspace.

## Start here

If you are a researcher, begin with the step-by-step guide in [`docs/getting-started.md`](docs/getting-started.md).

If you want to understand the architecture, read [`docs/concepts.md`](docs/concepts.md) and [`SPEC.md`](SPEC.md).

A MyST/Sphinx documentation site is included under [`docs/`](docs/) and configured for Read the Docs. It uses the Furo theme and Markdown-first authoring.

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
- **FAIR-oriented** — metadata, identifiers, and licensing are captured during the project rather than reconstructed only at publication.
- **Machine readable** — one canonical structured project description.
- **Reproducible** — optional capabilities can describe environments, workflows, and provenance.
- **Agent ready** — AI systems can discover project context without reverse-engineering filenames or repository history.

## Canonical project model

The canonical project record is:

```text
.research/project.yml
```

Workspace implementation/version information is separate:

```text
.research/workspace.yml
```

Optional feature activation is recorded in:

```text
.research/capabilities.yml
```

Human-facing documents, citation files, archival metadata, and agent context should be generated from or synchronized with the canonical project record rather than maintained independently.

## Template lifecycle

The GitHub template is an **initialization mechanism**, not a long-term upstream dependency.

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

## Repository contents

- [`docs/getting-started.md`](docs/getting-started.md) — step-by-step researcher guide.
- [`docs/concepts.md`](docs/concepts.md) — ORW concepts and architecture.
- [`docs/capabilities.md`](docs/capabilities.md) — FAIR, reproducibility, AI-ready, and agent-ready capability model.
- [`docs/faq.md`](docs/faq.md) — practical FAQ.
- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable project schema.
- [`examples/minimal.project.yml`](examples/minimal.project.yml) — minimal example project record.
- [`REFERENCE_IMPLEMENTATION.md`](REFERENCE_IMPLEMENTATION.md) — scientist-facing GitHub template requirements.
- [`TEMPLATE_WORKFLOW.md`](TEMPLATE_WORKFLOW.md) — template initialization and lifecycle model.
- [`docs/AI_READY_WORKSPACE.md`](docs/AI_READY_WORKSPACE.md) — generic AI-ready workspace capability.

## Roadmap

**v0 — Self-initializing GitHub template:** create, setup form, collaboration, files/data references, metadata, publish/DOI.

**v1 — FAIR capability:** persistent identifiers, richer metadata, DataCite export, RO-Crate, FAIR Signposting.

**v2 — Reproducible workspace:** environments, workflows, provenance, and automated QA.

**v3 — AI-ready workspace:** semantic project context, schemas, ontology mappings, and explicit policies.

**v4 — Agentic workspace:** reusable provider-neutral skills plus thin Codex/Claude/Copilot adapters operating against the same project model.

## Documentation development

```bash
python -m pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` locally after the build.

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

Early specification and GitHub-template reference implementation design. The documentation now defines the intended user journey; the self-initializing setup workflow itself remains part of the v0 implementation backlog.

## License

**OpenResearchWorkspace itself is MIT licensed.** This applies to the ORW software, template infrastructure, and reusable scaffolding in this repository; see [`LICENSE`](LICENSE).

Scientific projects created from the ORW template are independent projects and do **not** automatically inherit MIT for their research outputs. Each project should explicitly choose licenses appropriate for its own code, data, documentation, manuscripts, figures, and other outputs.
