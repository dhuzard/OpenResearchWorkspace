# One-shot Playwright capture for the beginner guide

This is **documentation tooling**, not a permanent E2E/CI system.

Its purpose is to run the real beginner onboarding once in a headed browser and produce the screenshots and video used in the ORW documentation.

## What it captures

The script follows the real beginner path:

```text
Open ORW template
→ create a disposable private repository
→ open “Set up my research project”
→ fill the real GitHub Issue Form
→ submit it
→ wait for the real ORW initialization workflow
→ capture the success message
→ open the initialized workspace
```

It produces:

```text
docs/assets/getting-started/
├── 01-use-template.png
├── 02-setup-project.png
├── 03-setup-form.png
├── 04-initialized-success.png
├── 05-initialized-workspace.png
└── orw-getting-started.webm
```

## Privacy / authentication

GitHub login happens in a **separate unrecorded browser context**. The script waits while you log in normally, including 2FA if needed. It then transfers the authenticated browser state into a fresh context and starts the documentation recording.

The temporary browser authentication state is stored only in a temporary local directory and is deleted when the script exits.

Do not share the temporary Playwright directory if the script is interrupted before cleanup.

## Install Playwright

From a local checkout of ORW:

```bash
python -m pip install playwright
python -m playwright install chromium
```

## Run once

For the Neuronautix organization:

```bash
python scripts/capture_getting_started.py --owner Neuronautix
```

The script creates a disposable repository named approximately:

```text
ORW-doc-demo-20260915-164500
```

You may override the name:

```bash
python scripts/capture_getting_started.py \
  --owner Neuronautix \
  --repo-name ORW-doc-demo
```

## During the run

1. A Chromium window opens at GitHub login.
2. Log in normally. This part is **not recorded**.
3. Return to the terminal and press **Enter**.
4. The recorded documentation flow starts.
5. If GitHub's owner selector has changed and Playwright cannot select `Neuronautix`, the script pauses and asks you to select the owner manually in the browser, then press **Enter**.
6. The rest of the onboarding is driven automatically using the real ORW setup form and real ORW initialization workflow.

## After the run

Review:

- the five screenshots;
- `orw-getting-started.webm`;
- the disposable GitHub repository.

The script deliberately **does not delete the disposable repository automatically**. Delete it manually only after the documentation artifacts have been checked.

The screenshots may then be referenced from `docs/getting-started.md`. The WebM may be kept as a source recording, converted to another format if needed, or used as the basis for a short documentation/demo video.

## Important

This script drives GitHub's web UI, which GitHub can change without notice. It is intentionally a one-shot documentation helper rather than a maintained UI test suite. If one selector breaks, fix the local selector or complete that single step manually; do not turn ORW v0 into a large Playwright maintenance project.
