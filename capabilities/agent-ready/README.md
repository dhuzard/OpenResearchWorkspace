# Agent-ready capability

Status: draft

This capability builds on an AI-ready OpenResearchWorkspace by adding bounded, reusable instructions for repository-aware agents.

## Principles

1. Scientific context is provider-neutral.
2. Source evidence and agent-derived outputs are separated.
3. Skills are task-specific and composable.
4. Skills must not redefine project metadata or scientific semantics.
5. Provider-specific instruction files are adapters, not independent sources of truth.
6. Agents must be able to determine what they may read, what they may modify, and what requires human approval.

## Recommended instruction hierarchy

```text
.research/project.yml
        ↓
context + machine-readable metadata
        ↓
AGENTS.md              # normative provider-neutral rules
        ↓
skills/*/SKILL.md      # bounded task procedures
        ↓
provider adapters      # optional compatibility files
```

## Skill contract

A skill SHOULD contain:

- `Purpose`
- `When to use`
- `Prerequisites`
- `Authoritative inputs`
- `Procedure`
- `Scientific constraints`
- `Forbidden assumptions`
- `Writable outputs`
- `Required provenance`
- `Human approval gates`

## Evidence policy

A compliant workspace SHOULD declare source evidence as read-only for agents and provide a designated writable area for derived outputs.

Recommended convention:

```text
source evidence -> read only
derived/        -> agent writable
```

Derived outputs SHOULD preserve:

- agent/provider identity where available;
- model/version where available;
- execution timestamp;
- inputs used;
- code or commands executed;
- output artifacts;
- limitations and unresolved assumptions.

## Initial generic skills

A minimal implementation may expose:

- `inspect-project`
- `check-data-quality`
- `summarize-evidence`
- `reproduce-analysis`
- `prepare-derived-analysis`

Domain-specific skills should be supplied as optional profiles rather than added to the Core specification.

## Human approval

Agents MUST NOT autonomously perform irreversible publication, overwrite source evidence, weaken access restrictions, or silently resolve scientific ambiguity. These operations require explicit human authorization.
