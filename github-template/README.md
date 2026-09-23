# OpenResearchWorkspace Template

**Minimal GitHub template for creating a researcher-owned OpenResearchWorkspace (ORW) project.**

> [!IMPORTANT]
> **This repository is the GitHub template distribution, not the ORW software-development repository.**
> The canonical ORW specification, schemas, CLI, browser generator, validation logic, FAIR/RO-Crate tooling, tests, and development documentation live in [`dhuzard/OpenResearchWorkspace`](https://github.com/dhuzard/OpenResearchWorkspace).
>
> **This repository is generated from that canonical repository.** Maintainer changes to the GitHub template are made under [`github-template/`](https://github.com/dhuzard/OpenResearchWorkspace/tree/main/github-template) in the canonical repository, tested there, and then published here.


## Start here — no coding required

**You do not need to know Git, write code, use a terminal, edit YAML, understand branches, or open GitHub Actions.**

If you are a researcher who simply wants to create and use a project workspace, follow the click-by-click guide:

### [→ Create my first ORW project: beginner step-by-step guide](GETTING_STARTED.md)

The guide explains unfamiliar GitHub words when they first appear and shows what to click, what information to enter, what ORW creates for you, where to put your files, how to invite collaborators, and what not to upload to GitHub.


### Beginner workflow

1. Click **Use this template → Create a new repository**.
2. In your new repository, open **Issues → New issue → Set up my research project**.
3. Fill the short scientific setup form and submit it.
4. ORW initializes the workspace automatically; no terminal or Git commands are required.

## Which repository do I need?

| If you want to… | Use |
| --- | --- |
| Create a new research project on GitHub | **This repository: `OpenResearchWorkspace-template`** |
| Understand or implement the ORW specification | [`OpenResearchWorkspace`](https://github.com/dhuzard/OpenResearchWorkspace) |
| Develop the ORW CLI, browser generator, validator, FAIR/RO-Crate support, agents, or MCP integrations | [`OpenResearchWorkspace`](https://github.com/dhuzard/OpenResearchWorkspace) |
| Contribute to the minimal GitHub researcher workflow | [`OpenResearchWorkspace/github-template`](https://github.com/dhuzard/OpenResearchWorkspace/tree/main/github-template) |

## What this repository is

This repository is a **thin GitHub-specific adapter** for ORW. Its purpose is to let a researcher create a clean ORW-compatible workspace using GitHub's **Use this template** workflow without inheriting ORW's development source tree.

The intended flow is:

```text
OpenResearchWorkspace
canonical ORW specification + tooling
          │
          │ defines and validates
          ▼
OpenResearchWorkspace-template
minimal GitHub distribution
          │
          │ Use this template
          ▼
your-research-project
independent ORW workspace
```

A research project created from this template becomes **your independent workspace**. It is not a fork of the ORW development project and does not need to continuously merge changes from this template.

## Source-of-truth rule

The canonical ORW scientific model does **not** live here.

This repository must not independently redefine:

- Investigation → Study → Assay semantics;
- canonical metadata schemas;
- validation rules;
- FAIR or RO-Crate generation behavior;
- workspace mutation semantics;
- agent or MCP policy.

Those belong in [`OpenResearchWorkspace`](https://github.com/dhuzard/OpenResearchWorkspace). This published repository is generated output and should not be hand-maintained. Template source changes are made in the canonical repository, built and contract-tested there, then synchronized here.

## What should live here

After initialization, a researcher workspace remains intentionally small and researcher-facing, approximately:

```text
my-research-project/
├── README.md
├── studies/
│   └── study-01/
│       ├── data/
│       ├── assays/
│       ├── analysis/
│       ├── results/
│       └── protocols/
├── references/
├── project-docs/
├── .research/
└── .github/          # GitHub-specific setup adapter
```

It should contain only the workspace scaffold and the minimum GitHub-specific initialization machinery required for a researcher.

It should **not** contain ORW development internals such as `src/`, the browser application, the full test suite, package/release machinery, or a separate copy of the canonical specification.

## Status

The minimal GitHub setup adapter is now present here. It installs an immutable, pinned revision of the canonical ORW core during initialization, then uses that core to generate the researcher’s ISA-aligned workspace. Scientific generation logic is therefore not duplicated in this repository.

For the current ORW implementation and documentation, see [`dhuzard/OpenResearchWorkspace`](https://github.com/dhuzard/OpenResearchWorkspace).
