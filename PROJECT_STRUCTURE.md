# OpenResearchWorkspace project structure

This document defines the recommended human-facing skeleton for an ORW research project.

The goal is simple: a scientist should immediately understand where inputs, analyses, outputs, methods, and project context belong, while machines and AI agents can rely on stable semantics underneath.

## Default visible structure

```text
my-research-project/
├── README.md
├── data/
│   ├── README.md
│   ├── raw/
│   ├── processed/
│   └── external/
├── analysis/
│   ├── README.md
│   ├── notebooks/
│   ├── scripts/
│   └── workflows/
├── results/
│   ├── README.md
│   ├── tables/
│   ├── figures/
│   └── reports/
├── protocols/
│   └── README.md
├── references/
│   └── README.md
└── project-docs/
    └── README.md
```

ORW infrastructure lives separately in hidden or implementation-oriented locations such as `.research/` and `.github/`.

## Folder semantics

### `data/`
Scientific inputs and data products.

- `raw/` contains authoritative source data when it is appropriate to keep them in the repository. Raw data SHOULD NOT be silently edited in place.
- `processed/` contains data derived reproducibly from raw or external inputs.
- `external/` contains manifests, links, checksums, access notes, or small reference files for data stored elsewhere.

Large, sensitive, regulated, or discipline-specific datasets MAY remain outside GitHub. Their authoritative location should still be documented in the workspace.

### `analysis/`
Code and workflows that transform data into scientific results.

- `notebooks/` for exploratory or narrative computational work;
- `scripts/` for reusable analysis scripts;
- `workflows/` for pipeline definitions and reproducible execution logic.

If the project develops reusable software, a separate `src/` package MAY be added later. ORW does not require one by default.

### `results/`
Derived outputs produced by analysis.

- `tables/` for machine-readable result tables;
- `figures/` for plots and visual outputs;
- `reports/` for generated reports or summaries.

Results should be traceable to the inputs and analysis that generated them.

### `protocols/`
Experimental, acquisition, preprocessing, or procedural methods used by the project.

Protocols may be Markdown files, PDFs, links to repositories, or persistent identifiers. Whenever possible, record version or date information.

### `references/`
Literature, citation exports, bibliographies, and links to external scientific resources relevant to the project.

### `project-docs/`
Human project context that is not itself an input dataset or analysis result.

Typical content includes:

- decisions and rationale;
- meeting/research notes;
- methods development notes;
- data-management notes;
- interpretation caveats;
- project history.

## Provenance direction

The intended scientific flow is:

```text
raw/external data
       ↓
processed data
       ↓
analysis
       ↓
results
       ↓
publication/archive package
```

This direction should remain legible to both humans and software.

## Authority and mutability

By default:

- source/raw inputs are authoritative and SHOULD be treated as read-only evidence;
- processed data are derived and SHOULD be reproducible from documented inputs and methods;
- analysis code is editable project logic;
- results are derived outputs;
- `.research/` contains machine-readable project context, capability state, and provenance metadata.

AI/agent capabilities may later impose stricter read/write boundaries through an explicit agent contract.

## Profiles

ORW uses one template but may initialize different subsets of this skeleton according to project type.

Recommended profiles:

- `experimental` — data, analysis, results, protocols, project-docs, references;
- `computational` — data, analysis, results, project-docs, references;
- `mixed` — full default skeleton;
- `literature` — references, analysis, results, project-docs;
- `other` — user-selected structure with the same folder semantics.

Profiles are convenience presets. They MUST NOT redefine the meaning of the standard folders.

## Design rule

ORW should prefer a small number of stable, semantically clear top-level folders over discipline-specific folder proliferation. Domain-specific detail belongs inside the canonical folders or in optional capabilities/profiles.