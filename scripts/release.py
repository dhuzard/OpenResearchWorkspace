"""Release utilities: build once, verify registry bytes, promote without rebuilding.

Only explicit publish jobs mint OIDC credentials. This script performs reads,
artifact checks and local installation tests; it never uploads to a registry.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "dhuzard/OpenResearchWorkspace"
WORKFLOW = ".github/workflows/release-alpha.yml"
INDEXES = {"testpypi": "https://test.pypi.org", "pypi": "https://pypi.org"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def version_from_source() -> str:
    tree = ast.parse((ROOT / "src/orw/_version.py").read_text(encoding="utf-8"))
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets))


def alpha_version(value: str) -> str:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+a[0-9]+", value):
        raise ValueError("An explicit alpha version such as 0.1.0a1 is required.")
    return value


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run(*args, **kwargs):
    subprocess.run([str(value) for value in args], check=True, **kwargs)


def github(resource: str):
    token = os.environ.get("GH_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ORW-release"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/repos/{REPOSITORY}/{resource}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def check_run(data: dict, run_id: str) -> dict:
    if (str(data.get("id")) != run_id or data.get("event") != "workflow_dispatch"
            or data.get("conclusion") != "success" or data.get("head_branch") != "main"
            or data.get("path", "").split("@")[0] != WORKFLOW
            or data.get("repository", {}).get("full_name") != REPOSITORY
            or not re.fullmatch(r"[0-9a-f]{40}", data.get("head_sha", ""))):
        raise ValueError("Run is not a successful main-branch rehearsal from the expected repository/workflow.")
    return data


def rehearsal_run(run_id: str) -> dict:
    if not run_id.isdecimal() or int(run_id) <= 0:
        raise ValueError("A numeric successful TestPyPI rehearsal run ID is required.")
    return check_run(github(f"actions/runs/{run_id}"), run_id)


def guard(phase: str, version: str, run_id: str, confirmation: str):
    alpha_version(version)
    if (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise ValueError("Publishing is only supported by explicit dispatch on the original repository's main branch.")
    environment = github(f"environments/{phase}")
    if not any(rule.get("type") == "required_reviewers" and rule.get("reviewers")
               for rule in environment.get("protection_rules", [])):
        raise ValueError(f"Configure at least one required reviewer for the {phase} environment before publishing.")
    if phase == "testpypi":
        if version != version_from_source():
            raise ValueError("Requested version does not match the source version.")
    else:
        if confirmation != f"publish {version}":
            raise ValueError(f"Public promotion requires the exact confirmation: publish {version}")
        rehearsal_run(run_id)


def verify_bundle(directory: Path, version: str) -> dict:
    manifest = load_json(directory / "manifest.json")
    if (manifest.get("format") != 1 or manifest.get("version") != alpha_version(version)
            or manifest.get("repository") != REPOSITORY
            or not re.fullmatch(r"[0-9a-f]{40}", manifest.get("source_sha", ""))):
        raise ValueError("Invalid release manifest identity.")
    expected = manifest.get("files", {})
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Manifest has no files.")
    package_names = [name for name in expected if name.startswith("packages/")]
    if (len(package_names) != 2 or sum(name.endswith(".whl") for name in package_names) != 1
            or sum(name.endswith(".tar.gz") for name in package_names) != 1):
        raise ValueError("Manifest must contain one wheel and one sdist.")
    for name, checksum in expected.items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name
                or not re.fullmatch(r"[0-9a-f]{64}", checksum)):
            raise ValueError("Unsafe manifest path or digest.")
        path = directory.joinpath(*relative.parts)
        if path.is_symlink() or not path.is_file() or digest(path) != checksum:
            raise ValueError(f"Artifact content differs from manifest: {name}")
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if actual - {"manifest.json", "rehearsal.json"} != set(expected):
        raise ValueError("Unlisted/missing release artifact files.")
    return manifest


def build(directory: Path, version: str):
    if version != version_from_source():
        raise ValueError("Version differs from source.")
    if directory.exists():
        raise ValueError("Build directory already exists; use a fresh directory.")
    directory.mkdir(parents=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True).strip()
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = epoch
    run(sys.executable, "-m", "build", "--outdir", directory / "packages", cwd=ROOT, env=env)
    artifacts = sorted((directory / "packages").iterdir())
    run(sys.executable, "-m", "twine", "check", "--strict", *artifacts, cwd=ROOT)
    run(sys.executable, ROOT / "scripts/test_distributions.py", directory / "packages", "--version", version)
    with tempfile.TemporaryDirectory() as temporary:
        run(sys.executable, ROOT / "scripts/build_browser.py", "--output", temporary)
        shutil.copyfile(Path(temporary) / "index.html", directory / "index.html")
    shutil.copyfile(ROOT / "LICENSE", directory / "LICENSE")
    archive = directory / f"orw-browser-generator-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in ("index.html", "LICENSE"):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(entry, (directory / name).read_bytes())
    manifest = {"format": 1, "version": alpha_version(version), "source_sha": sha,
                "repository": REPOSITORY, "files": {p.relative_to(directory).as_posix(): digest(p)
                for p in sorted(directory.rglob("*")) if p.is_file()}}
    save_json(directory / "manifest.json", manifest)
    verify_bundle(directory, version)


def check_registry_listing(data: dict, manifest: dict) -> dict:
    expected = {Path(name).name: checksum for name, checksum in manifest["files"].items() if name.startswith("packages/")}
    rows = data.get("urls", [])
    listed = {row.get("filename"): row for row in rows}
    if set(listed) != set(expected) or len(rows) != len(expected):
        raise ValueError("Registry artifact names do not match the frozen release.")
    if data.get("info", {}).get("version") != manifest["version"]:
        raise ValueError("Registry version mismatch.")
    for name, checksum in expected.items():
        if listed[name].get("digests", {}).get("sha256") != checksum:
            raise ValueError(f"Registry artifact checksum differs: {name}")
    return listed


def registry(directory: Path, version: str, index: str):
    manifest = verify_bundle(directory, version)
    url = f"{INDEXES[index]}/pypi/openresearchworkspace/{version}/json"
    for attempt in range(12):
        try:
            with urlopen(url, timeout=30) as response:
                data = json.load(response)
            listed = check_registry_listing(data, manifest)
            break
        except HTTPError as exc:
            if exc.code != 404 or attempt == 11:
                raise
            time.sleep(10)
    with tempfile.TemporaryDirectory(prefix="orw-registry-readback-") as temporary:
        downloaded = Path(temporary)
        for name, row in listed.items():
            parsed = urlparse(row["url"])
            if parsed.scheme != "https" or parsed.hostname not in {"files.pythonhosted.org", "test-files.pythonhosted.org"}:
                raise ValueError("Unexpected package download host.")
            target = downloaded / name
            with urlopen(row["url"], timeout=60) as response, target.open("xb") as output:
                shutil.copyfileobj(response, output)
            if digest(target) != row["digests"]["sha256"]:
                raise ValueError("Downloaded registry bytes failed checksum verification.")
        run(sys.executable, ROOT / "scripts/test_distributions.py", downloaded, "--version", version)
    if index == "testpypi" and not (directory / "rehearsal.json").exists():
        save_json(directory / "rehearsal.json", {"index": index, "version": version,
            "source_sha": manifest["source_sha"], "run_id": os.environ["GITHUB_RUN_ID"],
            "repository": REPOSITORY, "manifest_sha256": digest(directory / "manifest.json")})
    print(f"{index}: both frozen artifacts downloaded, hash-checked and installed successfully.")


def promotion(directory: Path, version: str, run_id: str):
    run_data = rehearsal_run(run_id)
    manifest = verify_bundle(directory, version)
    proof = load_json(directory / "rehearsal.json")
    expected = {"index": "testpypi", "version": version, "source_sha": run_data["head_sha"],
                "run_id": run_id, "repository": REPOSITORY,
                "manifest_sha256": digest(directory / "manifest.json")}
    if proof != expected or manifest["source_sha"] != run_data["head_sha"]:
        raise ValueError("Rehearsal proof/manifest does not match the successful source run.")
    run("git", "merge-base", "--is-ancestor", manifest["source_sha"], "HEAD", cwd=ROOT)
    # Refuse promotion if TestPyPI has disappeared or no longer matches.
    registry(directory, version, "testpypi")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"source_sha={manifest['source_sha']}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["guard", "build", "verify", "registry", "promotion"])
    parser.add_argument("--directory", type=Path, default=Path("candidate"))
    parser.add_argument("--version", default=os.environ.get("VERSION", ""))
    parser.add_argument("--index", choices=tuple(INDEXES), default=os.environ.get("PHASE", "testpypi"))
    parser.add_argument("--run-id", default=os.environ.get("REHEARSAL_RUN", ""))
    args = parser.parse_args()
    version = alpha_version(args.version)
    if args.command == "guard":
        guard(args.index, version, args.run_id, os.environ.get("CONFIRMATION", ""))
    elif args.command == "build":
        build(args.directory.resolve(), version)
    elif args.command == "verify":
        verify_bundle(args.directory, version)
    elif args.command == "registry":
        registry(args.directory, version, args.index)
    else:
        promotion(args.directory, version, args.run_id)


if __name__ == "__main__":
    main()
