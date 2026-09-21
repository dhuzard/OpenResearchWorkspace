# RO-Crate interoperability and export

OpenResearchWorkspace (ORW) uses **ISA Investigation–Study–Assay semantics as its scientific model** and treats **RO-Crate as an interoperability, packaging, and publication/export layer**.

RO-Crate is therefore **not** a second source of project truth that researchers must maintain manually.

## Design rule

The canonical editable ORW project record remains:

```text
.research/project.yml
```

A conforming exporter derives an RO-Crate from that record, the workspace layout, and explicitly selected files/resources:

```text
ORW workspace
  │
  ├── .research/project.yml       canonical scientific record
  ├── studies/...                 human-facing research workspace
  ├── protocols/...
  └── other resources
          │
          ▼
   deterministic export
          │
          ▼
  ro-crate-metadata.json          generated interoperability metadata
          +
  selected files / references
          │
          ▼
   RO-Crate directory or archive
```

Researchers SHOULD NOT need to edit `ro-crate-metadata.json` directly.

## Supported baseline

The first ORW RO-Crate exporter SHOULD target **RO-Crate 1.3** and declare the supported version explicitly.

RO-Crate 1.3 is the current long-term release and Recommendation:

- specification: https://www.researchobject.org/ro-crate/specification/1.3/
- persistent specification URI: https://w3id.org/ro/crate/1.3
- profiles: https://www.researchobject.org/ro-crate/specification/1.3/profiles.html

The implementation SHOULD keep the RO-Crate target version configurable so that support for future versions can be added without changing ORW's canonical project model.

## Source-of-truth boundaries

| Concern | Canonical ORW representation | RO-Crate role |
| --- | --- | --- |
| Investigation / Study / Assay semantics | `.research/project.yml` using ISA-aligned ORW fields | exported graph representation |
| Researcher-facing folder structure | ORW workspace filesystem | files/directories represented as Data Entities when exported |
| Contributors and identifiers | ORW project metadata | mapped to contextual entities such as Person/Organization |
| External datasets | ORW resource/data records with location/PID | represented by resolvable identifiers/URLs without requiring duplication |
| Provenance | ORW ISA-aligned process/protocol relationships as capabilities mature | exported provenance/context where expressible |
| Publication package | not canonical during active work | RO-Crate directory/archive generated intentionally |

An RO-Crate export MUST NOT silently become the editable canonical copy of project metadata.

## Minimum v0.x export

The first exporter should be deliberately small and deterministic.

Given a valid ORW workspace, it SHOULD generate:

```text
export/
├── ro-crate-metadata.json
├── .research/
│   └── project.yml
├── README.md
└── <selected workspace files>
```

The generated RO-Crate metadata MUST include the required RO-Crate Metadata File Descriptor and Root Data Entity.

At minimum, the Root Data Entity SHOULD expose, when available:

- project title;
- description;
- keywords;
- persistent identifier;
- license;
- creators/contributors;
- creation/export date where appropriate;
- links to included or referenced research resources.

The export SHOULD preserve the original ORW canonical record inside the crate so that the package remains understandable as an ORW workspace export.

## Mapping strategy

The initial mapping should be conservative.

### Investigation

The ORW Investigation maps to the RO-Crate Root Data Entity representing the exported research object.

### Contributors

ORW contributors map to RO-Crate contextual entities, normally `Person`, with ORCID used as a persistent identifier when available.

### Studies and Assays

ORW Studies and Assays SHOULD be represented explicitly in the RO-Crate graph rather than flattened into filenames.

The exact type/property mapping must be documented and covered by golden-file tests before ORW claims a stable RO-Crate profile.

Until that mapping is stable, ORW should describe the exporter as an **RO-Crate 1.3 export** rather than claiming conformance to a dedicated ORW RO-Crate profile.

### Files and directories

Included files can be represented as RO-Crate Data Entities. The exporter SHOULD derive their relationships from ORW metadata and layout roles rather than from filename guessing alone.

### External data

Large, sensitive, regulated, or externally managed datasets do not need to be copied into the crate. ORW should export their PID, URL, access status, checksum/manifest information, and other metadata where available.

## ORW RO-Crate profile

A versioned ORW RO-Crate profile is a useful later milestone, but it should follow implementation evidence rather than precede it.

The profile should be introduced only after:

1. the ORW → RO-Crate mapping is documented;
2. multiple representative preclinical workspaces have been exported;
3. exported crates validate against RO-Crate requirements;
4. round-trip expectations have been explicitly defined;
5. consumers can reliably identify Investigation, Study, Assay, people, data, protocols, and outputs.

A future profile URI SHOULD be persistent and versioned as recommended by the RO-Crate profile specification.

## CLI interface

The planned command is:

```bash
orw export . --format ro-crate --output dist/my-study-ro-crate
```

Optional archive output may later be supported:

```bash
orw export . --format ro-crate --output dist/my-study-ro-crate.zip
```

The exporter MUST validate the ORW project before generating the crate unless the user explicitly selects a diagnostic/non-strict mode.

## Browser interface

The planned browser generator should expose the same export capability after workspace creation:

```text
Create workspace
      ↓
Preview generated structure
      ↓
Download ORW workspace ZIP
      ↓
Optional: Download RO-Crate export
```

No GitHub account, Git installation, or server-side persistence should be required for the default browser path.

## Validation

The RO-Crate exporter should have three validation levels:

1. **ORW validation** — canonical `.research/project.yml` and workspace rules.
2. **RO-Crate validation** — generated crate satisfies the supported RO-Crate specification.
3. **ORW mapping tests** — golden fixtures confirm that key ISA/ORW semantics are represented consistently in the graph.

Tests SHOULD include at least:

- one Investigation / one Study / one Assay;
- multiple Studies;
- multiple Assays;
- external data only;
- mixed local + external data;
- contributor with ORCID;
- restricted/private data references;
- workspace with no scientifically meaningful Assay.

## Non-goals for the first exporter

The first implementation does not need to:

- make RO-Crate the editable project database;
- support arbitrary RO-Crate → ORW import;
- copy all raw data into the package;
- encode every future provenance capability;
- define a mature ORW RO-Crate profile before the mapping is tested.

The priority is a deterministic, validated export from the existing ORW canonical model.
