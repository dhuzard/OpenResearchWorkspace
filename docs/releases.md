# Alpha release process: TestPyPI first, public PyPI second

## Current status

`0.1.0a1` is prepared as an explicit software alpha. Preparation, passing pull-request checks, and downloadable review artifacts do **not** mean the package has been published. Only successful registry upload/read-back runs establish publication. The software version lives in `src/orw/_version.py`; ORW specification/template versions remain independent.

The supported release workflow is `.github/workflows/release-alpha.yml`. It only runs by explicit `workflow_dispatch` on the original repository's `main` branch. A fork, feature branch, or pull-request event cannot pass its publishing guard. No publishing credentials are available to ordinary PR/build tests.

## One-time maintainer setup

These are account/repository administration steps, not source-code changes. They have to be configured by a maintainer with the relevant privileges.

In the repository, create **two environments**, `testpypi` and `pypi`. Configure at least one required reviewer for each; the workflow explicitly checks that reviewers exist and refuses to publish without them. Restrict deployment branches to `main`. Where self-review is disabled, someone other than the workflow initiator must approve. Keep branch/PR review policies appropriate for a release repository.

Configure a GitHub **pending Trusted Publisher** in each registry account, or add it to the existing project if you already own that project name:

| Field | TestPyPI | PyPI |
| --- | --- | --- |
| Project name | `openresearchworkspace` | `openresearchworkspace` |
| Repository owner | `dhuzard` | `dhuzard` |
| Repository name | `OpenResearchWorkspace` | `OpenResearchWorkspace` |
| Workflow filename | `release-alpha.yml` | `release-alpha.yml` |
| Environment name | `testpypi` | `pypi` |

Enter the workflow **filename**, not its full `.github/workflows/` path. The registry accounts and publishers are separate. No long-lived PyPI token needs to be put in GitHub secrets or shared in a chat. The publishing job uses OIDC with `id-token: write`; build/test jobs do not receive that permission.

A pending publisher does not reserve the package name. Confirm ownership or availability when configuring it. A rejected or occupied name is a release blocker, not a reason to publish under an improvised name. The release script's environment-read preflight uses the workflow's `actions: read` permission; inability to read those settings fails closed.

Official references: [new-project Trusted Publishing](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/), [publishing with OIDC](https://docs.pypi.org/trusted-publishers/using-a-publisher/), [TestPyPI](https://packaging.python.org/en/latest/guides/using-testpypi/).

## Before a registry upload

Review and merge the browser and release-safety changes into `main`. At the time this preparation branch was opened, #32 contained the browser implementation and #33 contained release preparation; #33 includes #32's commits so that either a normal sequential merge or review of the combined diff can establish the release baseline. Do not create a release from an unmerged branch.

Check the alpha limits in the README and changelog. Run the platform matrix, ordinary core/CLI/export regression tests, cross-language browser contract tests, and real-browser tests. The matrix builds a wheel and source distribution and installs both in independent clean virtual environments outside the checkout. It checks packaged schemas and the actual `orw` executable. A no-upload build also exercises the release-candidate script itself.

The `alpha-review-artifacts` PR artifact is for review only. It cannot be used as a production rehearsal: the public workflow demands an artifact from a successful `workflow_dispatch` run on `main`, with a matching TestPyPI read-back proof.

## 1. TestPyPI rehearsal

In Actions, select **Publish alpha (TestPyPI first)** and run it on `main` with:

```text
phase: testpypi
version: 0.1.0a1
rehearsal_run: [leave empty]
confirmation: [leave empty]
```

After all checks/builds succeed, approve the `testpypi` environment deployment. The workflow then uploads the already built wheel and source distribution to TestPyPI. It fetches the registry's JSON record, verifies exact filenames and SHA-256 digests, downloads the actual registry files, checks their bytes, and installs each in a fresh environment.

Dependency installation uses the production PyPI index separately. Installation of the downloaded ORW artifact uses `--no-deps`; no mixed-index `--extra-index-url` resolution is used.

The successful run produces **`alpha-verified`** with the Python artifacts, standalone browser HTML/ZIP, license, hash manifest, and `rehearsal.json`. The proof binds the software version, source commit, workflow run, and manifest digest. Record this successful run ID. Inspect the TestPyPI project page and browser download before public promotion.

## 2. Public alpha promotion

Run the same workflow on `main` again:

```text
phase: pypi
version: 0.1.0a1
rehearsal_run: [successful TestPyPI run ID]
confirmation: publish 0.1.0a1
```

The workflow checks the source run's repository, workflow, event, branch and success state; downloads its `alpha-verified` artifact; verifies the manifest and rehearsal proof; confirms the original commit is an ancestor of current `main`; and rechecks TestPyPI bytes/installation. **It does not rebuild the wheel, source distribution, or browser asset.**

Approve the separate `pypi` environment deployment. The exact verified Python artifacts are uploaded to production, downloaded again, hash-checked and installed. Only after this succeeds does the workflow create the corresponding GitHub prerelease with the matching browser and Python assets.

The intended installation command, only after successful production verification, is:

```bash
pipx install openresearchworkspace==0.1.0a1
```

## Failures, retries and immutability

An environment or publisher not configured correctly stops publication. Missing/expired artifacts, changed files, a mismatched registry version/digest, and non-main or failed rehearsal runs stop promotion. TestPyPI is a rehearsal registry and may prune data; it is not the permanent distribution home.

`skip-existing` permits retrying a partial upload, but the mandatory read-back still requires exact filenames and hashes. It never legitimizes different bytes under an existing version. If the source/artifacts need to change after upload, increment to a new alpha (for example `0.1.0a2`), update the version-dependent examples/workflow defaults, and run a new rehearsal.

Verified build artifacts have a 30-day retention period. Promote promptly or perform a new properly versioned rehearsal; do not bypass the proof check. If creating the GitHub prerelease fails after production verification, the package may already be on PyPI. Repair only the missing release/tag/asset step using the recorded source SHA and manifest; do not invent replacement artifacts or describe the failed run as a successful release.

## Safety changes affecting users

Normal `orw init` requires a new or empty destination. It does not convert an arbitrary populated folder in place. The separate GitHub template path verifies the original placeholder metadata and preserves the previous overview and metadata under `.research/template-*`.

RO-Crate source and destination trees must be disjoint. When exporting the current directory, use an outside destination such as `orw export . --output ../my-study-crate`, not `dist/` inside the source. `--force` only replaces an unchanged ORW export recognized by `.orw-export.json`; modified exports and legacy unmarked exports require a new destination. The marker is an accidental-overwrite guard, not a signature or authorization boundary.

Open local directories with separately restricted/private/embargoed/unknown descendants are refused. Explicit metadata labels are necessary, but cannot detect sensitive files that were never labelled. Root ancestors are canonicalized to support host aliases such as macOS `/var`; the named roots and resource path components are checked for links/junctions. Use exclusive workspace access; these checks do not provide an OS sandbox or a crash-proof/concurrent filesystem transaction.

Always inspect exported metadata and the README before sharing them. They can contain names, internal locations or other sensitive context even when raw data were not included. Export does not deposit data, make it public, enforce access control, or encrypt it.

## Reproduce packaging without publishing

From a fresh source checkout or source archive with Python 3.10+:

```bash
python -m pip install . build twine
python -m unittest discover -s tests -v
python -m build --outdir dist/packages
python -m twine check --strict dist/packages/*
python scripts/test_distributions.py dist/packages --version 0.1.0a1
python scripts/build_browser.py
```

The platform-independent `release.py build` command additionally records Git source identity and therefore requires a Git checkout. The ordinary CLI and browser do not require Git.
