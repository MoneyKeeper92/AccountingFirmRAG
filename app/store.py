"""SQLite-backed document, chunk, fact and audit store.

Vectors are stored as float32 blobs and searched with brute-force cosine in
numpy. That is plenty for a small practice (tens of thousands of chunks).
For larger firms swap this module for pgvector / Qdrant - the interface is
small on purpose (see docs/ARCHITECTURE.md -> "Scaling the vector store").
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  entity_type TEXT,            -- individual | corporation | s_corp | partnership | nonprofit | trust
  industry TEXT,
  fiscal_year_end TEXT,
  notes TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(id),
  filename TEXT NOT NULL,
  doc_type TEXT,
  tax_year INTEGER,
  engagement TEXT,             -- tax | audit | review | bookkeeping | advisory
  summary TEXT,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER,
  page_count INTEGER,
  status TEXT NOT NULL,        -- processing | ready | failed
  error TEXT,
  extractor_model TEXT,
  canonical_json TEXT,         -- the normalised record produced at ingest
  uploaded_by TEXT,
  source_uri TEXT,             -- where the file lives (file share, DMS, SharePoint...) when we keep a pointer, not a copy
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  client_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  page INTEGER,
  section TEXT,
  text TEXT NOT NULL,
  embedding BLOB,
  embedding_model TEXT
);
CREATE INDEX IF NOT EXISTS chunks_client ON chunks(client_id);
CREATE TABLE IF NOT EXISTS facts (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  name TEXT NOT NULL,          -- wages, adjusted_gross_income, gross_receipts ...
  value REAL NOT NULL,
  unit TEXT,
  period INTEGER,              -- tax year
  source_quote TEXT,
  status TEXT NOT NULL DEFAULT 'extracted',   -- extracted | accepted | rejected | edited  (verify-before-use)
  original_value REAL,
  verified_by TEXT,
  verified_at REAL,
  note TEXT
);
CREATE INDEX IF NOT EXISTS facts_client ON facts(client_id, name, period);
CREATE TABLE IF NOT EXISTS request_lists (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(id),
  tax_year INTEGER NOT NULL,
  status TEXT NOT NULL,        -- draft | sent | complete
  email_subject TEXT,
  email_body TEXT,
  client_email TEXT,
  client_phone TEXT,
  reminder_days TEXT NOT NULL DEFAULT '7,14,21',   -- days after send / last reminder; stops when nothing is pending
  reminder_channel TEXT NOT NULL DEFAULT 'email',  -- email | email+sms | off
  sent_at REAL,
  last_reminder_at REAL,
  reminders_sent INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS organizer_answers (
  list_id TEXT NOT NULL REFERENCES request_lists(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  answer TEXT,                 -- yes | no | null
  note TEXT,
  updated_at REAL NOT NULL,
  PRIMARY KEY (list_id, key)
);
CREATE TABLE IF NOT EXISTS request_items (
  id TEXT PRIMARY KEY,
  list_id TEXT NOT NULL REFERENCES request_lists(id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL,
  key TEXT,
  category TEXT,
  item TEXT NOT NULL,
  why TEXT,
  status TEXT NOT NULL,        -- pending | received | not_applicable
  document_id TEXT,
  received_at REAL,
  note TEXT
);
CREATE INDEX IF NOT EXISTS request_items_list ON request_items(list_id);
CREATE TABLE IF NOT EXISTS client_links (
  token_hash TEXT PRIMARY KEY,
  list_id TEXT NOT NULL REFERENCES request_lists(id) ON DELETE CASCADE,
  created_by TEXT,
  created_at REAL NOT NULL,
  expires_at REAL NOT NULL,     -- link must be opened before this
  opened_at REAL,               -- single use: first open consumes the link...
  session_until REAL,           -- ...and starts a short working session for the client
  opened_ip TEXT
);
CREATE TABLE IF NOT EXISTS sync_state (
  connector TEXT PRIMARY KEY,
  cursor TEXT,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  actor TEXT,
  action TEXT NOT NULL,        -- upload | query | reindex | delete ...
  client_id TEXT,
  detail TEXT                  -- JSON
);
"""


@dataclass
class SearchHit:
    chunk_id: str
    document_id: str
    client_id: str
    filename: str
    doc_type: str | None
    tax_year: int | None
    page: int | None
    section: str | None
    text: str
    score: float


class Store:
    def __init__(self, path: Path | str):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.executescript(SCHEMA)
        # lightweight migrations for databases created before these columns existed
        self._ensure_columns("documents", {"source_uri": "TEXT"})
        self._ensure_columns("facts", {"status": "TEXT NOT NULL DEFAULT 'extracted'", "original_value": "REAL", "verified_by": "TEXT",
                                       "verified_at": "REAL", "note": "TEXT"})
        self._ensure_columns("request_lists", {"client_email": "TEXT", "client_phone": "TEXT", "reminder_days": "TEXT NOT NULL DEFAULT '7,14,21'",
                                               "reminder_channel": "TEXT NOT NULL DEFAULT 'email'", "sent_at": "REAL", "last_reminder_at": "REAL",
                                               "reminders_sent": "INTEGER NOT NULL DEFAULT 0"})

    def _ensure_columns(self, table: str, columns: dict[str, str]) -> None:
        existing = {r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns.items():
            if name not in existing:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
        self.conn.commit()

    # ------------------------------------------------------------- clients
    def upsert_client(self, name: str, entity_type: str | None = None, industry: str | None = None,
                      fiscal_year_end: str | None = None, notes: str | None = None, client_id: str | None = None) -> dict:
        cid = client_id or _slug(name)
        self.conn.execute(
            """INSERT INTO clients(id,name,entity_type,industry,fiscal_year_end,notes,created_at)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name,
                 entity_type=COALESCE(excluded.entity_type, clients.entity_type),
                 industry=COALESCE(excluded.industry, clients.industry),
                 fiscal_year_end=COALESCE(excluded.fiscal_year_end, clients.fiscal_year_end),
                 notes=COALESCE(excluded.notes, clients.notes)""",
            (cid, name, entity_type, industry, fiscal_year_end, notes, time.time()),
        )
        self.conn.commit()
        return self.get_client(cid)

    def get_client(self, client_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        return dict(row) if row else None

    def list_clients(self) -> list[dict]:
        rows = self.conn.execute(
            """SELECT c.*, COUNT(d.id) AS document_count, MAX(d.tax_year) AS latest_year
               FROM clients c LEFT JOIN documents d ON d.client_id=c.id
               GROUP BY c.id ORDER BY c.name"""
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_client(self, client_id: str) -> None:
        self.conn.execute("DELETE FROM request_items WHERE list_id IN (SELECT id FROM request_lists WHERE client_id=?)", (client_id,))
        self.conn.execute("DELETE FROM request_lists WHERE client_id=?", (client_id,))
        self.conn.execute("DELETE FROM facts WHERE client_id=?", (client_id,))
        self.conn.execute("DELETE FROM chunks WHERE client_id=?", (client_id,))
        self.conn.execute("DELETE FROM documents WHERE client_id=?", (client_id,))
        self.conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
        self.conn.commit()

    # ----------------------------------------------------------- documents
    def create_document(self, client_id: str, filename: str, sha256: str, size_bytes: int,
                        uploaded_by: str | None, engagement: str | None = None, tax_year: int | None = None,
                        source_uri: str | None = None) -> str:
        doc_id = uuid.uuid4().hex[:12]
        self.conn.execute(
            """INSERT INTO documents(id,client_id,filename,sha256,size_bytes,status,uploaded_by,engagement,tax_year,source_uri,created_at)
               VALUES(?,?,?,?,?,'processing',?,?,?,?,?)""",
            (doc_id, client_id, filename, sha256, size_bytes, uploaded_by, engagement, tax_year, source_uri, time.time()),
        )
        self.conn.commit()
        return doc_id

    def find_duplicate(self, client_id: str, sha256: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM documents WHERE client_id=? AND sha256=? AND status='ready'", (client_id, sha256)).fetchone()
        return dict(row) if row else None

    def finish_document(self, doc_id: str, *, doc_type: str | None, tax_year: int | None, summary: str | None,
                        page_count: int | None, extractor_model: str, canonical: dict[str, Any]) -> None:
        self.conn.execute(
            """UPDATE documents SET status='ready', doc_type=?, tax_year=COALESCE(?, tax_year), summary=?, page_count=?,
               extractor_model=?, canonical_json=? WHERE id=?""",
            (doc_type, tax_year, summary, page_count, extractor_model, json.dumps(canonical), doc_id),
        )
        self.conn.commit()

    def fail_document(self, doc_id: str, error: str) -> None:
        self.conn.execute("UPDATE documents SET status='failed', error=? WHERE id=?", (error[:2000], doc_id))
        self.conn.commit()

    def get_document(self, doc_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self, client_id: str | None = None) -> list[dict]:
        if client_id:
            rows = self.conn.execute("SELECT * FROM documents WHERE client_id=? ORDER BY tax_year DESC, created_at DESC", (client_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            canonical = json.loads(d.pop("canonical_json", None) or "{}")
            d["return_type"] = canonical.get("return_type")
            d["forms_present"] = canonical.get("forms_present", [])
            d["filing_status"] = canonical.get("filing_status")
            out.append(d)
        return out

    def delete_document(self, doc_id: str) -> None:
        self.conn.execute("DELETE FROM facts WHERE document_id=?", (doc_id,))
        self.conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
        self.conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        self.conn.commit()

    # -------------------------------------------------------------- chunks
    def add_chunks(self, document_id: str, client_id: str, chunks: Iterable[dict], embeddings: list[list[float]], embedding_model: str) -> int:
        n = 0
        for ordinal, (c, vec) in enumerate(zip(chunks, embeddings)):
            blob = np.asarray(vec, dtype=np.float32).tobytes()
            self.conn.execute(
                "INSERT INTO chunks(id,document_id,client_id,ordinal,page,section,text,embedding,embedding_model) VALUES(?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex[:16], document_id, client_id, ordinal, c.get("page"), c.get("section"), c["text"], blob, embedding_model),
            )
            n += 1
        self.conn.commit()
        return n

    def replace_embeddings(self, chunk_ids: list[str], embeddings: list[list[float]], embedding_model: str) -> None:
        for cid, vec in zip(chunk_ids, embeddings):
            self.conn.execute("UPDATE chunks SET embedding=?, embedding_model=? WHERE id=?",
                              (np.asarray(vec, dtype=np.float32).tobytes(), embedding_model, cid))
        self.conn.commit()

    def all_chunks(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, text, embedding_model FROM chunks ORDER BY document_id, ordinal").fetchall()
        return [dict(r) for r in rows]

    def stale_chunk_count(self, embedding_model: str) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM chunks WHERE embedding_model IS NOT ? OR embedding IS NULL", (embedding_model,)).fetchone()[0]

    def search(self, query_vec: list[float], embedding_model: str, client_id: str | None = None,
               top_k: int = 8, tax_year: int | None = None, doc_type: str | None = None) -> list[SearchHit]:
        sql = """SELECT ch.id, ch.document_id, ch.client_id, ch.page, ch.section, ch.text, ch.embedding,
                        d.filename, d.doc_type, d.tax_year
                 FROM chunks ch JOIN documents d ON d.id=ch.document_id
                 WHERE ch.embedding_model=? AND d.status='ready'"""
        args: list[Any] = [embedding_model]
        if client_id:
            sql += " AND ch.client_id=?"; args.append(client_id)
        if tax_year:
            sql += " AND d.tax_year=?"; args.append(tax_year)
        if doc_type:
            sql += " AND d.doc_type=?"; args.append(doc_type)
        rows = self.conn.execute(sql, args).fetchall()
        if not rows:
            return []
        mat = np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])
        q = np.asarray(query_vec, dtype=np.float32)
        denom = (np.linalg.norm(mat, axis=1) * (np.linalg.norm(q) or 1.0)) + 1e-9
        scores = mat @ q / denom
        order = np.argsort(-scores)[:top_k]
        return [
            SearchHit(chunk_id=rows[i]["id"], document_id=rows[i]["document_id"], client_id=rows[i]["client_id"],
                      filename=rows[i]["filename"], doc_type=rows[i]["doc_type"], tax_year=rows[i]["tax_year"],
                      page=rows[i]["page"], section=rows[i]["section"], text=rows[i]["text"], score=float(scores[i]))
            for i in order
        ]

    # --------------------------------------------------------------- facts
    def add_facts(self, client_id: str, document_id: str, facts: Iterable[dict]) -> int:
        n = 0
        for f in facts:
            if f.get("value") is None or not f.get("name"):
                continue
            self.conn.execute(
                "INSERT INTO facts(id,client_id,document_id,name,value,unit,period,source_quote) VALUES(?,?,?,?,?,?,?,?)",
                (uuid.uuid4().hex[:16], client_id, document_id, f["name"], float(f["value"]), f.get("unit", "USD"), f.get("period"), f.get("source_quote")),
            )
            n += 1
        self.conn.commit()
        return n

    def facts_for_client(self, client_id: str, names: list[str] | None = None, include_rejected: bool = False) -> list[dict]:
        """Facts used by planning, forecasting and the model. Rejected facts are excluded; edited values win."""
        sql = """SELECT f.*, d.filename FROM facts f JOIN documents d ON d.id=f.document_id
                 WHERE f.client_id=? AND d.status='ready'"""
        args: list[Any] = [client_id]
        if not include_rejected:
            sql += " AND f.status != 'rejected'"
        if names:
            sql += f" AND f.name IN ({','.join('?' * len(names))})"; args.extend(names)
        # last row wins in series_by_metric: books and transcripts first, returns last, then upload order
        sql += " ORDER BY f.name, f.period, CASE WHEN d.doc_type LIKE 'form_%' THEN 1 ELSE 0 END, d.created_at"
        return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    # ------------------------------------------------------- client context
    def client_text(self, client_id: str, max_chars: int = 200_000) -> str:
        rows = self.conn.execute(
            """SELECT ch.text FROM chunks ch JOIN documents d ON d.id=ch.document_id
               WHERE ch.client_id=? AND d.status='ready' ORDER BY d.tax_year DESC, ch.ordinal""", (client_id,)).fetchall()
        out, n = [], 0
        for r in rows:
            out.append(r["text"]); n += len(r["text"])
            if n > max_chars:
                break
        return "\n".join(out)

    def document_text(self, document_id: str) -> str:
        rows = self.conn.execute("SELECT text FROM chunks WHERE document_id=? AND section IS NOT 'canonical_record' ORDER BY ordinal", (document_id,)).fetchall()
        # strip the per-chunk header line added at ingest
        return "\n".join(r["text"].split("\n", 1)[1] if r["text"].startswith("[client_id=") else r["text"] for r in rows)

    def canonical_records(self, client_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT id, filename, doc_type, tax_year, canonical_json FROM documents WHERE client_id=? AND status='ready'", (client_id,)).fetchall()
        out = []
        for r in rows:
            rec = json.loads(r["canonical_json"]) if r["canonical_json"] else {}
            rec.update({"document_id": r["id"], "filename": r["filename"], "doc_type": r["doc_type"], "tax_year": r["tax_year"]})
            out.append(rec)
        return out

    # -------------------------------------------------------- request lists
    def create_request_list(self, client_id: str, tax_year: int, subject: str, body: str, items: list[dict]) -> dict:
        lid = uuid.uuid4().hex[:12]
        now = time.time()
        self.conn.execute("INSERT INTO request_lists(id,client_id,tax_year,status,email_subject,email_body,created_at,updated_at) VALUES(?,?,?,'draft',?,?,?,?)",
                          (lid, client_id, tax_year, subject, body, now, now))
        for i, it in enumerate(items):
            self.conn.execute("INSERT INTO request_items(id,list_id,ordinal,key,category,item,why,status) VALUES(?,?,?,?,?,?,?,'pending')",
                              (uuid.uuid4().hex[:12], lid, i, it.get("key"), it.get("category"), it["item"], it.get("why")))
        self.conn.commit()
        return self.get_request_list(lid)

    def get_request_list(self, list_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM request_lists WHERE id=?", (list_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        items = self.conn.execute(
            """SELECT ri.*, doc.filename AS received_filename FROM request_items ri
               LEFT JOIN documents doc ON doc.id=ri.document_id WHERE ri.list_id=? ORDER BY ri.ordinal""", (list_id,)).fetchall()
        d["items"] = [dict(i) for i in items]
        d["counts"] = {st: sum(1 for i in d["items"] if i["status"] == st) for st in ("pending", "received", "not_applicable")}
        return d

    def list_request_lists(self, client_id: str) -> list[dict]:
        rows = self.conn.execute(
            """SELECT rl.id, rl.tax_year, rl.status, rl.created_at, rl.updated_at,
                      SUM(ri.status='pending') AS pending, SUM(ri.status='received') AS received, COUNT(ri.id) AS total
               FROM request_lists rl LEFT JOIN request_items ri ON ri.list_id=rl.id
               WHERE rl.client_id=? GROUP BY rl.id ORDER BY rl.tax_year DESC, rl.created_at DESC""", (client_id,)).fetchall()
        return [dict(r) for r in rows]

    UPDATABLE_LIST_FIELDS = ("email_subject", "email_body", "status", "client_email", "client_phone", "reminder_days", "reminder_channel")

    def update_request_list(self, list_id: str, **fields) -> None:
        allowed = {k: v for k, v in fields.items() if k in self.UPDATABLE_LIST_FIELDS and v is not None}
        if not allowed:
            return
        sets = ", ".join(f"{k}=?" for k in allowed) + ", updated_at=?"
        self.conn.execute(f"UPDATE request_lists SET {sets} WHERE id=?", (*allowed.values(), time.time(), list_id))
        if allowed.get("status") == "sent":
            self.conn.execute("UPDATE request_lists SET sent_at=COALESCE(sent_at, ?) WHERE id=?", (time.time(), list_id))
        self.conn.commit()

    def due_reminders(self, now: float | None = None) -> list[dict]:
        """Lists that were sent, still have pending items, and whose next reminder interval has elapsed.
        A list with nothing pending is complete and never reminded again."""
        now = now or time.time()
        rows = self.conn.execute("""SELECT rl.*, c.name AS client_name, SUM(ri.status='pending') AS pending
                                    FROM request_lists rl JOIN clients c ON c.id=rl.client_id
                                    LEFT JOIN request_items ri ON ri.list_id=rl.id
                                    WHERE rl.status='sent' AND rl.reminder_channel != 'off'
                                    GROUP BY rl.id HAVING pending > 0""").fetchall()
        due = []
        for r in rows:
            d = dict(r)
            intervals = [int(x) for x in str(d.get("reminder_days") or "").split(",") if x.strip().isdigit()]
            n = int(d.get("reminders_sent") or 0)
            if n >= len(intervals):
                continue                                  # schedule exhausted; a person follows up
            anchor = d.get("last_reminder_at") or d.get("sent_at") or d["updated_at"]
            if now - anchor >= intervals[n] * 86400:
                d["days_since_last_touch"] = round((now - anchor) / 86400, 1)
                d["reminder_number"] = n + 1
                due.append(d)
        return due

    def record_reminder(self, list_id: str, now: float | None = None) -> None:
        self.conn.execute("UPDATE request_lists SET reminders_sent=reminders_sent+1, last_reminder_at=?, updated_at=? WHERE id=?",
                          (now or time.time(), time.time(), list_id))
        self.conn.commit()

    def organizer_answers(self, list_id: str) -> dict[str, dict]:
        return {r["key"]: dict(r) for r in self.conn.execute("SELECT * FROM organizer_answers WHERE list_id=?", (list_id,)).fetchall()}

    def set_organizer_answer(self, list_id: str, key: str, answer: str | None, note: str | None = None) -> None:
        self.conn.execute("""INSERT INTO organizer_answers(list_id,key,answer,note,updated_at) VALUES(?,?,?,?,?)
                             ON CONFLICT(list_id,key) DO UPDATE SET answer=excluded.answer, note=COALESCE(excluded.note, organizer_answers.note), updated_at=excluded.updated_at""",
                          (list_id, key, answer, note, time.time()))
        self.conn.commit()

    def items_by_key(self, list_id: str) -> dict[str, dict]:
        return {r["key"]: dict(r) for r in self.conn.execute("SELECT * FROM request_items WHERE list_id=?", (list_id,)).fetchall() if r["key"]}

    def add_request_item(self, list_id: str, item: str, why: str | None, category: str | None, key: str | None = None) -> dict:
        n = self.conn.execute("SELECT COALESCE(MAX(ordinal),-1)+1 FROM request_items WHERE list_id=?", (list_id,)).fetchone()[0]
        iid = uuid.uuid4().hex[:12]
        self.conn.execute("INSERT INTO request_items(id,list_id,ordinal,key,category,item,why,status) VALUES(?,?,?,?,?,?,?,'pending')",
                          (iid, list_id, n, key or "custom", category or "Other", item, why))
        self.conn.execute("UPDATE request_lists SET updated_at=? WHERE id=?", (time.time(), list_id))
        self.conn.commit()
        return dict(self.conn.execute("SELECT * FROM request_items WHERE id=?", (iid,)).fetchone())

    def get_request_item(self, item_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM request_items WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None

    def set_request_item(self, item_id: str, status: str, document_id: str | None = None, note: str | None = None) -> None:
        received_at = time.time() if status == "received" else None
        self.conn.execute("UPDATE request_items SET status=?, document_id=COALESCE(?, document_id), received_at=?, note=COALESCE(?, note) WHERE id=?",
                          (status, document_id, received_at, note, item_id))
        lid = self.conn.execute("SELECT list_id FROM request_items WHERE id=?", (item_id,)).fetchone()[0]
        pending = self.conn.execute("SELECT COUNT(*) FROM request_items WHERE list_id=? AND status='pending'", (lid,)).fetchone()[0]
        self.conn.execute("UPDATE request_lists SET updated_at=?, status=CASE WHEN ?=0 THEN 'complete' WHEN status='complete' THEN 'sent' ELSE status END WHERE id=?",
                          (time.time(), pending, lid))
        self.conn.commit()

    def facts_for_review(self, client_id: str) -> list[dict]:
        sql = """SELECT f.*, d.filename, d.doc_type FROM facts f JOIN documents d ON d.id=f.document_id
                 WHERE f.client_id=? AND d.status='ready' ORDER BY f.period DESC, d.filename, f.name"""
        return [dict(r) for r in self.conn.execute(sql, (client_id,)).fetchall()]

    def get_fact(self, fact_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM facts WHERE id=?", (fact_id,)).fetchone()
        return dict(row) if row else None

    def verify_fact(self, fact_id: str, status: str, actor: str, value: float | None = None, note: str | None = None) -> dict:
        f = self.get_fact(fact_id)
        if not f:
            raise KeyError(fact_id)
        if status == "edited" and value is not None:
            original = f["original_value"] if f["original_value"] is not None else f["value"]
            self.conn.execute("UPDATE facts SET status='edited', value=?, original_value=?, verified_by=?, verified_at=?, note=COALESCE(?, note) WHERE id=?",
                              (float(value), original, actor, time.time(), note, fact_id))
        elif status == "extracted":   # undo: back to the extracted value
            restored = f["original_value"] if f["original_value"] is not None else f["value"]
            self.conn.execute("UPDATE facts SET status='extracted', value=?, original_value=NULL, verified_by=NULL, verified_at=NULL, note=? WHERE id=?",
                              (restored, note, fact_id))
        else:
            self.conn.execute("UPDATE facts SET status=?, verified_by=?, verified_at=?, note=COALESCE(?, note) WHERE id=?",
                              (status, actor, time.time(), note, fact_id))
        self.conn.commit()
        return self.get_fact(fact_id)

    def verification_summary(self, client_id: str) -> dict:
        rows = self.conn.execute("""SELECT f.status, COUNT(*) AS n FROM facts f JOIN documents d ON d.id=f.document_id
                                    WHERE f.client_id=? AND d.status='ready' GROUP BY f.status""", (client_id,)).fetchall()
        out = {"extracted": 0, "accepted": 0, "rejected": 0, "edited": 0}
        for r in rows:
            out[r["status"]] = r["n"]
        out["total"] = sum(out.values())
        return out

    # ------------------------------------------------------------ client links
    def create_client_link(self, list_id: str, token_hash: str, created_by: str | None, ttl_seconds: int) -> dict:
        now = time.time()
        self.conn.execute("INSERT INTO client_links(token_hash,list_id,created_by,created_at,expires_at) VALUES(?,?,?,?,?)",
                          (token_hash, list_id, created_by, now, now + ttl_seconds))
        self.conn.commit()
        return {"list_id": list_id, "expires_at": now + ttl_seconds}

    def get_client_link(self, token_hash: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM client_links WHERE token_hash=?", (token_hash,)).fetchone()
        return dict(row) if row else None

    def open_client_link(self, token_hash: str, ip: str | None, session_seconds: int) -> None:
        now = time.time()
        self.conn.execute("UPDATE client_links SET opened_at=?, session_until=?, opened_ip=? WHERE token_hash=?",
                          (now, now + session_seconds, ip, token_hash))
        self.conn.commit()

    def revoke_client_links(self, list_id: str) -> int:
        n = self.conn.execute("DELETE FROM client_links WHERE list_id=?", (list_id,)).rowcount
        self.conn.commit()
        return n

    # ------------------------------------------------------------ connectors
    def get_sync_cursor(self, connector: str) -> str | None:
        row = self.conn.execute("SELECT cursor FROM sync_state WHERE connector=?", (connector,)).fetchone()
        return row["cursor"] if row else None

    def set_sync_cursor(self, connector: str, cursor: str) -> None:
        self.conn.execute("INSERT INTO sync_state(connector,cursor,updated_at) VALUES(?,?,?) ON CONFLICT(connector) DO UPDATE SET cursor=excluded.cursor, updated_at=excluded.updated_at",
                          (connector, cursor, time.time()))
        self.conn.commit()

    def list_sync_state(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM sync_state ORDER BY connector").fetchall()]

    # ----------------------------------------------------------------- audit
    def log(self, action: str, actor: str | None, client_id: str | None = None, **detail: Any) -> None:
        self.conn.execute("INSERT INTO audit_log(ts,actor,action,client_id,detail) VALUES(?,?,?,?,?)",
                          (time.time(), actor, action, client_id, json.dumps(detail, default=str)))
        self.conn.commit()

    def recent_audit(self, limit: int = 100) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["detail"] = json.loads(d["detail"]) if d["detail"] else {}
            out.append(d)
        return out

    def stats(self) -> dict:
        q = lambda s: self.conn.execute(s).fetchone()[0]  # noqa: E731
        return {"clients": q("SELECT COUNT(*) FROM clients"), "documents": q("SELECT COUNT(*) FROM documents"),
                "chunks": q("SELECT COUNT(*) FROM chunks"), "facts": q("SELECT COUNT(*) FROM facts")}


def _slug(name: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or uuid.uuid4().hex[:8]
