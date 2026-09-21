# RO-Crate interoperability and export

OpenResearchWorkspace (ORW) uses **ISA Investigation–Study–Assay semantics as its scientific model** and treats **RO-Crate as an interoperability, packaging, and publication/export layer**.

RO-Crate is therefore **not** a second source of project truth that researchers maintain manually. The canonical editable scientific record remains:

```text
.research/project.yml
```

## Status

A validated attached-directory **RO-Crate 1.3 exporter is implemented** in the provider-neutral ORW core.

```bash
orw export my-study --format ro-crate --output dist/my-study-ro-crate
```

The exporter:

1. validates the source ORW workspace;
2. derives an RO-Crate graph from canonical ORW metadata;
3. copies eligible attached files into a temporary crate;
4. writes `ro-crate-metadata.json`;
5. validates the generated crate against the RO-Crate 1.3 base requirements implemented by ORW;
6. only then moves the completed crate to the requested output directory.

The first implementation creates a directory crate. ZIP/archive output remains a later addition.

## Supported baseline

ORW currently targets **RO-Crate 1.3**.

Generated metadata declares:

```json
{
  "@context": "https://w3id.org/ro/crate/1.3/context"
}
```

and the metadata descriptor declares conformance to:

```text
https://w3id.org/ro/crate/1.3
```

The implementation is intentionally version-specific so future RO-Crate versions can be added without changing the canonical ORW scientific model.

## Source-of-truth boundary

```text
.research/project.yml
        │
        │ canonical ORW/ISA-aligned scientific record
        ▼
   ORW validation
        │
        ▼
 deterministic export
        │
        ▼
ro-crate-metadata.json
+ selected attached files
+ external resource references
```

An exported `ro-crate-metadata.json` MUST NOT silently become the editable canonical copy of project metadata.

## Output

A minimal export contains:

```text
my-study-ro-crate/
├── ro-crate-metadata.json
├── README.md
└── .research/
    └── project.yml
```

Additional explicitly declared **open** local resources may also be copied into their workspace-relative paths.

The canonical `.research/project.yml` is preserved inside the crate so a consumer can identify the package as an ORW-derived research object and inspect the richer ISA-aligned source representation.

## Current mapping

### Investigation → Root Data Entity

The ORW Investigation maps to the RO-Crate Root Data Entity:

```json
{
  "@id": "./",
  "@type": "Dataset"
}
```

The exporter currently maps, when available:

- Investigation title → `name`;
- description → `description`;
- Investigation identifier → `identifier`;
- keywords → `keywords`;
- declared license → `license`;
- contributors → `author`;
- Studies, canonical metadata, README, and resources → `hasPart`;
- export date → `datePublished`.

At this stage `datePublished` records the date on which the crate package is emitted. It should not be interpreted as the scientific article/publication date.

### Contributors → Person

ORW contributors become `Person` contextual entities.

When an ORCID is available, its HTTPS URI is used as the entity `@id`:

```json
{
  "@id": "https://orcid.org/0000-0002-1825-0097",
  "@type": "Person",
  "name": "Alex Scientist"
}
```

### Studies and Assays

Studies and Assays remain explicit graph entities rather than being inferred from filenames or flattened away.

Current conservative mapping:

```text
Root Dataset
  hasPart
     ↓
Study Dataset
  hasPart
     ↓
Assay Dataset
```

Their ORW identifiers are retained through `identifier`.

This representation provides explicit graph nodes and hierarchy without claiming that generic schema.org Dataset types encode the full ISA meaning. The authoritative ISA-aligned semantics remain in `.research/project.yml`.

A future ORW RO-Crate Profile may introduce stronger profile-specific semantics after the mapping has been tested across a wider range of preclinical workspaces.

### Canonical metadata and README

The exporter always packages, when present:

- `.research/project.yml` as a File Data Entity;
- `README.md` as a File Data Entity.

### Local resources

Local resources are only automatically attached when both are true:

1. the canonical ORW resource has a local `path`;
2. its `access` is explicitly `open`.

Example:

```yaml
resources:
  - name: Open analysis table
    path: results/summary.csv
    access: open
```

The file is copied and represented as a File Data Entity.

A directory resource is copied recursively and represented as a Dataset Data Entity.

### Private, restricted, embargoed, or unknown resources

RO-Crate export must not turn metadata packaging into accidental data disclosure.

Local resource content is **not copied automatically** when access is:

- `private`;
- `restricted`;
- `embargoed`;
- `unknown`;
- absent/not explicitly `open`.

The resource remains represented in metadata, including its access status and known identifier/path/location, but its content is not placed in the attached crate.

This is a deliberate safety boundary rather than a statement that every RO-Crate must use this policy.

### External data

Resources with an absolute URI location are represented as external entities and are **not downloaded**.

For example:

```yaml
resources:
  - name: Deposited dataset
    location: https://example.org/datasets/123
    access: open
```

becomes an entity whose `@id` is the external URI.

Large or institutionally managed data can therefore remain at their authoritative location.

## Path and overwrite safety

For attached local resources, the exporter rejects:

- absolute filesystem paths;
- `..` path traversal;
- paths escaping the ORW workspace;
- symlinked resources or symlinks nested inside a packaged directory;
- recursive situations where the requested export destination lies inside a directory being packaged.

The exporter does not overwrite an existing destination by default.

Explicit replacement requires:

```bash
orw export my-study --format ro-crate --output dist/my-study-ro-crate --force
```

The replacement occurs only after a new crate has been successfully generated and validated in a temporary directory.

## Validation

The export pipeline has three validation layers.

### 1. ORW source validation

Before export, the normal provider-neutral ORW validator checks:

- canonical project YAML;
- ORW JSON Schema;
- declared Study/Assay/resource paths;
- identifier consistency;
- initialized workspace state;
- spec-version consistency.

If the source workspace is invalid, export stops before an output crate is created.

### 2. RO-Crate 1.3 base validation

ORW validates the generated graph for the base RO-Crate requirements relevant to its attached-directory exporter, including:

- the RO-Crate 1.3 context;
- flattened `@graph`;
- `@id` and `@type` on graph entities;
- exact `ro-crate-metadata.json` descriptor identifier;
- descriptor type `CreativeWork`;
- descriptor `about` relationship to the Root Data Entity;
- Root Data Entity type `Dataset`;
- ISO 8601 `datePublished`;
- local/fragment reference resolution;
- presence of attached local File/Dataset entities;
- reachability of attached Data Entities from the Root through `hasPart`.

Recommended metadata such as a missing license is reported as a warning rather than making the crate invalid.

This validator is **not presented as an independent exhaustive implementation of every RO-Crate recommendation**, nor as an ORW RO-Crate Profile validator. Its purpose is to deterministically validate the base constraints used by the ORW 1.3 exporter.

### 3. ORW mapping/golden tests

The test suite covers:

- one Study / one Assay;
- multiple Studies;
- multiple Assays;
- contributor with ORCID;
- no-Assay workspace;
- external-only resources;
- mixed attached + external resources;
- private local resources not being copied;
- URI encoding of local Data Entity identifiers;
- invalid source workspace refusal;
- destination overwrite protection;
- generated-crate validation.

A golden semantic fixture checks that the ORW → RO-Crate graph remains stable across implementation changes.

## CLI

```bash
orw export my-study \
  --format ro-crate \
  --output dist/my-study-ro-crate
```

The default source workspace is the current directory:

```bash
orw export --format ro-crate --output dist/crate
```

Current format support:

```text
ro-crate
```

Future export targets may include ISA-JSON, ISA-Tab, DataCite metadata, and repository-specific deposit packages while consuming the same canonical ORW model.

## ORW RO-Crate Profile

ORW **does not yet claim a dedicated RO-Crate Profile**.

A versioned profile should be introduced only after:

1. the mapping has been exercised across representative preclinical workspace types;
2. Study/Assay/process/data semantics have a stable representation;
3. profile requirements and versioning are documented;
4. independent consumers can identify the ORW semantics reliably;
5. profile-level validation is implemented and tested.

The current claim is narrower: ORW can emit a validated **RO-Crate 1.3 export** from its canonical workspace model.

## Non-goals of the current exporter

The current implementation does not:

- make RO-Crate the editable ORW project database;
- import arbitrary RO-Crates back into ORW;
- copy every workspace file automatically;
- copy restricted/private/embargoed content simply because it is referenced;
- fetch external resources;
- encode all future ISA process/provenance semantics;
- claim an ORW RO-Crate Profile;
- create ZIP archives yet.
