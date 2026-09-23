# Changelog

## Unreleased

Merged after `0.1.0a1` was published, so none of the following is in the
released package.

### Added

- Deterministic workspace mutation API (`orw.mutate`) with `add_study`, `add_assay`, `register_resource`, `add_contributor` and `update_project_metadata`, plus the `orw study add`, `orw assay add`, `orw resource add`, `orw contributor add` and `orw metadata set` commands. Every mutation supports `--dry-run` diff review and `--json` plans, refuses to start from a workspace that does not validate, detects identifier/path/name conflicts before writing, and rolls back if the result would not validate. Exit code `5` reports a conflict.
- Structural YAML editing (`orw.edit`) so mutations replace only the located span of `.research/project.yml`, preserving comments, key order, quoting style and line endings.
- FAIR capability layer (`orw.fair`): `orw fair report` explains FAIR gaps and the command that closes each one, `orw fair citation` generates `CITATION.cff`, and `orw fair datacite` generates DataCite metadata. All three are generated views over the canonical record, never a second metadata store.
- Explicit per-scope licensing (`orw license set project|data|code|documentation`) and validated related identifiers (`orw identifier add`) using the DataCite relation vocabulary read from the bundled schema.
- Persistent-identifier recognition, normalization and check-digit validation for ORCID, DOI, arXiv, Handle, ARK, URN, PMID, ISBN and URL. A mistyped ORCID is refused at entry rather than deposited later.
- `orw contributor add --orcid ... --fetch` reads the public ORCID record, refusing an identifier the registry does not know and filling `given_name` and `family_name` from it, which is what lets `CITATION.cff` record a person rather than an organization. Names passed explicitly win. An unreachable registry warns and records the contributor anyway, so working offline is never blocked. This is the only command that uses the network.
- A **Look up** button beside the browser generator's ORCID field confirms the identifier against the registry and offers back the public name, filling the name field only when it is empty. It is the page's only connection and it needs a click: filling in the form, reviewing it and downloading the ZIP still reach nothing.
- Investigation `publisher`, `publication_year`, `version` and `doi`, plus contributor `given_name`, `family_name`, `affiliation` and `email`, in the schema and in `orw metadata set` / `orw contributor add`.
- The declared project license and contributor name parts now reach the RO-Crate export.

### Safety fixes

- A `CITATION.cff` that ORW did not generate is never replaced without an explicit `--force`.
- DataCite export refuses to invent a publisher, a publication year or a creator; missing mandatory properties are reported and nothing is written.
- CLI output degrades unencodable characters to escapes instead of aborting on a legacy console encoding.

### Limitations

- The FAIR readiness report covers metadata ORW can see in the canonical record. It is not a FAIR certification, and passing every check does not make the science well described.
- Generating DataCite metadata is not depositing them. No network call is made and no DOI is minted; intentional publication remains a separate workflow.
- `orw init` and the browser check an ORCID's **shape** when generating a workspace, because both implement one generation contract expressed as a JSON Schema, and a check digit cannot be written as a schema pattern. The check digit is applied wherever the contract does not reach: by `orw contributor add`, by the browser's *Look up* button, and by `orw fair report` on any record whatever its origin.
- Checking an ORCID against the registry is the only networked operation in ORW, and it happens only when asked for: `--fetch` on the command line, or the *Look up* button in the browser, whose Content Security Policy permits `pub.orcid.org` and no other origin. Everything else — generating, validating, exporting and generating deposit metadata — reaches nothing.

## 0.1.0a1 — 2026-09-22

Published to PyPI and tagged `v0.1.0a1`. The command surface is `orw init`,
`orw validate` and `orw export`.

### Added

- Provider-neutral workspace generation, CLI initialization and validation, and RO-Crate 1.3 directory export.
- Standalone browser generator with local ZIP creation and Python/browser contract checks.
- Wheel/source-distribution smoke tests and a staged TestPyPI → public PyPI publishing workflow using the same verified artifacts.
- Software version in `src/orw/_version.py`; specification/template versions remain independent.

### Safety fixes

- Normal initialization refuses every nonempty destination, including unmarked scientific projects and existing README files.
- Explicit template initialization verifies the original placeholder metadata and preserves the previous overview and metadata in `.research/template-*` files.
- Export source/output trees must be disjoint, even with `--force`.
- Forced replacement requires a recognized, unchanged ORW export inventory. Added or edited files, symlinks/junctions, and legacy unmarked exports are not deleted.
- New export is validated in staging before replacement; the previous export is renamed aside and restored if final promotion fails.
- Open resource directories cannot silently include separately private/restricted/embargoed/unknown resources. Contradictory access declarations fail before copy.

### Limitations

- Evaluation alpha, not a complete OSF replacement or a FAIR certification.
- Use disposable copies and exclusive access during filesystem mutations; these guards are not a sandbox against malicious concurrent path substitution.
- Export metadata may contain sensitive names or locations. Inspect before sharing; access labels do not encrypt or control filesystem access.
- A new output directory is required for exports created before inventory markers were introduced.
