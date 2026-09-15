# Getting started — your first OpenResearchWorkspace project

This guide is for researchers who have **never used Git or GitHub before**.

At the end, you will have your own initialized research workspace with a first **Study** and **Assay**, without installing Git, opening GitHub Actions, or editing YAML.

> **You need:** a free GitHub account and about 10 minutes. No programming or Git experience is required.  
> **Recommended:** an ORCID. You can register at https://orcid.org/register.

The beginner workflow is:

```text
Create project → Fill setup form → ORW initializes it → Add collaborators → Work
```

## Before you start: three scientific levels

GitHub calls your project a **repository**. In this guide, we simply call it your **project**.

ORW organizes the science using the ISA model:

- **Investigation** — the overall research project;
- **Study** — one study/design within that project;
- **Assay** — one measurement or test within a study, such as behaviour, imaging, electrophysiology, RNA-seq, or another measurement type.

You do not need to know ISA-JSON or ISA-Tab to start. ORW creates the structure for you.

### Example used throughout

- Project: `light-exposure-mouse-activity`
- Project title: Effects of light exposure on mouse activity
- Researcher: Jane Researcher
- First study: Light exposure study
- First measurement/assay: Behaviour
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

Use two tightly cropped screenshots:

1. **Use this template → Create a new repository**;
2. the repository name/visibility form.

Do not use full-screen screenshots with many unrelated controls.

---

## Step 2 — Set up your project

**Why?** The repository you just created is still a generic ORW template. The setup form turns it into **your research workspace**.

You do **not** need to find or run a GitHub Action. ORW uses automation behind the scenes, but the beginner interface is just a form.

### 2.1 Open the setup form

Either:

1. stay on the main page of **your new project repository**;
2. near the top of the README, click **→ Set up my research project**.

Or open **Issues** → **New issue** → **Set up my research project**.

GitHub opens a form titled **Set up my research project**.

> GitHub technically calls this form an **issue**. You do not need to use GitHub Issues or understand issue tracking. ORW is simply using GitHub's built-in form interface so that no separate website or account is required.

### 2.2 Fill the form

The form asks for:

- **Project title** — the human-readable name of the whole Investigation;
- **Short project description** — one or two sentences describing the research;
- **Your name** — your scientific/professional name as it should appear in project metadata;
- **First study title** — the first Study inside the Investigation;
- **What will you measure first?** — the first Assay/measurement, for example `Behaviour`, `Imaging`, `Electrophysiology`, or `RNA-seq`;
- **Where are the authoritative/raw data stored?** — a high-level location only;
- **Data access level** — private, restricted, embargoed, open, or unknown;
- **Keywords** — optional, separated by commas;
- **ORCID** — optional.

For our example:

```text
Project title: Effects of light exposure on mouse activity
Short project description: Study of how altered light exposure affects spontaneous mouse activity.
Your name: Jane Researcher
First study title: Light exposure study
What will you measure first?: Behaviour
Where are the authoritative/raw data stored?: Institutional research server
Data access level: private
Keywords: behaviour, circadian rhythm, mouse
```

Do **not** enter passwords, access tokens, participant identifiers, confidential clinical information, or other secrets in this form.

### 2.3 Submit the form

1. Tick the confirmation box at the bottom.
2. Click **Submit new issue**.

The wording **Submit new issue** comes from GitHub. In ORW, this simply means **send the setup form**.

After submission, stay on the page briefly while ORW initializes the repository in the background.

When initialization succeeds, ORW posts:

> ✅ **Your OpenResearchWorkspace project is initialized.**

The message contains a direct **Open your initialized workspace** link, and the setup form is closed automatically.

Click **Open your initialized workspace**.

> **✓ Done:** Your project README now shows your own project title, Study and Assay. A `studies/` folder exists and `.research/project.yml` contains the machine-readable project description.

### What setup created

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

You do **not** need to edit `.research/project.yml` yourself.

### Screenshot sequence to add

Use three small screenshots from a disposable project created from the template:

1. the **Set up my research project** link in the new repository README;
2. the setup form with example values;
3. the success message with **Open your initialized workspace**.

### Something went wrong?

**I cannot see `Set up my research project`.** Make sure you created the repository from the current ORW template and are looking at your new repository, not the ORW development repository.

**I submitted the form but nothing happened.** Wait briefly and refresh the page. If ORW starts but cannot complete setup, it leaves the form open and posts a failure message with a technical link that you can share when asking for help.

**The form says ORW could not finish initialization.** The repository may restrict GitHub automation or write permissions, or setup may have detected invalid/incomplete information. You do not need to interpret the technical log yourself; share the provided link with your repository owner/administrator or ORW support.

**My account or organization does not allow GitHub Actions.** ORW's current v0 initializer uses GitHub Actions behind the form. Repository/account/organization policy must therefore allow Actions and permit the workflow token to write repository contents and issue comments.

**I accidentally submitted setup twice.** ORW deliberately refuses to initialize an already initialized workspace rather than silently overwrite it. The second setup form remains open with a failure message; your existing initialized project is unchanged.

---

## Step 3 — Understand where your work belongs

You now have an ISA-aligned scientific hierarchy rather than one flat folder tree.

```text
Investigation
└── Study
    ├── study-wide data / protocols / analysis / results
    └── Assays
        └── measurement-specific data / analysis / results
```

Use **Study level** for material that applies to the study as a whole. Use **Assay level** for material specific to one measurement/test.

Example: study design and randomization information can live at Study level, while behavioural recordings and their measurement-specific analyses can live inside the Behaviour Assay.

You will also see `.research/` and `.github/`. These are ORW/GitHub infrastructure. You can ignore them during ordinary research work.

> **✓ Done:** You can identify your Study and Assay folders and understand which level a new research item belongs to.

For details, see [Project structure](project-structure.md) and [Why ORW uses ISA](isa.md).

---

## Step 4 — Add your first file

1. Open the appropriate Study or Assay folder.
2. Open the relevant subfolder, for example `protocols/`, `analysis/`, `results/`, or `project-docs/`.
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

The normal scientific mental model is:

```text
Investigation
├── Study 1
│   ├── Assay A
│   └── Assay B
└── Study 2
    └── Assay A
```

You do not need to interact with machine-readable metadata on every visit. ORW's purpose is to capture structured context without making metadata infrastructure your daily interface.

At this point your workspace is usable for active research.

---

## Coming next — publish and receive a DOI

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
> The one-action publication/DOI workflow is **not yet implemented end-to-end**. It is intentionally presented here as a coming capability rather than as a step you can already execute.

---

## What is implemented vs planned?

**Implemented and E2E-tested:** browser setup form; automatic initialization after form submission; repository write-permission check for the submitter; ISA Investigation/Study/Assay structure; researcher identity capture; generated project README; canonical `.research/project.yml`; data-location/access capture; success/failure feedback in the form thread; automatic closure on success; protection against accidental re-initialization.

**Still planned:** adding additional Studies/Assays through equally simple forms; collaborator simplification beyond GitHub's UI; richer metadata editing; license selection; validation dashboard; one-action archive/DOI publication; FAIR/reproducibility/AI/agent capabilities.

## Beginner usability test

Give this guide to at least three researchers who have never used GitHub and provide no additional instruction. Record every hesitation, unknown term, uncertain success state, and place where outside help is required.

**Target:** a GitHub-naive researcher can create and initialize a private ORW project using only this guide and the setup form, without ever opening the GitHub Actions interface.

## Video companion

Record the actual E2E sequence:

**OpenResearchWorkspace from zero: creating and initializing my first research project**

Show the real sequence:

```text
ORW
→ Use this template
→ create repository
→ Set up my research project
→ fill form
→ Submit new issue
→ success message
→ Open your initialized workspace
→ generated Study/Assay structure
```

The video should use the same example as this guide.

## Next

- [Project structure](project-structure.md)
- [Why ORW uses ISA](isa.md)
- [Concepts](concepts.md)
- [Capabilities](capabilities.md)
- [FAQ](faq.md)
