# Project structure

ORW uses a small, predictable scientific skeleton so researchers, collaborators, software, and AI agents can understand a project without reverse-engineering filenames.

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

## What belongs where

`data/` contains scientific inputs and data products. Raw data are authoritative evidence and should not be silently overwritten. Processed data should be reproducible from documented inputs and methods. External data can remain outside GitHub when that is more appropriate; ORW records where they live.

`analysis/` contains the computational logic that transforms data. Use notebooks for exploratory/narrative work, scripts for reusable analyses, and workflows for reproducible pipelines.

`results/` contains derived scientific outputs such as tables, figures, and reports. These should remain traceable to the analysis and data that generated them.

`protocols/` contains experimental, acquisition, preprocessing, and procedural methods.

`references/` contains literature, citation exports, and stable identifiers for external scientific resources.

`project-docs/` contains decisions, notes, rationale, project history, data-management notes, and interpretation caveats.

`.research/` contains machine-readable ORW context. Most researchers should not need to edit it directly.

## Scientific provenance direction

```text
raw or external data
        ↓
processed data
        ↓
analysis
        ↓
results
        ↓
publication / archive
```

This direction is part of the project semantics, not just folder decoration.

## Project profiles

The same ORW standard supports several initialization presets:

- **Experimental / wet lab** — data, analysis, results, protocols, references, project documentation.
- **Computational / data analysis** — data, analysis, results, references, project documentation.
- **Mixed** — full default skeleton.
- **Literature / systematic review** — references, analysis, results, project documentation.
- **Other** — user-selected folders with the same ORW semantics.

Profiles reduce clutter; they do not create different ORW standards.

For the normative structure definition, see `PROJECT_STRUCTURE.md` in the repository root.