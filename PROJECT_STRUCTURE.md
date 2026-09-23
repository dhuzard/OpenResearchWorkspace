# OpenResearchWorkspace project structure

This document defines the recommended human-facing skeleton for an ORW research project. The scientific hierarchy is based on **ISA: Investigation → Study → Assay**.

## Normative mapping

- The ORW workspace/repository represents an **Investigation**.
- `studies/<study-id>/` represents a **Study**.
- `studies/<study-id>/assays/<assay-id>/` represents an **Assay**.

This is not merely a folder naming convention. ORW's machine-readable project model MUST preserve these relationships so that the workspace can interoperate with ISA representations and tools.

## Why ISA

ISA provides an established model for experimental metadata rather than forcing ORW to invent one. An Investigation captures the overall research context and groups Studies. A Study describes the subjects/sources, design, factors, treatments and protocols for a unit of research. An Assay describes a measurement/test, its technology and measurement type, processing provenance, and links to resulting data.

That hierarchy is a better scientific model than a flat `data/analysis/results` repository because the latter becomes ambiguous as soon as one project contains several cohorts, experiments, interventions, modalities or measurement technologies.

## Visible structure uses progressive disclosure

The canonical scientific model supports Investigation → Study → Assay, but the visible folder tree SHOULD expose only the layers the researcher currently needs.

A simple one-Study project may begin as:

```text
my-research-project/                    # Investigation
├── README.md
├── studies/
│   └── my-study/                       # Study
│       ├── README.md
│       ├── data/
│       │   ├── raw/
│       │   ├── processed/
│       │   └── external/
│       ├── analysis/
│       ├── results/
│       └── protocols/                  # only when protocols are kept here
├── references/
└── project-docs/
```

When a Study contains several distinct measurement types, an `assays/` layer can be added. ORW MUST NOT require researchers to invent an Assay merely to satisfy folder structure.

ORW infrastructure lives separately in `.research/` and `.github/`.

## Investigation level

The repository root provides context shared across the entire Investigation: title, description, contributors, publications, related identifiers, references, project-level decisions and the collection of Studies.

Investigation-wide material belongs in `references/` and `project-docs/`. Scientific data should normally be associated with a Study or Assay rather than placed ambiguously at the Investigation root.

## Study level

Each Study is a coherent unit of research. Its metadata should describe the design, subjects/sources and samples, characteristics, factors/treatments and protocols relevant to its Assays.

Study-level folders may include:

- `data/` — Study inputs or data references;
- `analysis/` — Study-level computational work;
- `results/` — outputs produced at Study level;
- `protocols/` — when protocol documents are intentionally kept in the workspace;
- `assays/` — only when distinct measurements/tests benefit from their own layer.

## Assay level

An Assay represents a measurement or test. Examples include behavioural tracking, microscopy, RNA sequencing, electrophysiology, mass spectrometry or a clinical measurement.

An Assay should record its measurement type, technology type, relevant protocol/process information and the data files or external data resources it produces.

Assay-local `data/`, `analysis/` and `results/` keep modality-specific material together when that improves clarity. A simple project does not need to populate every possible subfolder.

## Data semantics

Within a Study or Assay:

- `data/raw/` contains authoritative source data when appropriate to keep them in GitHub;
- `data/processed/` contains reproducibly derived data;
- `data/external/` contains manifests, links, checksums, access notes or references to data stored elsewhere.

Large, sensitive, regulated or discipline-specific datasets MAY remain outside GitHub. ORW records their authoritative location/PID rather than requiring duplication.

## Provenance direction

The conceptual scientific flow is richer than a simple folder pipeline:

```text
Investigation
    ↓
Study
    ↓
subjects / sources / samples
    ↓
processes + protocols + factors
    ↓
Assay / measurement
    ↓
data
    ↓
analysis
    ↓
results / publication
```

ORW should preserve enough structure to later express this through ISA-compatible metadata and more detailed provenance capabilities.

## Simple projects remain simple

ISA alignment must not make ORW harder for beginners. A small experiment can begin as:

```text
My project (Investigation)
└── Main study (Study)
```

An Assay layer is added only when distinct measurement types need separate scientific structure. The setup interface should prefer the simplest valid representation and let researchers add complexity when the design requires it.

## Profiles

Profiles remain convenience presets, but they MUST NOT replace or redefine ISA semantics. Experimental and mixed projects use Investigation → Study → Assay explicitly. Computational or literature projects may use the closest meaningful subset while retaining an Investigation-level project context; ORW should not invent fake assays when no assay exists.

## Design rule

ORW uses ISA for scientific hierarchy and stable semantics, while its folder structure remains a pragmatic human interface. ISA-JSON/ISA-Tab are interoperability targets, not files that ordinary researchers must manually maintain.