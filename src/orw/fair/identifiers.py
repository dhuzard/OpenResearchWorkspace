"""Recognition, checksum validation and normalization of persistent identifiers.

A persistent identifier that is one character wrong is worse than none: it
resolves nowhere, and nothing downstream notices. ORCID, ISBN and ISSN carry
check digits precisely so that a typo can be caught at entry, so ORW checks them
rather than only matching a shape.

Identifiers are stored in the canonical record in their bare, normalized form.
The resolvable URL is derived when it is needed, never stored twice.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

ORCID_BASE = "https://orcid.org/"
DOI_BASE = "https://doi.org/"

SCHEMES = (
    "doi", "url", "handle", "arxiv", "pmid", "ark", "urn", "isbn", "accession", "other",
)

# DataCite relatedIdentifierType for each scheme ORW recognizes. Schemes with no
# DataCite equivalent map to None and are reported rather than silently coerced.
DATACITE_TYPES = {
    "doi": "DOI", "url": "URL", "handle": "Handle", "arxiv": "arXiv",
    "pmid": "PMID", "ark": "ARK", "urn": "URN", "isbn": "ISBN",
    "accession": None, "other": None,
}

# CITATION.cff only defines doi, url, swh and other.
CFF_TYPES = {"doi": "doi", "url": "url"}

_ORCID = re.compile(
    r"^(?:https?://(?:www\.)?orcid\.org/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$", re.IGNORECASE
)
_DOI = re.compile(
    r"^(?:doi:|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/\S+)$", re.IGNORECASE
)
_ARK = re.compile(r"^(?:https?://\S+?/)?(ark:/?\w{5,9}/\S+)$", re.IGNORECASE)
_URN = re.compile(r"^(urn:[a-z0-9][a-z0-9-]{0,31}:\S+)$", re.IGNORECASE)
_ARXIV = re.compile(
    r"^(?:arxiv:|https?://(?:www\.)?arxiv\.org/abs/)?"
    r"(\d{4}\.\d{4,5}(?:v\d+)?|[a-z-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)$",
    re.IGNORECASE,
)
_PMID = re.compile(r"^(?:pmid:\s*|https?://pubmed\.ncbi\.nlm\.nih\.gov/)?(\d{1,8})/?$", re.IGNORECASE)
_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
_HANDLE = re.compile(r"^(?:hdl:|https?://hdl\.handle\.net/)?(\d+(?:\.\d+)*/\S+)$", re.IGNORECASE)
_ISBN = re.compile(r"^(?:isbn[:\s-]*)?([\d\s-]{10,21}[\dX])$", re.IGNORECASE)


class IdentifierError(ValueError):
    """An identifier is malformed, or fails the check digit its scheme defines."""


@dataclass(frozen=True)
class Identifier:
    """A recognized identifier in bare form, with its resolver URL when one exists."""

    scheme: str
    value: str
    url: str | None = None

    @property
    def datacite_type(self) -> str | None:
        return DATACITE_TYPES.get(self.scheme)

    @property
    def cff_type(self) -> str:
        return CFF_TYPES.get(self.scheme, "other")


def orcid_check_digit(digits: str) -> str:
    """The ISO 7064 MOD 11-2 check character for the first 15 ORCID digits."""

    total = 0
    for character in digits:
        total = (total + int(character)) * 2
    remainder = total % 11
    result = (12 - remainder) % 11
    return "X" if result == 10 else str(result)


def parse_orcid(raw: str) -> Identifier:
    """Validate an ORCID's shape *and* its check digit, returning the bare form."""

    if not isinstance(raw, str) or not raw.strip():
        raise IdentifierError("An ORCID is required.")
    match = _ORCID.match(raw.strip())
    if not match:
        raise IdentifierError(
            f"{raw.strip()!r} is not an ORCID. Expected 0000-0000-0000-0000 "
            "(final character may be X), optionally prefixed by https://orcid.org/."
        )
    value = match.group(1).upper()
    digits = value.replace("-", "")
    if orcid_check_digit(digits[:15]) != digits[15]:
        raise IdentifierError(
            f"ORCID {value} fails its check digit, so it is mistyped or invented. "
            "Copy it from the researcher's ORCID record."
        )
    return Identifier("orcid", value, f"{ORCID_BASE}{value}")


def _isbn_valid(digits: str) -> bool:
    if len(digits) == 10:
        total = sum(
            (10 - index) * (10 if character == "X" else int(character))
            for index, character in enumerate(digits)
        )
        return total % 11 == 0
    if len(digits) == 13:
        if "X" in digits:
            return False
        total = sum(
            int(character) * (3 if index % 2 else 1)
            for index, character in enumerate(digits)
        )
        return total % 10 == 0
    return False


def detect_scheme(raw: str) -> str | None:
    """Identify an unambiguous scheme, or None when the caller must state one.

    Order matters: a DOI is also a Handle, and a resolver URL is also a URL.
    """

    value = raw.strip()
    for scheme, pattern in (
        ("doi", _DOI), ("ark", _ARK), ("urn", _URN), ("arxiv", _ARXIV),
    ):
        if pattern.match(value):
            return scheme
    if _ORCID.match(value):
        return "orcid"
    if value.lower().startswith("pmid") and _PMID.match(value):
        return "pmid"
    if value.lower().startswith(("isbn", "hdl:")) or "hdl.handle.net" in value.lower():
        return "isbn" if value.lower().startswith("isbn") else "handle"
    if _URL.match(value):
        return "url"
    if _HANDLE.match(value):
        return "handle"
    return None


def parse_identifier(raw: str, *, scheme: str | None = None) -> Identifier:
    """Recognize *raw*, optionally forced to *scheme*, and normalize it."""

    if not isinstance(raw, str) or not raw.strip():
        raise IdentifierError("An identifier is required.")
    value = raw.strip()

    if scheme is None:
        scheme = detect_scheme(value)
        if scheme is None:
            raise IdentifierError(
                f"Could not tell what kind of identifier {value!r} is. "
                f"State one with --scheme: {', '.join(SCHEMES)}."
            )
    elif scheme not in SCHEMES and scheme != "orcid":
        raise IdentifierError(f"Unknown identifier scheme {scheme!r}.")

    if scheme == "orcid":
        return parse_orcid(value)

    if scheme == "doi":
        match = _DOI.match(value)
        if not match:
            raise IdentifierError(
                f"{value!r} is not a DOI. Expected 10.<registrant>/<suffix>, "
                "optionally prefixed by https://doi.org/."
            )
        bare = match.group(1)
        return Identifier("doi", bare, f"{DOI_BASE}{bare}")

    if scheme == "ark":
        match = _ARK.match(value)
        if not match:
            raise IdentifierError(f"{value!r} is not an ARK. Expected ark:/<naan>/<name>.")
        bare = match.group(1).lower().replace("ark:", "ark:/").replace("ark://", "ark:/")
        return Identifier("ark", bare, f"https://n2t.net/{bare}")

    if scheme == "urn":
        match = _URN.match(value)
        if not match:
            raise IdentifierError(f"{value!r} is not a URN. Expected urn:<namespace>:<string>.")
        return Identifier("urn", match.group(1))

    if scheme == "arxiv":
        match = _ARXIV.match(value)
        if not match:
            raise IdentifierError(
                f"{value!r} is not an arXiv identifier. Expected 2401.01234 or math.GT/0309136."
            )
        bare = match.group(1)
        return Identifier("arxiv", f"arXiv:{bare}", f"https://arxiv.org/abs/{bare}")

    if scheme == "pmid":
        match = _PMID.match(value)
        if not match:
            raise IdentifierError(f"{value!r} is not a PubMed identifier.")
        bare = match.group(1)
        return Identifier(
            "pmid", f"PMID:{bare}", f"https://pubmed.ncbi.nlm.nih.gov/{bare}/"
        )

    if scheme == "isbn":
        match = _ISBN.match(value)
        digits = re.sub(r"[\s-]", "", match.group(1)).upper() if match else ""
        if not match or not _isbn_valid(digits):
            raise IdentifierError(
                f"{value!r} is not a valid ISBN, or fails its check digit."
            )
        return Identifier("isbn", f"ISBN:{digits}")

    if scheme == "handle":
        match = _HANDLE.match(value)
        if not match:
            raise IdentifierError(f"{value!r} is not a Handle. Expected <prefix>/<suffix>.")
        bare = match.group(1)
        return Identifier("handle", bare, f"https://hdl.handle.net/{bare}")

    if scheme == "url":
        if not _URL.match(value):
            raise IdentifierError(f"{value!r} is not an http(s) URL.")
        return Identifier("url", value, value)

    # accession and other carry no syntax ORW can check; they are kept verbatim.
    return Identifier(scheme, value)


# Short alias used inside the package, where the module name is already context.
parse = parse_identifier
