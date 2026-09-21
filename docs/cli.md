# ORW command-line interface

The ORW CLI creates and validates research workspaces locally without requiring Git, GitHub, GitLab, or another hosted forge.

## Status

The CLI is implemented in the repository and packaged as the `orw` command.

The Python distribution metadata currently uses the provisional package name `openresearchworkspace`. The package has **not** been published to PyPI as part of this milestone, so do not assume `pipx install openresearchworkspace` is available from the public package index yet.

## Install from a local ORW source release

From an extracted ORW source directory:

```bash
python -m pip install .
```

For an isolated command-line installation with `pipx`:

```bash
pipx install .
```

After installation:

```bash
orw --version
```

## Create a workspace interactively

```bash
orw init my-study
```

ORW asks for:

- project title;
- short description;
- researcher name;
- optional ORCID;
- first Study title;
- optional first measurement/Assay;
- authoritative data location;
- data access level;
- optional keywords.

An Assay can be omitted when it is not scientifically applicable.

The resulting workspace uses the same provider-neutral generation core as the GitHub setup adapter.

## Create a workspace non-interactively

For CI, agents, scripts, or reproducible setup, provide the normalized JSON setup contract:

```bash
orw init my-study --config setup.json
```

Example:

```json
{
  "project_title": "Effects of light exposure on mouse activity",
  "project_description": "Study of altered light exposure and spontaneous activity.",
  "creator": {
    "name": "Jane Researcher",
    "orcid": "0000-0002-1825-0097"
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

The same contract can be streamed through standard input:

```bash
cat setup.json | orw init my-study --config -
```

This is the preferred interface for automation because it avoids interactive prompts.

## Validate a workspace

```bash
orw validate my-study
```

Validation currently checks:

1. the canonical `.research/project.yml` can be parsed as YAML;
2. project metadata validate against the ORW Core JSON Schema;
3. Study, Assay, and local resource paths declared in metadata exist;
4. declared paths are relative and do not escape the workspace;
5. an Assay path remains inside its parent Study path when both are declared;
6. Study identifiers are unique;
7. Assay identifiers are unique within each Study;
8. `.research/workspace.yml` is parseable and records an initialized workspace;
9. `.research/initialized` is present and consistent;
10. project/workspace specification versions agree;
11. the canonical project-record location remains `.research/project.yml`.

Validation does not require a `.git/` or `.github/` directory.

## Machine-readable validation

```bash
orw validate my-study --json
```

Example successful output:

```json
{
  "valid": true,
  "workspace": "/path/to/my-study",
  "issues": []
}
```

Invalid workspaces return structured issues:

```json
{
  "valid": false,
  "workspace": "/path/to/my-study",
  "issues": [
    {
      "code": "missing_declared_path",
      "message": "Declared workspace path does not exist: studies/study-01",
      "path": ".research/project.yml:studies[0].path"
    }
  ]
}
```

## Exit status

| Exit status | Meaning |
| --- | --- |
| `0` | command succeeded / workspace is valid |
| `1` | workspace validation failed |
| `2` | setup/configuration/input error |
| `3` | initialization refused because the workspace is already initialized |

These statuses are intended to be stable enough for CI and agent workflows.

## Relationship to the GitHub adapter

The two interfaces share the same core:

```text
GitHub setup form ─┐
                   ├─ normalized setup payload ─→ ORW core ─→ workspace
orw init ──────────┘
```

GitHub-specific logic handles permissions, form parsing, commits, and feedback. It does not define a separate scientific workspace model.

## Next CLI capability

The next planned command is the interoperability exporter:

```bash
orw export my-study --format ro-crate
```

That belongs to the RO-Crate implementation milestone rather than this CLI MVP.
