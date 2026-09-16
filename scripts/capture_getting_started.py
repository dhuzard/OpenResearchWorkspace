#!/usr/bin/env python3
"""One-shot headed Playwright capture of the ORW beginner onboarding flow.

This is documentation tooling, not permanent CI infrastructure.

Authentication deliberately uses a persistent local Chrome profile. This avoids
copying GitHub cookies between Playwright contexts and is more reliable for
GitHub login/2FA/passkey flows than a fresh bundled Chromium session.

Usage:
    python -m pip install playwright
    python scripts/capture_getting_started.py --owner Neuronautix

By default the script uses the installed Google Chrome browser and stores the
one-shot browser profile in ~/.orw-playwright-github. The profile remains local
and MUST NOT be committed or shared.

The script creates a disposable private repository from the ORW template,
submits the real setup form, waits for the real ORW initialization workflow,
and writes screenshots + a WebM video to docs/assets/getting-started/.

It does NOT delete the disposable repository automatically. Review the captured
artifacts first, then delete the repository manually when no longer needed.
"""

from __future__ import annotations

import argparse
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

TEMPLATE_REPO = "https://github.com/dhuzard/OpenResearchWorkspace"
TEMPLATE_NEW = "https://github.com/new?template_name=OpenResearchWorkspace&template_owner=dhuzard"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner",
        default="Neuronautix",
        help="GitHub account/organization that should own the disposable repository.",
    )
    parser.add_argument(
        "--repo-name",
        default=None,
        help="Disposable repository name. Defaults to ORW-doc-demo-<UTC timestamp>.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/assets/getting-started",
        help="Where screenshots and the video are written.",
    )
    parser.add_argument(
        "--profile-dir",
        default=str(Path.home() / ".orw-playwright-github"),
        help="Persistent local browser profile used only for this documentation capture.",
    )
    parser.add_argument(
        "--browser",
        choices=("chrome", "chromium"),
        default="chrome",
        help="Browser to use. 'chrome' uses installed Google Chrome and is recommended for GitHub login.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Maximum time to wait for ORW initialization after form submission.",
    )
    return parser.parse_args()


def screenshot(page: Page, path: Path, *, full_page: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=full_page)
    print(f"Saved screenshot: {path}")


def get_page(context) -> Page:
    pages = context.pages
    return pages[0] if pages else context.new_page()


def ensure_github_login(page: Page) -> None:
    """Verify that the persistent browser profile is authenticated to GitHub."""
    page.goto("https://github.com/settings/profile", wait_until="domcontentloaded")

    if "/login" in page.url or page.get_by_label(re.compile(r"username|email", re.I)).count():
        print("\nGitHub is not authenticated in the documentation browser profile.")
        print("Log into GitHub in the opened *Google Chrome* window, including 2FA/passkey if needed.")
        print("This login is NOT recorded. The authenticated profile stays only on this computer.")
        input("When GitHub login is complete and you can see a normal GitHub page, press Enter... ")
        page.goto("https://github.com/settings/profile", wait_until="domcontentloaded")

    if "/login" in page.url:
        raise RuntimeError(
            "GitHub is still not authenticated. Do not keep retrying credentials in an automated browser. "
            "Close the script, open the persistent profile with system Chrome, sign in once, then rerun. "
            "See docs/CAPTURE_GETTING_STARTED.md for the fallback command."
        )

    print("GitHub authentication confirmed.")


def select_owner(page: Page, owner: str) -> None:
    """Best-effort selection of the repository owner on GitHub's new-repo page."""
    body = page.locator("body")
    if re.search(rf"\b{re.escape(owner)}\b", body.inner_text(), flags=re.IGNORECASE):
        selected_candidates = [
            page.locator("button").filter(has_text=re.compile(rf"^{re.escape(owner)}$", re.I)),
            page.locator("summary").filter(has_text=re.compile(rf"^{re.escape(owner)}$", re.I)),
        ]
        if any(candidate.count() for candidate in selected_candidates):
            return

    candidates = [
        page.get_by_role("button", name=re.compile(r"owner|choose an owner", re.I)),
        page.locator("button").filter(has_text=re.compile(r"choose an owner|owner", re.I)),
        page.locator("summary").filter(has_text=re.compile(r"choose an owner|owner", re.I)),
    ]
    for candidate in candidates:
        try:
            if candidate.count():
                candidate.first.click()
                option = page.get_by_text(owner, exact=True)
                if option.count():
                    option.first.click()
                    return
        except Exception:
            pass

    print("\nCould not select the GitHub repository owner automatically.")
    print(f"In the browser, select owner '{owner}', then return here.")
    input("Press Enter after the owner is selected... ")


def fill_repo_creation(page: Page, owner: str, repo_name: str) -> None:
    select_owner(page, owner)

    name_input = page.get_by_label(re.compile(r"repository name", re.I))
    if not name_input.count():
        name_input = page.locator("input[name='repository[name]'], input#repository_name")
    name_input.first.fill(repo_name)

    private_radio = page.get_by_label(re.compile(r"private", re.I))
    if private_radio.count():
        private_radio.first.check()
    else:
        private_text = page.get_by_text("Private", exact=True)
        if private_text.count():
            private_text.first.click()

    create_button = page.get_by_role("button", name=re.compile(r"create repository", re.I))
    create_button.first.wait_for(state="visible")
    create_button.first.click()
    page.wait_for_url(re.compile(rf"github\.com/{re.escape(owner)}/{re.escape(repo_name)}(?:/)?$"), timeout=120_000)


def fill_setup_form(page: Page) -> None:
    page.get_by_label("Project title").fill("Effects of light exposure on mouse activity")
    page.get_by_label("Short project description").fill(
        "Study of how altered light exposure affects spontaneous mouse activity."
    )
    page.get_by_label("Your name").fill("Jane Researcher")
    page.get_by_label("First study title").fill("Light exposure study")
    page.get_by_label("What will you measure first?").fill("Behaviour")
    page.get_by_label("Where are the authoritative/raw data stored?").fill(
        "Institutional research server"
    )

    access = page.get_by_label("Data access level")
    if access.count():
        access.select_option(label="private")

    page.get_by_label("Keywords (optional)").fill("behaviour, circadian rhythm, mouse")

    ready = page.get_by_label(
        re.compile(r"I understand that submitting this form will initialize", re.I)
    )
    ready.check()


def launch_persistent(p, profile_dir: Path, *, record_video_dir: Path | None = None):
    kwargs = {
        "user_data_dir": str(profile_dir),
        "headless": False,
        "viewport": {"width": 1440, "height": 1000},
    }
    if record_video_dir is not None:
        kwargs["record_video_dir"] = str(record_video_dir)
        kwargs["record_video_size"] = {"width": 1440, "height": 1000}

    if ARGS.browser == "chrome":
        kwargs["channel"] = "chrome"

    return p.chromium.launch_persistent_context(**kwargs)


def main() -> int:
    global ARGS
    ARGS = parse_args()
    repo_name = ARGS.repo_name or (
        "ORW-doc-demo-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    )
    output_dir = Path(ARGS.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = Path(ARGS.profile_dir).expanduser().resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    screenshots = {
        "template": output_dir / "01-use-template.png",
        "setup_entry": output_dir / "02-setup-project.png",
        "form": output_dir / "03-setup-form.png",
        "success": output_dir / "04-initialized-success.png",
        "workspace": output_dir / "05-initialized-workspace.png",
    }
    final_video = output_dir / "orw-getting-started.webm"
    video_dir = output_dir / ".capture-video-tmp"
    if video_dir.exists():
        shutil.rmtree(video_dir)
    video_dir.mkdir(parents=True, exist_ok=True)

    print(f"Disposable repository: {ARGS.owner}/{repo_name}")
    print(f"Output directory: {output_dir}")
    print(f"Persistent GitHub browser profile: {profile_dir}")

    with sync_playwright() as p:
        # Phase 1: authenticate in a normal installed Chrome profile. Nothing is recorded.
        try:
            auth_context = launch_persistent(p, profile_dir)
        except Exception as exc:
            if ARGS.browser == "chrome":
                raise RuntimeError(
                    "Could not launch installed Google Chrome. Install Chrome or rerun with --browser chromium "
                    "after `python -m playwright install chromium`."
                ) from exc
            raise

        auth_page = get_page(auth_context)
        ensure_github_login(auth_page)
        auth_context.close()

        # Phase 2: reopen the exact same authenticated profile and start recording.
        context = launch_persistent(p, profile_dir, record_video_dir=video_dir)
        page = get_page(context)
        video = page.video

        page.goto(TEMPLATE_REPO, wait_until="networkidle")
        page.get_by_text("OpenResearchWorkspace", exact=True).first.wait_for(state="visible")
        screenshot(page, screenshots["template"])
        time.sleep(1.0)

        page.goto(TEMPLATE_NEW, wait_until="domcontentloaded")
        fill_repo_creation(page, ARGS.owner, repo_name)
        page.wait_for_load_state("networkidle")

        setup_link = page.get_by_role("link", name=re.compile(r"Set up my research project", re.I))
        setup_link.wait_for(state="visible", timeout=60_000)
        screenshot(page, screenshots["setup_entry"])
        time.sleep(1.0)
        setup_link.click()

        page.get_by_text("Set up your research project", exact=True).first.wait_for(
            state="visible", timeout=30_000
        )
        fill_setup_form(page)
        screenshot(page, screenshots["form"], full_page=True)
        time.sleep(1.0)

        submit = page.get_by_role("button", name=re.compile(r"Submit new issue", re.I))
        submit.click()
        page.wait_for_url(re.compile(r"/issues/\d+$"), timeout=30_000)

        success = page.get_by_text(
            re.compile(r"Your OpenResearchWorkspace project is initialized", re.I)
        )
        try:
            success.wait_for(state="visible", timeout=ARGS.timeout_seconds * 1000)
        except PlaywrightTimeoutError:
            screenshot(page, output_dir / "ERROR-initialization-timeout.png", full_page=True)
            raise RuntimeError(
                "ORW initialization did not report success within the timeout. "
                "A diagnostic screenshot was saved."
            )

        screenshot(page, screenshots["success"], full_page=True)
        time.sleep(1.0)

        open_workspace = page.get_by_role(
            "link", name=re.compile(r"Open your initialized workspace", re.I)
        )
        open_workspace.click()
        page.wait_for_url(
            re.compile(rf"github\.com/{re.escape(ARGS.owner)}/{re.escape(repo_name)}(?:/)?$"),
            timeout=30_000,
        )
        page.get_by_text("Research structure", exact=True).wait_for(state="visible")

        screenshot(page, screenshots["workspace"], full_page=True)
        time.sleep(2.0)

        page.close()
        context.close()

        recorded = list(video_dir.glob("*.webm"))
        if video is not None:
            try:
                video.save_as(str(final_video))
            except Exception:
                if recorded:
                    shutil.copy2(recorded[0], final_video)
        elif recorded:
            shutil.copy2(recorded[0], final_video)

        if final_video.exists():
            print(f"Saved video: {final_video}")
        else:
            print("Warning: no final WebM was found; screenshots were still captured.")

    shutil.rmtree(video_dir, ignore_errors=True)

    print("\nCapture complete.")
    print(f"Disposable repository left in place for review: https://github.com/{ARGS.owner}/{repo_name}")
    print("Delete it manually after you have reviewed the screenshots/video.")
    print(f"Local browser profile retained at: {profile_dir}")
    print("Delete that profile directory after the documentation capture if you no longer need it.")
    return 0


ARGS: argparse.Namespace

if __name__ == "__main__":
    raise SystemExit(main())
