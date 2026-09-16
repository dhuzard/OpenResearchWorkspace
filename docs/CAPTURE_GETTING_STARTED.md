# One-shot Playwright capture for the beginner guide

This is **documentation tooling**, not a permanent E2E/CI system.

Its purpose is to run the real beginner onboarding once in a headed browser and produce the screenshots and video used in the ORW documentation.

## What it captures

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

The WebM is an instructional recording. Before each automated interaction it
shows a numbered caption and highlights the relevant GitHub control in yellow.
These temporary guides are burned into the video but removed from the clean
documentation screenshots.

## Authentication: use installed Google Chrome

The first version of this helper used Playwright's fresh bundled Chromium session and transferred its storage state into the recorded browser. GitHub login can fail or behave differently in that environment, especially with 2FA, passkeys, device verification, or browser checks.

The current helper therefore uses **installed Google Chrome with a persistent local profile**.
When authentication is required, it closes Playwright and opens Chrome as a normal,
non-automated process. This is important for accounts that use Google as their GitHub
sign-in method: Google may refuse a browser carrying automation flags.

The default profile is:

```text
~/.orw-playwright-github
```

The flow is:

```text
check dedicated local profile
→ if needed, close Playwright and open normal Chrome
→ log into GitHub normally
→ close Chrome completely
→ reopen the SAME authenticated profile
→ start video capture
→ run the ORW documentation flow
```

The interactive login phase itself is not recorded. The raw video may begin with
a brief visit to GitHub's profile settings while the helper verifies the saved
session; the documentation screenshots begin at the ORW template.

Do not commit, upload, or share the browser profile directory. It contains authenticated browser state. Delete it after the documentation capture if you no longer need it.

## Install

You only need the Python Playwright package if Google Chrome is already installed:

```bash
python -m pip install playwright
```

Then run:

```bash
python scripts/capture_getting_started.py --owner Neuronautix
```

You do **not** need `playwright install chromium` when using the default `--browser chrome` mode.

If Google Chrome is not installed, the fallback is:

```bash
python -m playwright install chromium
python scripts/capture_getting_started.py --owner Neuronautix --browser chromium
```

Chrome is recommended for GitHub authentication.

## During the run

1. The helper checks the dedicated ORW capture profile.
2. If that profile is not yet logged into GitHub, the Playwright window closes and a normal Chrome window opens.
3. Sign in normally, including 2FA/passkey/device verification if GitHub asks for it.
4. **Close that Chrome window completely**, then return to the terminal and press **Enter**.
5. The same profile reopens and recording begins.
6. Playwright creates the disposable repository and runs the real ORW setup flow.
7. If GitHub changes an owner-selector control and the script cannot select `Neuronautix`, select it manually in the browser and press **Enter** in the terminal.

## If GitHub login still fails

Do not keep retrying passwords or try to bypass GitHub's browser/security checks.

First confirm that the script is using installed Chrome, not bundled Chromium:

```bash
python scripts/capture_getting_started.py --owner Neuronautix --browser chrome
```

If the dedicated profile became corrupted or contains a partial login, delete it and retry once:

Linux/macOS:

```bash
rm -rf ~/.orw-playwright-github
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$HOME\.orw-playwright-github"
```

Then rerun the script and complete GitHub login in the opened Google Chrome window.

Do not attempt Google sign-in in a window showing an automation warning such as
`You are using an unsupported command-line flag: --no-sandbox`. Close that window and
let the helper open the separate normal Chrome authentication window. That window is
not controlled or recorded by Playwright.

If GitHub still refuses sign-in in the normal authentication window, stop there rather than weakening browser security. For a one-time documentation capture, the practical fallback is to complete that login/setup interaction manually in your usual browser and capture those few screens manually.

## Optional arguments

Choose a fixed disposable repository name:

```bash
python scripts/capture_getting_started.py \
  --owner Neuronautix \
  --repo-name ORW-doc-demo
```

Resume a capture after the repository was created but a later browser step failed:

```bash
python scripts/capture_getting_started.py \
  --owner Neuronautix \
  --repo-name ORW-doc-demo-20260916-061025 \
  --resume-existing
```

`--resume-existing` requires `--repo-name` and skips repository creation.

Use another local browser profile directory:

```bash
python scripts/capture_getting_started.py \
  --owner Neuronautix \
  --profile-dir ~/.orw-doc-profile
```

## After the run

Review the five screenshots, `orw-getting-started.webm`, and the disposable GitHub repository.

The script deliberately **does not delete the disposable repository automatically**. Delete it manually only after the documentation artifacts have been checked.

The screenshots may then be referenced from `docs/getting-started.md`. The WebM may be kept as the source recording or converted if needed.

## Important

This script drives GitHub's web UI, which GitHub can change without notice. It is intentionally a one-shot documentation helper rather than a maintained UI test suite. If one selector breaks, fix that single selector or complete that one step manually; do not turn ORW v0 into a large Playwright maintenance project.
