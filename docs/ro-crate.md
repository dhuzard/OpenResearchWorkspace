# RO-Crate interoperability and export

ORW treats RO-Crate as a generated interoperability/package representation. The canonical editable scientific record remains **`.research/project.yml`**, organized using Investigation–Study–Assay semantics. Researchers should not maintain the generated `ro-crate-metadata.json` as a second source of truth.

## Implemented scope

The CLI and Python API create an attached RO-Crate 1.3 **directory**:

```bash
orw export my-study --format ro-crate --output my-study-crate
```

The output contains `ro-crate-metadata.json`, the canonical project record, the README when present, and eligible declared open local resources. External resources are referenced, not downloaded. ZIP export and arbitrary RO-Crate-to-ORW import remain unimplemented.

The metadata uses `https://w3id.org/ro/crate/1.3/context`. Its `CreativeWork` metadata descriptor references the Root Dataset through `about` and declares `conformsTo` using `https://w3id.org/ro/crate/1.3`.

Reference specification: https://www.researchobject.org/ro-crate/specification/1.3/

## Current mapping

| ORW source | RO-Crate representation |
| --- | --- |
| Investigation | Root Dataset `./` with name, description, identifier, keywords, declared license where available, and export date |
| Contributors | Person entities; an ORCID HTTPS URI is used as identifier when supplied |
| Studies | Explicit contextual Dataset entities linked from the root by `hasPart` |
| Assays | Explicit contextual Dataset entities linked from their Study by `hasPart` |
| Canonical project metadata / README | Attached File entities |
| Open local file / directory resources | Attached File / Dataset entities |
| External URI resources | Referenced Dataset entities; no network fetch |
| Non-open local resources | Metadata-only contextual entities, with recorded access status and known identifier/location |

Study and Assay identifiers and their hierarchy are preserved. Generic Dataset nodes do **not** encode all ISA semantics; the richer canonical source remains included. A dedicated ORW RO-Crate Profile is not yet claimed. Stronger semantics/profile validation require broader mapping evidence and stable profile requirements.

`datePublished` currently records when the crate package is emitted, not the date of a scientific paper. A fixed `date_published` argument in the Python API allows deterministic graph comparisons. No license is invented or inherited from the ORW software license.

## Access-aware attachment policy

A local resource needs a declared `path` and explicit `access: open` before its content can be attached:

```yaml
resources:
  - name: Open analysis table
    path: results/summary.csv
    access: open
```

Private, restricted, embargoed, unknown or absent access status keeps content out of the crate. An open directory conflicting with a separately non-open descendant is **refused**, as is an open child overlapping a non-open parent. Overlapping distinct open directory declarations are unsupported in this alpha; use non-overlapping resource paths.

These checks operate on declared metadata. They cannot identify sensitive content that was never labelled. A directory marked open authorizes its otherwise unclassified contents, so inspect it before export. Hard-link aliases and malicious concurrent filesystem changes are not a complete security boundary.

The canonical project record and README are included independently of raw-data attachment. They may contain names, internal locations or other sensitive metadata. **Review both before sharing.** Access labels are neither encryption nor filesystem access control, and exporting a crate does not publish it.

## Destination and overwrite safety in 0.1.0a1

Source and output trees must be **disjoint**, even with `--force`. A source folder, its ancestor, or any descendant cannot be an export replacement target. For the current workspace use an outside destination:

```bash
orw export . --output ../my-study-crate
```

Existing output is protected by default. Explicit `--force` can only replace a previous ORW export containing a matching `.orw-export.json` file/directory inventory. Added, modified or removed files cause refusal. Unrelated directories and unmarked exports from earlier versions require a new destination; do not delete research content to satisfy the guard.

The new crate is built in a fresh staging directory, validated, and checked for source changes. Only then is the previous unchanged export renamed aside and the new crate promoted. An ordinary promotion failure restores the previous export; an unexpected change to the backup preserves it instead of deleting it.

The marker is an accidental-overwrite guard, not a signature. Use exclusive workspace access and backups: this is not an OS sandbox, distributed lock, or crash-proof transaction. Ancestors of selected roots are canonicalized to support operating-system aliases; final workspace/output roots and attached resource components are checked for symlinks/junctions. Special files and reserved metadata/infrastructure payload paths are refused.

## Validation layers

**Source workspace validation:** YAML parsing, bundled ORW schema, declared local paths, Study/Assay relationships, identifiers and implementation-state consistency. Invalid input stops export before the destination is changed.

**Generated-crate checks:** the current validator checks the 1.3 context, flattened graph, unique identifiers and entity types, descriptor/root relation, Root Dataset/date, local reference resolution, attached local file/directory presence, and reachability through `hasPart`. Missing recommended metadata such as a project license is reported as a warning.

**Mapping and regression tests:** golden semantic graph comparisons plus ORCID, multiple Studies/Assays, no-Assay, external-only/mixed resources, non-open attachment refusal, encoded filenames, invalid input, overwrite protection, rollback and conflicting access declarations.

The built-in validator is bounded to the exporter. It is not advertised as an exhaustive independent implementation of every RO-Crate recommendation or an ORW Profile validator.

## Python API

```python
from orw import export_rocrate

result = export_rocrate("my-study", "my-study-crate", date_published="2026-09-22")
print(result.output, result.validation.valid)
```

The public export boundary is `orw.export_rocrate` / `orw.export.rocrate.export_rocrate`. The private `_rocrate_model` module contains the graph renderer and base checks; it is not a supported direct filesystem-write API.

## Planned extensions

RO-Crate archives, browser RO-Crate download, fuller ISA process/protocol/provenance mapping, stronger independently tested profile conformance, and controlled import are future capabilities. They must consume the same canonical ORW record rather than create duplicate editable metadata.
