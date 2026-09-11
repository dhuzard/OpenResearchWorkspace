# OpenResearchWorkspace

**A research workspace specification with a GitHub template as its primary reference implementation.**

OpenResearchWorkspace (ORW) defines a portable format/contract for research workspaces that are **human usable, FAIR-oriented, machine readable, reproducible, and agent ready**.

The normal researcher does **not** fork ORW and does not use a central ORW application.

> **Use template → initialize project → collaborate → work → publish**

Each researcher or lab creates an independent repository from the ORW GitHub template. That repository becomes the canonical project workspace and remains owned by the researcher/lab.

GitHub is infrastructure, not the user model. Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or release mechanics to use the workspace.

## ORW uses the ISA Investigation–Study–Assay model

ORW adopts **ISA (Investigation, Study, Assay)** as the scientific organizational backbone rather than inventing a new experiment hierarchy.

ISA is an established metadata framework for life-science, environmental and biomedical experiments. Its three levels map naturally onto research practice:

- **Investigation** — the overall research project/context: objectives, people, publications and the studies that belong together.
- **Study** — a unit of research describing subjects/sources, study design, factors, treatments and protocols.
- **Assay** — a measurement or test performed on study material or subjects, including measurement/technology type, processing provenance and links to resulting data.

This matters for ORW because ISA already provides semantics for the relationships that ORW would otherwise have to invent: project → study → measurement, subjects/samples → processes → data, protocols, factors, technologies and ontology annotations. ISA also has established ISA-Tab and ISA-JSON serializations and an existing tooling ecosystem.

ORW therefore **uses ISA semantics as the scientific backbone while keeping the beginner interface simpler than ISA itself**. Researchers should see understandable project/study/assay concepts and forms; ORW infrastructure can generate or interoperate with ISA-compatible representations behind the scenes.

ORW does not equate a GitHub repository with an ISA Assay. The repository is the workspace/container. In the normal case, one ORW workspace represents one **Investigation**, containing one or more **Studies**, each containing one or more **Assays**.

See [`docs/isa.md`](docs/isa.md) for the rationale and mapping.

## Start here

If you are a researcher, begin with the step-by-step guide in [`docs/getting-started.md`](docs/getting-started.md) and the project skeleton in [`docs/project-structure.md`](docs/project-structure.md).

If you want to understand the architecture, read [`docs/concepts.md`](docs/concepts.md), [`docs/isa.md`](docs/isa.md), and [`SPEC.md`](SPEC.md).

## What ORW is

ORW has two distinct layers:

1. **Specification / contract** — defines what an ORW-compatible research workspace must expose and how core concepts are represented.
2. **Reference implementations** — practical ways to create or emit a conforming workspace.

The primary reference implementation is this GitHub template. Other software can produce ORW-compatible workspaces without using the template.

## Researcher-facing workflow

```text
Use this template
      ↓
Create my research repository (Investigation)
      ↓
Run first-time setup
      ↓
Describe the Investigation
      ↓
Add one or more Studies
      ↓
Add Assays/measurements where relevant
      ↓
Collaborate and work
      ↓
Publish when ready
```

A very simple project can still start with one Investigation, one Study and one Assay. Complexity is added only when the science requires it.

## Default scientific project skeleton

```text
my-research-project/                 # Investigation workspace
├── README.md
├── studies/
│   └── study-01/
│       ├── README.md
│       ├── data/
│       │   ├── raw/
│       │   ├── processed/
│       │   └── external/
│       ├── assays/
│       │   └── assay-01/
│       ├── analysis/
│       ├── results/
│       └── protocols/
├── references/
├── project-docs/
├── .research/
└── .github/
```

The hierarchy follows ISA: the workspace represents an Investigation; `studies/` contains its research units; `assays/` contains measurements/tests belonging to a Study. Analysis and results remain close to the Study they interpret, while Investigation-wide references and project documentation remain at the root.

See [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) for the normative definition.

## Core design principles

Every ORW-compatible workspace should be:

- **Human usable** — understandable without learning repository internals.
- **FAIR-oriented** — metadata, identifiers, and licensing are captured during the project rather than reconstructed only at publication.
- **Machine readable** — one canonical structured project description with ISA-aligned scientific semantics.
- **Reproducible** — subjects/samples, processes, assays, data, analyses and outputs can be related through provenance.
- **Agent ready** — AI systems can discover project context without reverse-engineering filenames or repository history.
- **Interoperable rather than bespoke** — ORW reuses ISA for experimental structure instead of defining a competing Investigation/Study/Assay model.

## Canonical machine-readable files

```text
.research/project.yml       canonical ORW project record, ISA-aligned
.research/workspace.yml     ORW implementation/version state
.research/capabilities.yml  optional capability activation
.research/layout.yml        folder roles and ISA/provenance semantics
.research/profiles.yml      initialization presets
```

Normal researchers should not need to edit these files directly once first-run setup exists. ISA-JSON and ISA-Tab should be treated as interoperable representations/exports rather than additional metadata that scientists must maintain manually.

## Project profiles

ORW uses one standard and one template, with initialization presets rather than separate template families. Profiles may simplify which folders are initially shown, but they must preserve the ISA hierarchy when experimental Studies and Assays exist.

## Repository contents

- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) — canonical ISA-aligned scientific project skeleton.
- [`docs/project-structure.md`](docs/project-structure.md) — researcher-facing explanation of the skeleton.
- [`docs/isa.md`](docs/isa.md) — why ORW adopts ISA and how the mapping works.
- [`docs/getting-started.md`](docs/getting-started.md) — step-by-step researcher guide.
- [`docs/concepts.md`](docs/concepts.md) — ORW concepts and architecture.
- [`docs/capabilities.md`](docs/capabilities.md) — FAIR, reproducibility, AI-ready, and agent-ready capability model.
- [`docs/faq.md`](docs/faq.md) — practical FAQ.
- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable project schema.

## Roadmap

**v0 — Self-initializing ISA-aligned GitHub template:** create Investigation, setup form, add Studies/Assays, collaboration, files/data references, metadata, publish/DOI.

**v1 — FAIR + ISA interoperability:** richer metadata, ontology annotations, ISA-JSON/ISA-Tab interoperability, persistent identifiers, DataCite export, RO-Crate, FAIR Signposting.

**v2 — Reproducible workspace:** ISA process/provenance links plus environments, workflows and automated QA.

**v3 — AI-ready workspace:** semantic project context, ISA-aligned entities, schemas, ontology mappings and explicit policies.

**v4 — Agentic workspace:** reusable provider-neutral skills plus thin agent adapters operating against the same project model.

## Non-goals

ORW is not intended to become a required central hosted application, require scientists to fork the ORW development repository, replace repositories designed for large scientific datasets, store sensitive research data on GitHub by default, prescribe a single archival or AI provider, or create a competing experimental metadata hierarchy where an established standard already exists.

## Status

Early specification and GitHub-template reference implementation design. **ISA Investigation–Study–Assay is now the required scientific organizational model.** The schema and reference implementation will continue to be tightened toward ISA interoperability while preserving the beginner-first UX.

## License

**OpenResearchWorkspace itself is MIT licensed.** This applies to the ORW software, template infrastructure, and reusable scaffolding in this repository; see [`LICENSE`](LICENSE).

Scientific projects created from the ORW template are independent projects and do **not** automatically inherit MIT for their research outputs.
