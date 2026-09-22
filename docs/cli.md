# ORW command-line interface

Create, validate and export research workspaces locally without requiring Git, GitHub or another hosted forge. This is the `0.1.0a1` evaluation alpha. A release-preparation commit is not proof of publication; see the [release process](releases.md).

## Install

From an extracted ORW source directory:

```bash
python -m pip install .
# Alternatively: pipx install .
orw --version
```

After the public alpha is actually published, the versioned package can be installed with `pipx install openresearchworkspace==0.1.0a1`. Python 3.10 or later is required. Browser users do not need to install Python.

## Create a workspace interactively

```bash
orw init my-study
```

The destination must be new or empty. An existing README, data, metadata, or any other content causes refusal without overwriting those files. There is no general initialization `--force` option. The explicit GitHub template adapter has a separate checked initialization path that preserves its original overview and placeholder metadata.

The questions cover project title, description, researcher name, optional ORCID, first Study, optional measurement/Assay, authoritative data location, access level and keywords. Leave the Assay blank when it is not scientifically applicable. Initial creation supports one Study and an optional first Assay; richer workspace editing remains planned.

## Create a workspace non-interactively

```bash
orw init my-study --config setup.json
```

Example normalized setup contract:

```json
{
  "project_title": "Effects of light exposure on mouse activity",
  "project_description": "Study of altered light exposure and spontaneous activity.",
  "creator": {"name": "Jane Researcher", "orcid": "0000-0002-1825-0097"},
  "first_study": {"title": "Light exposure study"},
  "first_assay": {"title": "Behaviour"},
  "data": {"location": "Institutional research server", "access": "private"},
  "keywords": ["behaviour", "circadian rhythm", "mouse"]
}
```

Use `"first_assay": null` for no Assay. JSON can also arrive through standard input:

```bash
cat setup.json | orw init my-study --config -
```

In PowerShell, `Get-Content -Raw setup.json | orw init my-study --config -` supplies the same contract. This is appropriate for scripts/agents; it does not bypass validation or overwrite rules.

## Validate a workspace

```bash
orw validate my-study
orw validate my-study --json
```

Validation parses canonical project YAML, applies the bundled ORW JSON Schema, checks declared paths, Study/Assay containment and identifier uniqueness, and checks initialized-state/spec-version consistency. No `.git` or `.github` directory is required. The report is not a FAIR certification or a complete scientific quality/security assessment.

Successful JSON report:

```json
{"valid": true, "workspace": "/path/to/my-study", "issues": []}
```

Failures contain `code`, `message` and, where available, `path` fields. Without a folder argument, `orw validate` checks the current directory.

## Record Studies, Assays, resources, contributors and metadata

A workspace grows after it is created. These commands are the supported way to record that growth; they write the canonical `.research/project.yml` through the same core functions the browser and future agent interfaces use, rather than editing YAML by hand.

```bash
orw study add "Sleep deprivation"
orw assay add "Open field" --study sleep-deprivation
orw resource add "Imaging archive" --type dataset --location "Institutional store" --access restricted
orw contributor add "Ada Lovelace" --role "Data analyst" --orcid 0000-0002-1825-0097
orw metadata set --status paused --keyword sleep --keyword mouse
```

Each command takes `--workspace DIR` (default: the current folder), `--dry-run` and `--json`.

### Review before writing

```bash
orw study add "Sleep deprivation" --dry-run
```

A dry run prints the exact unified diff that applying would write to `.research/project.yml`, followed by every folder and file it would create. Nothing is written. `--json` emits the same plan as a machine-readable object with `applied`, `operation`, `identifier`, `diff`, `new_directories` and `new_files` fields, which is the form an agent or another tool should consume.

### What each command records

| Command | Records | Creates on disk |
| --- | --- | --- |
| `orw study add TITLE` | An ISA Study in `studies` | `studies/<identifier>/` with the same layout `orw init` writes |
| `orw assay add TITLE --study ID` | An ISA Assay inside that Study | `<study path>/assays/<identifier>/` with its data, analysis and results folders |
| `orw resource add NAME` | An entry in `resources`, or in `outputs` with `--collection outputs` | Nothing; ORW records references, it does not copy research data |
| `orw contributor add NAME` | An entry in `contributors` | Nothing |
| `orw metadata set` | Investigation `title`, `description`, `status` or `keywords` | Nothing |

Identifiers double as folder names and default to a slug of the title; pass `--id` to choose one. Only lowercase letters, digits and single hyphens are accepted. `--path` overrides the default folder, and an Assay path must stay inside its Study path because the validator requires that containment.

`orw resource add` needs at least one of `--path` (an existing file or folder in the workspace), `--location` (data held elsewhere) or `--identifier` (a DOI or accession). A `--path` that does not exist is refused, because a declared path that is missing makes the workspace invalid.

`--keyword` replaces the whole keyword list, so repeat it once per keyword you want to keep; `--clear-keywords` records an empty list.

### Guarantees and refusals

Every mutation:

- **refuses to start** from a workspace that does not already validate, and prints the validation issues;
- **detects conflicts** before touching the filesystem — a duplicate Study or Assay identifier, a duplicate contributor name or ORCID, a duplicate resource name, a folder that already exists and is not empty, or a path that overlaps one the record already declares;
- **preserves the rest of the file byte for byte.** Comments, key order, quoting style and line endings you chose are kept; only the lines the operation adds or changes appear in the diff;
- **validates the result and rolls back** if it would not validate, restoring the record and removing the folders and files it had created.

Rollback assumes exclusive access to the workspace for the duration of the command. It recovers from an ordinary failure; it is not a filesystem transaction against another process writing at the same time. As everywhere else in ORW, evaluate on disposable copies during the alpha.

These commands do not rewrite `README.md`. The workspace overview belongs to its authors, so a renamed Investigation or a new Study is recorded in the canonical metadata and left for you to describe in prose.

## Export a RO-Crate directory

```bash
orw export my-study --format ro-crate --output my-study-crate
```

The source workspace is validated before export. `.research/project.yml` remains canonical and is preserved in the crate. Local resource content is attached only when explicitly declared open; external data are referenced rather than fetched. Metadata and README text may itself be sensitive: review before sharing.

**The destination must be outside the source workspace.** To export your current directory:

```bash
orw export . --format ro-crate --output ../my-study-crate
```

Only a recognized, unchanged previous ORW export can be replaced:

```bash
orw export my-study --format ro-crate --output my-study-crate --force
```

`--force` does not authorize deletion of a source subdirectory, unrelated directory, modified export or unmarked legacy export. The exporter inventories the previous output and stages/validates the new crate before promotion. On an ordinary promotion failure it restores the previous export. Exclusive workspace access is required; this is not a general concurrent or crash-proof filesystem transaction.

See [RO-Crate mapping and safety](ro-crate.md). ZIP RO-Crate output is not yet implemented; the browser ZIP is an ORW workspace, not a RO-Crate archive.

## Exit status

| Code | Meaning |
| --- | --- |
| `0` | Command succeeded / workspace valid |
| `1` | Workspace validation failed |
| `2` | Setup/configuration/input error, including a nonempty initialization destination |
| `3` | Initialization refused because the workspace is already initialized |
| `4` | Export failed for another reason, including a protected destination |
| `5` | A mutation conflicts with what the workspace already records |

## Interface and source-of-truth boundary

The browser, CLI and GitHub adapter use the same normalized setup contract and canonical model. Provider identity belongs in implementation metadata, not in a parallel scientific record. The mutation commands above are a thin front end over `orw.mutate`, whose functions — `add_study`, `add_assay`, `register_resource`, `add_contributor` and `update_project_metadata` — are the single supported way to evolve a workspace. Browser editing, publication/DOI, provenance, MCP and agent layers are expected to call those functions rather than reimplement the rules; they remain planned and are not silently activated by these commands.
