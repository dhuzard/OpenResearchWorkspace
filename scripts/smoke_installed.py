"""Exercise the installed wheel/sdist from outside the repository (stdlib only)."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    import orw
    assert orw.__version__ == args.version
    assert importlib.metadata.version("openresearchworkspace") == args.version
    assert Path(orw.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), orw.__file__
    executable = Path(sys.executable).parent / ("orw.exe" if os.name == "nt" else "orw")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        payload = {"project_title": "Alpha smoke test", "project_description": "Synthetic data only.",
                   "creator": {"name": "Release test"}, "first_study": {"title": "Study"},
                   "first_assay": None, "data": {"location": "Local storage", "access": "private"}}
        (root / "setup.json").write_text(json.dumps(payload), encoding="utf-8")
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONUTF8"] = "1"
        def run(*arguments, code=0):
            result = subprocess.run([str(executable), *arguments], cwd=root, env=env,
                                    capture_output=True, text=True, encoding="utf-8")
            assert result.returncode == code, (arguments, result.returncode, result.stdout, result.stderr)
            return result.stdout
        assert args.version in run("--version")
        run("init", "study", "--config", "setup.json")
        # Mutations, including a dry run and the refusal paths, on the installed CLI.
        run("study", "add", "Second study", "--workspace", "study", "--dry-run")
        assert not (root / "study/studies/second-study").exists()
        plan = json.loads(run("study", "add", "Second study", "--workspace", "study",
                              "--dry-run", "--json"))
        assert plan["applied"] is False and plan["operation"] == "study.add", plan
        run("study", "add", "Second study", "--workspace", "study")
        run("study", "add", "Second study", "--workspace", "study", code=5)
        run("study", "add", "Third", "--workspace", "study", "--id", "Not A Slug", code=2)
        run("assay", "add", "Open field", "--study", "second-study", "--workspace", "study")
        run("contributor", "add", "Second author", "--orcid", "0000-0002-1825-0097",
            "--workspace", "study")
        run("resource", "add", "External archive", "--location", "Local storage",
            "--access", "private", "--workspace", "study")
        run("metadata", "set", "--status", "paused", "--keyword", "smoke",
            "--workspace", "study")
        assert (root / "study/studies/second-study/assays/open-field/data/raw").is_dir()
        assert json.loads(run("validate", "study", "--json"))["valid"]
        run("export", "study", "--output", "crate")
        run("export", "study", "--output", "crate", "--force")
        run("export", "study", "--output", "study/project-docs", "--force", code=4)
        (root / "occupied").mkdir()
        original = root / "occupied/README.md"
        original.write_text("preserve me", encoding="utf-8")
        run("init", "occupied", "--config", "setup.json", code=2)
        assert original.read_text(encoding="utf-8") == "preserve me"
        (root / "crate/user-note.txt").write_text("keep", encoding="utf-8")
        run("export", "study", "--output", "crate", "--force", code=4)
        assert (root / "crate/user-note.txt").read_text(encoding="utf-8") == "keep"
    print(f"Installed artifact smoke checks passed: {args.version}")


if __name__ == "__main__":
    main()
