# Getting started

This guide is written for researchers, not Git specialists.

The intended experience is:

```text
Use template → initialize → collaborate → work → publish
```

## 1. Create your research workspace

Open the OpenResearchWorkspace template on GitHub and choose **Use this template**.

Create a new repository for your study. Use a descriptive project name. Keep it private if the project contains unpublished or restricted material.

You are creating an independent research workspace, not a fork that must remain synchronized with the ORW development repository.

## 2. Run first-time setup

The template is intended to provide a first-run setup workflow that asks only for the information needed to initialize the workspace.

The initial setup should collect:

- project title;
- short description;
- contributors;
- ORCIDs where available;
- keywords;
- data location;
- whether data are sensitive or restricted;
- initial licensing choices;
- optional capabilities to enable.

The setup process writes the structured `.research/` files for you. Normal users should not need to edit YAML directly.

:::{note}
The setup workflow is part of the v0 implementation backlog. Until it is implemented, the repository already defines the target metadata contract and lifecycle, but initialization is not yet fully self-service.
:::

## 3. Work in the project

The researcher-facing project should stay simple. The main areas are:

```text
README.md       Project overview

data/           Data files or links to authoritative data locations
analysis/       Analysis code, notebooks, and workflows
results/        Derived outputs
docs/           Protocols, notes, decisions, and documentation
```

Infrastructure such as `.research/`, validation workflows, generated metadata, and later agent instructions can remain in the repository without becoming part of the everyday user experience.

## 4. Collaborate

Invite project collaborators through GitHub repository access.

ORW treats GitHub as infrastructure. A future lightweight UI may simplify collaborator management, but the project remains owned by the scientist or lab.

## 5. Keep metadata current

The canonical project record is `.research/project.yml`.

The long-term design is that forms or lightweight tooling update this record and generate downstream formats such as citation metadata, archival metadata, and FAIR packaging automatically.

The scientist should provide information once; ORW should avoid asking them to maintain redundant metadata files.

## 6. Add data responsibly

GitHub is suitable for code, notebooks, text, configuration, schemas, and small research artifacts. It is not the default storage system for large, sensitive, regulated, or discipline-specific scientific datasets.

For those data, keep the authoritative files in an appropriate repository or institutional system and record their location or persistent identifier in the workspace.

## 7. Enable optional capabilities

ORW uses one workspace rather than separate templates for FAIR, reproducible, or AI-ready projects.

Capabilities are enabled on the same project as needed. Examples include:

- archival publication and DOI;
- FAIR enrichment;
- reproducibility and provenance;
- AI-ready context;
- agent-ready skills and policies.

See {doc}`capabilities`.

## 8. Publish intentionally

Publication should always be an explicit action.

The target workflow is:

```text
Check project
→ review what will become public
→ confirm publication
→ create a version
→ archive in the configured repository
→ receive DOI/PID
```

Routine edits should never accidentally publish a permanent scientific record.

## What you should not need to learn

To use ORW normally, a researcher should not need to understand:

- Git branching strategies;
- commit internals;
- CI/CD;
- tags;
- YAML syntax;
- release automation internals.

Advanced users may still use all of these directly.

## Next

Read {doc}`concepts` to understand the ORW model, or return to the {doc}`index`.
