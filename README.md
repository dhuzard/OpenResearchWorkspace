# OpenResearchWorkspace

**A portable research workspace specification with GitHub as one supported reference implementation.**

OpenResearchWorkspace (ORW) defines a portable format/contract for research workspaces that are **human usable, FAIR-oriented, machine readable, reproducible, and agent ready**.

ORW is **forge-agnostic by design**. A valid workspace does not require GitHub, GitLab, Git, or any central ORW service.

Two creation paths are implemented:

- the existing beginner-oriented GitHub template and setup form;
- a local `orw` CLI that creates and validates the same workspace without requiring Git or a hosted forge.

The browser generator remains the next beginner-facing portable interface.

> **Create workspace → collaborate/work wherever appropriate → validate → publish intentionally**

GitHub remains an adapter rather than part of the scientific format.

Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or GitHub Actions to use the workspace.

## What works today

| Capability | Status | Current implementation |
| --- | --- | --- |
| Portable ORW scientific model | **Implemented** | ISA-aligned `.research/project.yml` plus provider-neutral schemas/core |
| GitHub beginner setup | **Implemented** | Template + guided setup form + automatic initialization |
| Local workspace creation | **Implemented** | `orw init`, interactive or JSON/stdin-driven |
| Local validation | **Implemented** | `orw validate` with JSON Schema, path, relationship, and initialization checks |
| Machine-readable validation | **Implemented** | `orw validate --json` with stable exit codes |
| RO-Crate interoperability | **Implemented** | Validated RO-Crate 1.3 directory export with `orw export --format ro-crate` |
| Restricted-data protection during export | **Implemented** | Local content is attached only when explicitly marked `access: open`; restricted/private/embargoed resources stay metadata-only |
| Forge-independent use | **Implemented** | Core, CLI, validation, and export work without GitHub/GitLab/Git |
| Browser workspace generator | **Planned next** | Static local-first form + ZIP download, no account/backend required ([#23](https://github.com/dhuzard/OpenResearchWorkspace/issues/23)) |
| Intentional publish/DOI workflow | **Planned** | Validate → preview → explicit confirmation → archive/PID ([#3](https://github.com/dhuzard/OpenResearchWorkspace/issues/3)) |
| FAIR capability layer | **Planned** | CITATION.cff, DataCite, PID/license checks, FAIR Signposting, FAIR-readiness reporting ([#4](https://github.com/dhuzard/OpenResearchWorkspace/issues/4)) |
| Reproducibility/provenance | **Planned** | Environments, workflows, checksums, provenance, reproducibility reports ([#5](https://github.com/dhuzard/OpenResearchWorkspace/issues/5)) |
| AI-ready workspace model | **Planned** | Structured semantic context, authoritative-resource declarations, agent-readable constraints ([#6](https://github.com/dhuzard/OpenResearchWorkspace/issues/6)) |
| Agent Contract + portable Skill | **Planned** | Provider-neutral rules and data-steward skill ([#25](https://github.com/dhuzard/OpenResearchWorkspace/issues/25)) |
| Deterministic MCP operations | **Planned** | Constrained local ORW operations for agents; no unrestricted filesystem/shell access ([#26](https://github.com/dhuzard/OpenResearchWorkspace/issues/26)) |
| Agent-conformance benchmark | **Planned** | Test whether agents obey ORW data-management constraints ([#27](https://github.com/dhuzard/OpenResearchWorkspace/issues/27)) |
| Provider-specific LLM packaging | **Planned later** | Thin OpenAI/Anthropic/other adapters over the same contract + MCP layer ([#28](https://github.com/dhuzard/OpenResearchWorkspace/issues/28)) |

The distinction matters: **implemented** means the capability exists in the repository and is covered by automated tests; **planned** means the design direction exists but should not yet be described as available to users.

## What is coming next

The current implementation order is:

```text
DONE
  provider-neutral core
        ↓
  CLI init + validate
        ↓
  RO-Crate 1.3 export

NEXT
  static browser generator (#23)
        ↓
  richer FAIR / publication capabilities
        ↓
  reproducibility + provenance
        ↓
  AI-ready context
        ↓
  Agent Contract / Skill (#25)
        ↓
  deterministic MCP execution layer (#26)
        ↓
  agent-conformance benchmark (#27)
        ↓
  provider-specific packaging/adapters (#28)
```

The architectural rule remains the same throughout: **scientific rules live in the ORW specification/core; browser, forge, MCP, and LLM-provider integrations are adapters around the same canonical model.**

## Local CLI

The local CLI is now implemented for researchers, automation, and agents that do not want to depend on GitHub:

```bash
python -m pip install .
orw init my-study
orw validate my-study
orw export my-study --format ro-crate --output dist/my-study-ro-crate
```

Non-interactive initialization uses the same normalized setup contract as the GitHub adapter:

```bash
orw init my-study --config setup.json
orw validate my-study --json
```

The Python package is prepared but is **not yet published to PyPI**, so the installation command above refers to a local/downloaded ORW source release.

See [CLI usage](docs/cli.md).

## New project? Set it up here

If you are reading this README **inside a new repository that you just created from the ORW template**, use the setup form below:

### [→ Set up my research project](../../issues/new?template=orw-setup.yml)

The form asks for your project title, first Study, first measurement/Assay, data location, and a few optional metadata fields. After you submit it, ORW initializes the workspace automatically and replies when it is ready.

You do **not** need to open GitHub Actions, run code, install Git, or edit YAML.

> GitHub calls the setup form an **issue** and may label the final button **Create** or **Submit new issue**. In ORW this simply means sending the project setup form. It is closed automatically after successful initialization.

If you are viewing the **OpenResearchWorkspace development repository itself**, do not submit the setup form here. First use **Use this template** to create your own repository.

## ORW uses the ISA Investigation–Study–Assay model

ORW adopts **ISA (Investigation, Study, Assay)** as the scientific organizational backbone rather than inventing a new experiment hierarchy.

ISA is an established metadata framework for life-science, environmental and biomedical experiments. Its three levels map naturally onto research practice:

- **Investigation** — the overall research project/context: objectives, people, publications and the studies that belong together.
- **Study** — a unit of research describing subjects/sources, study design, factors, treatments and protocols.
- **Assay** — a measurement or test performed on study material or subjects, including measurement/technology type, processing provenance and links to resulting data.

This matters for ORW because ISA already provides semantics for the relationships that ORW would otherwise have to invent: project → study → measurement, subjects/samples → processes → data, protocols, factors, technologies and ontology annotations. ISA also has established ISA-Tab and ISA-JSON serializations and an existing tooling ecosystem.

ORW therefore **uses ISA semantics as the scientific backbone while keeping the beginner interface simpler than ISA itself**. Researchers should see understandable project/study/measurement concepts and forms; ORW infrastructure can generate or interoperate with ISA-compatible representations behind the scenes.

ORW does not equate a GitHub repository with an ISA Assay. The repository is the workspace/container. In the normal case, one ORW workspace represents one **Investigation**, containing one or more **Studies**, each containing one or more **Assays**.

See [`docs/isa.md`](docs/isa.md) for the rationale and mapping.

## Start here

If you are a researcher, begin with the step-by-step guide in [`docs/getting-started.md`](docs/getting-started.md) and the project skeleton in [`docs/project-structure.md`](docs/project-structure.md).

### Visual walkthrough

[▶ Watch the annotated setup walkthrough (WebM)](docs/assets/getting-started/orw-getting-started.webm)

The recording provides numbered instructions and highlights each GitHub control before it is used.

| Create a project from the template | Complete the guided setup form |
| --- | --- |
| ![The OpenResearchWorkspace template page with the Use this template button visible](docs/assets/getting-started/01-use-template.png) | ![The ORW setup form filled with example research-project values](docs/assets/getting-started/03-setup-form.png) |

![The initialized workspace showing its generated Study and Assay structure](docs/assets/getting-started/05-initialized-workspace.png)

If you want to understand the architecture, read [`docs/concepts.md`](docs/concepts.md), [`docs/isa.md`](docs/isa.md), and [`SPEC.md`](SPEC.md).

## What ORW is

ORW has two distinct layers:

1. **Specification / contract** — defines what an ORW-compatible research workspace must expose and how core concepts are represented.
2. **Reference implementations** — practical ways to create or emit a conforming workspace.

The currently implemented interfaces are the GitHub template adapter and the local `orw` CLI. Both target the same provider-neutral generation contract. The browser generator is planned as the next portable interface.

## Portable implementation architecture

ORW separates the scientific contract from the interface used to create a workspace:

```text
                    ORW specification
                           │
                           ▼
              canonical generation contract
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           ORW CLI    Browser generator  Forge adapter
              │            │            │
              └────────────┼────────────┘
                           ▼
                    ORW workspace
                           │
                           ▼
                  interoperability export
                           │
                           ▼
                       RO-Crate
```

The canonical scientific record remains `.research/project.yml`. GitHub-specific automation must not become a separate scientific implementation.

- [Portable CLI/browser architecture](docs/portable-implementations.md)
- [RO-Crate interoperability and export](docs/ro-crate.md)

The browser generator is planned as a static, local-first interface: fill the scientific form, preview the ISA structure, and download a workspace ZIP without requiring a Git provider account or server-side persistence. The CLI currently implements `orw init`, `orw validate`, and validated RO-Crate 1.3 export through `orw export --format ro-crate`.

## Researcher-facing workflow

```text
Use this template
      ↓
Create my research repository (Investigation)
      ↓
Click “Set up my research project”
      ↓
Fill a short form
      ↓
ORW initializes automatically
      ↓
First Study + first Assay are created
      ↓
Collaborate and work
      ↓
Publish when ready
```

A very simple project can start with one Investigation, one Study and one Assay. Complexity is added only when the science requires it.

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

Normal researchers should not need to edit these files directly. ISA-JSON and ISA-Tab should be treated as interoperable representations/exports rather than additional metadata that scientists must maintain manually.

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
- [`docs/portable-implementations.md`](docs/portable-implementations.md) — provider-neutral core, CLI, browser generator, and forge-adapter plan.
- [`docs/ro-crate.md`](docs/ro-crate.md) — RO-Crate interoperability/export design.
- [`docs/cli.md`](docs/cli.md) — local CLI installation, initialization, validation, JSON output, and exit codes.
- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable project schema.

## Roadmap

**Current foundation — implemented:** ISA-aligned canonical workspace model; provider-neutral generation core; GitHub setup adapter; `orw init`; `orw validate`; machine-readable validation; validated RO-Crate 1.3 directory export; shared contract/golden fixtures.

**Next — browser-first portability:** static local-first workspace generator with form validation, ISA structure preview, local ZIP download, and no required account/backend ([#23](https://github.com/dhuzard/OpenResearchWorkspace/issues/23)).

**V0 completion — scientist-facing project lifecycle:** simplify adding Studies/Assays, collaboration and file/data-reference workflows; add intentional publication/archive/DOI flow with validation, preview, and explicit confirmation ([#3](https://github.com/dhuzard/OpenResearchWorkspace/issues/3)).

**V1 — FAIR + interoperability:** richer metadata and ontology annotations; ISA-JSON/ISA-Tab interoperability; CITATION.cff/DataCite; persistent identifiers and licenses; FAIR Signposting/readiness; evaluate when the tested RO-Crate mapping is mature enough for a versioned ORW RO-Crate Profile ([#4](https://github.com/dhuzard/OpenResearchWorkspace/issues/4)).

**V2 — reproducibility + provenance:** environments, workflow/run records, checksums/manifests, experimental and computational provenance, data/version linkage, automated QA and reproducibility/readiness reports ([#5](https://github.com/dhuzard/OpenResearchWorkspace/issues/5)).

**V3 — AI-ready workspace:** explicit semantic relations, authoritative-resource declarations, ontology/schema mappings, context manifests, machine-readable policies and validation for AI-facing context ([#6](https://github.com/dhuzard/OpenResearchWorkspace/issues/6)).

**V4 — constrained agentic workspace:** provider-neutral Agent Contract + portable Skill ([#25](https://github.com/dhuzard/OpenResearchWorkspace/issues/25)); deterministic MCP operations ([#26](https://github.com/dhuzard/OpenResearchWorkspace/issues/26)); agent-conformance benchmarking ([#27](https://github.com/dhuzard/OpenResearchWorkspace/issues/27)); then thin provider-specific LLM packaging/adapters without moving canonical scientific rules into any one provider ([#28](https://github.com/dhuzard/OpenResearchWorkspace/issues/28)).

## Non-goals

ORW is not intended to become a required central hosted application, require scientists to fork the ORW development repository, replace repositories designed for large scientific datasets, store sensitive research data on GitHub by default, prescribe a single archival or AI provider, or create a competing experimental metadata hierarchy where an established standard already exists.

## Status

Early specification with a working GitHub-template adapter and provider-neutral local CLI. **ISA Investigation–Study–Assay is the required scientific organizational model.** Workspaces can now be created, validated, and exported as RO-Crate 1.3 directories without GitHub; the static browser generator remains planned for a no-install beginner path.

## License

**OpenResearchWorkspace itself is MIT licensed.** This applies to the ORW software, template infrastructure, and reusable scaffolding in this repository; see [`LICENSE`](LICENSE).

Scientific projects created from the ORW template are independent projects and do **not** automatically inherit MIT for their research outputs.
