"""Sync a client file share into the archive, once or continuously.

    python scripts/sync_folder.py "S:\\Clients"                       # one pass
    python scripts/sync_folder.py "S:\\Clients" --watch 300           # every 5 minutes
    python scripts/sync_folder.py /mnt/clients --client-depth 1 --source-prefix "\\\\fileserver\\Clients"

Folder convention: <root>/<Client>/<Year or engagement>/files. The client folder depth is the
index of the segment that names the client (0 = directly under root). Only new or modified
files since the last run are read; identical files are deduplicated by hash.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.connectors import FolderConnector, run_sync  # noqa: E402
from app.main import AppState  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--client-depth", type=int, default=0)
    ap.add_argument("--source-prefix", default=None, help="UNC prefix to use in citations instead of the local path")
    ap.add_argument("--watch", type=int, default=0, help="seconds between passes; 0 = run once")
    ap.add_argument("--no-create-clients", action="store_true")
    args = ap.parse_args()

    state = AppState(Settings.load())
    conn = FolderConnector(args.root, client_depth=args.client_depth, source_prefix=args.source_prefix)
    while True:
        r = run_sync(conn, state.store, state.pipeline, actor="folder-sync", create_clients=not args.no_create_clients)
        print(json.dumps({k: v for k, v in r.items() if k != "files"}))
        for f in r["files"]:
            if f["status"] != "duplicate":
                print("  ", f)
        if not args.watch:
            break
        time.sleep(args.watch)


if __name__ == "__main__":
    main()
