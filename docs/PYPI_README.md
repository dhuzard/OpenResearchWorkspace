# OpenResearchWorkspace — public alpha

A local-first toolkit for creating, evolving, validating, and exporting research workspaces. Git, a hosted forge, and an AI provider are not required. The canonical scientific record is `.research/project.yml`, organized around Investigation, Study, and Assay concepts.

## Install

Once the alpha is published:

```bash
pipx install openresearchworkspace==0.1.0a1
```

Alternatively, in a Python 3.10+ virtual environment:

```bash
python -m pip install openresearchworkspace==0.1.0a1
```

## Use

```bash
orw init my-study
orw validate my-study
orw validate my-study --json
orw export my-study --format ro-crate --output my-study-crate
```

Record the research as it grows, from inside the workspace:

```bash
orw study add "Sleep deprivation" --dry-run
orw study add "Sleep deprivation"
orw assay add "Open field" --study sleep-deprivation
orw resource add "Imaging archive" --location "Institutional store" --access restricted
orw contributor add "Ada Lovelace" --orcid 0000-0002-1825-0097
orw metadata set --status paused --keyword sleep
```

Each mutation refuses to start from a workspace that does not validate, detects conflicts before writing, changes only the lines it adds in `.research/project.yml`, and rolls back if the result would not validate. `--dry-run` shows the diff without writing; `--json` emits the same plan for scripts.

Automated initialization accepts the normalized setup contract through `--config setup.json` or `--config -` for standard input. Normal initialization requires a new or empty destination. Export destinations must be outside the source workspace. `--force` only replaces a previously marked ORW export whose files have not been added, removed, or changed.

## Browser path

The matching standalone HTML generator is distributed separately as a versioned release asset. Open it in a browser, describe the project, review the structure and metadata, and download a workspace ZIP. Python is not required by that browser path. The ZIP is not encrypted and exporting it does not publish anything.

## Alpha boundaries

This release is for evaluation on disposable copies. It is not a complete research-data repository, a security sandbox, or a guarantee of FAIR compliance. Initialization creates one Study and an optional first Assay; further Studies, Assays, resources and contributors are added with the mutation commands. Browser editing of existing workspaces, DOI deposition, richer provenance, and agent integrations remain planned.

RO-Crate output is a local package, not a publication. Base checks are bounded to the exporter; a dedicated ORW RO-Crate Profile is not claimed. Metadata and the project README are included, so inspect them for sensitive information before sharing. Only explicitly open local resources are copied; overlapping open/restricted declarations are refused. Metadata access labels are not filesystem permissions or encryption. Mutation operations require exclusive workspace access; concurrent or hostile filesystem mutation is outside the alpha's guarantees.

## Documentation and source

[CLI guide](https://github.com/dhuzard/OpenResearchWorkspace/blob/main/docs/cli.md) · [Browser guide](https://github.com/dhuzard/OpenResearchWorkspace/blob/main/docs/browser-generator.md) · [Release process](https://github.com/dhuzard/OpenResearchWorkspace/blob/main/docs/releases.md) · [Issues](https://github.com/dhuzard/OpenResearchWorkspace/issues)

The software is MIT licensed. Research outputs do not automatically inherit that license. ORW specification and template versions are independent of the software release version.
