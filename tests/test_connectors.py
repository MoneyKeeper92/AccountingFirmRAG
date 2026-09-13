import json
import time
from pathlib import Path

from app.connectors.base import hints_from_path
from tests.conftest import SAMPLE


def test_hints_from_path():
    assert hints_from_path("ABC Company/2025/1120S/return.pdf") == ("ABC Company", 2025, "tax_1120s")
    assert hints_from_path("Clients/Doe, John/2024 Tax/1040.pdf", client_depth=1) == ("Doe, John", 2024, "tax_1040")
    assert hints_from_path("Riverbend/2025/Bookkeeping/TB.xlsx") == ("Riverbend", 2025, "bookkeeping")
    assert hints_from_path("loose.pdf") == (None, None, None)


def _make_share(tmp_path: Path) -> Path:
    root = tmp_path / "share"
    (root / "ABC Company" / "2025" / "1120S").mkdir(parents=True)
    (root / "ABC Company" / "2024").mkdir(parents=True)
    (root / "Doe, John & Maria" / "2025 Tax").mkdir(parents=True)
    (root / "ABC Company" / "2025" / "1120S" / "ABC_1120S_2025.txt").write_bytes((SAMPLE / "abc_company" / "ABC_Company_1120S_2025.txt").read_bytes())
    (root / "ABC Company" / "2024" / "ABC_1120S_2024.txt").write_bytes((SAMPLE / "abc_company" / "ABC_Company_1120S_2024.txt").read_bytes())
    (root / "Doe, John & Maria" / "2025 Tax" / "1040_summary.json").write_bytes((SAMPLE / "john_doe" / "John_Doe_1040_2025_summary.json").read_bytes())
    (root / "Doe, John & Maria" / "2025 Tax" / "~$temp.xlsx").write_bytes(b"lock")
    (root / "Doe, John & Maria" / "2025 Tax" / "photo.heic").write_bytes(b"img")
    (root / "readme_at_root.txt").write_text("not under a client folder")
    return root


def test_folder_sync_creates_clients_and_is_incremental(client, tmp_path):
    root = _make_share(tmp_path)
    r = client.post("/api/admin/sync/folder", json={"root": str(root), "source_prefix": "\\\\fileserver\\Clients"}).json()
    assert r["seen"] == 4 and r["ingested"] == 3 and r["skipped_no_client"] == 1 and r["failed"] == 0
    assert set(r["clients_created"]) == {"abc-company", "doe-john-maria"}
    docs = client.get("/api/clients/abc-company/documents").json()
    assert {d["tax_year"] for d in docs} == {2024, 2025}
    assert all(d["engagement"] == "tax_1120s" for d in docs)
    assert docs[0]["source_uri"].startswith("\\\\fileserver\\Clients\\ABC Company\\")
    doe = client.get("/api/clients/doe-john-maria/documents").json()
    assert doe[0]["doc_type"] == "form_1040" and doe[0]["engagement"] == "tax_1040"

    # second pass: nothing new
    r2 = client.post("/api/admin/sync/folder", json={"root": str(root)}).json()
    assert r2["seen"] == 0
    assert client.get("/api/admin/sync").json()[0]["connector"].startswith("folder:")

    # a new file appears -> only it is picked up
    time.sleep(0.05)
    (root / "ABC Company" / "2025" / "1120S" / "TB_2025.csv").write_bytes((SAMPLE / "abc_company" / "ABC_Company_Trial_Balance_2025.csv").read_bytes())
    r3 = client.post("/api/admin/sync/folder", json={"root": str(root)}).json()
    assert r3["seen"] == 1 and r3["ingested"] == 1 and r3["files"][0]["doc_type"] == "trial_balance"

    audit = client.get("/api/admin/audit").json()
    assert audit[0]["action"] == "sync" and audit[0]["detail"]["ingested"] == 1


def test_graph_connector_request_shapes(monkeypatch):
    """Drive the Graph connector with a fake HTTP client: delta paging, filtering, download, cursor."""
    from app.connectors.graph import GraphConnector

    calls = []

    class FakeResp:
        def __init__(self, payload=None, content=b""):
            self._p, self.content = payload, content
        def raise_for_status(self): pass
        def json(self): return self._p

    class FakeHttp:
        def get(self, url, headers=None, follow_redirects=False):
            calls.append((url, headers))
            if url.endswith("/root:/Clients:/delta"):
                return FakeResp({"value": [
                    {"id": "1", "name": "ABC_1120S_2025.pdf", "file": {}, "size": 10, "lastModifiedDateTime": "2026-02-01T10:00:00Z",
                     "parentReference": {"path": "/drive/root:/Clients/ABC Company/2025"}, "webUrl": "https://firm.sharepoint.com/x/ABC_1120S_2025.pdf",
                     "@microsoft.graph.downloadUrl": "https://download.example/1"},
                    {"id": "2", "name": "2025", "folder": {}, "parentReference": {"path": "/drive/root:/Clients/ABC Company"}},
                    {"id": "3", "name": "old.pdf", "file": {}, "deleted": {}, "parentReference": {"path": "/drive/root:/Clients/ABC Company"}},
                ], "@odata.nextLink": "https://graph.microsoft.com/v1.0/next"})
            if url.endswith("/next"):
                return FakeResp({"value": [
                    {"id": "4", "name": "photo.heic", "file": {}, "parentReference": {"path": "/drive/root:/Clients/Doe"}},
                ], "@odata.deltaLink": "https://graph.microsoft.com/v1.0/delta?token=abc"})
            if url == "https://download.example/1":
                return FakeResp(content=b"%PDF fake")
            if url.startswith("https://graph.microsoft.com/v1.0/delta?token="):
                return FakeResp({"value": [], "@odata.deltaLink": url})
            raise AssertionError(url)

    g = GraphConnector(drive_id="drv1", root_path="Clients", http=FakeHttp(), token_provider=lambda: "tok")
    files, cursor = g.list_changes(None)
    assert cursor == "https://graph.microsoft.com/v1.0/delta?token=abc"
    assert [f.path for f in files] == ["ABC Company/2025/ABC_1120S_2025.pdf"]
    f = files[0]
    assert (f.client_hint, f.year_hint, f.engagement_hint) == ("ABC Company", 2025, "tax_1120s")
    assert f.source_uri.startswith("https://firm.sharepoint.com/")
    assert g.read(f) == b"%PDF fake"
    assert calls[0][1] == {"Authorization": "Bearer tok"} and calls[-1][1] is None      # download URL is pre-authenticated
    files2, cursor2 = g.list_changes(cursor)
    assert calls[-1][0] == cursor and cursor2 == cursor
