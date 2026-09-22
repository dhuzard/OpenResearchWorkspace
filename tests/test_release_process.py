"""Offline tests for release identity and fail-closed publishing prerequisites."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("orw_release", ROOT / "scripts/release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bundle = Path(self.tmp.name) / "candidate"
        (self.bundle / "packages").mkdir(parents=True)
        self.version = "0.1.0a1"
        for name, data in {
            "packages/openresearchworkspace-0.1.0a1-py3-none-any.whl": b"synthetic wheel bytes",
            "packages/openresearchworkspace-0.1.0a1.tar.gz": b"synthetic sdist bytes",
            "index.html": b"synthetic browser bytes",
        }.items():
            (self.bundle / name).write_bytes(data)
        self.manifest = {
            "format": 1, "version": self.version, "source_sha": "a" * 40,
            "repository": release.REPOSITORY,
            "files": {p.relative_to(self.bundle).as_posix(): release.digest(p)
                      for p in sorted(self.bundle.rglob("*")) if p.is_file()},
        }
        release.save_json(self.bundle / "manifest.json", self.manifest)
        self.run = {
            "id": 123, "event": "workflow_dispatch", "conclusion": "success",
            "head_branch": "main", "path": release.WORKFLOW,
            "repository": {"full_name": release.REPOSITORY}, "head_sha": "a" * 40,
        }
        self.env = {
            "GITHUB_REPOSITORY": release.REPOSITORY,
            "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "workflow_dispatch",
        }
        self.protected = {"protection_rules": [{"type": "required_reviewers", "reviewers": [{"type": "User"}]}]}

    def test_explicit_alpha_and_source_version(self):
        self.assertEqual(release.version_from_source(), self.version)
        self.assertEqual(release.alpha_version(self.version), self.version)
        for value in ("0.1.0", "v0.1.0a1", "0.1.0rc1", "0.1.0a1; echo injected"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                release.alpha_version(value)

    def test_manifest_accepts_exact_artifacts(self):
        self.assertEqual(release.verify_bundle(self.bundle, self.version), self.manifest)

    def test_changed_artifact_is_refused(self):
        (self.bundle / "index.html").write_bytes(b"different bytes")
        with self.assertRaises(ValueError):
            release.verify_bundle(self.bundle, self.version)

    def test_unlisted_file_is_refused(self):
        (self.bundle / "extra.whl").write_bytes(b"unexpected")
        with self.assertRaises(ValueError):
            release.verify_bundle(self.bundle, self.version)

    def test_traversing_manifest_is_refused(self):
        self.manifest["files"]["../outside"] = "a" * 64
        release.save_json(self.bundle / "manifest.json", self.manifest)
        with self.assertRaises(ValueError):
            release.verify_bundle(self.bundle, self.version)

    def test_wrong_version_is_refused(self):
        with self.assertRaises(ValueError):
            release.verify_bundle(self.bundle, "0.1.0a2")

    def test_registry_requires_exact_names_and_digests(self):
        data = {"info": {"version": self.version}, "urls": [
            {"filename": Path(name).name, "digests": {"sha256": checksum}}
            for name, checksum in self.manifest["files"].items() if name.startswith("packages/")
        ]}
        self.assertEqual(len(release.check_registry_listing(data, self.manifest)), 2)
        for mutation in ("digest", "extra", "version"):
            altered = deepcopy(data)
            if mutation == "digest":
                altered["urls"][0]["digests"]["sha256"] = "0" * 64
            elif mutation == "extra":
                altered["urls"].append(altered["urls"][0])
            else:
                altered["info"]["version"] = "0.1.0a2"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                release.check_registry_listing(altered, self.manifest)

    def test_rehearsal_run_identity_is_fail_closed(self):
        self.assertEqual(release.check_run(self.run, "123"), self.run)
        for key, value in (("event", "pull_request"), ("head_branch", "feature"),
                           ("conclusion", "failure"), ("path", "other.yml"),
                           ("head_sha", "not-a-sha"), ("repository", {"full_name": "other/repo"})):
            altered = dict(self.run, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                release.check_run(altered, "123")

    def test_publishing_requires_original_main_dispatch(self):
        for key, value in (("GITHUB_REF", "refs/heads/feature"),
                           ("GITHUB_REPOSITORY", "other/repo"),
                           ("GITHUB_EVENT_NAME", "pull_request")):
            with self.subTest(key=key), patch.dict(release.os.environ, dict(self.env, **{key: value}), clear=True):
                with self.assertRaises(ValueError), patch.object(release, "github") as request:
                    release.guard("testpypi", self.version, "", "")
                request.assert_not_called()

    def test_publishing_requires_environment_reviewer(self):
        with patch.dict(release.os.environ, self.env, clear=True), patch.object(release, "github", return_value={"protection_rules": []}):
            with self.assertRaises(ValueError):
                release.guard("testpypi", self.version, "", "")

    def test_public_promotion_requires_explicit_confirmation(self):
        with patch.dict(release.os.environ, self.env, clear=True), patch.object(release, "github", return_value=self.protected):
            with self.assertRaises(ValueError), patch.object(release, "rehearsal_run") as check:
                release.guard("pypi", self.version, "123", "")
            check.assert_not_called()
            with patch.object(release, "rehearsal_run", return_value=self.run) as check:
                release.guard("pypi", self.version, "123", "publish 0.1.0a1")
                check.assert_called_once_with("123")

    def test_promotion_requires_matching_rehearsal_proof(self):
        proof = {"index": "testpypi", "version": self.version, "source_sha": "a" * 40,
                 "run_id": "123", "repository": release.REPOSITORY,
                 "manifest_sha256": release.digest(self.bundle / "manifest.json")}
        release.save_json(self.bundle / "rehearsal.json", proof)
        with patch.object(release, "rehearsal_run", return_value=self.run), patch.object(release, "run"), patch.object(release, "registry") as registry, patch.dict(release.os.environ, {}, clear=True):
            release.promotion(self.bundle, self.version, "123")
            registry.assert_called_once_with(self.bundle, self.version, "testpypi")
            proof["run_id"] = "999"
            release.save_json(self.bundle / "rehearsal.json", proof)
            with self.assertRaises(ValueError):
                release.promotion(self.bundle, self.version, "123")


if __name__ == "__main__":
    unittest.main()
