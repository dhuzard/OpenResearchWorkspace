# OpenResearchWorkspace

**A portable research workspace specification with GitHub as one supported reference implementation.**

> **Software alpha preparation: `0.1.0a1`.** The browser, CLI, workspace mutation commands, FAIR outputs, validation and RO-Crate directory exporter are implemented. A preparation commit is not a published release: TestPyPI rehearsal and public PyPI promotion are separate, explicitly approved stages. See the [release guide](docs/releases.md) and [changelog](CHANGELOG.md).
>
> Evaluate on disposable copies. Ordinary initialization requires an empty destination. Export destinations must be outside the source workspace; `--force` only replaces an unchanged, identifiable ORW export. Metadata and the README can themselves be sensitive. These tools are not a FAIR certification, an OS sandbox, or a complete hosted research repository.

OpenResearchWorkspace (ORW) defines a portable format/contract for research workspaces that are **human usable, FAIR-oriented, machine readable, reproducible, and agent ready**.

ORW is **forge-agnostic by design**. A valid workspace does not require GitHub, GitLab, Git, or any central ORW service.

Three creation paths are implemented:

- a **static browser generator**: form → review → local workspace ZIP, with no account or installation;
- the beginner-oriented GitHub template and setup form;
- a local `orw` CLI for creation, validation, and RO-Crate export.

The browser is a portable static build, not a required hosted ORW service. A public hosted instance is not automatically deployed.

> **Create workspace → collaborate/work wherever appropriate → validate → publish intentionally**

GitHub remains an adapter rather than part of the scientific format.

Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or GitHub Actions to use the workspace.

## Browser generator — no account required

Open a **built** copy of the generator, describe your project, review the exact
folder tree and metadata, then download the workspace ZIP. Keep the `.research`
folder when extracting it. The ZIP contains scaffolding and entered metadata;
no research data are read or uploaded.

See the [browser guide](docs/browser-generator.md) for the researcher workflow
and distribution instructions. Maintainers build `dist/browser/index.html` with
`python scripts/build_browser.py` after installing the repository's Python
dependencies. That single file can be distributed directly or served from any
static host; researchers do not need Python or Node to use it.

**Current scope:** one Investigation, one Study, and an optional first Assay;
local schema checks, review confirmation, and ZIP download. Browser editing of
existing workspaces and browser RO-Crate download remain planned. Additional
Studies, Assays, resources and contributors can already be recorded with the
CLI (`orw study add`, `orw assay add`), and RO-Crate export already exists
there too.

## GitHub template: set up a new project

If you are reading this README **inside a new repository that you just created from the ORW template**, use the setup form below:

### [→ Set up my research project](../../issues/new?template=orw-setup.yml)

The form asks for your project title, first Study, first measurement/Assay, data location, and a few optional metadata fields. After you submit it, ORW initializes the workspace automatically and replies when it is ready.

You do **not** need to open GitHub Actions, run code, install Git, or edit YAML.

> GitHub calls the setup form an **issue** and may label the final button **Create** or **Submit new issue**. In ORW this simply means sending the project setup form. It is closed automatically after successful initialization.

If you are viewing the **OpenResearchWorkspace development repository itself**, do not submit the setup form here. First use **Use this template** to create your own repository.

The template adapter verifies the original placeholder scientific metadata before replacing them and preserves the old overview/metadata in `.research/template-*`. Edited or unrecognized metadata cause refusal, not silent reinitialization.

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

Choose the [browser guide](docs/browser-generator.md) for local ZIP creation, the [GitHub setup guide](docs/getting-started.md) for the template workflow, or [CLI usage](docs/cli.md) for command-line automation. All use the same [scientific project structure](docs/project-structure.md).

### Visual walkthrough — GitHub path

[▶ Watch the annotated setup walkthrough (WebM)](docs/assets/getting-started/orw-getting-started.webm)

The recording provides numbered instructions and highlights each GitHub control before it is used.

| Create a project from the template | Complete the guided setup form |
| --- | --- |
| ![The OpenResearchWorkspace template page with the Use this template button visible](docs/assets/getting-started/01-use-template.png) | ![The ORW setup form filled with example research-project values](docs/assets/getting-started/03-setup-form.png) |

![The initialized workspace showing its generated Study and Assay structure](docs/assets/getting-started/05-initialized-workspace.png)

For the architecture, read [`docs/concepts.md`](docs/concepts.md), [`docs/isa.md`](docs/isa.md), and [`SPEC.md`](SPEC.md).

## What ORW is

ORW has two distinct layers:

1. **Specification / contract** — defines what an ORW-compatible research workspace must expose and how core concepts are represented.
2. **Reference implementations** — practical ways to create or emit a conforming workspace.

The implemented interfaces are the browser generator, the GitHub template adapter, and the local `orw` CLI. They target the same canonical schemas and generation contract. Browser scaffolding is built from the Python core templates and checked against shared fixtures rather than maintained as a second scientific model.

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

The browser generator implements local form validation, structure/metadata review, and ZIP download without a Git-provider account or backend. The CLI implements `orw init`, `orw validate`, the workspace mutation commands (`orw study add`, `orw assay add`, `orw resource add`, `orw contributor add`, `orw metadata set`), and RO-Crate 1.3 directory export through `orw export --format ro-crate`. Browser RO-Crate download and a hosted deployment are not included in the browser MVP.

## GitHub researcher-facing workflow

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

## Local CLI

From an extracted ORW source directory:

```bash
python -m pip install .
orw init my-study
orw validate my-study
orw export my-study --format ro-crate --output my-study-crate
```

Non-interactive initialization uses the same normalized setup contract as the GitHub adapter:

```bash
orw init my-study --config setup.json
orw validate my-study --json
```

Research does not stop at creation. Studies, measurements, data references and people are recorded afterwards with provider-neutral mutation commands:

```bash
cd my-study
orw study add "Sleep deprivation" --dry-run   # show the exact diff, write nothing
orw study add "Sleep deprivation"
orw assay add "Open field" --study sleep-deprivation
orw resource add "Imaging archive" --location "Institutional store" --access restricted
orw contributor add "Ada Lovelace" --orcid 0000-0002-1825-0097
orw metadata set --status paused --keyword sleep
```

FAIR metadata are captured the same way, and the formats repositories expect are generated from them:

```bash
orw license set project CC-BY-4.0     # per-scope rights: project, data, code, documentation
orw identifier add 10.5281/zenodo.1234567 --relation IsSupplementTo
orw fair report                       # every gap, with the command that closes it
orw fair citation                     # generate CITATION.cff
orw fair datacite                     # the metadata a deposit would submit
```

Identifiers are validated, not just shape-matched: an ORCID that fails its check digit is refused. Generating a deposit payload is not depositing it — no network call is made and no DOI is minted. See the [FAIR guide](docs/fair.md).

Every mutation refuses to start from a workspace that does not validate, detects conflicts before touching the filesystem, preserves the rest of `.research/project.yml` byte for byte (including your comments and key order), and rolls the whole operation back if the result would not validate. `--json` emits the same plan for scripts and agents.

The `0.1.0a1` package is prepared; public-index availability must be established by the release workflow, not inferred from this README. After successful public publication, use `pipx install openresearchworkspace==0.1.0a1`.

**Write safeguards:** `orw init` rejects nonempty destinations. Mutation commands refuse duplicate identifiers, occupied folders and overlapping declared paths, and never overwrite a file a researcher has edited. Export source/output trees must be disjoint; when exporting `.` use an outside destination such as `../my-study-crate`. `--force` only replaces a recognized export whose inventoried contents have not changed. It never authorizes deletion of a source subdirectory or an unrelated folder. Exclusive workspace access is required during mutations.

See [CLI usage](docs/cli.md), the [FAIR capability layer](docs/fair.md) and [release instructions](docs/releases.md).

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
└── .github/                        # optional GitHub adapter; absent from browser ZIP
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
- **Interoperable rather than bespoke** — ORW reuses ISA for scientific hierarchy instead of defining a competing Investigation/Study/Assay model.

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
- [`docs/browser-generator.md`](docs/browser-generator.md) — browser workflow, static distribution, privacy boundary, and current limitations.
- [`docs/releases.md`](docs/releases.md) — alpha release checks, Trusted Publisher setup, TestPyPI rehearsal and public promotion.
- [`CHANGELOG.md`](CHANGELOG.md) — versioned changes and limitations.
- [`browser/README.md`](browser/README.md) — build and cross-language/browser testing instructions.
- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable project schema.

## What works today

| Capability | Status | Current implementation |
| --- | --- | --- |
| Portable ORW scientific model | **Implemented** | ISA-aligned `.research/project.yml` plus provider-neutral schemas/core |
| GitHub beginner setup | **Implemented** | Template + guided setup form + checked initialization with preserved originals |
| Local workspace creation | **Implemented** | `orw init`, interactive or JSON/stdin-driven; empty destination required |
| Local validation | **Implemented** | `orw validate` with JSON Schema, path, relationship, and initialization checks |
| Machine-readable validation | **Implemented** | `orw validate --json` with stable exit codes |
| RO-Crate interoperability | **Implemented** | RO-Crate 1.3 directory export with bounded base checks |
| Access-aware export | **Implemented** | Explicitly open local content attached; contradictory overlapping access declarations refused; metadata still needs review |
| Overwrite protection | **Implemented** | Source/output separation; inventory-protected replacement; regression tests |
| Forge-independent use | **Implemented** | Core, CLI, validation, and export work without GitHub/GitLab/Git |
| Browser workspace generator | **Implemented — static build** | Local form, schema checks, exact-file review, and ZIP download; shared core templates and fixtures ([guide](docs/browser-generator.md)) |
| Alpha packaging and staged publishing | **Prepared — publication separate** | Wheel/sdist tests, versioned browser asset, TestPyPI read-back and exact-artifact public promotion ([guide](docs/releases.md)) |
| Workspace mutation API and CLI | **Implemented** | `add_study`, `add_assay`, `register_resource`, `add_contributor`, `update_project_metadata` and the matching `orw study/assay/resource/contributor/metadata` commands, with `--dry-run` diffs, conflict detection and validated rollback |
| Browser editing and browser RO-Crate download | **Planned** | Current browser creates new workspaces only; use the CLI to edit an existing workspace or export RO-Crate |
| Intentional research publish/DOI workflow | **Planned** | Validate → preview → explicit confirmation → archive/PID ([#3](https://github.com/dhuzard/OpenResearchWorkspace/issues/3)); distinct from software package publishing |
| FAIR capability layer | **Partly implemented** | `orw fair report` (actionable gaps, not a score), `CITATION.cff` generation, DataCite metadata with refusal on missing mandatory properties, per-scope licensing, PID validation with check digits ([guide](docs/fair.md)). FAIR Signposting, ISA-JSON/ISA-Tab and a versioned RO-Crate profile remain planned ([#4](https://github.com/dhuzard/OpenResearchWorkspace/issues/4)) |
| Reproducibility/provenance | **Planned** | Environments, workflows, checksums, provenance, reproducibility reports ([#5](https://github.com/dhuzard/OpenResearchWorkspace/issues/5)) |
| AI-ready workspace model | **Planned** | Structured semantic context, authoritative-resource declarations, agent-readable constraints ([#6](https://github.com/dhuzard/OpenResearchWorkspace/issues/6)) |
| Agent Contract + portable Skill | **Planned** | Provider-neutral rules and data-steward skill ([#25](https://github.com/dhuzard/OpenResearchWorkspace/issues/25)) |
| Deterministic MCP operations | **Planned** | Constrained local ORW operations for agents; no unrestricted filesystem/shell access ([#26](https://github.com/dhuzard/OpenResearchWorkspace/issues/26)) |
| Agent-conformance benchmark | **Planned** | Test whether agents obey ORW data-management constraints ([#27](https://github.com/dhuzard/OpenResearchWorkspace/issues/27)) |
| Provider-specific LLM packaging | **Planned later** | Thin OpenAI/Anthropic/other adapters over the same contract + MCP layer ([#28](https://github.com/dhuzard/OpenResearchWorkspace/issues/28)) |

**Implemented** describes code and test coverage in this source tree, not maturity or certification. **Prepared** publishing infrastructure still needs account configuration, successful registry verification and approval. **Planned** capabilities are not yet user-available.

## What is coming next

```text
IMPLEMENTED
  provider-neutral core
        ↓
  CLI init + validate
        ↓
  RO-Crate 1.3 export
        ↓
  static browser generator (#23)
        ↓
  deterministic workspace mutation API + CLI
        ↓
  FAIR outputs: CITATION.cff, DataCite, readiness (#4)

RELEASE GATE
  0.1.0a1 safety + packaging checks
        ↓
  approved TestPyPI rehearsal
        ↓
  exact-artifact public alpha promotion
        ↓
  researcher pilot and feedback

LATER
  richer metadata editing / FAIR / research publication
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

## Roadmap

**Current foundation — implemented:** ISA-aligned canonical workspace model; provider-neutral generation core; GitHub setup adapter; `orw init`; `orw validate`; machine-readable validation; a deterministic workspace mutation API and its CLI commands; FAIR outputs (CITATION.cff, DataCite metadata, per-scope licensing, PID validation, readiness reporting); RO-Crate 1.3 directory export; static browser generator; shared contract/golden fixtures and browser acceptance tests.

**Alpha release — prepared:** address data-loss hazards, test wheel and source installations across supported operating systems, rehearse through TestPyPI, then promote the identical artifacts to public PyPI after explicit approval. A software release is not a research-data publication or a DOI workflow.

**Browser-first portability — implemented:** static local-first setup, ISA structure/metadata review, and ZIP download without an account/backend ([browser guide](docs/browser-generator.md)). Distribution and hosting are separate deployment choices, not automatic publication. Browser editing and browser RO-Crate download remain follow-ups.

**V0 completion — scientist-facing project lifecycle:** Studies, Assays, resources, contributors and metadata are now recorded through the deterministic mutation API; next come browser editing on top of that same API, collaboration and file/data-reference workflows; add intentional publication/archive/DOI flow with validation, preview, and explicit confirmation ([#3](https://github.com/dhuzard/OpenResearchWorkspace/issues/3)).

**V1 — FAIR + interoperability:** CITATION.cff, DataCite metadata, persistent identifiers, per-scope licensing and FAIR-readiness reporting are implemented ([guide](docs/fair.md)); richer metadata and ontology annotations, ISA-JSON/ISA-Tab interoperability and FAIR Signposting remain; evaluate when the tested RO-Crate mapping is mature enough for a versioned ORW RO-Crate Profile ([#4](https://github.com/dhuzard/OpenResearchWorkspace/issues/4)).

**V2 — reproducibility + provenance:** environments, workflow/run records, checksums/manifests, experimental and computational provenance, data/version linkage, automated QA and reproducibility/readiness reports ([#5](https://github.com/dhuzard/OpenResearchWorkspace/issues/5)).

**V3 — AI-ready workspace:** explicit semantic relations, authoritative-resource declarations, ontology/schema mappings, context manifests, machine-readable policies and validation for AI-facing context ([#6](https://github.com/dhuzard/OpenResearchWorkspace/issues/6)).

**V4 — constrained agentic workspace:** provider-neutral Agent Contract + portable Skill ([#25](https://github.com/dhuzard/OpenResearchWorkspace/issues/25)); deterministic MCP operations ([#26](https://github.com/dhuzard/OpenResearchWorkspace/issues/26)); agent-conformance benchmarking ([#27](https://github.com/dhuzard/OpenResearchWorkspace/issues/27)); then thin provider-specific LLM packaging/adapters without moving canonical scientific rules into any one provider ([#28](https://github.com/dhuzard/OpenResearchWorkspace/issues/28)).

## Non-goals

ORW is not intended to become a required central hosted application, require scientists to fork the ORW development repository, replace repositories designed for large scientific datasets, store sensitive research data on GitHub by default, prescribe a single archival or AI provider, or create a competing experimental metadata hierarchy where an established standard already exists.

## Status

Evaluation-alpha software with a working browser generator, GitHub-template adapter, and provider-neutral local CLI. **ISA Investigation–Study–Assay is the required scientific organizational model.** The browser provides no-install workspace creation; the CLI provides validation and RO-Crate directory export. No central hosted service, automatic research deposition/DOI workflow, or browser RO-Crate export is claimed. See the release workflow for actual registry publication status.

## License

**OpenResearchWorkspace itself is MIT licensed.** This applies to the ORW software, template infrastructure, and reusable scaffolding in this repository; see [`LICENSE`](LICENSE).

Scientific projects created from the ORW template are independent projects and do **not** automatically inherit MIT for their research outputs.
