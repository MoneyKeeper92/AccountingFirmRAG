"""Microsoft Graph connector (SharePoint document library / OneDrive folder).

Uses the drive delta API so incremental syncs only see what changed:
  GET /drives/{drive_id}/root:/{path}:/delta        (first run)
  GET <@odata.deltaLink>                            (later runs; the delta link is the cursor)
Files are downloaded through '@microsoft.graph.downloadUrl'. Auth is the client-credentials
flow with an app registration granted Files.Read.All / Sites.Read.All (application permission).

Environment: MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET, GRAPH_DRIVE_ID, GRAPH_ROOT_PATH.
The HTTP client is injectable so the request shapes can be tested without a tenant.
"""
from __future__ import annotations

import os
import time
from typing import Any, Callable

import httpx

from .base import SKIP_PREFIXES, SUPPORTED_EXT, Connector, RemoteFile, hints_from_path

GRAPH = "https://graph.microsoft.com/v1.0"


class GraphConnector(Connector):
    def __init__(self, drive_id: str | None = None, root_path: str | None = None, client_depth: int = 0,
                 http: httpx.Client | None = None, token_provider: Callable[[], str] | None = None):
        self.drive_id = drive_id or os.environ["GRAPH_DRIVE_ID"]
        self.root_path = (root_path or os.environ.get("GRAPH_ROOT_PATH", "")).strip("/")
        self.client_depth = client_depth
        self.http = http or httpx.Client(timeout=60)
        self._token_provider = token_provider or self._client_credentials_token
        self._token: tuple[str, float] | None = None
        self.name = f"graph:{self.drive_id}:{self.root_path}"

    # ------------------------------------------------------------------ auth
    def _client_credentials_token(self) -> str:
        if self._token and self._token[1] > time.time() + 60:
            return self._token[0]
        tenant = os.environ["MS_TENANT_ID"]
        r = self.http.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={"client_id": os.environ["MS_CLIENT_ID"], "client_secret": os.environ["MS_CLIENT_SECRET"],
                  "scope": "https://graph.microsoft.com/.default", "grant_type": "client_credentials"},
        )
        r.raise_for_status()
        body = r.json()
        self._token = (body["access_token"], time.time() + int(body.get("expires_in", 3600)))
        return self._token[0]

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token_provider()}"}

    # ------------------------------------------------------------- listing
    def list_changes(self, cursor: str | None) -> tuple[list[RemoteFile], str]:
        url = cursor or (f"{GRAPH}/drives/{self.drive_id}/root:/{self.root_path}:/delta" if self.root_path
                         else f"{GRAPH}/drives/{self.drive_id}/root/delta")
        out: list[RemoteFile] = []
        delta_link = cursor or ""
        while url:
            r = self.http.get(url, headers=self._headers())
            r.raise_for_status()
            page: dict[str, Any] = r.json()
            for item in page.get("value", []):
                if "file" not in item or "deleted" in item:
                    continue
                name = item["name"]
                if name.startswith(SKIP_PREFIXES) or os.path.splitext(name)[1].lower() not in SUPPORTED_EXT:
                    continue
                parent = item.get("parentReference", {}).get("path", "")       # "/drive/root:/Clients/ABC/2025"
                rel_parent = parent.split("root:", 1)[1].strip("/") if "root:" in parent else ""
                if self.root_path and rel_parent.lower().startswith(self.root_path.lower()):
                    rel_parent = rel_parent[len(self.root_path):].strip("/")
                rel = f"{rel_parent}/{name}" if rel_parent else name
                client, year, engagement = hints_from_path(rel, self.client_depth)
                modified = _parse_iso(item.get("lastModifiedDateTime"))
                out.append(RemoteFile(path=rel, name=name, size=int(item.get("size", 0)), modified=modified,
                                      source_uri=item.get("webUrl", ""), client_hint=client, year_hint=year, engagement_hint=engagement))
                # stash the download URL on the object for read(); it is short-lived, so read soon after listing
                out[-1].__dict__["_download_url"] = item.get("@microsoft.graph.downloadUrl")
                out[-1].__dict__["_item_id"] = item.get("id")
            url = page.get("@odata.nextLink")
            delta_link = page.get("@odata.deltaLink", delta_link)
        return out, delta_link

    def read(self, f: RemoteFile) -> bytes:
        url = f.__dict__.get("_download_url")
        if not url:
            item_id = f.__dict__.get("_item_id")
            url = f"{GRAPH}/drives/{self.drive_id}/items/{item_id}/content"
            r = self.http.get(url, headers=self._headers(), follow_redirects=True)
        else:
            r = self.http.get(url, follow_redirects=True)      # pre-authenticated URL: no bearer header
        r.raise_for_status()
        return r.content


def _parse_iso(value: str | None) -> float:
    if not value:
        return time.time()
    from datetime import datetime, timezone

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except ValueError:
        return time.time()
