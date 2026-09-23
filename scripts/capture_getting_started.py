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
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import (
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

TEMPLATE_REPO = "https://github.com/dhuzard/OpenResearchWorkspace-template"
TEMPLATE_NEW = (
    "https://github.com/new?template_name=OpenResearchWorkspace-template&template_owner=dhuzard"
)
GUIDE_STEP = 0


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
        "--resume-existing",
        action="store_true",
        help="Resume capture from an existing --repo-name instead of creating it again.",
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


def clear_video_guide(page: Page) -> None:
    """Remove the temporary instructional overlay and target highlight."""
    page.evaluate(
        """() => {
            document.getElementById('orw-video-guide')?.remove();
            document.getElementById('orw-video-guide-style')?.remove();
            document.querySelectorAll('.orw-video-guide-target').forEach(
                (node) => node.classList.remove('orw-video-guide-target')
            );
        }"""
    )


def show_video_guide(
    page: Page, message: str, target=None, *, seconds: float = 1.4
) -> None:
    """Burn a step caption and optional control highlight into the recorded page."""
    global GUIDE_STEP
    GUIDE_STEP += 1
    clear_video_guide(page)

    if target is not None:
        target.first.scroll_into_view_if_needed()
        target.first.evaluate(
            "element => element.classList.add('orw-video-guide-target')"
        )

    page.evaluate(
        """({step, message}) => {
            const style = document.createElement('style');
            style.id = 'orw-video-guide-style';
            style.textContent = `
                .orw-video-guide-target {
                    outline: 5px solid #f7c843 !important;
                    outline-offset: 4px !important;
                    box-shadow: 0 0 0 10px rgba(247, 200, 67, .28) !important;
                    border-radius: 6px !important;
                }
                #orw-video-guide {
                    position: fixed;
                    top: 22px;
                    left: 50%;
                    transform: translateX(-50%);
                    z-index: 2147483647;
                    max-width: 760px;
                    padding: 14px 20px;
                    border: 2px solid #f7c843;
                    border-radius: 10px;
                    background: rgba(13, 17, 23, .96);
                    color: white;
                    font: 600 18px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    text-align: center;
                    box-shadow: 0 8px 30px rgba(0, 0, 0, .35);
                    pointer-events: none;
                }
                #orw-video-guide strong { color: #f7c843; }
            `;
            document.head.appendChild(style);

            const guide = document.createElement('div');
            guide.id = 'orw-video-guide';
            const label = document.createElement('strong');
            label.textContent = `Step ${step}: `;
            guide.append(label, document.createTextNode(message));
            document.body.appendChild(guide);
        }""",
        {"step": GUIDE_STEP, "message": message},
    )
    page.wait_for_timeout(int(seconds * 1000))


def guided_fill(page: Page, locator, value: str, message: str) -> None:
    show_video_guide(page, message, locator)
    locator.first.fill(value)
    clear_video_guide(page)


def guided_choose(page: Page, label: str, option: str, message: str) -> None:
    control = page.get_by_label(label)
    show_video_guide(page, message, control)
    tag = control.first.evaluate("element => element.tagName")
    if tag == "SELECT":
        control.first.select_option(label=option)
    else:
        control.first.click()
        candidate = page.get_by_text(option, exact=True)
        candidate.first.wait_for(state="visible", timeout=10_000)
        candidate.first.click()
    clear_video_guide(page)


def get_page(context) -> Page:
    pages = context.pages
    return pages[0] if pages else context.new_page()


def github_is_authenticated(page: Page) -> bool:
    """Return whether the persistent browser profile is authenticated to GitHub."""
    page.goto("https://github.com/settings/profile", wait_until="domcontentloaded")
    # An unauthenticated request is redirected to /login. Do not look for an
    # email-labelled control: the authenticated profile settings page contains
    # an email setting too, which caused valid sessions to be rejected.
    return urlparse(page.url).path.rstrip("/") == "/settings/profile"


def find_chrome_executable() -> str:
    """Find an installed Chrome executable without relying on Playwright."""
    candidates: list[str | None] = [
        shutil.which("google-chrome"),
        shutil.which("chrome"),
    ]

    if sys.platform == "win32":
        candidates.extend(
            str(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
            for base in (
                os.environ.get("PROGRAMFILES"),
                os.environ.get("PROGRAMFILES(X86)"),
                os.environ.get("LOCALAPPDATA"),
            )
            if base
        )
    elif sys.platform == "darwin":
        candidates.append(
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
    else:
        candidates.extend(
            [
                shutil.which("google-chrome-stable"),
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
            ]
        )

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate

    raise RuntimeError(
        "Could not find installed Google Chrome. Install Chrome or use --browser chromium "
        "and authenticate with a GitHub method that does not depend on Google sign-in."
    )


def authenticate_in_normal_chrome(profile_dir: Path) -> None:
    """Open Chrome outside Playwright so identity-provider login is not automated."""
    chrome = find_chrome_executable()
    command = [
        chrome,
        f"--user-data-dir={profile_dir}",
        "--profile-directory=Default",
        "--disable-background-mode",
        "https://github.com/login",
    ]

    print("\nGitHub is not authenticated in the dedicated documentation profile.")
    print("Opening a normal Google Chrome window outside Playwright.")
    print(
        "Sign into GitHub there, including 2FA/passkey/device verification if requested."
    )
    print(
        "Then CLOSE that Chrome window completely so the profile can be reopened safely."
    )
    process = subprocess.Popen(command)
    input("After Chrome is closed, press Enter to continue... ")

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "The authentication Chrome process is still running. Close the dedicated Chrome "
            "window completely, then rerun the command."
        ) from exc


def select_owner(page: Page, owner: str) -> None:
    """Best-effort selection of the repository owner on GitHub's new-repo page."""
    selected_owner = page.get_by_role(
        "button", name=re.compile(rf"^{re.escape(owner)},\s*Owner", re.I)
    )
    if selected_owner.count() and selected_owner.first.is_visible():
        return

    owner_button = page.get_by_role(
        "button", name=re.compile(r"Owner\s*\(Required\)", re.I)
    )
    try:
        owner_button.first.wait_for(state="visible", timeout=10_000)
        show_video_guide(page, f"Choose {owner} as the repository owner.", owner_button)
        owner_button.first.click()
        option = page.get_by_text(owner, exact=True)
        option.first.wait_for(state="visible", timeout=10_000)
        show_video_guide(page, f"Select {owner} from the owner list.", option)
        option.first.click()
        selected_owner.first.wait_for(state="visible", timeout=10_000)
        clear_video_guide(page)
        return
    except PlaywrightError:
        pass

    print("\nCould not select the GitHub repository owner automatically.")
    print(f"In the browser, select owner '{owner}', then return here.")
    input("Press Enter after the owner is selected... ")


def fill_repo_creation(page: Page, owner: str, repo_name: str) -> None:
    select_owner(page, owner)

    name_input = page.get_by_label(re.compile(r"repository name", re.I))
    if not name_input.count():
        name_input = page.locator(
            "input[name='repository[name]'], input#repository_name"
        )
    guided_fill(
        page,
        name_input,
        repo_name,
        "Enter a unique name for the new research workspace.",
    )

    private_radio = page.get_by_label(re.compile(r"^private$", re.I))
    if private_radio.count() and private_radio.first.is_visible():
        private_radio.first.check()
    else:
        visibility = page.get_by_role(
            "button", name=re.compile(r"^(Public|Private|Internal)$")
        )
        if (
            visibility.count()
            and visibility.first.inner_text().strip().lower() != "private"
        ):
            show_video_guide(
                page, "Open the repository visibility choices.", visibility
            )
            visibility.first.click()
            private_option = page.get_by_text("Private", exact=True)
            private_option.first.wait_for(state="visible", timeout=10_000)
            show_video_guide(
                page,
                "Keep research setup private while getting started.",
                private_option,
            )
            private_option.first.click()
            clear_video_guide(page)

    print(f"Waiting for GitHub to validate repository name '{repo_name}'...")
    try:
        page.get_by_text(
            re.compile(rf"^{re.escape(repo_name)} is available\.$", re.I)
        ).wait_for(state="visible", timeout=30_000)
    except PlaywrightTimeoutError as exc:
        screenshot(
            page,
            Path(ARGS.output_dir).resolve() / "ERROR-repository-form.png",
            full_page=True,
        )
        raise RuntimeError(
            f"GitHub did not confirm that repository name '{repo_name}' is available. "
            "A diagnostic screenshot was saved."
        ) from exc

    create_button = page.get_by_role(
        "button", name=re.compile(r"create repository", re.I)
    )
    create_button.first.wait_for(state="visible")
    print(f"Creating repository {owner}/{repo_name}...")
    show_video_guide(
        page, "Create the repository from the ORW template.", create_button
    )
    create_button.first.click()
    try:
        page.wait_for_url(
            re.compile(
                rf"github\.com/{re.escape(owner)}/{re.escape(repo_name)}(?:/)?$"
            ),
            wait_until="domcontentloaded",
            timeout=120_000,
        )
    except PlaywrightError as exc:
        if not page.is_closed():
            screenshot(
                page,
                Path(ARGS.output_dir).resolve() / "ERROR-repository-creation.png",
                full_page=True,
            )
            current_url = page.url
        else:
            current_url = "browser closed"
        raise RuntimeError(
            f"GitHub did not create {owner}/{repo_name}. Current page: {current_url}. "
            "A diagnostic screenshot was saved if the browser remained open."
        ) from exc

    print(f"Repository created: https://github.com/{owner}/{repo_name}")


def fill_setup_form(page: Page) -> None:
    guided_fill(
        page,
        page.get_by_label("Project title"),
        "Effects of light exposure on mouse activity",
        "Enter the overall research project title.",
    )
    guided_fill(
        page,
        page.get_by_label("What is this project about?"),
        "Study of how altered light exposure affects spontaneous mouse activity.",
        "Briefly describe the research question or objective.",
    )
    guided_fill(
        page,
        page.get_by_label("Your name"),
        "Jane Researcher",
        "Enter the project creator's name.",
    )

    guided_choose(
        page,
        "How is this research organized?",
        "One Study — this project is essentially one Study",
        "Choose the simplest Study structure that fits the project.",
    )
    guided_choose(
        page,
        "Do your Studies contain several distinct measurement types?",
        "No — keep data, analysis and results directly at Study level",
        "Keep the initial project flat when a separate Assay layer is unnecessary.",
    )
    guided_choose(
        page,
        "Do you want to keep protocol documents in this workspace?",
        "Yes — create a protocols folder",
        "Choose whether protocol documents should have a folder in this workspace.",
    )

    guided_fill(
        page,
        page.get_by_label("Where are the authoritative or raw data stored?"),
        "Institutional research server",
        "Record the authoritative data location without entering secrets.",
    )
    guided_choose(
        page,
        "Current data access",
        "private",
        "Choose the current access level for the authoritative data.",
    )

    guided_fill(
        page,
        page.get_by_label("Keywords (optional)"),
        "behaviour, circadian rhythm, mouse",
        "Add a few searchable project keywords.",
    )

    ready = page.get_by_label(
        re.compile(r"I understand that submitting this form will initialize", re.I)
    )
    show_video_guide(
        page, "Confirm that the repository is ready to be initialized.", ready
    )
    ready.check()
    clear_video_guide(page)


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
    if ARGS.resume_existing and not ARGS.repo_name:
        raise RuntimeError("--resume-existing requires --repo-name.")

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
        # Open the capture context once and keep it alive after authentication.
        # Closing and immediately reopening a persistent Chrome profile can race
        # with Chrome's asynchronous shutdown and close the replacement context.
        try:
            context = launch_persistent(p, profile_dir, record_video_dir=video_dir)
        except Exception as exc:
            if ARGS.browser == "chrome":
                raise RuntimeError(
                    "Could not launch installed Google Chrome. Install Chrome or rerun with --browser chromium "
                    "after `python -m playwright install chromium`."
                ) from exc
            raise

        auth_page = get_page(context)
        authenticated = github_is_authenticated(auth_page)

        if not authenticated:
            context.close()
            if ARGS.browser != "chrome":
                raise RuntimeError(
                    "The Chromium profile is not authenticated. Rerun with --browser chrome so "
                    "the script can open a normal installed Chrome window for sign-in."
                )
            authenticate_in_normal_chrome(profile_dir)

            context = launch_persistent(p, profile_dir, record_video_dir=video_dir)
            auth_page = get_page(context)
            authenticated = github_is_authenticated(auth_page)
            if not authenticated:
                context.close()
                raise RuntimeError(
                    "GitHub is still not authenticated in the dedicated profile. Do not keep "
                    "retrying credentials in an automated browser. See "
                    "docs/CAPTURE_GETTING_STARTED.md for recovery options."
                )

        print("GitHub authentication confirmed.")

        # Reuse the persistent context's initial page. Closing that page after
        # creating a second recorded page can make headed Chrome terminate the
        # entire persistent context (TargetClosedError on the next navigation).
        page = auth_page
        video = page.video

        # GitHub keeps background connections active, so "networkidle" may
        # never occur. The following element wait is the real readiness check.
        page.goto(TEMPLATE_REPO, wait_until="domcontentloaded")
        page.get_by_text("OpenResearchWorkspace Template", exact=True).first.wait_for(
            state="visible"
        )
        screenshot(page, screenshots["template"])
        use_template = page.get_by_role(
            "button", name=re.compile(r"Use this template", re.I)
        )
        if use_template.count():
            show_video_guide(
                page,
                "Start by using the ORW template to create your own project.",
                use_template,
            )
            clear_video_guide(page)

        if ARGS.resume_existing:
            existing_repo = f"https://github.com/{ARGS.owner}/{repo_name}"
            print(f"Resuming existing repository: {existing_repo}")
            page.goto(existing_repo, wait_until="domcontentloaded")
            if page.title().lower().startswith("page not found"):
                raise RuntimeError(
                    f"Cannot resume because {ARGS.owner}/{repo_name} was not found."
                )
        else:
            page.goto(TEMPLATE_NEW, wait_until="domcontentloaded")
            fill_repo_creation(page, ARGS.owner, repo_name)
            page.wait_for_load_state("domcontentloaded")

        setup_link = page.locator("a[href$='/issues/new?template=orw-setup.yml']")
        setup_link.wait_for(state="visible", timeout=60_000)
        setup_link.scroll_into_view_if_needed()
        screenshot(page, screenshots["setup_entry"])
        show_video_guide(page, "Open the guided ORW project setup form.", setup_link)
        setup_link.click()

        page.get_by_text("Set up your research project", exact=True).first.wait_for(
            state="visible", timeout=30_000
        )
        fill_setup_form(page)
        screenshot(page, screenshots["form"], full_page=True)
        time.sleep(1.0)

        submit = page.locator("button").filter(
            has_text=re.compile(r"^\s*(Submit new issue|Create)\s*(?:\(|$)", re.I)
        )
        submit.first.wait_for(state="visible", timeout=30_000)
        show_video_guide(
            page, "Submit the form to initialize the research workspace.", submit
        )
        submit.first.click()
        page.wait_for_url(re.compile(r"/issues/\d+$"), timeout=30_000)

        success = page.get_by_text(
            re.compile(r"Your OpenResearchWorkspace project is initialized", re.I)
        )
        try:
            success.wait_for(state="visible", timeout=ARGS.timeout_seconds * 1000)
        except PlaywrightTimeoutError:
            screenshot(
                page, output_dir / "ERROR-initialization-timeout.png", full_page=True
            )
            raise RuntimeError(
                "ORW initialization did not report success within the timeout. "
                "A diagnostic screenshot was saved."
            )

        screenshot(page, screenshots["success"], full_page=True)
        time.sleep(1.0)

        open_workspace = page.get_by_role(
            "link", name=re.compile(r"Open your initialized workspace", re.I)
        )
        show_video_guide(
            page, "Open the initialized research workspace.", open_workspace
        )
        open_workspace.click()
        page.wait_for_url(
            re.compile(
                rf"github\.com/{re.escape(ARGS.owner)}/{re.escape(repo_name)}(?:/)?$"
            ),
            timeout=30_000,
        )
        clear_video_guide(page)
        page.get_by_text("Your research structure", exact=True).wait_for(state="visible")

        screenshot(page, screenshots["workspace"], full_page=True)
        show_video_guide(
            page,
            "Done — the repository is now an initialized OpenResearchWorkspace.",
            seconds=2.5,
        )
        clear_video_guide(page)

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
    print(
        f"Disposable repository left in place for review: https://github.com/{ARGS.owner}/{repo_name}"
    )
    print("Delete it manually after you have reviewed the screenshots/video.")
    print(f"Local browser profile retained at: {profile_dir}")
    print(
        "Delete that profile directory after the documentation capture if you no longer need it."
    )
    return 0


ARGS: argparse.Namespace

if __name__ == "__main__":
    raise SystemExit(main())
