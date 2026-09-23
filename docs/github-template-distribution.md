# GitHub template distribution

`dhuzard/OpenResearchWorkspace-template` is a **generated distribution** of the canonical OpenResearchWorkspace repository. It is not an independent implementation and should not be used as a source of scientific ORW rules.

## Source of truth

The distribution is assembled from two kinds of source in this repository:

```text
OpenResearchWorkspace/
├── src/orw/templates/
│   ├── project.yml
│   ├── workspace.yml
│   ├── capabilities.yml
│   ├── layout.yml
│   └── profiles.yml
│
└── github-template/
    ├── README.md
    ├── GETTING_STARTED.md
    ├── .github/
    │   ├── ISSUE_TEMPLATE/
    │   └── workflows/initialize-project.yml
    └── scripts/
        ├── parse_setup_issue.py
        └── initialize_project.py
```

The first group is canonical ORW workspace metadata. The second group contains only GitHub-specific presentation and adapter code.

The published template repository must not define its own copy of scientific generation logic.

## Build

From the canonical repository:

```bash
python scripts/build_github_template.py \
  --output dist/github-template \
  --core-revision "$(git rev-parse HEAD)" \
  --force
```

The builder:

1. copies the GitHub-specific assets;
2. injects the exact canonical commit into the initialization workflow;
3. copies canonical `.research/*.yml` placeholders from `src/orw/templates/`;
4. writes `.research/template-source.yml`;
5. rejects development-only files such as `src/`, `tests/`, `browser/`, `docs/`, or `pyproject.toml`;
6. verifies that the generated canonical placeholders are byte-identical to their sources.

## Contract test

Run:

```bash
python -m unittest tests.test_github_template_distribution -v
```

The test suite builds a fresh distribution, checks the canonical files, runs the generated issue-form parser, initializes the generated template using the **local canonical ORW core**, and validates the resulting workspace.

This is deliberately stronger than testing copied files individually: the generated distribution must actually be able to become a valid ORW project.

CI runs the same contract in `.github/workflows/test-github-template.yml` and uploads the tested generated tree as an artifact.

## Drift check

If a checkout of the published template is available:

```bash
python scripts/build_github_template.py \
  --output dist/github-template \
  --core-revision "<published canonical revision>" \
  --force \
  --check-against ../OpenResearchWorkspace-template
```

Any manually edited or missing generated file causes a non-zero exit.

## Publishing

The workflow `.github/workflows/publish-github-template.yml` provides a controlled publication path.

It always:

1. runs the generated-template contract tests;
2. builds the template from the exact canonical commit;
3. uploads the generated tree for review.

When the workflow is launched with **publish = true**, it replaces the contents of `dhuzard/OpenResearchWorkspace-template` with that tested tree and commits the source canonical SHA.

Cross-repository publication requires the repository secret:

```text
ORW_TEMPLATE_SYNC_TOKEN
```

Use a fine-grained GitHub token restricted to `dhuzard/OpenResearchWorkspace-template` with **Contents: write** permission. The token is only needed for publication; generation and tests do not require it.

## Maintenance rule

Do not fix scientific behavior directly in `OpenResearchWorkspace-template`.

Instead:

```text
change canonical ORW source
        ↓
change GitHub adapter source if necessary
        ↓
build template
        ↓
run contract test
        ↓
review generated artifact
        ↓
publish generated tree
```

A researcher-created repository remains independent after initialization. Regenerating the template does not rewrite existing research projects.
