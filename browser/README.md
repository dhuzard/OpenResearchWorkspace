# Browser workspace generator

This directory contains the sources for the static ORW browser generator (#23).
**`page.html` is a build template, not the runnable application.**

From the repository root, build once:

```bash
python -m pip install .
python scripts/build_browser.py
```

Distribute **`dist/browser/index.html`**. It contains its own scripts, styles,
schemas, and core-derived templates. Researchers can open the built file locally
or use a copy served from institutional/static hosting. They do not need Python,
Node, a package manager, or an account to use that file.

No hosted service is provisioned by the build. No data are uploaded or persisted
by the application. The first request to a hosted page still reaches that host.

See [the researcher and deployment guide](../docs/browser-generator.md).

## Development checks

Node.js is needed for the cross-language contract tests, not for the application:

```bash
python -m unittest discover -s tests -p test_browser_contract.py -v
python -m pip install -r browser/requirements-test.txt
python -m playwright install chromium
python -m unittest discover -s browser/tests -v
```

The UI suite defaults to real HTTP and local-file navigation. `ORW_CHROMIUM` can
select an installed Chromium executable. On restricted hosts that block all
navigation, `ORW_BROWSER_LOAD=content` loads the same HTML through Playwright's
`set_content`; the file-navigation test is then explicitly skipped, not passed.
Use the default mode for release acceptance. `ORW_SCREENSHOT_DIR` optionally saves
synthetic-fixture screenshots.

## Contract, not a second scientific model

`build_browser.py` calls the Python generator for the four Assay/ORCID variants
and bundles the resulting templates with the canonical setup/project schemas.
The browser substitutes normalized values; it does not define another project
schema or maintain its own README/folder templates. Project metadata use native
JSON serialization in `.research/project.yml` (JSON-compatible YAML); their
parsed content is compared with the Python output.

`engine.js` includes a bounded interpreter for the schema keywords currently used
by ORW. The build rejects unsupported keywords rather than ignoring them. This is
not a general-purpose JSON Schema validator. Python `jsonschema` and
`validate_workspace` independently check the browser output in the tests.

The small ZIP32 writer supports generated UTF-8 text, uses fixed timestamps,
checks path safety, and rejects packages over 16 MiB. It does not read ZIP uploads,
attach arbitrary local files, or provide encryption. Python `zipfile` independently
checks the ZIP directory, CRCs, filenames, and extracted content.
