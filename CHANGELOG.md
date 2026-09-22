# Changelog

## 0.1.0a1 — release candidate; not yet published

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
