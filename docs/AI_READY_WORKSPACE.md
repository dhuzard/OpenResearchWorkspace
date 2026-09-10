# AI-ready workspace capability

Status: draft

This capability defines a provider-neutral way to package research outputs so that humans and repository-aware AI agents can understand the project without reconstructing scientific meaning from filenames alone.

It extends the OpenResearchWorkspace Core; it does not replace it.

## Objectives

An AI-ready workspace should make the following explicit:

- what the project is;
- which resources are authoritative;
- what the observational or experimental units are;
- how tables and identifiers relate;
- what quality or access constraints apply;
- what analyses are reproducible;
- what agents may read, derive, or modify;
- where derived outputs must be written.

## Recommended layout

```text
workspace/
├── README.md
├── AGENTS.md
├── .research/
│   ├── project.yml
│   ├── manifest.yaml
│   └── provenance.md
├── context/
│   ├── STUDY.md
│   ├── SCIENTIFIC_CONTEXT.md
│   ├── DATA_DICTIONARY.md
│   ├── QUALITY_AND_LIMITATIONS.md
│   └── REPRODUCIBILITY.md
├── metadata/
│   ├── data_dictionary.yml
│   └── quality_status.yml
├── data/
├── quality/
├── results/
├── config/
├── skills/
└── derived/
```

The human-readable Markdown documents SHOULD be generated from, or remain consistent with, machine-readable metadata wherever possible.

## Evidence boundary

A workspace SHOULD distinguish immutable or authoritative source evidence from agent-generated derivative work.

Recommended policy:

```text
source evidence: read-only
agent outputs:   derived/
```

The exact directories are implementation-specific, but the boundary MUST be machine-readable and documented for humans.

## Data dictionary

`metadata/data_dictionary.yml` SHOULD describe each machine-readable resource, including where applicable:

- path;
- role;
- observational/experimental unit;
- identity and key columns;
- column meanings;
- units;
- semantic role of identifiers;
- join/grouping constraints;
- known missingness semantics.

A JSON Schema for this metadata is provided in `schema/data_dictionary.schema.json`.

## Quality state

`metadata/quality_status.yml` SHOULD expose quality and qualification state in a form that agents can inspect before analysis.

The model intentionally separates dimensions such as:

- execution status;
- data/stream completeness;
- data quality;
- scientific qualification or acceptance.

These concepts MUST NOT be collapsed into a single generic PASS/FAIL field when they represent different evidence claims.

A JSON Schema is provided in `schema/quality_status.schema.json`.

## Agent instructions

`AGENTS.md` SHOULD be the provider-neutral normative contract when agent instructions are shipped with a workspace.

Provider-specific files such as IDE, model, or assistant instructions SHOULD be thin adapters pointing to the same canonical rules and project context rather than independent scientific specifications.

## Skills

Skills are optional capability modules that tell an agent how to execute a bounded task against the workspace.

A skill SHOULD declare:

- purpose;
- prerequisites;
- authoritative inputs;
- scientific constraints;
- forbidden assumptions;
- expected outputs;
- provenance requirements;
- writable locations.

Skills MUST NOT redefine the Core project model or silently alter source evidence.

## Reproducibility

AI-readiness is not satisfied by prose context alone. Where an agent is expected to reproduce or extend an analysis, the workspace SHOULD provide:

- executable or otherwise precise rerun instructions;
- software/environment information;
- version identifiers;
- input/output relationships;
- provenance sufficient to distinguish source evidence from derived output.

## Provider neutrality

The capability MUST NOT depend on a particular AI vendor. A compliant workspace should remain understandable even when no AI tooling is installed.

Provider-specific adapters MAY be added as optional modules.
