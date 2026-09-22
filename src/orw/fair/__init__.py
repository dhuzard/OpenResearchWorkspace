"""FAIR-by-design views generated from the canonical ORW record.

`.research/project.yml` stays the single source of truth. CITATION.cff,
DataCite metadata and the readiness report are derived from it on demand, so a
researcher never maintains the same metadata twice and no view can drift.

Every capability here is optional: nothing in the ORW core depends on it, and a
workspace that uses none of it is still a valid workspace.
"""
from ._common import FairError, FairExportError, LICENSE_SCOPES
from .citation import is_generated as citation_is_generated, render as citation_cff
from .datacite import build as datacite_metadata, missing_properties, skipped_identifiers
from .identifiers import (
    Identifier, IdentifierError, SCHEMES, detect_scheme, parse_identifier, parse_orcid,
)
from .report import FairCheck, FairReport, build as fair_report

__all__ = [
    "FairCheck", "FairError", "FairExportError", "FairReport", "Identifier",
    "IdentifierError", "LICENSE_SCOPES", "SCHEMES", "citation_cff",
    "citation_is_generated", "datacite_metadata", "detect_scheme", "fair_report",
    "missing_properties", "parse_identifier", "parse_orcid", "skipped_identifiers",
]
