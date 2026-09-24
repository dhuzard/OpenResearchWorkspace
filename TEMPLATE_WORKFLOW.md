# ORW GitHub template workflow

The researcher-facing GitHub template is distributed from the separate repository:

`dhuzard/OpenResearchWorkspace-template`

That repository is generated from the canonical ORW development repository. It is an initialization and GitHub-adapter distribution, not an independent scientific implementation.

## Source and distribution boundary

Canonical source:

```text
OpenResearchWorkspace/
├── src/orw/                 # scientific core
├── src/orw/templates/       # canonical template metadata
├── github-template/         # GitHub-specific forms, workflows and researcher docs
└── scripts/build_github_template.py
```

Published distribution:

```text
OpenResearchWorkspace-template/
├── README.md
├── GETTING_STARTED.md
├── .research/               # generated canonical placeholders
├── .github/                 # GitHub forms/workflows
└── scripts/                 # thin GitHub adapters
```

The template repository must not contain an independent copy of ORW scientific generation logic.

## Researcher sequence

```text
Use this template
      ↓
Create independent research repository
      ↓
Set up my research project
      ↓
Choose the simplest useful structure
      ↓
ORW creates the first Study
      ↓
Work in the existing Study
      ↓
Register authoritative data early
      ↓
Add Study / Assay only when scientifically needed
      ↓
Add contributors during the project
      ↓
Check workspace
      ↓
Share / archive / publish intentionally
```

## First-time setup

The current GitHub setup asks for:

- project title and short description;
- researcher name and optional ORCID;
- one Study versus several Studies;
- optional first Study title;
- whether distinct measurement types need an Assays layer;
- whether protocol documents should live in the workspace;
- authoritative/raw data location and access status;
- optional keywords.

The setup deliberately does **not** require a first Assay name.

These workspace-shaping choices are implementation preferences in `.research/workspace.yml`; they are not scientific claims in `.research/project.yml`.

## Progressive visible structure

A simple project may initialize as:

```text
README.md
studies/
└── my-study/
    ├── data/
    ├── analysis/
    ├── results/
    └── protocols/      # only when selected
references/
project-docs/
.research/
.github/
```

An `assays/` layer is created only when distinct measurement types need their own structure.

## Post-initialization no-code actions

The generated README links to GitHub Issue Forms for:

- Add another Study;
- Add a measurement / Assay;
- Register a data source;
- Add a contributor;
- Check my workspace.

Those forms are thin adapters over the same provider-neutral mutation and validation APIs used by the CLI.

The core must not infer these UI actions merely from `provider: github`; the current GitHub adapter explicitly declares that it contains them. This prevents broken links in legacy GitHub repositories.

## Compatibility

Repositories created before the dedicated template split may contain the entire ORW development repository, old workflows, old root-level scientific folders, and historical metadata placeholders.

The current initializer:

- accepts exact known legacy uninitialized workspace placeholders;
- preserves existing human guidance files such as `project-docs/README.md` and `references/README.md`;
- detects legacy development-repository markers and writes `.research/legacy-template-notice.md`;
- refuses to silently rewrite already-initialized pre-core scientific metadata.

See [Legacy GitHub template migration](docs/legacy-template-migration.md).

## Publication and synchronization

A research project created from the template becomes independent. It is not expected to merge changes from either ORW repository.

Template releases are generated and contract-tested in the canonical repository, then synchronized to `OpenResearchWorkspace-template`.

Existing research projects should receive future ORW changes through explicit migrations or optional tooling, not upstream template merges.
