# AGENTS.md — OpenResearchWorkspace (ORW)

## Repository responsibility
This is the **canonical ORW specification and reference-implementation repository**: ISA-aligned project model, source schemas, Python `orw` CLI, portable browser generator, validation, FAIR outputs and RO-Crate export. It is not a hosted service. `dhuzard/OpenResearchWorkspace-template` is a **generated GitHub delivery template**, not an independent scientific contract or implementation. Ordinary workspace instances are independent, version-pinned research projects.

## Read before editing
`SPEC.md`, `README.md`, `REFERENCE_IMPLEMENTATION.md`, `docs/github-template-distribution.md`, `docs/releases.md` and `docs/cli.md`.
- `src/orw/model.py`, `src/orw/schemas/`, `src/orw/templates/` own canonical ORW data and validation.
- `src/orw/initialize.py`, `edit.py`, `mutate.py`, `validate.py` own changes and safety.
- `src/orw/export/` owns RO-Crate packaging and output checks.
- `github-template/`, `scripts/build_github_template.py` generate the template distribution. Don't edit distributed template output as an independent authority.

## Non-negotiable behaviors
- Preserve Investigation–Study–Assay relationships and explicitly modeled resource provenance; never infer scientific meaning from folders alone.
- Refuse unsafe paths, symlink traversal, source/output overlap, destructive mutation and unvalidated changes. Keep dry-run, conflict detection and rollback semantics.
- Export to a separate destination. `--force` cannot justify overwriting unrelated content. RO-Crate export alone is not FAIR certification or publication/DOI minting.
- ORCID lookup is a user-controlled network operation; the default generation/export path must remain local-first. Never upload research content without explicit authorization.
- Respect alpha stability: breaking schema changes require a version/migration plan and contract/golden tests, including consistency among CLI, browser and template.

## Checks
```bash
python -m pip install -e . pytest
python -m pytest -q
python scripts/build_browser.py
```
Consult the actual CI workflow and tests for any further browser/template qualification; no distribution, release, template overwrite or publish action without explicit review.
