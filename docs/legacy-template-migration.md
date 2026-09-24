# Legacy GitHub template migration

OpenResearchWorkspace used the main development repository itself as the GitHub template before the dedicated `dhuzard/OpenResearchWorkspace-template` repository was created on 23 September 2026.

That split improved the architecture, but repositories created from the old combined template can carry development files and older initialization behavior. This document defines the compatibility boundary and the safe migration strategy.

## First principle

Do **not** delete or overwrite a legacy repository wholesale merely because it contains ORW development files. A researcher may already have added project-specific material.

Migration should distinguish:

1. unchanged ORW template/development artifacts;
2. initialized ORW scientific metadata;
3. researcher-created or edited content.

The current initializer therefore preserves unknown or user-editable files and only replaces recognized template placeholders.

## Legacy states

### A. Uninitialized repository from the old combined template

Typical signs:

- root `pyproject.toml`, `src/`, `tests/`, `browser/`, `docs/`;
- `.github/workflows/release-checks.yml`, `test-core.yml`, or `test-browser.yml`;
- `.research/project.yml` describing OpenResearchWorkspace itself;
- `.research/workspace.yml` with `initialized: false`;
- no `.research/initialized` marker.

The current core can initialize this state when invoked through a current compatible adapter.

Compatibility handling:

- the exact historical pre-`preferences:` `.research/workspace.yml` placeholder is recognized;
- current and known historical template placeholders are migrated rather than treated as user edits;
- existing `project-docs/README.md` and `references/README.md` are preserved instead of overwritten;
- a legacy-template notice is written to `.research/legacy-template-notice.md` when development-repository markers are detected.

For a disposable test repository, recreating it from `OpenResearchWorkspace-template` is simpler and preferred.

For a real research repository, use controlled migration and review the legacy notice.

## B. Pre-core initialized repository

The earliest GitHub initializer, used around 15–20 September 2026, wrote a metadata shape that predates the current provider-neutral generation contract.

Typical signs include:

- `.research/initialized` exists;
- `.research/project.yml` contains both a top-level `project:` object and an `investigation:` object whose Studies are nested inside it;
- Study/Assay identifiers are stored as `id` rather than the current canonical `identifier`;
- `.research/workspace.yml` may still say `initialized: false`.

Modern `orw validate` reports:

```text
legacy_template_format
```

for this case.

This state should **not** be silently rewritten. It needs an explicit metadata migration because scientific metadata are already present.

Until a dedicated migration command is implemented:

- preserve the repository;
- do not rerun first-time initialization;
- do not edit the YAML manually merely to make validation green;
- for disposable/demo projects, recreate from the current template;
- for real projects, migrate with a reviewed transformation from the legacy project record to the current canonical schema.

## C. Current-format workspace created from the old combined repository

Later pre-split repositories may already contain current-format `.research/project.yml` but still carry the entire ORW development tree.

They can be scientifically valid while remaining operationally noisy.

Review these inherited files:

```text
.github/workflows/release-alpha.yml
.github/workflows/release-checks.yml
.github/workflows/test-browser.yml
.github/workflows/test-core.yml
.readthedocs.yaml
pyproject.toml
MANIFEST.in
src/
tests/
browser/
docs/
schema/
examples/
capabilities/
CHANGELOG.md
REFERENCE_IMPLEMENTATION.md
SPEC.md
TEMPLATE_WORKFLOW.md
```

The development workflows are especially important. `release-checks.yml` runs on pushes to `main`; `test-core.yml` and `test-browser.yml` can also run when matching development paths change. These are ORW software-development CI jobs, not research-project workflows.

The current initializer detects this legacy signature and records it in:

```text
.research/legacy-template-notice.md
```

ORW does not automatically delete these files because a researcher may have edited or reused them.

## Root LICENSE caveat

The old combined repository also copied ORW's MIT software `LICENSE` into every project.

That file licenses the ORW software repository. It must **not** be interpreted automatically as the license of:

- research data;
- protocols;
- documentation;
- manuscripts;
- figures;
- other scientific outputs.

Review licensing intentionally before publication or sharing.

## Old root-level scientific folders

The combined template exposed root folders such as:

```text
data/
analysis/
results/
protocols/
```

The current researcher-facing model places scientific work under the relevant Study, with an Assay layer only when needed.

If a legacy project contains real researcher material in the old root folders, migrate it deliberately. Do not delete it.

If those folders contain only unchanged ORW guidance files, they are legacy template artifacts and can be removed after review.

## Post-initialization no-code actions

The dedicated current template includes Issue Forms for:

- Add another Study;
- Add a measurement / Assay;
- Register a data source;
- Add a contributor;
- Check my workspace.

Legacy GitHub repositories do not necessarily contain those forms.

The core therefore does **not** infer no-code actions merely from `provider: github`. The current GitHub adapter explicitly declares that capability. This prevents repaired legacy repositories from receiving README links to forms that do not exist.

### Short-lived post-split snapshots

During the transition on 23 September 2026, a repository could have been initialized with a README that mentioned the no-code actions before all of the corresponding Issue Forms and `project-actions.yml` workflow were present in that repository.

Detection is simple:

```text
README contains ?template=orw-add-study.yml
but
.github/ISSUE_TEMPLATE/orw-add-study.yml does not exist
```

or the Issue Form exists but `.github/workflows/project-actions.yml` does not.

Do not add only one missing file. The forms, handler script, project-actions workflow, and pinned core revision are an adapter set and should be upgraded together from one generated template revision.

## Repairing a failed disposable repository

Preferred route:

1. delete the disposable repository;
2. create a new repository from `dhuzard/OpenResearchWorkspace-template`;
3. submit the current **Set up my research project** form;
4. verify initialization;
5. run **Check my workspace**.

This tests the product that a new researcher receives now.

## Repairing a real uninitialized legacy repository

Do not replace the repository wholesale.

First establish which initializer generation it contains.

If `.github/workflows/initialize-project.yml` contains an `ORW_CORE_REVISION` pin, update the adapter/core as a coherent set.

If it has no core revision and invokes a bundled local `src/orw` or a standalone local initializer, it is a frozen pre-split adapter. Replacing only one file is unsafe because the Issue Form, parser, workflow and initializer are version-coupled.

Migrate these adapter files together from the current generated template:

```text
.github/ISSUE_TEMPLATE/
.github/workflows/initialize-project.yml
scripts/parse_setup_issue.py
scripts/initialize_project.py
```

Then submit a **new** setup form. Preserve all project-specific content and review the legacy-template notice.

## Compatibility policy going forward

The dedicated GitHub template is generated and contract-tested from the canonical repository.

Future compatibility changes should follow these rules:

- template placeholders may evolve, but exact known historical placeholders should have explicit migration support;
- scientific metadata already written by a previous ORW version must not be silently rewritten;
- human-authored files must not be overwritten simply because a newer scaffold would generate the same path;
- provider-specific UI features must be capability-declared, not inferred from a provider name;
- old template artifacts may be detected and warned about, but deletion must require high confidence or explicit user action;
- real E2E tests should always create a repository from the currently published dedicated template.
