"""Connector interface: where a firm's documents already live.

A connector lists files that changed since a cursor and reads their bytes. The sync runner
turns each file into an ingest call with client / year / engagement hints inferred from the
path, and stores a `source_uri` so citations open the file where it lives (pointer mode).

Research (Sept 2026) ranked connectors for 3-30 staff firms: Microsoft Graph (SharePoint /
OneDrive) first, a watched folder on the NAS / file server second (this also covers Drake DMS
and FileCabinet CS, which store files on the filesystem), then Dropbox, SmartVault, ShareFile
and Karbon. Partner-gated: CCH Axcess, GoFileRoom, SafeSend. TaxDome has no confirmed public
bulk API; use its export folder or Zapier.
"""
from __future__ import annotations

import abc
import re
from dataclasses import dataclass

SUPPORTED_EXT = {".pdf", ".csv", ".xlsx", ".xlsm", ".json", ".txt", ".md"}
SKIP_PREFIXES = ("~$", ".~lock", ".DS_Store", "Thumbs.db")


@dataclass
class RemoteFile:
    path: str                  # connector-relative path, e.g. "ABC Company/2025/1120S/return.pdf"
    name: str
    size: int
    modified: float            # unix timestamp
    source_uri: str            # what a browser should open: UNC path, SharePoint web URL...
    client_hint: str | None = None
    year_hint: int | None = None
    engagement_hint: str | None = None


class Connector(abc.ABC):
    name: str = "connector"

    @abc.abstractmethod
    def list_changes(self, cursor: str | None) -> tuple[list[RemoteFile], str]:
        """Return (files changed since cursor, new cursor)."""

    @abc.abstractmethod
    def read(self, f: RemoteFile) -> bytes: ...


_ENGAGEMENT_WORDS = [
    (r"1120-?s|s[-\s]?corp", "tax_1120s"), (r"1120(?!-?s)|c[-\s]?corp", "tax_1120"), (r"1065|partnership", "tax_1065"),
    (r"1040|individual", "tax_1040"), (r"1041|trust", "tax_1041"), (r"bookkeeping|books|quickbooks|qbo", "bookkeeping"),
    (r"payroll", "payroll"), (r"planning|projection", "planning"), (r"\btax\b", "tax"),
]


def hints_from_path(rel_path: str, client_depth: int = 0) -> tuple[str | None, int | None, str | None]:
    """Infer (client, year, engagement) from a path like 'Clients/ABC Company/2025/1120S/return.pdf'.

    client_depth is the index of the path segment that names the client (0 = first folder)."""
    parts = [p for p in re.split(r"[\\/]+", rel_path) if p]
    client = parts[client_depth] if len(parts) > client_depth + 1 else None
    years = [int(y) for y in re.findall(r"(?<!\d)(20[0-4]\d)(?!\d)", rel_path)]
    year = max(years) if years else None
    engagement = None
    lowered = rel_path.lower().replace("_", " ")
    for pat, eng in _ENGAGEMENT_WORDS:
        if re.search(pat, lowered):
            engagement = eng
            break
    return client, year, engagement
