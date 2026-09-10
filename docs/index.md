# OpenResearchWorkspace

**A simple, self-initializing research workspace built on an open specification.**

OpenResearchWorkspace (ORW) is designed for researchers who want a structured, durable project workspace without having to learn Git mechanics.

The normal workflow is intentionally simple:

```text
Use template → initialize project → collaborate → work → publish
```

The repository remains owned by the scientist or lab. ORW provides the format, structure, metadata contract, and optional capabilities around that repository.

::::{grid} 2
:gutter: 3

:::{grid-item-card} Start a project
:link: getting-started
:link-type: doc

Create a repository from the ORW template and initialize it with a short project setup flow.
:::

:::{grid-item-card} Understand ORW
:link: concepts
:link-type: doc

See how the specification, template, capabilities, and future agent support fit together.
:::

:::{grid-item-card} Add capabilities
:link: capabilities
:link-type: doc

FAIR, reproducibility, archival publication, AI-readiness, and agent-readiness are layered onto the same project.
:::

:::{grid-item-card} Questions
:link: faq
:link-type: doc

What ORW replaces, what it does not replace, and how it differs from a fork or a central web app.
:::

::::

## Core principles

ORW aims to make every workspace:

- **human usable**;
- **FAIR-oriented**;
- **machine readable**;
- **reproducible**;
- **agent ready**.

The canonical project metadata live in `.research/project.yml`, while implementation/version information and optional capabilities remain separate.

```{toctree}
:maxdepth: 2
:hidden:

getting-started
concepts
capabilities
AI_READY_WORKSPACE
faq
../SPEC
../REFERENCE_IMPLEMENTATION
../TEMPLATE_WORKFLOW
```
