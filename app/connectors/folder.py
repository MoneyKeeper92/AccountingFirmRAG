"""Watched folder / file share connector.

Point it at the firm's client root (a mapped drive, a NAS share, the Drake DMS or
FileCabinet CS folder, or a OneDrive-synced folder). Folder convention assumed:
<root>/<Client>/<Year or engagement>/... ; the client folder depth is configurable.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import SKIP_PREFIXES, SUPPORTED_EXT, Connector, RemoteFile, hints_from_path


class FolderConnector(Connector):
    def __init__(self, root: str | Path, client_depth: int = 0, source_prefix: str | None = None):
        self.root = Path(root)
        self.client_depth = client_depth
        # what to put in citations: a UNC path the firm's staff can open, defaulting to the local path
        self.source_prefix = source_prefix
        self.name = f"folder:{self.root}"

    def list_changes(self, cursor: str | None) -> tuple[list[RemoteFile], str]:
        since = float(cursor) if cursor else 0.0
        newest = since
        out: list[RemoteFile] = []
        for dirpath, _dirs, files in os.walk(self.root):
            for fn in files:
                if fn.startswith(SKIP_PREFIXES) or Path(fn).suffix.lower() not in SUPPORTED_EXT:
                    continue
                p = Path(dirpath) / fn
                try:
                    st = p.stat()
                except OSError:
                    continue
                if st.st_mtime <= since:
                    continue
                rel = str(p.relative_to(self.root))
                client, year, engagement = hints_from_path(rel, self.client_depth)
                uri = (self.source_prefix.rstrip("\\/") + "\\" + rel.replace("/", "\\")) if self.source_prefix else p.as_uri()
                out.append(RemoteFile(path=rel, name=fn, size=st.st_size, modified=st.st_mtime, source_uri=uri,
                                      client_hint=client, year_hint=year, engagement_hint=engagement))
                newest = max(newest, st.st_mtime)
        out.sort(key=lambda f: f.modified)
        return out, repr(newest)

    def read(self, f: RemoteFile) -> bytes:
        return (self.root / f.path).read_bytes()
