# Capabilities

ORW uses one research workspace that can progressively gain capabilities. Researchers should not need to choose between separate templates such as “basic”, “FAIR”, “reproducible”, or “AI-ready”.

The same project evolves.

## Capability model

```text
Human-usable core
      ↓
FAIR capability
      ↓
Reproducibility + provenance
      ↓
AI-ready context
      ↓
Agent-ready skills and policies
```

Capabilities are declared separately from project metadata so that enabling a feature does not redefine the scientific project itself.

## Core

The core should always provide:

- project identity and description;
- contributors;
- resources and data references;
- outputs;
- related identifiers;
- a predictable project structure.

This is the minimum required for both humans and machines to understand the workspace.

## FAIR capability

Implemented ([guide](fair.md)):

- ORCID and other persistent identifiers, validated against their check digits;
- explicit licenses, declared separately for project, data, code and documentation;
- DataCite-compatible metadata, refused rather than invented when mandatory properties are missing;
- `CITATION.cff` generated from the canonical record;
- related identifiers using the DataCite relation vocabulary;
- a readiness report that names each gap and the command that closes it.

Still planned: archival repository linkage, FAIR Signposting, and a versioned ORW RO-Crate profile. RO-Crate export itself exists in the CLI and carries the declared project license.

The guiding principle is FAIR-by-design: metadata are captured during the project rather than reconstructed only at publication.

## Reproducibility capability

Planned elements include:

- environment declarations;
- workflow definitions;
- input/output provenance;
- versioned data references;
- reproducibility checks;
- explicit limitations and assumptions.

## AI-ready capability

AI-readiness means that an agent should not need to infer the meaning of the workspace from filenames alone.

The workspace can therefore expose:

- machine-readable data dictionaries;
- authoritative-resource declarations;
- explicit observational units;
- quality/qualification states;
- scientific context;
- read/write boundaries;
- semantic mappings where useful.

See {doc}`AI_READY_WORKSPACE`.

## Agent-ready capability

Agent-readiness adds operational instructions and reusable skills on top of AI-ready data and context.

The intended sequence is:

```text
Agent contract
→ skills
→ provider-specific adapters
→ evaluation
```

Scientific rules should remain provider-neutral. Provider files for systems such as Codex, Claude, or GitHub Copilot should mainly point agents toward the shared contract and skills rather than duplicating the scientific logic.

## Archival publication

Publishing is a capability, not the definition of the workspace.

A project may use Zenodo, a domain repository, an institutional repository, or another suitable archival system. ORW should record the relationship and persistent identifiers without prescribing a single provider.

## Future capability activation

A lightweight setup form or UI may eventually allow a researcher to enable capabilities without editing `.research/capabilities.yml` manually.

The repository remains the canonical workspace; the UI is only a helper around it.
