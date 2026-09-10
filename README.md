# OpenResearchWorkspace

**A research workspace specification with a GitHub template as its primary reference implementation.**

OpenResearchWorkspace (ORW) defines a portable format/contract for research workspaces that are **human usable, FAIR-oriented, machine readable, reproducible, and agent ready**.

The normal researcher does **not** fork ORW and does not use a central ORW application.

> **Use template → initialize project → collaborate → work → publish**

Each researcher or lab creates an independent repository from the ORW GitHub template. That repository becomes the canonical project workspace and remains owned by the researcher/lab.

GitHub is infrastructure, not the user model. Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or release mechanics to use the workspace.

## Start here

If you are a researcher, begin with the step-by-step guide in [`docs/getting-started.md`](docs/getting-started.md) and the project skeleton in [`docs/project-structure.md`](docs/project-structure.md).

If you want to understand the architecture, read [`docs/concepts.md`](docs/concepts.md) and [`SPEC.md`](SPEC.md).

## What ORW is

ORW has two distinct layers:

1. **Specification / contract** — defines what an ORW-compatible research workspace must expose and how core concepts are represented.
2. **Reference implementations** — practical ways to create or emit a conforming workspace.

The primary reference implementation is this GitHub template. Other software can produce ORW-compatible workspaces without using the template.

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
Work in a clear scientific project skeleton
      ↓
Publish when ready
```

## Default scientific project skeleton

ORW now defines a small, explicit day-to-day structure for research projects:

```text
my-research-project/
├── README.md
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
├── project-docs/
├── .research/
└── .github/
```

The semantics are deliberate: source/raw data are authoritative evidence; processed data are reproducibly derived; analysis contains computational methods; results contain derived outputs; protocols describe procedures; references capture scholarly context; and `project-docs/` records decisions, notes, rationale, and project history.

See [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) for the normative definition. The machine-readable mapping lives in [`.research/layout.yml`](.research/layout.yml), and initialization presets are declared in [`.research/profiles.yml`](.research/profiles.yml).

## Core design principles

Every ORW-compatible workspace should be:

- **Human usable** — understandable without learning repository internals.
- **FAIR-oriented** — metadata, identifiers, and licensing are captured during the project rather than reconstructed only at publication.
- **Machine readable** — one canonical structured project description plus stable workspace semantics.
- **Reproducible** — inputs, transformations, and outputs have clear roles and can be linked through provenance.
- **Agent ready** — AI systems can discover project context without reverse-engineering filenames or repository history.

## Canonical machine-readable files

```text
.research/project.yml       scientific project metadata
.research/workspace.yml     ORW implementation/version state
.research/capabilities.yml  optional capability activation
.research/layout.yml        folder roles and provenance semantics
.research/profiles.yml      initialization presets
```

Normal researchers should not need to edit these files directly once the first-run setup workflow exists.

## Project profiles

ORW uses one standard and one template, with simple initialization presets rather than separate template families:

- Experimental / wet lab
- Computational / data analysis
- Mixed experimental + computational
- Literature / systematic review
- Other

Profiles only decide which parts of the canonical skeleton are useful at initialization; they do not redefine folder semantics or create incompatible project types.

## Repository contents

- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) — canonical scientific project skeleton.
- [`docs/project-structure.md`](docs/project-structure.md) — researcher-facing explanation of the skeleton.
- [`docs/getting-started.md`](docs/getting-started.md) — step-by-step researcher guide.
- [`docs/concepts.md`](docs/concepts.md) — ORW concepts and architecture.
- [`docs/capabilities.md`](docs/capabilities.md) — FAIR, reproducibility, AI-ready, and agent-ready capability model.
- [`docs/faq.md`](docs/faq.md) — practical FAQ.
- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable project schema.
- [`REFERENCE_IMPLEMENTATION.md`](REFERENCE_IMPLEMENTATION.md) — scientist-facing GitHub template requirements.
- [`TEMPLATE_WORKFLOW.md`](TEMPLATE_WORKFLOW.md) — template initialization and lifecycle model.

## Roadmap

**v0 — Self-initializing GitHub template:** create, setup form, scientific skeleton/profile selection, collaboration, files/data references, metadata, publish/DOI.

**v1 — FAIR capability:** persistent identifiers, richer metadata, DataCite export, RO-Crate, FAIR Signposting.

**v2 — Reproducible workspace:** environments, workflows, provenance, and automated QA.

**v3 — AI-ready workspace:** semantic project context, schemas, ontology mappings, and explicit policies.

**v4 — Agentic workspace:** reusable provider-neutral skills plus thin Codex/Claude/Copilot adapters operating against the same project model.

## Non-goals

OpenResearchWorkspace is not intended to become a required central hosted application, require scientists to fork the ORW development repository, replace repositories designed for large scientific datasets, store sensitive research data on GitHub by default, prescribe a single archival or AI provider, or require researchers to maintain redundant metadata formats.

## Status

Early specification and GitHub-template reference implementation design. The canonical scientific project skeleton is now explicit; the self-initializing setup workflow that selects a profile and writes project metadata remains part of the v0 implementation backlog.

## License

**OpenResearchWorkspace itself is MIT licensed.** This applies to the ORW software, template infrastructure, and reusable scaffolding in this repository; see [`LICENSE`](LICENSE).

Scientific projects created from the ORW template are independent projects and do **not** automatically inherit MIT for their research outputs. Each project should explicitly choose licenses appropriate for its own code, data, documentation, manuscripts, figures, and other outputs.
