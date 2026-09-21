from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]


class GitHubAdapterTests(unittest.TestCase):
    def test_issue_form_normalizes_and_initializes_through_core(self) -> None:
        issue_body = """### Project title
Effects of light exposure on mouse activity

### Short project description
Study of how altered light exposure affects spontaneous mouse activity.

### Your name
Jane Researcher

### First study title
Light exposure study

### What will you measure first?
Behaviour

### Where are the authoritative/raw data stored?
Institutional research server

### Data access level
private

### Keywords (optional)
behaviour, circadian rhythm, mouse

### Your ORCID (optional)
0000-0002-1825-0097

### Ready to initialize
- [x] I understand that submitting this form will initialize this repository as my research workspace.
"""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            event_path = tmp_path / "event.json"
            output_path = tmp_path / "github-output.txt"
            workspace_path = tmp_path / "workspace"

            event_path.write_text(
                json.dumps({"issue": {"body": issue_body}}, ensure_ascii=False),
                encoding="utf-8",
            )
            output_path.write_text("", encoding="utf-8")

            parse_env = os.environ.copy()
            parse_env.update(
                {
                    "GITHUB_EVENT_PATH": str(event_path),
                    "GITHUB_OUTPUT": str(output_path),
                }
            )
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "parse_setup_issue.py")],
                cwd=REPO_ROOT,
                env=parse_env,
                check=True,
                capture_output=True,
                text=True,
            )

            output = output_path.read_text(encoding="utf-8").strip()
            self.assertTrue(output.startswith("setup_payload="))
            setup_payload = output.split("=", 1)[1]
            normalized = json.loads(setup_payload)

            self.assertEqual(
                normalized["first_study"]["title"],
                "Light exposure study",
            )
            self.assertEqual(
                normalized["keywords"],
                ["behaviour", "circadian rhythm", "mouse"],
            )

            initialize_env = os.environ.copy()
            initialize_env.update(
                {
                    "ORW_SETUP_JSON": setup_payload,
                    "ORW_PROVIDER": "github",
                    "ORW_PROVIDER_USER": "jane-researcher",
                    "ORW_DESTINATION": str(workspace_path),
                }
            )
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "initialize_project.py")],
                cwd=REPO_ROOT,
                env=initialize_env,
                check=True,
                capture_output=True,
                text=True,
            )

            project = (
                workspace_path / ".research" / "project.yml"
            ).read_text(encoding="utf-8")
            workspace = (
                workspace_path / ".research" / "workspace.yml"
            ).read_text(encoding="utf-8")

            self.assertIn('title: "Effects of light exposure on mouse activity"', project)
            self.assertIn('identifier: "light-exposure-study"', project)
            self.assertIn('identifier: "behaviour"', project)
            self.assertIn('orcid: "0000-0002-1825-0097"', project)
            self.assertNotIn("github", project.lower())

            self.assertIn('name: "github"', workspace)
            self.assertIn('user: "jane-researcher"', workspace)


if __name__ == "__main__":
    unittest.main()
