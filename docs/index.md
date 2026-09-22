# OpenResearchWorkspace

**A portable research workspace built on an open specification.**

OpenResearchWorkspace (ORW) is designed for researchers who want a structured,
durable project workspace without having to learn Git mechanics.

Three creation paths are implemented: a static browser generator, the local CLI,
and the GitHub template/setup form. The browser build can be distributed as one
HTML file; a public hosted instance is not automatically deployed.

```text
Create workspace → review metadata → keep/work locally or collaborate → publish intentionally
```

The scientist or lab controls the workspace. ORW provides its format, structure,
metadata contract, and optional capabilities. ZIP creation and RO-Crate export
are local packaging operations, not publication or DOI issuance.

::::{grid} 2
:gutter: 3

:::{grid-item-card} Create in the browser
:link: browser-generator
:link-type: doc

Use a built static page to enter metadata, review the ISA structure, and download
a workspace ZIP without an account or installation.
:::

:::{grid-item-card} Use the local CLI
:link: cli
:link-type: doc

Create and validate workspaces locally; export a RO-Crate through the same core.
:::

:::{grid-item-card} GitHub setup guide
:link: getting-started
:link-type: doc

Create a repository from the ORW template and initialize it with a short form.
:::

:::{grid-item-card} Project structure
:link: project-structure
:link-type: doc

See where data, analyses, results, protocols, references, and context belong.
:::

:::{grid-item-card} Understand ORW
:link: concepts
:link-type: doc

See how the specification, implementations, capabilities, and planned agent support fit together.
:::

:::{grid-item-card} Capability roadmap
:link: capabilities
:link-type: doc

Distinguish the current foundation from planned FAIR, reproducibility,
publication, and agent capabilities.
:::

::::

## Core principles

ORW aims to make every workspace human usable, FAIR-oriented, machine readable,
reproducible, and agent ready. These are design goals, not automatic certification.

Canonical metadata live in `.research/project.yml`; implementation state, layout,
profiles, and optional capabilities remain separate.

## License

**ORW itself is MIT licensed.** Its software and reusable scaffolding are distinct
from the independent research projects created with it. Those projects should
choose licenses appropriate for their scientific outputs.

## Specification documents

The normative documents remain in the repository root: `SPEC.md`,
`PROJECT_STRUCTURE.md`, `REFERENCE_IMPLEMENTATION.md`, and `TEMPLATE_WORKFLOW.md`.

```{toctree}
:maxdepth: 2
:hidden:

browser-generator
cli
ro-crate
portable-implementations
getting-started
project-structure
concepts
capabilities
AI_READY_WORKSPACE
faq
```
