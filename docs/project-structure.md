# Project structure

ORW organizes experimental research using the established **ISA hierarchy: Investigation → Study → Assay**.

You do not need to learn ISA file formats to use ORW. The hierarchy simply gives clear names to three levels researchers already encounter:

- **Investigation** = your overall research project;
- **Study** = a coherent unit of research/experimental design inside that project;
- **Assay** = a measurement or test performed within a Study.

```text
my-research-project/                 ← Investigation
├── README.md
├── studies/
│   └── study-01/                    ← Study
│       ├── README.md
│       ├── data/
│       │   ├── raw/
│       │   ├── processed/
│       │   └── external/
│       ├── assays/
│       │   └── assay-01/            ← Assay
│       │       ├── data/
│       │       ├── analysis/
│       │       └── results/
│       ├── analysis/
│       ├── results/
│       └── protocols/
├── references/
├── project-docs/
├── .research/
└── .github/
```

## A concrete example

Imagine a project asking how light exposure changes mouse behaviour and physiology.

The **Investigation** is the overall project. A **Study** might be the controlled light-exposure experiment in one cohort. Its **Assays** might include home-cage behavioural tracking and ECG recording. A second Study could later test a different cohort or experimental design without mixing its subjects, factors and measurements with the first.

This is why ORW uses ISA rather than a single flat `data/analysis/results` tree: the flat structure becomes ambiguous as soon as a project contains several studies or measurement modalities.

## What belongs where

Study-level `data/` contains inputs shared across the Study or data that do not belong to one specific measurement. Assay-level data belong with the measurement that produced them when useful.

`analysis/` contains computational logic. Study-level analysis can integrate multiple Assays; Assay-level analysis can remain specific to one modality.

`results/` contains derived outputs and should remain traceable to the Study/Assay data and methods that generated them.

`protocols/` contains Study procedures and protocol references. Assays can additionally record measurement-specific protocols.

Root `references/` and `project-docs/` contain Investigation-wide scholarly context, decisions, notes and project history.

`.research/` contains machine-readable ISA-aligned ORW context. Most researchers should not edit it directly.

## Simple projects remain simple

A beginner does not need to design a complex hierarchy. ORW can initialize:

```text
My project
└── Main study
    └── Main measurement
```

Additional Studies and Assays are created only when scientifically needed.

## Data stored elsewhere

Large, sensitive, regulated or domain-specific data do not have to be stored on GitHub. ORW records their authoritative location or persistent identifier while keeping their Study/Assay relationship explicit.

## Why ISA matters

ISA is an established experimental metadata framework with defined ISA-Tab and ISA-JSON serializations and tooling. Reusing it gives ORW a mature model for project context, study design, subjects/samples, factors, protocols, measurements, technologies and sample-to-data relationships instead of inventing a competing ORW-specific model.

See [ISA in OpenResearchWorkspace](isa.md) for the rationale and technical mapping. For the normative structure, see `PROJECT_STRUCTURE.md`.