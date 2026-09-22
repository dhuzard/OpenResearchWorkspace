"""Build-independent installation tests for exact release artifacts."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def test_artifacts(directory: Path, version: str) -> None:
    artifacts = sorted(directory.glob("*.whl")) + sorted(directory.glob("*.tar.gz"))
    if len(artifacts) != 2:
        raise ValueError("Expected exactly one wheel and one source distribution.")
    smoke = Path(__file__).with_name("smoke_installed.py").resolve()
    for artifact in artifacts:
        with tempfile.TemporaryDirectory(prefix="orw-installed-") as temporary:
            root = Path(temporary)
            environment = root / "env"
            venv.EnvBuilder(with_pip=True).create(environment)
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["PYTHONUTF8"] = "1"
            command = [str(python), "-m", "pip", "--isolated", "install", "--index-url", "https://pypi.org/simple/"]
            subprocess.run([*command, "PyYAML>=6.0,<7", "jsonschema>=4.22,<5"], cwd=root, env=env, check=True)
            # TestPyPI artifacts are downloaded and hash-checked separately.
            # Do not mix dependency indexes or resolve project names on TestPyPI.
            subprocess.run([*command, "--no-deps", str(artifact.resolve())], cwd=root, env=env, check=True)
            subprocess.run([str(python), str(smoke), "--version", version], cwd=root, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    test_artifacts(args.directory, args.version)


if __name__ == "__main__":
    main()
