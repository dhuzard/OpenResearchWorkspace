# FAIR capability layer

FAIR metadata are easiest to get right while the research is open, and hardest to reconstruct at publication. ORW therefore captures them as the project goes, and generates the formats repositories and citation tools expect.

`.research/project.yml` stays canonical. `CITATION.cff`, DataCite metadata and the readiness report are **generated views** over it. You never enter the same metadata twice, and no view can drift from the record.

Everything here is optional. A workspace that uses none of it is still a valid ORW workspace.

## Record the metadata

```bash
orw license set project CC-BY-4.0 --url https://creativecommons.org/licenses/by/4.0/
orw license set data CC0-1.0
orw license set code MIT

orw contributor add "Ada Lovelace" \
  --given-name Ada --family-name Lovelace \
  --orcid 0000-0002-1825-0097 --affiliation "Example Institute"

orw metadata set --publisher "Example Institute" --publication-year 2026 --version-label 1.0.0

orw identifier add 10.5281/zenodo.1234567 --relation IsSupplementTo
orw identifier add https://example.org/protocol --relation References --title "Field protocol"
```

These are ordinary mutation commands: they support `--dry-run`, `--json`, conflict detection and validated rollback like every other one. See the [CLI guide](cli.md).

### Licenses are declared per scope

Research outputs rarely share one licence — code under a software licence and data under a Creative Commons licence is the ordinary case. So `project`, `data`, `code` and `documentation` are declared separately.

**An undeclared scope stays undeclared.** ORW never treats silence as permission, never copies the project license onto the data, and never writes a licence into a generated view that you did not declare.

Prefer an SPDX identifier (`CC-BY-4.0`, `MIT`, `CC0-1.0`). An identifier ORW does not recognize as SPDX is still recorded, but `CITATION.cff` then carries `license-url` instead of `license`, because a CITATION.cff with an invented SPDX identifier fails validation downstream.

### Identifiers are validated, not just shaped

`orw identifier add` and `orw contributor add --orcid` recognize, validate and normalize the identifier before writing it:

| Scheme | Accepted forms | Stored as |
| --- | --- | --- |
| DOI | `10.5281/zenodo.1`, `doi:10.…`, `https://doi.org/10.…` | `10.5281/zenodo.1` |
| ORCID | `0000-0002-1825-0097`, `https://orcid.org/…` | `0000-0002-1825-0097` |
| arXiv | `2401.01234`, `arXiv:…`, `https://arxiv.org/abs/…` | `arXiv:2401.01234` |
| URL | `https://…` | as given |
| Handle, ARK, URN, PMID, ISBN | prefixed or resolver-URL forms | normalized bare form |
| accession, other | any text, with `--scheme` | as given |

ORCID and ISBN carry check digits, and ORW verifies them. `0000-0002-1825-0098` is refused: it has the right shape but is mistyped or invented, and would credit nobody.

A check digit only proves an identifier is well formed, not that it belongs to
anyone. `orw contributor add --orcid … --fetch` goes further and asks the
registry, refusing an ORCID that does not exist and filling the contributor's
given and family names from the public record. It is the only ORW command that
uses the network, and it warns rather than fails when the registry cannot be
reached. See [the CLI guide](cli.md).

Where detection is ambiguous — a bare `12345678` could be many things — ORW asks for `--scheme` rather than guessing.

`--relation` uses the DataCite relation vocabulary (`IsSupplementTo`, `IsDerivedFrom`, `Cites`, `References`, `IsPartOf`, …). The list is read from the bundled schema, so the CLI and the schema cannot drift apart.

> Workspaces created by `orw init` or the browser check an ORCID's **shape** but not its check digit, because both share a generation contract that the browser must implement identically. `orw fair report` flags a failing check digit wherever the record came from.

## Read the readiness report

```bash
orw fair report
orw fair report --json
orw fair report --strict
```

The report is deliberately **not a score**. "62% FAIR" tells a researcher nothing actionable and invites optimizing the number. Every check instead names the gap and the command that closes it:

```text
Reusable
  GAP [R1-project-license] No project license is declared, so others have no right to reuse this work.
        Fix: orw license set project CC-BY-4.0
  GAP [R3-datacite-ready] DataCite metadata cannot be exported yet: publisher: not recorded. …
        Fix: Record the properties named above, then run 'orw fair datacite'.
```

Checks are grouped by FAIR principle and carry a severity:

- **required** — a deposit would fail, or the generated metadata would mislead;
- **recommended** — the work would be harder to find, cite or reuse.

`orw fair report` exits `1` while a required gap remains, and `0` otherwise. `--strict` also fails on recommended gaps, for a CI gate. `--json` emits every check with its `code`, `principle`, `severity`, `status` and `remedy`.

This reports on metadata ORW can see. **It is not a FAIR certification**, and a workspace where every check passes can still be poorly described science.

## Generate CITATION.cff

```bash
orw fair citation              # writes CITATION.cff in the workspace
orw fair citation --output -   # print it instead
```

The file is generated from the canonical record, carries a header saying so, and is regenerated in place when the record changes. `orw fair report` tells you when it has fallen out of date.

**A `CITATION.cff` that ORW did not generate is never replaced.** If you maintain one by hand, ORW refuses and tells you to pass `--force` if you really mean it. The readiness check treats a hand-maintained file as satisfied and leaves it alone.

Nothing is inferred. An undeclared license produces no `license` field. A contributor recorded only as `name` is emitted in CITATION.cff's *entity* form rather than being split into given and family names by guesswork — cultural name orders differ, and a wrong split misattributes someone's work. Record `--given-name` and `--family-name` to have them cited as a person; the report flags contributors where this is missing.

## Generate DataCite metadata

```bash
orw fair datacite                        # to standard output
orw fair datacite --output datacite.json
```

This is the payload a deposition workflow would submit, prepared before anyone asks for a DOI. That is the point of preparing it early: DataCite's mandatory properties become visible as concrete gaps while the research is still open.

**Missing mandatory properties are refused, not invented:**

```text
DataCite metadata are incomplete, so nothing was exported.
- publisher: not recorded. Set it with 'orw metadata set --publisher "…"'.
- publicationYear: not recorded. Set it with 'orw metadata set --publication-year YYYY'.
```

ORW does not guess a publisher, guess a year, or file the creator as "Anonymous".

Every recorded contributor becomes a DataCite **creator**. Splitting the list into creators and contributors would mean inferring seniority from a free-text role, which silently demotes people; a workspace's contributor list is its author list.

Related identifiers whose scheme has no DataCite equivalent (`accession`, `other`), or which have no `--relation`, are left out of the payload and reported rather than coerced into something a repository would misread.

> **Generating this payload is not depositing it.** No network call happens, no DOI is minted, and nothing is sent anywhere. Intentional deposit and DOI minting are a separate, explicitly confirmed workflow ([#3](https://github.com/dhuzard/OpenResearchWorkspace/issues/3)).

## What reaches the RO-Crate export

`orw export --format ro-crate` carries the declared **project** license onto the crate's root dataset — with its URL as a `CreativeWork` when one is declared — and carries contributors' given names, family names and affiliations onto their `Person` entities.

Per-scope data, code and documentation licenses are recorded in the canonical record but are not yet mapped onto individual crate entities.

## Boundaries

- These are generated views, not a metadata store. Edit `.research/project.yml` (through the mutation commands), never the generated files.
- The readiness report covers metadata ORW can see in the canonical record. It cannot judge whether a description is accurate, whether data are actually accessible, or whether a licence is the right one.
- ORW recognizes an SPDX identifier against a bundled list of licences common in research. An identifier outside that list is recorded faithfully but is not asserted to be SPDX in CITATION.cff.
- FAIR Signposting, ISA-JSON/ISA-Tab interoperability and a versioned ORW RO-Crate profile remain planned ([#4](https://github.com/dhuzard/OpenResearchWorkspace/issues/4)).
