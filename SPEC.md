# OpenResearchWorkspace Core Specification v0.1

Status: **Draft**

## 1. Product definition

OpenResearchWorkspace (ORW) is a workspace format/contract plus reference implementations. The specification defines what an ORW-compatible workspace is without requiring a particular hosting provider, UI, archive service or AI system.

ORW adopts the **ISA Investigation–Study–Assay abstract model as the normative scientific hierarchy for experimental research**. ORW MUST NOT redefine Investigation, Study or Assay with incompatible meanings.

## 2. ISA scientific model

For experimental projects:

- an ORW workspace normally represents one ISA **Investigation**;
- an Investigation contains one or more **Studies**;
- a Study contains zero or more **Assays**, with one or more expected when analytical measurements/tests are represented.

Investigation captures overall project context and grouping. Study captures study design, subjects/sources and samples, factors/treatments and protocols. Assay captures a measurement/test, measurement and technology type, relevant processing/protocol provenance and resulting data relationships.

ORW MAY support projects where Assay is not scientifically applicable (for example some literature or purely computational work). Implementations MUST NOT create scientifically meaningless Assays merely to satisfy a folder template.

## 3. Canonical project description

An ORW workspace has one canonical scientific project description:

```text
.research/project.yml
```

This record MUST preserve the Investigation → Study → Assay relationships. Human-facing documents, citation files, ISA serializations, repository metadata, archival metadata and agent context SHOULD be generated from or synchronized with the canonical record rather than independently maintained.

Implementation/lifecycle metadata MUST NOT be mixed into the scientific model; it belongs in `.research/workspace.yml`. Capability state belongs in `.research/capabilities.yml`.

## 4. ISA interoperability

ORW's scientific model SHOULD be capable of deterministic mapping to ISA concepts. ISA-JSON and ISA-Tab are interoperability representations, not additional sources of truth that ordinary researchers must manually maintain.

A future conforming ISA interoperability capability SHOULD provide validated export and import and SHOULD test semantic round trips where technically possible.

ORW-specific metadata outside ISA's scope MAY coexist with the ISA-aligned scientific model but MUST NOT alter ISA semantics.

## 5. Workspace layout semantics

The primary GitHub implementation maps the scientific hierarchy to:

```text
README.md                              # Investigation
studies/<study-id>/                    # Study
studies/<study-id>/assays/<assay-id>/ # Assay
references/                            # Investigation-wide scholarly context
project-docs/                          # Investigation-wide project context
```

Study and Assay folders MAY contain pragmatic workspace subfolders such as data, analysis, results and protocols. Paths are a human interface; canonical metadata MUST explicitly represent scientific relationships rather than relying only on folder inference.

Authoritative data MAY live outside GitHub and be referenced by location or persistent identifier.

## 6. Core entities

### `spec_version`
ORW specification version.

### `investigation`
The canonical overall scientific project context. It SHOULD support an identifier, title, description, contacts/contributors, publications, related identifiers and Studies.

### `studies`
Research units belonging to the Investigation. Each Study MUST have a stable workspace identifier and SHOULD describe design context, subjects/sources/samples, factors, protocols and Assays as appropriate.

### `assays`
Measurements/tests belonging to a Study. Each Assay SHOULD identify what is measured, the technology/method, relevant protocol/process context and associated data.

### `resources` and `outputs`
ORW MAY describe workspace resources and outputs not fully represented by ISA, including software, documentation, manuscripts, models and workflows. These MUST be related to the relevant Investigation, Study or Assay when scientifically applicable.

## 7. Provenance

ORW SHOULD progressively preserve ISA-compatible subject/sample/process/data relationships. A simplified conceptual flow is:

```text
Investigation
→ Study
→ subjects/sources/samples
→ processes + protocols + factors
→ Assay
→ data
→ analysis
→ results/publication
```

Source evidence SHOULD NOT be silently overwritten. Derived data and outputs SHOULD be traceable to their inputs and methods as reproducibility capabilities mature.

## 8. Profiles

Profiles are initialization conveniences, not alternate scientific models. Experimental and mixed profiles MUST preserve ISA hierarchy. Other profiles MAY use a meaningful subset and MUST NOT invent fake ISA entities.

## 9. Workspace lifecycle and capabilities

`.research/workspace.yml` records ORW implementation/version state. `.research/capabilities.yml` records optional capabilities such as archival publication, FAIR enrichment, reproducibility, AI-ready context or agent support.

Capabilities MUST NOT redefine ISA or Core semantics.

## 10. GitHub reference implementation

The intended workflow is:

```text
Use template
→ create Investigation workspace
→ first-time setup
→ describe Investigation
→ create initial Study
→ create Assay/measurement where applicable
→ collaborate/work
→ publish intentionally
```

The beginner UI SHOULD automatically create a sensible one-Investigation/one-Study structure and ask about Assays only in scientifically understandable language such as "What measurements or tests are you performing?".

## 11. Human interface

Implementations SHOULD NOT require ordinary researchers to understand Git, YAML, ISA-Tab, ISA-JSON, CI/CD, tags or GitHub Actions. ISA semantics should be captured through researcher-facing language and forms.

## 12. Publication

Publication MUST be intentional. Automated validation MAY determine readiness, but routine edits MUST NOT automatically create permanent scientific releases.

## 13. Extensibility and agent readiness

Extensions and agents MUST consume the canonical ISA-aligned project model rather than create parallel scientific truth. Agent-specific instructions are not part of Core v0.1, but agents should eventually be able to distinguish Investigation, Study, Assay, subjects/samples, processes, data and derived outputs explicitly.

## 14. Validation

A conforming project record MUST validate against `schema/project.schema.json`. The schema will evolve from the current draft toward stronger ISA alignment and validated ISA import/export. Until that mapping is complete, ORW MUST describe itself as ISA-aligned rather than claiming full ISA serialization conformance.