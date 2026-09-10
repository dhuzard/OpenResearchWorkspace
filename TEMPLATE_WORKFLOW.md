# ORW GitHub template workflow

The GitHub template is the primary way an ordinary researcher creates an OpenResearchWorkspace.

It is a bootstrap mechanism, not a long-term synchronization relationship with the ORW development repository.

## Before project creation

The template contains two layers:

```text
scientist-facing skeleton
├── data/
├── analysis/
├── results/
├── protocols/
├── references/
└── project-docs/

ORW infrastructure
├── .research/
├── .github/
├── schema/
└── capabilities/
```

The folder semantics are defined in `PROJECT_STRUCTURE.md` and `.research/layout.yml`.

## Project creation

The researcher selects **Use this template** and creates an independent repository.

Recommended ownership options include a personal GitHub account, laboratory organization, or institutional organization. The created repository is the canonical workspace for that project.

## First-run initialization

The repository should expose one obvious action:

> **Set up this research project**

The setup should ask only for information needed to initialize the workspace:

- title and short description;
- contributors and ORCIDs where available;
- keywords and project status;
- where authoritative data live;
- whether data are sensitive/restricted;
- licensing choices;
- project profile;
- optional capabilities.

### Project profile

The researcher should choose one initialization preset:

- Experimental / wet lab
- Computational / data analysis
- Mixed experimental + computational
- Literature / systematic review
- Other

Profiles are defined in `.research/profiles.yml`. They decide which parts of the canonical skeleton are useful at initialization; they do not create different ORW standards or redefine folder semantics.

The setup process then generates/synchronizes internal records:

```text
researcher form
      ↓
.research/project.yml
.research/workspace.yml
.research/capabilities.yml
.research/layout.yml
      ↓
project README + selected project skeleton
      ↓
later generated citation/archival/FAIR metadata
```

The same information should not need to be entered separately into several metadata files.

## Scientific skeleton

The default mixed project profile is:

```text
README.md
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
└── project-docs/
```

The intended provenance direction is:

```text
raw/external data → processed data → analysis → results → publication/archive
```

Raw source evidence should not be silently overwritten. External data may remain outside GitHub and be represented by links, identifiers, manifests, checksums, or access metadata.

## Workspace state

`.research/workspace.yml` tracks ORW implementation state, including the specification/template version and initialization status.

Once initialized, the research repository evolves independently from the ORW template. Researchers should not be expected to maintain a fork relationship, merge upstream template commits, or understand ORW's own Git history.

Future ORW tooling may inspect recorded versions and offer explicit workspace/schema migrations when needed.

## Capabilities

`.research/capabilities.yml` records optional functionality independently from the scientific project description. A project should not need a different template for each combination of features.

Examples include archival publication/DOI, FAIR enrichment, reproducibility/provenance, AI-ready context, and agent skills.

## Optional UI

A future lightweight UI may provide forms for initialization, metadata editing, capability activation, and publication.

The UI is a view/editor over the repository. It is not the authoritative project database. The repository remains usable without a central ORW service.
