# Getting started — your first OpenResearchWorkspace project

This guide is for researchers who have **never used Git or GitHub before**.

At the end, you will have your own initialized research workspace with a first **Study** and **Assay**, without installing Git or editing YAML.

> **You need:** a free GitHub account and about 10 minutes. No programming or Git experience is required.  
> **Recommended:** an ORCID. You can register at https://orcid.org/register.

The beginner workflow is:

```text
Create project → Initialize it → Add collaborators → Add/reference data → Work → Publish
```

## Before you start: three words you will see

GitHub calls your project a **repository**. In this guide, we simply call it your **project**.

ORW organizes the science using the ISA model:

- **Investigation** — the overall research project;
- **Study** — one study/design within that project;
- **Assay** — one measurement or test within a study, such as behaviour, imaging, electrophysiology, RNA-seq, or another measurement type.

You do not need to know ISA-JSON or ISA-Tab to start. ORW creates the structure for you.

### Example used throughout

- Project: `light-exposure-mouse-activity`
- Project title: Effects of light exposure on mouse activity
- First study: Light exposure study
- First assay: Behaviour
- Data location: Institutional research server

Replace these values with your own study.

---

## Step 0 — Create a GitHub account

If you do not already have one, follow GitHub's account-creation instructions: https://docs.github.com/en/account-and-profile/how-tos/account-management/creating-an-account-on-github

> **✓ Done:** You can sign in to GitHub.

---

## Step 1 — Create your research project

**Why?** This creates your own independent workspace from the ORW template.

1. Open the OpenResearchWorkspace repository on GitHub.
2. Click **Use this template**.
3. Choose **Create a new repository**.
4. Under **Repository name**, enter a short project name. Example: `light-exposure-mouse-activity`.
5. Choose **Private** for ongoing/unpublished work unless your team has decided otherwise.
6. Click **Create repository**.

> **✓ Done:** GitHub now shows a new repository under your account or organization. This is your project. It is independent from OpenResearchWorkspace.

> [!IMPORTANT]
> ORW itself is MIT licensed, but your scientific outputs do not automatically inherit MIT. You will choose appropriate licenses for your own research outputs later.

### Screenshot to add

Add a tightly cropped screenshot showing **Use this template → Create a new repository**, and a second crop showing the repository name/visibility form. Do not use a full-screen screenshot with many unrelated controls.

---

## Step 2 — Initialize your project

**Why?** The repository you created is still a copy of the generic template. Initialization turns it into **your study workspace** by asking a few questions and creating the appropriate ISA Investigation → Study → Assay structure automatically.

In this guide, **run** only means "ask GitHub to execute this setup form for you." You do not run a program on your computer.

### 2.1 Open the setup form

From **your new project repository**:

1. Click the **Actions** tab near the top of the GitHub page.
2. In the left-hand list, click **Initialize research project**.
3. Click **Run workflow** on the right.

A small form opens directly on GitHub.

### 2.2 Fill the form

Enter:

- **Project title** — the human-readable name of the whole Investigation;
- **Short description** — one or two sentences describing the research;
- **First study title** — the first Study inside the Investigation;
- **First assay or measurement** — the first Assay, for example `Behaviour`, `Imaging`, or `RNA-seq`;
- **Data location** — where the authoritative/raw data are stored;
- **Data access level** — private, restricted, embargoed, open, or unknown;
- **Keywords** — optional, separated by commas;
- **ORCID** — optional.

For our example:

```text
Project title: Effects of light exposure on mouse activity
Short description: Study of how altered light exposure affects spontaneous mouse activity.
First study title: Light exposure study
First assay or measurement: Behaviour
Data location: Institutional research server
Data access level: private
Keywords: behaviour, circadian rhythm, mouse
```

### 2.3 Start initialization

1. Click the green **Run workflow** button at the bottom of the form.
2. GitHub returns to the workflow page. A new run named **Initialize research project** should appear.
3. Wait for it to finish. Refresh the page if necessary.
4. A **green check mark** means initialization succeeded.
5. Click the **Code** tab to return to your project.

ORW will have created/updated the files for you. You do **not** need to edit `.research/project.yml` yourself.

> **✓ Done:** Your repository README now displays your project title, first Study and first Assay. A `studies/` folder exists, and `.research/project.yml` contains the machine-readable project description.

### What initialization actually did

For the example above, ORW creates approximately:

```text
light-exposure-mouse-activity/          Investigation
│
├── studies/
│   └── light-exposure-study/           Study
│       ├── data/
│       ├── protocols/
│       ├── analysis/
│       ├── results/
│       └── assays/
│           └── behaviour/              Assay
│               ├── data/
│               ├── analysis/
│               └── results/
│
├── references/
├── project-docs/
└── .research/project.yml
```

### Screenshot sequence to add

Use four small screenshots, each immediately beside the relevant instruction:

1. the **Actions** tab;
2. **Initialize research project** in the left sidebar;
3. the opened **Run workflow** form with example values;
4. the successful run with the **green check mark**.

These screenshots should be taken from a repository created from the template, not from the ORW development repository.

### Something went wrong?

**I cannot see `Initialize research project`.** Confirm that you created your repository from the ORW template and that the workflow exists under `.github/workflows/initialize-project.yml`.

**GitHub asks me to enable Actions.** Enable repository Actions if your account/organization policy allows it. In an institution-managed organization, an administrator may control this setting.

**The run has a red X.** Click the failed run, then **Create project structure and metadata** to see which step failed. Do not repeatedly initialize the project: the workflow deliberately refuses to overwrite an already initialized workspace.

---

## Step 3 — Understand where your work belongs

You now have an ISA-aligned scientific hierarchy rather than one flat folder tree.

```text
Investigation
└── Study
    ├── study-wide data/protocols/analysis/results
    └── Assays
        └── measurement-specific data/analysis/results
```

Use **Study level** for material that applies to the study as a whole. Use **Assay level** for material specific to one measurement/test.

Example: a behavioural recording protocol and its tracking outputs can live in the Behaviour assay, while randomization/design information that applies to all measurements belongs at Study level.

You will also see `.research/` and `.github/`. These are ORW/GitHub infrastructure. You can ignore them during ordinary research work.

> **✓ Done:** You can identify your Study and Assay folders and understand which level a new research item belongs to.

For details, see [Project structure](project-structure.md) and [Why ORW uses ISA](isa.md).

---

## Step 4 — Add your first file

1. Open the appropriate Study or Assay folder.
2. Open the relevant subfolder, for example `project-docs/`, `protocols/`, `analysis/`, or `results/`.
3. Click **Add file** → **Upload files**.
4. Drag in a small, non-sensitive test file.
5. Save the change using GitHub's proposed defaults.

GitHub may call the saved change a **commit**. You can simply think of it as a saved, versioned change.

> **✓ Done:** The file appears in the chosen folder and GitHub keeps its change history.

Do not use this test to upload confidential participant information, credentials, or very large raw datasets.

---

## Step 5 — Invite a collaborator

1. Open your project.
2. Click **Settings**.
3. Open the repository access/collaborator settings.
4. Choose the option to add a collaborator/person.
5. Search for their GitHub account and send the invitation.

> **✓ Done:** They appear as invited/added. They must accept the invitation before accessing a private project.

---

## Step 6 — Add or reference data responsibly

GitHub is appropriate for code, notebooks, documentation, schemas, configuration, and small research artifacts when appropriate. It is not the default storage system for large, sensitive, regulated, or discipline-specific datasets.

If authoritative data remain on institutional storage, a domain repository, Zenodo, DANDI, or another system, keep them there and record their location/PID in ORW rather than duplicating them unnecessarily.

> **✓ Done:** Someone inspecting the project can determine what data the study uses and where the authoritative data live.

---

## Step 7 — Continue working

The normal scientific mental model is now:

```text
Investigation
├── Study 1
│   ├── Assay A
│   └── Assay B
└── Study 2
    └── Assay A
```

You do not need to interact with machine-readable metadata on every visit. ORW's purpose is to capture structured context without making metadata infrastructure your daily interface.

---

## Step 8 — Publish when ready

The target publication experience is:

```text
Publish project
→ validate project
→ preview what becomes public
→ explicit human confirmation
→ create version
→ archive
→ DOI/PID
```

Routine edits should never accidentally create a permanent scientific release.

> [!NOTE]
> The one-action publication workflow is still part of the v0 implementation backlog. Unlike Step 2, this part is not yet implemented end-to-end.

---

## What is implemented vs planned?

**Implemented by the initialization workflow in this branch:** browser-based project form; ISA Investigation/Study/Assay initialization; project README generation; canonical `.research/project.yml`; data-location/access capture; protection against accidental re-initialization.

**Still planned:** adding additional Studies/Assays through equally simple forms; collaborator simplification beyond GitHub's UI; richer metadata editing; license selection; validation dashboard; one-action archive/DOI publication; FAIR/reproducibility/AI/agent capabilities.

## Beginner usability test

Give this guide to at least three researchers who have never used GitHub and provide no additional instruction. Record every hesitation, unknown term, uncertain success state, and place where outside help is required.

**Target:** a GitHub-naive researcher can create and initialize a private ORW project using only this guide.

## Video companion

Record the actual E2E sequence after this workflow is merged:

**OpenResearchWorkspace from zero: creating and initializing my first research project**

Show the real sequence: ORW → Use this template → new repository → Actions → Initialize research project → fill form → Run workflow → green check → Code → generated Study/Assay structure. The video should use the same example as this guide.

## Next

- [Project structure](project-structure.md)
- [Why ORW uses ISA](isa.md)
- [Concepts](concepts.md)
- [Capabilities](capabilities.md)
- [FAQ](faq.md)
