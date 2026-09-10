# Concepts

OpenResearchWorkspace is best understood as a **format/contract plus reference implementations**.

## ORW is a standard, not a central app

ORW defines what a research workspace should expose and how core concepts are represented. The primary reference implementation is a GitHub template.

```text
ORW specification
      │
      ├── GitHub template
      ├── external exporters/adapters
      ├── future lightweight UI
      └── future CLI/tools
              │
              ▼
        ORW-compatible workspace
```

The scientist's repository is the project instance. ORW is the standard and tooling around it.

## The canonical project model

Project metadata belong in:

```text
.research/project.yml
```

This file answers questions such as:

- What is this project?
- Who contributes?
- What data and resources exist?
- Where are they located?
- What outputs exist?
- Which persistent identifiers connect this project to other research objects?

Other formats should be generated from or synchronized with this canonical record wherever possible.

## Workspace metadata are separate

Implementation/version state belongs in:

```text
.research/workspace.yml
```

This prevents ORW implementation details from being mixed with scientific metadata.

A workspace can therefore say which ORW specification and template version created it while the scientific project metadata remain stable.

## Capabilities are layered

Optional functionality is recorded separately in:

```text
.research/capabilities.yml
```

This allows one project to progressively become more FAIR, reproducible, AI-ready, or agent-ready without being recreated from another template.

## Template creation is not forking

A normal researcher should use the GitHub template to create an independent repository.

They are not expected to merge changes from the ORW development repository. Future ORW upgrades should be handled as explicit workspace/schema migrations.

## Researcher-facing vocabulary

ORW should hide Git-specific terminology where it does not help scientists.

| Infrastructure concept | Researcher-facing concept |
| --- | --- |
| repository | project |
| commit | change |
| issue | task / discussion |
| release | published version |
| tag | version |
| CI check | project check |

## One scientific object, multiple representations

A mature ORW workspace may expose several representations of the same project metadata:

```text
.research/project.yml
       │
       ├── README / project overview
       ├── CITATION.cff
       ├── DataCite metadata
       ├── RO-Crate
       ├── FAIR Signposting
       └── agent context
```

The goal is to avoid asking researchers to maintain each representation independently.

## Human-first, machine-ready

The repository should remain understandable to a scientist while also being deterministic enough for software and AI systems to navigate.

That means the visible workflow can stay simple while structured metadata, provenance, validation, and agent policies remain available underneath.
