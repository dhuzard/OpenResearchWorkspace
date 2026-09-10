# OpenResearchWorkspace

**A simple research workspace for scientists — human usable, FAIR-oriented, machine readable, reproducible, and ready to evolve toward agentic science.**

OpenResearchWorkspace is designed as a lightweight, GitHub-backed replacement for the everyday collaborative project layer that many researchers used in OSF Projects.

The researcher-facing workflow is intentionally simple:

> **Create → Describe → Collaborate → Work → Publish**

GitHub is infrastructure, not the user model. Ordinary researchers should not need to learn Git, YAML, CI/CD, branches, tags, or release mechanics to use the workspace.

## Design principles

Every OpenResearchWorkspace should be:

- **Human usable** — understandable without learning repository internals.
- **FAIR-oriented** — metadata, identifiers and licensing are captured during the project, not reconstructed only at publication.
- **Machine readable** — one canonical structured project description.
- **Reproducible** — optional capabilities can describe environments, workflows and provenance.
- **Agent ready** — future AI systems can discover project context without reverse-engineering the repository.

## Architecture

The project separates three layers:

1. **Core specification** — what the research project *is*.
2. **Optional capabilities** — what the workspace *can do* (archival publication, RO-Crate, reproducibility, etc.).
3. **Agent skills** — what an AI agent can safely do with the project.

The canonical machine-readable record is:

```text
.research/project.yml
```

Human-facing documents, citation files, archival metadata and future agent context should be generated from or synchronized with that record rather than maintained independently.

## v0 goal

The first reference implementation is deliberately narrow:

```text
Create project
↓
Describe project
↓
Invite collaborators
↓
Add files and/or data links
↓
Work
↓
Publish a permanent citable version
```

The first usability test is simple:

> Can a scientist unfamiliar with Git create, understand, collaborate on, and publish a research project without reading Git documentation?

## Repository contents

- [`SPEC.md`](SPEC.md) — Research Workspace Core v0.1 draft specification.
- [`schema/project.schema.json`](schema/project.schema.json) — machine-readable JSON Schema.
- [`examples/minimal.project.yml`](examples/minimal.project.yml) — minimal example project record.
- [`REFERENCE_IMPLEMENTATION.md`](REFERENCE_IMPLEMENTATION.md) — requirements for the scientist-facing implementation.

## Roadmap

**v0 — Simple project:** create, collaborate, files/data references, metadata, publish/DOI.

**v1 — FAIR project:** persistent identifiers, richer metadata, DataCite export, RO-Crate, FAIR Signposting.

**v2 — Reproducible workspace:** environments, workflows, provenance and automated QA.

**v3 — AI-ready workspace:** semantic project context, schemas, ontology mappings and explicit policies.

**v4 — Agentic workspace:** reusable Codex/Claude/generic skills and scientific agents operating against the same project model.

## Non-goals for v0.1

OpenResearchWorkspace is not intended to:

- replace repositories designed for large scientific datasets;
- store sensitive research data on GitHub by default;
- prescribe a single archival provider;
- prescribe a single AI provider;
- require researchers to maintain redundant metadata formats.

## Status

Early specification and reference implementation design. Feedback and real-world research use cases are welcome.

## License

The specification and reusable scaffolding are released under CC0-1.0.
