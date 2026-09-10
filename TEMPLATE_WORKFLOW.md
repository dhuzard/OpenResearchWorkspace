# ORW GitHub template workflow

The GitHub template is the primary way an ordinary researcher creates an OpenResearchWorkspace.

It is a bootstrap mechanism, not a long-term synchronization relationship with the ORW development repository.

## Before project creation

The template contains generic infrastructure:

```text
README.md
.research/
.github/
schema/
capabilities/
```

The repository is not yet a scientific project until initialization is completed.

## Project creation

The researcher selects **Use this template** and creates an independent repository.

Recommended ownership options:

- personal GitHub account;
- laboratory organization;
- institutional organization.

The created repository is the canonical workspace for that project.

## First-run initialization

The repository should expose one obvious action:

> **Set up this research project**

The setup asks only information needed to create a useful project record:

- title;
- short description;
- contributors;
- ORCIDs where available;
- keywords;
- project status;
- data location;
- whether data are sensitive/restricted;
- licensing choices;
- optional capabilities.

The setup process then generates/synchronizes the internal records.

```text
researcher form
      ↓
.research/project.yml
.research/workspace.yml
.research/capabilities.yml
      ↓
project README and later derived metadata
```

The same information should not need to be entered separately into several metadata files.

## Workspace state

`.research/workspace.yml` tracks ORW implementation state.

Example before initialization:

```yaml
orw:
  spec_version: "0.1"
  template_version: "0.1.0"
  initialized: false
  initialized_at: null
```

After initialization, `initialized` becomes `true` and the initialization timestamp is recorded.

## Capabilities

`.research/capabilities.yml` records optional functionality independently from the scientific project description.

A project should not need a different template for each combination of features.

```text
one ORW template
      ↓
initial setup
      ↓
capabilities enabled as required
```

Examples of later capabilities include:

- archival publication / DOI;
- FAIR enrichment;
- reproducibility and provenance;
- AI-ready context;
- agent skills.

## Independent evolution

Once initialized, the research repository evolves independently from the ORW template.

Researchers should not be expected to:

- maintain a fork relationship;
- merge upstream template commits;
- understand ORW's own Git history.

Future ORW tooling may inspect the recorded `spec_version` and `template_version` and offer an explicit migration when needed.

## Migration principle

Workspace upgrades should behave conceptually like schema migrations:

```text
ORW 0.1 workspace
      ↓
validate current state
      ↓
show migration changes
      ↓
human confirmation when consequential
      ↓
ORW 0.2 workspace
```

Scientific evidence and project history must not be silently rewritten merely because ORW infrastructure evolves.

## Optional UI

A future lightweight UI may provide forms for initialization, metadata editing, capability activation, and publication.

The UI is a view/editor over the repository. It is not the authoritative project database.

The repository remains usable without a central ORW service.
