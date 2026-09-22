# Create a workspace in your browser

**Implemented:** a static, local-first generator for one Investigation, one Study,
and an optional first Assay. It creates an ORW workspace ZIP without a Git account,
installation, or metadata upload. A public hosted instance is **not** automatically
deployed by this implementation.

## Researcher workflow

Open a **built** copy of the ORW generator (`index.html`) supplied by your lab or
project maintainer. It can be opened locally in a browser or served by static or
institutional hosting. Do not open the source template `browser/page.html`.

1. Enter the project title and description, your name, and the first study title.
   ORCID and the first measurement/test are optional. Leave the measurement blank
   when no Assay is scientifically applicable.
2. Record the high-level location of the authoritative data and their access
   status. Private is the default. This records metadata; it neither opens a
   connection to those data nor changes storage permissions.
3. Select **Review workspace**. Check the folder tree and optionally inspect the
   canonical metadata. Correct any errors; changing an entry invalidates the old
   review and disables its download.
4. Confirm that you reviewed the metadata, then select **Download workspace ZIP**.
   Extract the ZIP and open `README.md`. Keep the hidden `.research` directory.
   Place study-wide and measurement-specific work in the indicated folders.

**Try an example** fills a clearly labelled demonstration. Replace those entries
before creating a real project. **Clear form** removes the current entries and
preview. The page has no automatic draft saving.

## What the ZIP contains

The generated folder tree comes from the same Python core used by `orw init`.
It includes the project overview, Study/Assay guidance, and:

```text
.research/project.yml       canonical scientific metadata
.research/workspace.yml     implementation state; browser adapter identified
.research/initialized       initialized-workspace marker
```

The browser writes the canonical record as JSON-compatible YAML. Different text
formatting is expected; its parsed scientific content matches the Python core.

No research data, credentials, or existing workspace files are read or copied.
The ZIP contains scaffolding and your entered metadata. It is **not encrypted**.
Data-access labels do not stop someone from reading a ZIP you share.

## Privacy and validation boundaries

All form processing and ZIP creation occur in the browser. The built document
has no remote scripts, fonts, analytics, backend requests, cookies, or application
storage. Its Content Security Policy blocks connections and form submissions;
script/style hashes allow only the code embedded by the build.

A hosted copy still requires a page request to the host. The host can modify what
it serves; the page cannot control browser extensions, browser-managed history,
backups, or the destination to which you later share the ZIP. Do not enter
passwords, access tokens, participant identifiers, or confidential clinical data.

Setup and generated metadata are checked against bundled ORW schemas. Cross-language
fixtures independently validate extracted ZIPs using Python `jsonschema` and the
ORW workspace validator. This is schema/workspace validation—not FAIR certification,
scientific review, or an identity check. ORCID checking is currently format-only.

## Build and share — maintainers

From an ORW source checkout/release with its Python dependencies installed:

```bash
python scripts/build_browser.py
```

The output is a single **`dist/browser/index.html`**. Send that file directly, place
it on institutional hosting, or serve it from any static server. It has no fixed
hostname, URL prefix, or runtime CDN dependency. The build does not publish a
website, register a domain, or modify hosting settings.

The **Browser generator** CI workflow builds and tests the page, then offers an
`orw-browser-generator` build artifact for distribution. GitHub is just one build
and distribution adapter; the same build command works outside GitHub.

For a local hosted check:

```bash
python -m http.server 8000 --directory dist/browser
```

Open the localhost address printed by the server. Browser or institutional policy
may prohibit opening local HTML files; static hosting is the alternative in that
case. No application backend is needed.

Do not edit the generated document to change the scientific contract. Change the
core/schema sources, rebuild, and run the shared tests. Source hashes embedded in
the document identify the generator and schema inputs used for that build.

## Implemented versus planned

| Capability | Status |
| --- | --- |
| Form, local validation, exact-file preview, ZIP download | Implemented |
| Unicode metadata and optional Assay/ORCID | Implemented |
| Private-by-default access metadata and explicit review | Implemented |
| Portable standalone/static build | Implemented; hosting is a separate deployment |
| Adding more Studies/Assays or editing existing workspaces through the browser | Planned |
| Browser RO-Crate download | Planned; use the existing CLI exporter for now |
| File upload, collaboration accounts, remote storage integration | Not part of this MVP |
| Publication/archive/DOI workflow | Planned; ZIP creation does not publish anything |

After working in the extracted workspace, the existing CLI remains available:

```bash
orw validate my-study --json
orw export my-study --format ro-crate --output dist/my-study-ro-crate
```

See [CLI usage](cli.md), [RO-Crate export](ro-crate.md), and
[portable implementation architecture](portable-implementations.md).

## Implementation references

The browser uses standard Blob downloads and the ZIP file layout, not an external
file-hosting service:

- [Blob object URLs](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static)
- [Content Security Policy connection restrictions](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/connect-src)
- [PKWARE ZIP APPNOTE](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)
