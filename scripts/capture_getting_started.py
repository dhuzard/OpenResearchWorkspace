#!/usr/bin/env python3
"""One-shot headed Playwright capture of the ORW beginner onboarding flow.

This is documentation tooling, not permanent CI infrastructure.

It deliberately performs GitHub login in a separate, unrecorded browser context
so credentials / 2FA are never included in the documentation video. The
authenticated storage state is kept only in a temporary directory and deleted
when the script exits.

Usage:
    python -m pip install playwright
    python -m playwright install chromium
    python scripts/capture_getting_started.py --owner Neuronautix

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
import tempfile
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


def select_owner(page: Page, owner: str) -> None:
    """Best-effort selection of the repository owner on GitHub's new-repo page.

    GitHub occasionally changes this control. If the automated selectors stop
    matching, the script pauses and lets the user select the owner manually.
    """
    body = page.locator("body")
    if re.search(rf"\b{re.escape(owner)}\b", body.inner_text(), flags=re.IGNORECASE):
        # The requested owner may already be selected.
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

    # Prefer private for the documentation path because that is the intended
    # default for ongoing / unpublished research.
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


def main() -> int:
    args = parse_args()
    repo_name = args.repo_name or (
        "ORW-doc-demo-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    )
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    screenshots = {
        "template": output_dir / "01-use-template.png",
        "setup_entry": output_dir / "02-setup-project.png",
        "form": output_dir / "03-setup-form.png",
        "success": output_dir / "04-initialized-success.png",
        "workspace": output_dir / "05-initialized-workspace.png",
    }
    final_video = output_dir / "orw-getting-started.webm"

    print(f"Disposable repository: {args.owner}/{repo_name}")
    print(f"Output directory: {output_dir}")

    with tempfile.TemporaryDirectory(prefix="orw-playwright-") as tmpdir:
        tmp = Path(tmpdir)
        storage_state = tmp / "github-auth.json"
        video_dir = tmp / "video"
        video_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            # Login happens outside the recorded documentation session.
            login_context = browser.new_context(viewport={"width": 1440, "height": 1000})
            login_page = login_context.new_page()
            login_page.goto("https://github.com/login", wait_until="domcontentloaded")
            print("\nLog into GitHub in the opened browser window (including 2FA if needed).")
            input("When GitHub login is complete, return here and press Enter... ")
            login_context.storage_state(path=str(storage_state))
            login_context.close()

            # Start a fresh authenticated context. Only this context is recorded.
            context = browser.new_context(
                storage_state=str(storage_state),
                viewport={"width": 1440, "height": 1000},
                record_video_dir=str(video_dir),
                record_video_size={"width": 1440, "height": 1000},
            )
            page = context.new_page()
            video = page.video

            # 1. Template entry point.
            page.goto(TEMPLATE_REPO, wait_until="networkidle")
            page.get_by_text("OpenResearchWorkspace", exact=True).first.wait_for(state="visible")
            screenshot(page, screenshots["template"])
            time.sleep(1.0)

            # Use direct template-new URL after capturing the real template page;
            # this avoids depending on GitHub's transient dropdown implementation.
            page.goto(TEMPLATE_NEW, wait_until="domcontentloaded")
            fill_repo_creation(page, args.owner, repo_name)
            page.wait_for_load_state("networkidle")

            # 2. Setup entry point in the newly-created repository README.
            setup_link = page.get_by_role("link", name=re.compile(r"Set up my research project", re.I))
            setup_link.wait_for(state="visible", timeout=60_000)
            screenshot(page, screenshots["setup_entry"])
            time.sleep(1.0)
            setup_link.click()

            # 3. Real GitHub Issue Form.
            page.get_by_text("Set up your research project", exact=True).first.wait_for(
                state="visible", timeout=30_000
            )
            fill_setup_form(page)
            screenshot(page, screenshots["form"], full_page=True)
            time.sleep(1.0)

            submit = page.get_by_role("button", name=re.compile(r"Submit new issue", re.I))
            submit.click()
            page.wait_for_url(re.compile(r"/issues/\d+$"), timeout=30_000)

            # 4. Wait for the real ORW workflow to finish and post its success message.
            success = page.get_by_text(
                re.compile(r"Your OpenResearchWorkspace project is initialized", re.I)
            )
            try:
                success.wait_for(state="visible", timeout=args.timeout_seconds * 1000)
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
                re.compile(rf"github\.com/{re.escape(args.owner)}/{re.escape(repo_name)}(?:/)?$"),
                timeout=30_000,
            )
            page.get_by_text("Research structure", exact=True).wait_for(state="visible")

            # 5. Final initialized workspace.
            screenshot(page, screenshots["workspace"], full_page=True)
            time.sleep(2.0)

            page.close()
            context.close()
            browser.close()

            # Save the single documentation video under a stable name.
            if video is not None:
                video.save_as(str(final_video))
                print(f"Saved video: {final_video}")
            else:
                recorded = list(video_dir.glob("*.webm"))
                if recorded:
                    shutil.copy2(recorded[0], final_video)
                    print(f"Saved video: {final_video}")

    print("\nCapture complete.")
    print(f"Disposable repository left in place for review: https://github.com/{args.owner}/{repo_name}")
    print("Delete it manually after you have reviewed the screenshots/video.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
