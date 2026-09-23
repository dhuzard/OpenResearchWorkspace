"""Read a public ORCID record. The only module in ORW that uses the network.

Everything else here works offline: a workspace is generated, validated and
exported without reaching anything. `orw contributor add --fetch` opts in
explicitly, so the network boundary is this file and nowhere else. Only public
registry data is read, and nothing is sent but the identifier being looked up.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable
import urllib.error
import urllib.request

from ._version import __version__
from .fair.identifiers import IdentifierError, parse_orcid

API = "https://pub.orcid.org/v3.0/{orcid}/person"
TIMEOUT = 10.0


class OrcidLookupError(Exception):
    """A lookup could not be completed."""


class OrcidNotFound(OrcidLookupError):
    """The registry has no such record, so the identifier credits nobody."""


class OrcidUnavailable(OrcidLookupError):
    """The registry could not be reached, so nothing was learned either way."""


@dataclass(frozen=True)
class OrcidPerson:
    """The public name on a record. Either part may be withheld by its owner."""

    orcid: str
    given_name: str | None
    family_name: str | None


def _name_part(name: Any, key: str) -> str | None:
    part = name.get(key) if isinstance(name, dict) else None
    value = part.get("value") if isinstance(part, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def fetch_person(
    orcid: str,
    *,
    timeout: float = TIMEOUT,
    opener: Callable[..., Any] | None = None,
) -> OrcidPerson:
    """Look up the public name on an ORCID record.

    Raises OrcidNotFound when the registry says the record does not exist, which
    is a fact about the identifier. Raises OrcidUnavailable when the registry
    could not be asked, which says nothing about the identifier; callers that
    must keep working offline treat only the second as recoverable.
    """

    try:
        # Refuse a mistyped identifier before spending a request on it.
        identifier = parse_orcid(orcid).value
    except IdentifierError as exc:
        raise OrcidLookupError(str(exc)) from exc

    request = urllib.request.Request(
        API.format(orcid=identifier),
        headers={"Accept": "application/json", "User-Agent": f"orw/{__version__}"},
    )
    open_url = opener if opener is not None else urllib.request.urlopen
    try:
        with open_url(request, timeout=timeout) as response:
            if getattr(response, "status", 200) != 200:
                raise OrcidUnavailable(
                    f"ORCID registry returned HTTP {response.status} for {identifier}."
                )
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise OrcidNotFound(
                f"ORCID {identifier} is not in the registry. Copy it from the "
                "researcher's ORCID record."
            ) from exc
        raise OrcidUnavailable(
            f"ORCID registry returned HTTP {exc.code} for {identifier}."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OrcidUnavailable(f"ORCID registry could not be reached: {exc}.") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise OrcidUnavailable(
            f"ORCID registry returned something that is not JSON for {identifier}."
        ) from exc

    # A record exists even when its owner keeps the name private, so a lookup
    # that fills nothing is still a successful verification of the identifier.
    name = payload.get("name") if isinstance(payload, dict) else None
    return OrcidPerson(
        identifier, _name_part(name, "given-names"), _name_part(name, "family-name")
    )
