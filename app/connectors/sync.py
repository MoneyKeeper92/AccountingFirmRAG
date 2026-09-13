"""Run a connector against the ingestion pipeline."""
from __future__ import annotations

import logging
import re
from typing import Any

from ..ingest.pipeline import IngestPipeline
from ..store import Store
from .base import Connector

log = logging.getLogger(__name__)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def run_sync(connector: Connector, store: Store, pipeline: IngestPipeline, actor: str = "sync",
             create_clients: bool = True, max_files: int | None = None) -> dict[str, Any]:
    cursor = store.get_sync_cursor(connector.name)
    files, new_cursor = connector.list_changes(cursor)
    if max_files:
        files = files[:max_files]
    results = {"connector": connector.name, "seen": len(files), "ingested": 0, "duplicates": 0, "failed": 0, "skipped_no_client": 0,
               "clients_created": [], "files": []}
    known = {c["id"]: c for c in store.list_clients()}
    by_name = {_slug(c["name"]): c["id"] for c in known.values()}
    for f in files:
        hint = f.client_hint
        if not hint:
            results["skipped_no_client"] += 1
            results["files"].append({"path": f.path, "status": "skipped", "reason": "no client folder in path"})
            continue
        slug = _slug(hint)
        client_id = known.get(slug, {}).get("id") or by_name.get(slug)
        if not client_id:
            if not create_clients:
                results["skipped_no_client"] += 1
                results["files"].append({"path": f.path, "status": "skipped", "reason": f"unknown client '{hint}'"})
                continue
            c = store.upsert_client(name=hint, client_id=slug)
            client_id = c["id"]
            known[slug] = c
            results["clients_created"].append(client_id)
        try:
            data = connector.read(f)
        except Exception as e:  # noqa: BLE001
            results["failed"] += 1
            results["files"].append({"path": f.path, "status": "failed", "reason": f"read: {e}"})
            continue
        r = pipeline.ingest_bytes(client_id=client_id, filename=f.name, data=data, uploaded_by=actor,
                                  engagement=f.engagement_hint, tax_year=f.year_hint, source_uri=f.source_uri)
        status = r["status"]
        results["ingested" if status == "ready" else "duplicates" if status == "duplicate" else "failed"] += 1
        results["files"].append({"path": f.path, "client_id": client_id, "status": status, "document_id": r.get("document_id"),
                                 "doc_type": r.get("doc_type"), "tax_year": r.get("tax_year")})
    if new_cursor:
        store.set_sync_cursor(connector.name, new_cursor)
    store.log("sync", actor, None, connector=connector.name, seen=results["seen"], ingested=results["ingested"],
              duplicates=results["duplicates"], failed=results["failed"], clients_created=results["clients_created"])
    return results
