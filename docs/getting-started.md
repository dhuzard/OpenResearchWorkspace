# Getting started — your first OpenResearchWorkspace project

This guide is for researchers who have **never used Git or GitHub before**.

At the end, you will understand how to create your own research workspace, where your research material belongs, how collaborators fit in, and how publication will work.

> **You need:** a free GitHub account, about 5–10 minutes, and no programming or Git experience.

The basic workflow is:

```text
Create project → Describe it → Add collaborators → Add/reference data → Work → Publish
```

## Before you start: what you are creating

OpenResearchWorkspace (ORW) uses GitHub as infrastructure, but you can think of the repository simply as your **research project**.

GitHub may use unfamiliar words. You only need a few translations:

| GitHub says | Think of it as |
|---|---|
| Repository | Your research project |
| Commit | A saved change |
| Issue | A task or discussion |
| Release | A published project version |

You do **not** need to learn branches, command-line Git, CI/CD, tags, YAML, or GitHub Actions to follow this guide.

### Example used throughout this guide

We will use one fictional project so that every step is concrete:

- **Project:** `light-exposure-mouse-activity`
- **Title:** Effects of light exposure on mouse activity
- **Description:** Study of how altered light exposure affects spontaneous mouse activity.
- **Data:** Raw videos stored on an institutional research server
- **Analysis:** Activity-analysis notebooks and scripts

Replace these example values with information from your own study.

---

## Step 1 — Create your research project

**Why?** This creates your own independent workspace from the ORW template.

1. Open the OpenResearchWorkspace repository on GitHub.
2. Click **Use this template**.
3. Choose **Create a new repository**.
4. Under **Repository name**, enter a short project name. For our example: `light-exposure-mouse-activity`.
5. Add a short description if you want.
6. Choose the project visibility appropriate for your work. For ongoing or unpublished research, **Private** is usually the safer starting point unless your team has decided otherwise.
7. Click **Create repository**.

> **✓ Done:** GitHub should now show a new repository under your account or organization, with the project name you chose. This is your research workspace. Changes you make here do **not** modify OpenResearchWorkspace itself.

**Something went wrong?** If you cannot see **Use this template**, the ORW repository may not yet have been enabled as a GitHub template. If you cannot create a private repository in the intended organization, ask the organization's administrator about your permissions.

:::{important}
**OpenResearchWorkspace itself is MIT licensed**, but your new research project is independent. Its scientific outputs do not automatically inherit MIT. Your project should choose appropriate licenses for its own code, data, documentation, manuscripts, figures, and other outputs.
:::

---

## Step 2 — Describe your research

**Why?** ORW keeps a structured description of the project so the same information can later support citation, FAIR metadata, archiving, and other tools without asking you to enter it repeatedly.

The planned first-run setup will ask for:

- project title;
- short description;
- contributors;
- ORCIDs, where available;
- keywords;
- where the project's data live;
- whether any data are sensitive or restricted;
- initial licensing choices.

For our example, you might enter:

```text
Title: Effects of light exposure on mouse activity
Description: Study of how altered light exposure affects spontaneous mouse activity.
Data location: Institutional research server
Sensitive/restricted data: No
```

ORW will write the structured `.research/` information behind the scenes. Normal users should not need to edit YAML files.

> **✓ Done:** Your project overview should show the information you supplied, and ORW should report that the basic project information is complete.

:::{note}
The self-service setup form is still part of the v0 implementation backlog. The current repository defines the target structure and metadata contract, but this step is not yet fully automated. This guide describes the intended beginner workflow rather than pretending the unfinished setup is already available.
:::

---

## Step 3 — Know where your work belongs

**Why?** A predictable structure makes the project understandable to collaborators, future-you, software tools, and later AI agents.

A normal ORW project uses these main areas:

```text
data/           research data or references to authoritative data
analysis/       notebooks, scripts, and computational workflows
results/        derived tables, figures, reports, and other outputs
protocols/      experimental or analytical protocols
references/     literature and reference material
project-docs/   project notes, decisions, rationale, and history
```

For the example project:

```text
data/           documents where the raw videos are stored
analysis/       activity-analysis notebooks/scripts
results/        activity tables and figures
protocols/      light-exposure and recording procedures
project-docs/   study decisions and meeting notes
```

You will also see `.research/` and `.github/`. These are ORW/GitHub infrastructure. **You can ignore them during normal day-to-day research work.**

> **✓ Done:** You can identify where a new dataset reference, analysis script, figure, protocol, or project note belongs without needing to understand the technical infrastructure.

For the detailed folder semantics, see [Project structure](project-structure.md).

---

## Step 4 — Add your first file

**Why?** This verifies that you can use the workspace for ordinary research material without installing Git.

Using the GitHub website:

1. Open the folder where the file belongs, for example `project-docs/`.
2. Click **Add file**.
3. Choose **Upload files**.
4. Drag a small non-sensitive test file into the page, or choose it from your computer.
5. Scroll to the bottom and save the change using GitHub's proposed defaults.

GitHub may call the saved change a **commit**. For normal ORW use, you can simply think of it as saving a versioned change to your project.

> **✓ Done:** The file should now appear in the folder. GitHub also keeps a history of the saved change automatically.

**Something went wrong?** Do not use this test to upload confidential participant information, credentials, very large raw data, or files that your institution does not permit you to store on GitHub.

---

## Step 5 — Invite a collaborator

**Why?** Collaboration is one of the main reasons to use a shared research workspace.

1. Open your project on GitHub.
2. Click **Settings**.
3. Find the repository access/collaborator settings. GitHub's exact label can vary depending on whether the project belongs to a personal account or an organization.
4. Choose the option to add a collaborator or person.
5. Search for their GitHub account and send the invitation.

> **✓ Done:** The collaborator should appear as invited or added, and GitHub will send them an invitation. They must accept it before they can access a private project.

**Can't find them?** Confirm that they have a GitHub account and that you have permission to add people to the repository or organization.

ORW treats them as **project collaborators**; you do not need to learn GitHub's wider organization model unless your lab needs more advanced permission management.

---

## Step 6 — Add or reference your data responsibly

**Why?** Your project should say what data exist and where the authoritative data live, without assuming that every scientific file belongs on GitHub.

GitHub is appropriate for things such as:

- code and scripts;
- notebooks;
- text and documentation;
- schemas and configuration;
- small research artifacts when appropriate.

GitHub is **not** the default storage location for large, sensitive, regulated, or discipline-specific scientific datasets.

For our example, the raw behavioural videos remain on institutional research storage. The ORW project records their location and contains the analysis that uses them.

```text
ORW project
├── data/        → description/reference to raw videos
├── analysis/    → analysis code
└── results/     → derived results

Institutional storage
└── raw videos   → authoritative large data
```

When data are eventually deposited in Zenodo, DANDI, another domain repository, or an institutional repository, ORW can record the persistent identifier rather than duplicating the data unnecessarily.

> **✓ Done:** Someone reading the project can determine what data the study uses and where the authoritative data can be found or requested.

---

## Step 7 — Continue working

You can now use the project for day-to-day research.

The simple mental model is:

```text
Project overview
│
├── Data
├── Analysis
├── Results
├── Protocols
├── References
├── Project notes
└── Collaborators
```

You do not need to interact with ORW's machine-readable metadata on every visit. The long-term design is that forms and lightweight tooling update the canonical project record and generate downstream metadata automatically.

> **✓ Done:** If you can add material, find it again, understand where it belongs, and collaborate with your team, the workspace is already doing its basic job.

---

## Step 8 — Publish when the project is ready

**Why?** Publication creates an intentional, citable snapshot rather than making every routine edit a permanent scientific release.

The target ORW publication experience is:

```text
Publish project
      ↓
Check project information
      ↓
Check what will become public
      ↓
Warn about sensitive/restricted material
      ↓
You explicitly confirm
      ↓
Create a version
      ↓
Archive it in the configured repository
      ↓
Receive DOI/PID
```

Routine edits should **never** accidentally publish a permanent scientific record.

The initial archival integration is planned around Zenodo/GitHub, while the architecture remains open to domain repositories.

> **✓ Done:** After this capability is implemented and configured, ORW should show the published version and its DOI/PID without requiring you to understand Git tags or GitHub release mechanics.

:::{note}
The one-action publication workflow is part of the v0 implementation backlog. Do not interpret this section as saying that the complete automated publication interface already exists.
:::

---

## What you need to do now vs later

### During normal project setup and work

1. Create the project.
2. Describe it.
3. Add collaborators.
4. Add files and/or document where data live.
5. Work normally.

### When you are ready to publish

Complete contributor information, ORCIDs where available, licensing, required metadata, publication checks, and archival configuration.

### Optional capabilities later

RO-Crate, DataCite export, FAIR Signposting, computational environments, detailed provenance, AI-ready context, and agent skills are optional capability layers. You do **not** need them to start using an ORW project.

---

## Frequently asked beginner questions

**Do I need to install Git?**  
No for the beginner workflow. You can perform the basic steps through the GitHub website.

**Do I need to know how to program?**  
No. ORW is intended for research projects, not only computational projects.

**Is my project automatically public?**  
No. Visibility depends on the repository settings you choose. For unpublished work, starting private is often appropriate.

**Can I break the original OpenResearchWorkspace template?**  
No. A project created with **Use this template** is an independent repository.

**Should I upload all my raw data to GitHub?**  
No. Large, sensitive, regulated, or domain-specific data often belong in appropriate research storage or repositories. ORW should document where those authoritative data live.

**What if I make a mistake?**  
GitHub records the history of saved changes. The beginner workflow should make common changes recoverable without requiring you to understand Git internals.

**What are Zenodo and a DOI?**  
Zenodo is one possible archival repository. A DOI is a persistent identifier that makes a published research object easier to cite and find. ORW's publication layer is designed to hide most of the technical release mechanics.

---

## Beginner usability test

The release criterion for this guide should not be "the documentation looks clear to us." It should be tested.

Give this guide to at least three researchers who have never used GitHub and provide no additional instruction. Observe:

- where they hesitate;
- words they do not understand;
- places where they are unsure what to click;
- places where they cannot tell whether a step succeeded;
- questions they ask;
- steps where they need outside help.

Each repeated point of confusion should become a documentation or product issue.

**Target:** a GitHub-naive researcher can go from the ORW homepage to a functioning private research workspace using only this guide, without assistance.

## Video companion

A short video should complement rather than duplicate this guide. Record the complete process from the ORW homepage with a fresh beginner-style project:

> **OpenResearchWorkspace from zero: creating my first research project**

Aim for roughly 5–8 minutes. Show the real clicks and the complete flow. The video answers *"What does the whole process look like?"*; this written guide answers *"I am on Step 4 — exactly what do I do now?"*

## Next

- Read [Project structure](project-structure.md) to understand where research material belongs.
- Read [Concepts](concepts.md) if you want to understand the ORW architecture.
- Read [Capabilities](capabilities.md) for the later FAIR, reproducibility, AI-ready, and agent-ready layers.
- Read [FAQ](faq.md) for practical questions.
