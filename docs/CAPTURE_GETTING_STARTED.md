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

## Authentication: use installed Google Chrome

The first version of this helper used Playwright's fresh bundled Chromium session and transferred its storage state into the recorded browser. GitHub login can fail or behave differently in that environment, especially with 2FA, passkeys, device verification, or browser checks.

The current helper therefore uses **installed Google Chrome with a persistent local profile**.

The default profile is:

```text
~/.orw-playwright-github
```

The flow is:

```text
open installed Chrome with dedicated local profile
→ log into GitHub normally
→ close that browser context
→ reopen the SAME authenticated profile
→ start video capture
→ run the ORW documentation flow
```

The login phase itself is not recorded.

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

1. Google Chrome opens using the dedicated ORW capture profile.
2. If that profile is not yet logged into GitHub, sign in normally, including 2FA/passkey/device verification if GitHub asks for it.
3. Return to the terminal and press **Enter** only after GitHub is visibly logged in.
4. The unrecorded login context closes.
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

If GitHub still refuses sign-in specifically in the automated Chrome window, stop there rather than weakening browser security. For a one-time documentation capture, the practical fallback is to complete that login/setup interaction manually in your normal browser and capture those few screens manually.

## Optional arguments

Choose a fixed disposable repository name:

```bash
python scripts/capture_getting_started.py \
  --owner Neuronautix \
  --repo-name ORW-doc-demo
```

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
