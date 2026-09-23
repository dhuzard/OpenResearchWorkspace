# Getting started with OpenResearchWorkspace

**A click-by-click guide for researchers who do not code and have little or no GitHub experience.**

You do **not** need to:

- program;
- install Git;
- use a terminal or command line;
- edit YAML or other configuration files;
- understand branches, commits, pull requests, or GitHub Actions;
- install the ORW Python package.

The normal beginner workflow is:

```text
Create my project
      ↓
Fill in a short setup form
      ↓
ORW creates the research structure
      ↓
Add collaborators and research files
      ↓
Work normally
```

## Before you begin

You need only:

1. a GitHub account;
2. a short name for your research project;
3. a one- or two-sentence description of the project;
4. a high-level description of where your authoritative/raw data are stored.

ORCID, a specific Study title, and an Assay name are **not required** to get started.

### Four GitHub words you may see

GitHub uses software-development vocabulary. For the beginner ORW workflow, you can translate it as follows:

| GitHub says | For this guide, think |
| --- | --- |
| **Repository** | Your research project's online workspace |
| **Issue** | A form or discussion page; ORW uses one as the project setup form |
| **Commit** | A saved change with history |
| **GitHub Actions** | Background automation used by ORW; you normally do not open it |

You do not need to learn Git itself to follow this workflow.

---

## Step 1 — Open the ORW template

Open this repository:

[**OpenResearchWorkspace-template**](https://github.com/dhuzard/OpenResearchWorkspace-template)

Check that the repository name at the top is:

```text
dhuzard / OpenResearchWorkspace-template
```

Do **not** create your research project from `dhuzard/OpenResearchWorkspace`. That other repository is where ORW itself is developed.

**Success check:** you are viewing `OpenResearchWorkspace-template`.

---

## Step 2 — Create your own project

1. Click **Use this template** near the top-right of the repository.
2. Choose **Create a new repository**.
3. Choose the GitHub account or organization that should own the project.
4. Enter a short repository name, for example:

```text
light-exposure-mouse-activity
```

5. For ongoing or unpublished research, choose **Private** unless your team has explicitly decided the project should already be public.
6. Click **Create repository**.

GitHub now creates a new project under **your** account or organization. The new project is independent from the ORW template.

**Success check:** the repository name at the top is now your project name, not `OpenResearchWorkspace-template`.

---

## Step 3 — Set up the research project

Your new repository initially contains a generic ORW workspace. The setup form turns it into your actual research project.

On the main page of **your new repository**, click the prominent:

**→ Set up my research project**

If you do not see that link, use **Issues → New issue → Set up my research project**.

> GitHub calls this an **issue**, but you can treat it simply as a form. You do not need to understand GitHub issue tracking.

---

## Step 4 — Fill in the setup form

The form asks for a small amount of project information, then three choices that control how much structure ORW creates initially.

You will provide:

- **Project title** — the human-readable title of the overall research project;
- **What is this project about?** — one or two sentences describing the question or objective;
- **Your name** and optional **ORCID**;
- **How is this research organized?** — one Study, several Studies, or not sure yet;
- **First Study title (optional)** — leave blank for a one-Study project and ORW will reuse the project title;
- **Do your Studies contain several distinct measurement types?** — choose **Yes** only if a separate Assays layer is genuinely useful;
- **Do you want to keep protocol documents in this workspace?** — choose whether ORW creates a protocols folder now;
- **Where are the authoritative or raw data stored?**;
- **Current data access** — private, restricted, embargoed, open, or unknown;
- optional **keywords**.

ORW deliberately does **not** ask you to invent a first Assay or measurement name during setup.

For a simple project, a reasonable configuration is:

```text
Project title:
Effects of light exposure on mouse activity

What is this project about?
Study of how altered light exposure affects spontaneous mouse activity.

How is this research organized?
One Study — this project is essentially one Study

First Study title:
[leave blank]

Do your Studies contain several distinct measurement types?
No — keep data, analysis and results directly at Study level

Do you want to keep protocol documents in this workspace?
Yes — create a protocols folder

Authoritative/raw data location:
Institutional research server

Current data access:
private
```

This produces a deliberately simple project. If your research later grows into several Studies or several measurement types, ORW can add that structure later.

### Do not put secrets in the setup form

Do not enter:

- passwords;
- API keys or access tokens;
- confidential participant identifiers;
- patient-identifying information;
- authentication credentials;
- information that your institution prohibits from being stored on GitHub.

Use a **high-level data location** such as `Institutional secure server`, not a password or secret access URL.

---

## Step 5 — Submit the setup form

1. Review the information you entered.
2. Tick any confirmation box shown by the form.
3. Click **Create** or **Submit new issue**. GitHub may use either wording.

ORW then runs the initialization automatically.

You should not need to:

- open GitHub Actions;
- edit `.research/project.yml`;
- run a script;
- use a command line.

When initialization succeeds, the setup page should provide a link back to the initialized workspace.

**Success check:** your project README shows your project information and a `studies/` folder exists.

---

## Step 6 — Understand the scientific structure

ORW uses the ISA idea of **Investigation → Study → Assay**, but it does not force every project to display all three levels.

For a simple one-Study project:

```text
Investigation
└── Study
    ├── data
    ├── analysis
    ├── results
    └── protocols       # only if you chose to store protocols here
```

If a Study genuinely contains several distinct measurement types, ORW can expose an Assays layer:

```text
Investigation
└── Study
    └── Assays
        ├── Measurement A
        └── Measurement B
```

The initial workspace therefore depends on your setup choices. A simple project may look approximately like:

```text
your-project/
├── README.md
├── studies/
│   └── your-study/
│       ├── data/
│       ├── analysis/
│       ├── results/
│       └── protocols/      # only when selected
├── references/
├── project-docs/
└── .research/
```

If you selected several measurement types, an `assays/` container is also created, but ORW does not invent Assay names for you.

You can normally ignore `.research/` and `.github/`. They contain machine-readable metadata and GitHub automation rather than day-to-day research material.

---

## Step 7 — Add a normal research file without using Git

You can upload a small file entirely through the GitHub website:

1. Open the folder where the file belongs.
2. Click **Add file**.
3. Click **Upload files**.
4. Drag the file into the page or select it from your computer.
5. Follow GitHub's save/commit controls to save the change.

If GitHub uses the word **commit**, think **save this version**.

Suitable examples include:

- protocols;
- analysis scripts or notebooks;
- documentation;
- figures;
- small non-sensitive research artifacts;
- references or supporting documents when licensing permits.

---

## Step 8 — Do not treat GitHub as the default raw-data store

ORW can describe and reference data without requiring the data themselves to be stored in GitHub.

Large, sensitive, regulated, confidential, or discipline-specific datasets should normally remain in an appropriate system such as:

- institutional research storage;
- a secure institutional server;
- a discipline-specific repository;
- an archival repository;
- another storage system approved for the data type.

Record where the authoritative data live rather than copying them into GitHub without a reason.

This distinction matters: **the ORW workspace organizes the research project; it does not require every research byte to live inside the repository.**

---

## Step 9 — Invite a collaborator

For a private repository:

1. Open your project repository.
2. Click **Settings**.
3. Find the repository access or collaborator section.
4. Choose the option to add a collaborator or person.
5. Search for their GitHub account.
6. Send the invitation.

They must accept the invitation before they can access a private project.

If the project belongs to an institutional GitHub organization, your organization may control who can invite collaborators.

---

## Step 10 — Work normally

At this point, the important mental model is scientific rather than technical:

```text
Project
├── Study 1
│   ├── Assay A
│   └── Assay B
└── Study 2
    └── Assay A
```

Add research material at the level where it belongs. ORW's structured metadata and validation machinery should remain mostly behind the scenes.

You do not need to edit machine-readable metadata during ordinary day-to-day work unless you specifically want to.

---

## If something goes wrong

### I cannot see **Use this template**

Confirm that you are viewing `dhuzard/OpenResearchWorkspace-template` and that the **Use this template** button appears near the top of the repository.

### I cannot see **Set up my research project**

Confirm that you are looking at the repository you created from this template, not `dhuzard/OpenResearchWorkspace-template` itself and not the ORW development repository. Then open **Issues → New issue → Set up my research project**.

### The setup form was submitted but initialization failed

Do not edit `.research/` or GitHub workflow files to try to repair the project manually. Keep the failure message or link and report it to the repository owner or ORW maintainers.

### I submitted setup twice

ORW should refuse to silently reinitialize an already initialized workspace. The existing project should remain the source of truth.

### My institution does not allow GitHub Actions

The GitHub template path relies on GitHub automation for initialization. If institutional policy prevents that workflow, use another ORW creation path from the canonical project, such as the browser generator, once appropriate for your context.

---

## What you should not need to learn

A successful beginner workflow should **not** require you to learn:

```text
git clone
git add
git commit
git push
branches
pull requests
YAML
JSON Schema
Python packaging
GitHub Actions
RO-Crate internals
```

Those technologies may exist underneath ORW, but they are implementation details rather than prerequisites for managing a research project.

---

## One-page checklist

- [ ] I created the project from **OpenResearchWorkspace-template**, not the development repository.
- [ ] I chose an appropriate visibility setting, usually **Private** for active unpublished work.
- [ ] I completed the **Set up my research project** form.
- [ ] My README shows my own project information.
- [ ] I understand whether this project currently uses one or several Studies and whether it needs an Assays layer.
- [ ] I know where my authoritative/raw data live.
- [ ] I did not put passwords, credentials, or sensitive participant information in the setup form.
- [ ] I can upload an ordinary project file through the GitHub website.
- [ ] I know how to invite a collaborator if needed.

Once those points are true, you can use the workspace without learning Git or programming.

---

## ORW itself versus this template

This repository is deliberately minimal. The ORW software, specification, schemas, CLI, browser generator, validation logic, FAIR/RO-Crate support, tests, and future agent/MCP integrations are developed in:

[`dhuzard/OpenResearchWorkspace`](https://github.com/dhuzard/OpenResearchWorkspace)

You normally do not need that repository to use this template as a researcher.
