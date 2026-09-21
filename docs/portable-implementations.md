# Portable ORW implementations: core, CLI, browser, and forge adapters

## Objective

OpenResearchWorkspace should be usable without requiring GitHub, GitLab, Git, or any hosted forge.

The target architecture separates:

1. the **ORW specification and canonical project model**;
2. a **provider-neutral generation/validation/export core**;
3. researcher-facing interfaces such as a **CLI** and **browser generator**;
4. optional forge adapters such as GitHub Actions.

GitHub remains a supported reference deployment, but it must not define what an ORW workspace is.

## Architectural principle

```text
                    ORW specification
                           │
                           ▼
             canonical schemas + generation contract
                           │
                 ┌─────────┼─────────┐
                 │         │         │
                 ▼         ▼         ▼
              ORW CLI   Browser UI  GitHub adapter
                 │         │         │
                 └─────────┼─────────┘
                           ▼
                    ORW workspace
                           │
                  ┌────────┼────────┐
                  ▼        ▼        ▼
               validate   export   collaborate
                           │
                           ▼
                        RO-Crate
```

The same user input must produce semantically equivalent workspaces regardless of interface.

## Existing code to reuse

The current implementation already contains useful generator logic in:

```text
scripts/initialize_project.py
scripts/parse_setup_issue.py
.github/workflows/initialize-project.yml
.github/ISSUE_TEMPLATE/orw-setup.yml
```

The important refactor is to move workspace generation out of environment-variable-driven GitHub automation into a callable, testable core.

## Phase 1 — Define a provider-neutral generation contract

Before implementing a CLI or browser UI, define one normalized setup payload.

Example:

```json
{
  "project_title": "Effects of light exposure on mouse activity",
  "project_description": "Study of altered light exposure and spontaneous activity.",
  "creator": {
    "name": "Jane Researcher",
    "orcid": "0000-0000-0000-0000"
  },
  "first_study": {
    "title": "Light exposure study"
  },
  "first_assay": {
    "title": "Behaviour"
  },
  "data": {
    "location": "Institutional research server",
    "access": "private"
  },
  "keywords": ["behaviour", "circadian rhythm", "mouse"]
}
```

This input contract should be schema-validated and independent of GitHub fields such as `github_login`.

Provider-specific identity may be added as optional implementation metadata, not as required scientific metadata.

## Phase 2 — Extract ORW core

Refactor `scripts/initialize_project.py` into pure functions that accept structured input and an output directory.

Suggested target:

```text
src/orw/
├── __init__.py
├── model.py
├── initialize.py
├── validate.py
├── export/
│   └── rocrate.py
└── templates/
```

Conceptual API:

```python
from pathlib import Path
from orw.initialize import create_workspace

create_workspace(
    config=setup_config,
    destination=Path("my-study"),
)
```

Important properties:

- no dependency on GitHub environment variables;
- no implicit use of the current repository root;
- deterministic output;
- refusal to overwrite an initialized workspace unless explicitly allowed;
- validation before writing;
- clear machine-readable errors;
- unit-testable without network access.

The existing GitHub workflow should eventually call this same core.

## Phase 3 — Small CLI

### Minimum commands

```bash
orw init my-study
orw validate my-study
orw export my-study --format ro-crate
```

### `orw init`

Interactive mode:

```text
Project title:
Short description:
Your name:
ORCID (optional):
First study:
First measurement/assay:
Authoritative data location:
Data access [private/restricted/embargoed/open/unknown]:
Keywords:
```

Non-interactive mode should also be supported for automation:

```bash
orw init my-study --config setup.json
```

### `orw validate`

Return both human-readable and machine-readable output.

```bash
orw validate my-study
orw validate my-study --json
```

Exit status:

- `0`: valid;
- non-zero: validation failure.

### `orw export`

First target:

```bash
orw export my-study --format ro-crate --output dist/my-study-ro-crate
```

Later targets may include ISA-JSON, ISA-Tab, DataCite metadata, and repository-specific deposit packages.

### Packaging

The CLI should be installable using a standard Python distribution route, for example:

```bash
pipx install openresearchworkspace
```

The package name and publication target should be confirmed before release.

## Phase 4 — Browser generator for ordinary researchers

The browser generator should be a static, client-side application where possible.

### User journey

```text
Open ORW generator
      ↓
Fill simple scientific form
      ↓
Validate entries locally
      ↓
Preview Investigation / Study / Assay structure
      ↓
Create workspace
      ↓
Download .zip
```

Optional next actions:

```text
Download ORW ZIP
Download RO-Crate
Push to a supported forge
Save to institutional storage
```

Only the first two need to exist for the first browser release.

### Privacy target

Default behavior should require:

- no account;
- no Git provider;
- no server-side database;
- no persistence of entered metadata;
- no upload of user files to an ORW service.

Workspace generation should occur in the browser and produce a local download.

### Implementation choices

Two approaches are reasonable.

#### A. Static TypeScript/JavaScript implementation

Advantages:

- small deployment footprint;
- fast startup;
- easy ZIP generation;
- works on ordinary static hosting.

Risk:

- duplicates some generation logic from the Python core.

Mitigation:

- share JSON Schemas, templates, and golden input/output fixtures;
- require contract tests against the CLI output.

#### B. Run the Python core in the browser

For example, using a browser Python runtime.

Advantage:

- maximum code reuse.

Costs:

- larger initial download;
- more complex packaging;
- slower startup;
- more deployment/debugging complexity.

For ORW, approach **A** is the better first implementation unless contract drift becomes a real maintenance problem.

## Generation contract tests

The CLI, browser generator, and GitHub adapter should be tested against the same fixtures.

For each fixture:

```text
setup input
    ↓
expected project.yml
expected folder tree
expected README semantic fields
```

The test does not need byte-identical README formatting across interfaces, but canonical machine-readable output must match.

Initial fixtures:

1. basic experimental project;
2. multiple keywords + ORCID;
3. restricted external data;
4. assay omitted because it is not scientifically applicable;
5. unusual but valid Unicode project metadata;
6. invalid ORCID;
7. attempted overwrite of initialized workspace.

## GitHub becomes an adapter

The current GitHub setup remains useful.

Target workflow:

```text
GitHub issue form
      ↓
parse GitHub-specific form
      ↓
normalized ORW setup payload
      ↓
ORW core generator
      ↓
commit generated workspace
```

GitHub-specific code should only handle:

- permissions;
- issue/form parsing;
- repository checkout/commit/push;
- user feedback in GitHub.

It should not contain a separate scientific workspace implementation.

The same principle can later support GitLab, Forgejo/Codeberg, or institutional systems.

## Browser deployment should itself be portable

The browser generator should be buildable as static assets:

```text
dist/
├── index.html
├── assets/
└── ...
```

Those files could be hosted on:

- an ORW project website;
- GitHub Pages;
- GitLab Pages;
- Codeberg Pages;
- institutional web hosting;
- a local web server.

The application must not depend on the hostname on which it is served.

## Proposed delivery order

### Milestone A — Core extraction — implemented

- normalized setup schema;
- pure workspace generator;
- tests;
- GitHub workflow migrated to core.

### Milestone B — CLI MVP — implemented

- `orw init`;
- `orw validate`;
- installable Python package metadata;
- non-interactive JSON/stdin setup;
- machine-readable validation reports;
- installed-command E2E test outside the source checkout.

The package is not yet published to PyPI; see `docs/cli.md`.

### Milestone C — RO-Crate export — implemented

- ORW → RO-Crate 1.3 mapping;
- `orw export --format ro-crate`;
- source-workspace and generated-crate validation;
- conservative access-aware attachment policy;
- representative and golden mapping fixtures.

A dedicated ORW RO-Crate Profile remains a later step after broader mapping evidence.

### Milestone D — Browser generator

- static form;
- local validation;
- structure preview;
- ZIP download;
- contract tests against CLI fixtures.

### Milestone E — Additional adapters

Only after the portable path works:

- GitLab;
- Forgejo/Codeberg;
- institutional deployment;
- direct repository/deposition integrations.

## Definition of success

ORW is genuinely forge-agnostic when all of the following are true:

1. a valid ORW workspace can be created without Git;
2. the same workspace can be created from CLI, browser, or GitHub;
3. `.research/project.yml` has the same semantics across implementations;
4. validation runs locally without a hosted service;
5. RO-Crate export runs locally;
6. deleting `.github/` does not make the scientific workspace invalid;
7. GitHub-specific metadata is optional and never required for scientific interpretation.
