"""FastAPI application: REST API + static UI."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import mimetypes
import secrets
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import checklist, forecast
from .connectors import FolderConnector, run_sync
from .notify import build_notifier, reminder_text
from .config import Settings
from .ingest import IngestPipeline
from .providers import build_embedding_provider, build_llm_provider
from .providers.ocr import build_ocr_provider
from .providers.registry import known_providers
from .ingest import transcript as transcript_mod
from .rag import RagEngine
from .store import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("firm_rag")

STATIC = Path(__file__).parent / "static"


class ClientIn(BaseModel):
    name: str
    entity_type: str | None = None
    industry: str | None = None
    fiscal_year_end: str | None = None
    notes: str | None = None


class ChatIn(BaseModel):
    question: str = Field(min_length=2)
    client_id: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


class ProfileIn(BaseModel):
    profile: str


class FolderSyncIn(BaseModel):
    root: str
    client_depth: int = 0
    source_prefix: str | None = None
    create_clients: bool = True


class RequestListIn(BaseModel):
    tax_year: int | None = None
    firm_name: str = "our office"


class RequestEmailIn(BaseModel):
    email_subject: str | None = None
    email_body: str | None = None
    status: str | None = None          # draft | sent | complete
    client_email: str | None = None
    client_phone: str | None = None
    reminder_days: str | None = Field(default=None, pattern=r"^\d+(,\d+)*$")
    reminder_channel: str | None = Field(default=None, pattern="^(email|email\+sms|off)$")


class FactVerifyIn(BaseModel):
    status: str = Field(pattern="^(accepted|rejected|edited|extracted)$")
    value: float | None = None
    note: str | None = None


class FeedbackIn(BaseModel):
    verdict: str = Field(pattern="^(accept|reject)$")
    question: str | None = None
    document_id: str | None = None
    client_id: str | None = None
    excerpt: str | None = None
    note: str | None = None


class OrganizerAnswersIn(BaseModel):
    answers: list[dict[str, Any]]      # [{key, answer: yes|no|null, note?}]


class ClientLinkIn(BaseModel):
    ttl_minutes: int = Field(default=15, ge=5, le=60 * 24 * 7)     # link must be opened within this window
    session_minutes: int = Field(default=60, ge=10, le=240)         # once opened, how long the client can keep working


class RequestItemIn(BaseModel):
    item: str = Field(min_length=2)
    why: str | None = None
    category: str | None = None


class RequestItemStatusIn(BaseModel):
    status: str = Field(pattern="^(pending|received|not_applicable)$")
    note: str | None = None



class AppState:
    """Everything that depends on the model profile lives here so it can be hot-swapped."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = Store(settings.db_path)
        self.llm = build_llm_provider(settings.llm)
        self.extractor = build_llm_provider(settings.extractor)
        self.embedder = build_embedding_provider(settings.embedding)
        self.ocr = build_ocr_provider(settings.ocr)
        self.pipeline = IngestPipeline(self.store, self.extractor, self.embedder, settings.uploads_dir, keep_originals=settings.keep_originals, ocr=self.ocr)
        self.rag = RagEngine(self.store, self.llm, self.embedder)
        self.notifier = build_notifier()

    def describe(self) -> dict[str, Any]:
        return {
            "profile": self.settings.profile_name,
            "available_profiles": self.settings.available_profiles,
            "llm": self.llm.identity,
            "extractor": self.extractor.identity,
            "embedding": self.embedder.identity,
            "embedding_dimensions": self.embedder.dimensions,
            "ocr": self.ocr.identity if self.ocr else "none (text layer only)",
            "stale_chunks": self.store.stale_chunk_count(self.embedder.identity),
            "keep_originals": self.settings.keep_originals,
            "known_providers": known_providers(),
            "stats": self.store.stats(),
        }


def dispatch_reminder(state: "AppState", list_id: str, actor: str, firm_name: str = "our office") -> dict[str, Any]:
    """Draft and send (or log) the next reminder for a request list; stops automatically once nothing is pending."""
    rl = state.store.get_request_list(list_id)
    if not rl:
        raise KeyError(list_id)
    pending = [i for i in rl["items"] if i["status"] == "pending"]
    if not pending:
        return {"list_id": list_id, "sent": False, "reason": "nothing pending; list is complete"}
    if rl.get("reminder_channel") == "off":
        return {"list_id": list_id, "sent": False, "reason": "reminders are off for this list"}
    client = state.store.get_client(rl["client_id"]) or {}
    rl["client_name"] = client.get("name")
    rl["reminder_number"] = int(rl.get("reminders_sent") or 0) + 1
    subject, body, sms = reminder_text(rl, pending, firm_name)
    deliveries = [state.notifier.send_email(rl.get("client_email"), subject, body).__dict__]
    if rl.get("reminder_channel") == "email+sms":
        deliveries.append(state.notifier.send_sms(rl.get("client_phone"), sms).__dict__)
    state.store.record_reminder(list_id)
    state.store.log("reminder_sent", actor, rl["client_id"], list_id=list_id, reminder_number=rl["reminder_number"], pending=len(pending),
                    deliveries=deliveries, subject=subject, body=body)
    return {"list_id": list_id, "sent": True, "reminder_number": rl["reminder_number"], "pending": len(pending), "deliveries": deliveries,
            "subject": subject, "body": body}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    state = AppState(settings)
    app = FastAPI(title="Firm Archive Assistant", version="0.1.0")
    app.state.rag_state = state

    def auth(x_api_token: str | None = Header(default=None)) -> str:
        expected = state.settings.api_token
        if expected and x_api_token != expected:
            raise HTTPException(status_code=401, detail="Missing or invalid X-API-Token header")
        return "staff"

    def current() -> AppState:
        return app.state.rag_state

    # ------------------------------------------------------------- pages
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/health")
    def health():
        return {"ok": True, **current().describe()}

    # ----------------------------------------------------------- clients
    @app.get("/api/clients", dependencies=[Depends(auth)])
    def list_clients():
        return current().store.list_clients()

    @app.post("/api/clients", dependencies=[Depends(auth)])
    def create_client(body: ClientIn, actor: str = Depends(auth)):
        c = current().store.upsert_client(**body.model_dump())
        current().store.log("client_upsert", actor, c["id"], name=c["name"])
        return c

    @app.delete("/api/clients/{client_id}", dependencies=[Depends(auth)])
    def delete_client(client_id: str, actor: str = Depends(auth)):
        s = current().store
        if not s.get_client(client_id):
            raise HTTPException(404, "client not found")
        s.delete_client(client_id)
        s.log("client_delete", actor, client_id)
        return {"deleted": client_id}

    @app.get("/api/clients/{client_id}/documents", dependencies=[Depends(auth)])
    def client_documents(client_id: str):
        return current().store.list_documents(client_id)

    @app.get("/api/clients/{client_id}/facts", dependencies=[Depends(auth)])
    def client_facts(client_id: str):
        facts = current().store.facts_for_client(client_id)
        return {"facts": facts, "series": forecast.series_by_metric(facts)}

    @app.get("/api/clients/{client_id}/forecast", dependencies=[Depends(auth)])
    def client_forecast(client_id: str, periods_ahead: int = 1):
        return forecast.forecast_client(current().store.facts_for_client(client_id), periods_ahead)

    @app.get("/api/clients/{client_id}/risk", dependencies=[Depends(auth)])
    def client_risk(client_id: str):
        return forecast.assess_risk(current().store.facts_for_client(client_id))

    # -------------------------------------------------- verify before use
    @app.get("/api/clients/{client_id}/facts/review", dependencies=[Depends(auth)])
    def facts_review(client_id: str):
        st = current()
        return {"facts": st.store.facts_for_review(client_id), "summary": st.store.verification_summary(client_id)}

    @app.patch("/api/facts/{fact_id}", dependencies=[Depends(auth)])
    def verify_fact(fact_id: str, body: FactVerifyIn, actor: str = Depends(auth)):
        st = current()
        before = st.store.get_fact(fact_id)
        if not before:
            raise HTTPException(404, "fact not found")
        if body.status == "edited" and body.value is None:
            raise HTTPException(400, "an edited fact needs a value")
        after = st.store.verify_fact(fact_id, body.status, actor, body.value, body.note)
        st.store.log("fact_verify", actor, after["client_id"], fact_id=fact_id, name=after["name"], period=after["period"],
                     status=body.status, value_before=before["value"], value_after=after["value"], note=body.note)
        return after

    @app.post("/api/feedback", dependencies=[Depends(auth)])
    def feedback(body: FeedbackIn, actor: str = Depends(auth)):
        """Accept / reject a citation or an answer. Goes to the audit log; the weekly review reads it."""
        current().store.log("citation_feedback", actor, body.client_id, verdict=body.verdict, question=body.question,
                            document_id=body.document_id, excerpt=(body.excerpt or "")[:300], note=body.note)
        return {"recorded": True}

    # --------------------------------------------------------- documents
    @app.post("/api/documents", dependencies=[Depends(auth)])
    async def upload(client_id: str = Form(...), engagement: str | None = Form(None), tax_year: int | None = Form(None),
                     source_uri: str | None = Form(None), files: list[UploadFile] = File(...), actor: str = Depends(auth)):
        st = current()
        if not st.store.get_client(client_id):
            raise HTTPException(404, f"client '{client_id}' not found - create the client first")
        results = []
        for f in files:
            data = await f.read()
            if len(data) > 50 * 1024 * 1024:
                results.append({"filename": f.filename, "status": "failed", "error": "file larger than 50 MB"})
                continue
            r = st.pipeline.ingest_bytes(client_id=client_id, filename=f.filename or "upload", data=data, uploaded_by=actor,
                                         engagement=engagement, tax_year=tax_year, source_uri=(source_uri or None))
            r["filename"] = f.filename
            results.append(r)
        return {"results": results}

    @app.get("/api/documents/{doc_id}", dependencies=[Depends(auth)])
    def get_document(doc_id: str):
        d = current().store.get_document(doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        return d

    @app.get("/api/documents/{doc_id}/file")
    def open_document_file(doc_id: str, token: str | None = None, x_api_token: str | None = Header(default=None)):
        """Serve the stored original so a citation can be opened in a new tab.

        Browsers cannot send custom headers on a plain link, so this one route also accepts
        the token as a query parameter. In production replace this with short-lived signed
        URLs issued per click (see docs/RISKS.md)."""
        st = current()
        expected = st.settings.api_token
        if expected and token != expected and x_api_token != expected:
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        d = st.store.get_document(doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        matches = sorted((st.settings.uploads_dir / d["client_id"]).glob(f"{doc_id}__*"))
        if not matches:
            if d.get("source_uri"):
                # pointer mode: the file lives on the firm's share / DMS; send the browser there
                st.store.log("file_open", "staff", d["client_id"], document_id=doc_id, filename=d["filename"], redirected_to=d["source_uri"])
                return RedirectResponse(d["source_uri"], status_code=307)
            raise HTTPException(404, "No stored copy and no source link for this document. Re-upload with a source link or enable FIRM_RAG_KEEP_ORIGINALS.")
        path = matches[0]
        media_type = mimetypes.guess_type(d["filename"])[0] or "application/octet-stream"
        st.store.log("file_open", "staff", d["client_id"], document_id=doc_id, filename=d["filename"])
        # inline so PDFs open in the browser tab (and honour #page=N); other types download.
        disposition = "inline" if media_type in ("application/pdf", "text/plain", "application/json", "text/csv") else "attachment"
        return FileResponse(path, media_type=media_type, filename=d["filename"], content_disposition_type=disposition)

    @app.delete("/api/documents/{doc_id}", dependencies=[Depends(auth)])
    def delete_document(doc_id: str, actor: str = Depends(auth)):
        s = current().store
        d = s.get_document(doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        s.delete_document(doc_id)
        s.log("document_delete", actor, d["client_id"], document_id=doc_id, filename=d["filename"])
        return {"deleted": doc_id}

    # -------------------------------------------------- tax request lists
    @app.post("/api/clients/{client_id}/request-lists", dependencies=[Depends(auth)])
    def create_request_list(client_id: str, body: RequestListIn, actor: str = Depends(auth)):
        st = current()
        try:
            r = checklist.build_for_client(st.store, st.llm, client_id, body.tax_year, body.firm_name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        st.store.log("request_list_create", actor, client_id, list_id=r["id"], tax_year=r["tax_year"], items=len(r["items"]))
        return r

    @app.get("/api/clients/{client_id}/request-lists", dependencies=[Depends(auth)])
    def list_request_lists(client_id: str):
        return current().store.list_request_lists(client_id)

    @app.get("/api/request-lists/{list_id}", dependencies=[Depends(auth)])
    def get_request_list(list_id: str):
        r = current().store.get_request_list(list_id)
        if not r:
            raise HTTPException(404, "request list not found")
        return r

    @app.patch("/api/request-lists/{list_id}", dependencies=[Depends(auth)])
    def update_request_list(list_id: str, body: RequestEmailIn, actor: str = Depends(auth)):
        st = current()
        if not st.store.get_request_list(list_id):
            raise HTTPException(404, "request list not found")
        st.store.update_request_list(list_id, **body.model_dump())
        if body.status == "sent":
            st.store.log("request_list_sent", actor, st.store.get_request_list(list_id)["client_id"], list_id=list_id)
        return st.store.get_request_list(list_id)

    @app.post("/api/request-lists/{list_id}/items", dependencies=[Depends(auth)])
    def add_request_item(list_id: str, body: RequestItemIn):
        st = current()
        if not st.store.get_request_list(list_id):
            raise HTTPException(404, "request list not found")
        return st.store.add_request_item(list_id, body.item, body.why, body.category)

    @app.patch("/api/request-lists/{list_id}/items/{item_id}", dependencies=[Depends(auth)])
    def set_request_item(list_id: str, item_id: str, body: RequestItemStatusIn):
        st = current()
        it = st.store.get_request_item(item_id)
        if not it or it["list_id"] != list_id:
            raise HTTPException(404, "item not found")
        st.store.set_request_item(item_id, body.status, note=body.note)
        return st.store.get_request_list(list_id)

    @app.get("/api/reminders/due", dependencies=[Depends(auth)])
    def reminders_due():
        return current().store.due_reminders()

    @app.post("/api/reminders/{list_id}/send", dependencies=[Depends(auth)])
    def send_reminder(list_id: str, firm_name: str = "our office", actor: str = Depends(auth)):
        try:
            return dispatch_reminder(current(), list_id, actor, firm_name)
        except KeyError:
            raise HTTPException(404, "request list not found")

    @app.get("/api/request-lists/{list_id}/organizer", dependencies=[Depends(auth)])
    def get_organizer(list_id: str):
        st = current()
        rl = st.store.get_request_list(list_id)
        if not rl:
            raise HTTPException(404, "request list not found")
        answers = st.store.organizer_answers(list_id)
        rt = checklist._return_type(st.store.get_client(rl["client_id"]) or {}, st.store.canonical_records(rl["client_id"]))
        qs = checklist.organizer_for(rt, rl["tax_year"])
        for q in qs:
            a = answers.get(q["key"], {})
            q["answer"], q["note"] = a.get("answer"), a.get("note")
        return {"return_type": rt, "questions": qs}

    @app.post("/api/request-lists/{list_id}/organizer", dependencies=[Depends(auth)])
    def answer_organizer(list_id: str, body: OrganizerAnswersIn, actor: str = Depends(auth)):
        st = current()
        rl = st.store.get_request_list(list_id)
        if not rl:
            raise HTTPException(404, "request list not found")
        qmap = {q["key"]: q for q in checklist.ORGANIZER_QUESTIONS}
        effects = {"added": 0, "reopened": 0, "retired": 0}
        for a in body.answers:
            q = qmap.get(a.get("key"))
            if not q:
                continue
            ans = a.get("answer")
            if ans not in ("yes", "no", None):
                raise HTTPException(400, f"answer for {a.get('key')} must be yes, no or null")
            st.store.set_organizer_answer(list_id, q["key"], ans, a.get("note"))
            e = checklist.apply_organizer_answer(st.store, rl, q, ans)
            for k in effects:
                effects[k] += e[k]
        st.store.log("organizer_answers", actor, rl["client_id"], list_id=list_id, answers=[(a.get("key"), a.get("answer")) for a in body.answers], **effects)
        return {"effects": effects, "list": st.store.get_request_list(list_id)}

    @app.post("/api/request-lists/{list_id}/reconcile-transcript", dependencies=[Depends(auth)])
    async def reconcile_transcript(list_id: str, document_id: str | None = Form(None), files: list[UploadFile] | None = File(None),
                                   actor: str = Depends(auth)):
        """Use the IRS wage & income transcript to make the request list specific: one item per payer the IRS
        knows about, generic items retired, already-received documents matched. Upload the transcript here or
        point at one already in the client's folder."""
        st = current()
        rl = st.store.get_request_list(list_id)
        if not rl:
            raise HTTPException(404, "request list not found")
        doc_id = document_id
        if files:
            f = files[0]
            r = st.pipeline.ingest_bytes(client_id=rl["client_id"], filename=f.filename or "transcript.txt", data=await f.read(),
                                         uploaded_by=actor, engagement="tax", tax_year=rl["tax_year"] - 1 if rl.get("tax_year") else None)
            if r["status"] not in ("ready", "duplicate"):
                raise HTTPException(400, f"transcript could not be ingested: {r.get('error')}")
            doc_id = r["document_id"]
        if not doc_id:
            raise HTTPException(400, "provide a transcript file or a document_id")
        doc = st.store.get_document(doc_id)
        if not doc or doc["client_id"] != rl["client_id"]:
            raise HTTPException(404, "transcript document not found for this client")
        canonical = json.loads(doc.get("canonical_json") or "{}")
        raw = canonical.get("transcript_entries")
        if raw is None:
            raise HTTPException(400, "that document is not an IRS wage & income transcript")
        entries = [transcript_mod.TranscriptEntry(form=e["form"], payer=e["payer"], amount=e.get("amount"), amount_label=e.get("amount_label")) for e in raw]
        result = transcript_mod.reconcile(st.store, rl, entries, doc_id, actor)
        result["transcript_document_id"] = doc_id
        result["list"] = st.store.get_request_list(list_id)
        return result

    # ------------------------------------------------- client-facing organizer (magic link)
    # Research (Prompt 14F): portals are link-only (SmartVault forbids iframes); Liscio-style magic links are
    # short-lived and single-use. Pattern here: short expiry, consumed on first open, then a bounded working
    # session; IP recorded but not enforced. The page shows only this list's questions and upload slots.
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @app.post("/api/request-lists/{list_id}/client-link", dependencies=[Depends(auth)])
    def create_client_link(list_id: str, body: ClientLinkIn, request: Request, actor: str = Depends(auth)):
        st = current()
        rl = st.store.get_request_list(list_id)
        if not rl:
            raise HTTPException(404, "request list not found")
        token = secrets.token_urlsafe(32)
        st.store.create_client_link(list_id, _hash(token), actor, body.ttl_minutes * 60)
        st.store.log("client_link_create", actor, rl["client_id"], list_id=list_id, ttl_minutes=body.ttl_minutes, session_minutes=body.session_minutes)
        base = str(request.base_url).rstrip("/")
        return {"url": f"{base}/client/{token}", "expires_in_minutes": body.ttl_minutes, "session_minutes": body.session_minutes,
                "note": "Single use. Send it to the client through the firm's usual channel; do not post it anywhere."}

    @app.delete("/api/request-lists/{list_id}/client-link", dependencies=[Depends(auth)])
    def revoke_client_links(list_id: str, actor: str = Depends(auth)):
        n = current().store.revoke_client_links(list_id)
        return {"revoked": n}

    def _client_session(token: str, request: Request, consume: bool = False) -> dict:
        st = current()
        link = st.store.get_client_link(_hash(token))
        now = dt.datetime.now().timestamp()
        if not link:
            raise HTTPException(404, "This link is not valid.")
        if link["opened_at"] is None:
            if now > link["expires_at"]:
                raise HTTPException(410, "This link has expired. Ask your preparer for a new one.")
            if consume:
                ip = request.client.host if request.client else None
                session_seconds = int(request.query_params.get("s", "3600"))
                st.store.open_client_link(_hash(token), ip, max(600, min(session_seconds, 4 * 3600)))
                link = st.store.get_client_link(_hash(token))
            else:
                raise HTTPException(403, "Open the link first.")
        elif now > (link["session_until"] or 0):
            raise HTTPException(410, "This session has ended. Ask your preparer for a new link.")
        return link

    @app.get("/client/{token}", response_class=HTMLResponse, include_in_schema=False)
    def client_page(token: str, request: Request):
        link = _client_session(token, request, consume=True)
        return HTMLResponse((STATIC / "client.html").read_text().replace("__TOKEN__", token))

    @app.get("/api/client/{token}/list")
    def client_list(token: str, request: Request):
        st = current()
        link = _client_session(token, request)
        rl = st.store.get_request_list(link["list_id"])
        client = st.store.get_client(rl["client_id"]) or {}
        rt = checklist._return_type(client, st.store.canonical_records(rl["client_id"]))
        answers = st.store.organizer_answers(rl["id"])
        qs = [{"key": q["key"], "text": q["text"], "answer": answers.get(q["key"], {}).get("answer")} for q in checklist.organizer_for(rt, rl["tax_year"])]
        items = [{"id": i["id"], "item": i["item"], "category": i["category"], "status": i["status"]} for i in rl["items"] if i["status"] != "not_applicable"]
        return {"client_name": client.get("name"), "tax_year": rl["tax_year"], "questions": qs, "items": items,
                "session_until": link["session_until"]}

    @app.post("/api/client/{token}/answers")
    def client_answers(token: str, body: OrganizerAnswersIn, request: Request):
        st = current()
        link = _client_session(token, request)
        rl = st.store.get_request_list(link["list_id"])
        qmap = {q["key"]: q for q in checklist.ORGANIZER_QUESTIONS}
        for a in body.answers:
            q = qmap.get(a.get("key"))
            if q and a.get("answer") in ("yes", "no", None):
                st.store.set_organizer_answer(rl["id"], q["key"], a.get("answer"), a.get("note"))
                checklist.apply_organizer_answer(st.store, rl, q, a.get("answer"))
        st.store.log("client_organizer_answers", "client", rl["client_id"], list_id=rl["id"], answers=[(a.get("key"), a.get("answer")) for a in body.answers])
        return {"ok": True}

    @app.post("/api/client/{token}/upload/{item_id}")
    async def client_upload(token: str, item_id: str, request: Request, files: list[UploadFile] = File(...)):
        st = current()
        link = _client_session(token, request)
        rl = st.store.get_request_list(link["list_id"])
        it = st.store.get_request_item(item_id)
        if not it or it["list_id"] != rl["id"]:
            raise HTTPException(404, "item not found")
        results = []
        for f in files:
            data = await f.read()
            if len(data) > 50 * 1024 * 1024:
                results.append({"filename": f.filename, "status": "failed", "error": "file larger than 50 MB"})
                continue
            r = st.pipeline.ingest_bytes(client_id=rl["client_id"], filename=f.filename or "upload", data=data, uploaded_by="client",
                                         engagement="tax", tax_year=rl["tax_year"])
            if r["status"] in ("ready", "duplicate"):
                st.store.set_request_item(item_id, "received", document_id=r["document_id"])
            results.append({"filename": f.filename, "status": r["status"]})
        st.store.log("client_upload", "client", rl["client_id"], list_id=rl["id"], item_id=item_id, files=[x["filename"] for x in results])
        return {"results": results}

    def _ingest_for_list(st: AppState, rl: dict, filename: str, data: bytes, actor: str, source_uri: str | None = None) -> dict:
        return st.pipeline.ingest_bytes(client_id=rl["client_id"], filename=filename, data=data, uploaded_by=actor,
                                        engagement="tax", tax_year=rl["tax_year"], source_uri=source_uri)

    @app.post("/api/request-lists/{list_id}/items/{item_id}/upload", dependencies=[Depends(auth)])
    async def upload_for_item(list_id: str, item_id: str, files: list[UploadFile] = File(...), actor: str = Depends(auth)):
        """Staff received a document for a specific checklist item: file it in the client folder and tick the item."""
        st = current()
        rl = st.store.get_request_list(list_id)
        it = st.store.get_request_item(item_id)
        if not rl or not it or it["list_id"] != list_id:
            raise HTTPException(404, "item not found")
        results = []
        for f in files:
            r = _ingest_for_list(st, rl, f.filename or "upload", await f.read(), actor)
            if r["status"] in ("ready", "duplicate"):
                st.store.set_request_item(item_id, "received", document_id=r["document_id"])
            results.append({"filename": f.filename, **r})
        return {"results": results, "list": st.store.get_request_list(list_id)}

    @app.post("/api/request-lists/{list_id}/inbound", dependencies=[Depends(auth)])
    async def inbound(list_id: str, files: list[UploadFile] = File(...), sender: str | None = Form(None), subject: str | None = Form(None),
                      actor: str = Depends(auth)):
        """A client reply arrived (from a mailbox connector or a portal webhook): file every attachment into the client's
        folder, match each one to a pending item, and leave anything unrecognised for staff to assign."""
        st = current()
        rl = st.store.get_request_list(list_id)
        if not rl:
            raise HTTPException(404, "request list not found")
        results = []
        for f in files:
            data = await f.read()
            r = _ingest_for_list(st, rl, f.filename or "attachment", data, actor or sender)
            pending = [i for i in st.store.get_request_list(list_id)["items"] if i["status"] == "pending"]
            head = ""
            if r["status"] == "ready":
                head = (r.get("summary") or "")
            match = checklist.match_inbound(f.filename or "", head, pending)
            if match and r["status"] in ("ready", "duplicate"):
                st.store.set_request_item(match["id"], "received", document_id=r["document_id"])
            results.append({"filename": f.filename, "document_id": r.get("document_id"), "ingest_status": r["status"],
                            "matched_item": match["item"] if match else None, "matched_item_id": match["id"] if match else None})
        st.store.log("request_list_inbound", actor, rl["client_id"], list_id=list_id, sender=sender, subject=subject,
                     files=[x["filename"] for x in results], matched=sum(1 for x in results if x["matched_item"]))
        return {"results": results, "list": st.store.get_request_list(list_id)}

    # ---------------------------------------------------------------- chat
    @app.post("/api/chat", dependencies=[Depends(auth)])
    def chat(body: ChatIn, actor: str = Depends(auth)):
        st = current()
        if body.client_id and not st.store.get_client(body.client_id):
            raise HTTPException(404, "client not found")
        try:
            r = st.rag.ask(body.question, body.client_id, body.history, actor=actor, today=dt.date.today().isoformat())
        except RuntimeError as e:
            raise HTTPException(502, str(e))
        return {"answer": r.answer, "citations": r.citations, "tool_trace": r.tool_trace, "model": r.model, "usage": r.usage}

    @app.get("/api/search", dependencies=[Depends(auth)])
    def search(q: str, client_id: str | None = None, tax_year: int | None = None, k: int = 8):
        hits = current().rag.retrieve(q, client_id, tax_year, top_k=k)
        return [h.__dict__ for h in hits]

    # --------------------------------------------------------------- admin
    @app.get("/api/admin/models", dependencies=[Depends(auth)])
    def models():
        return current().describe()

    @app.post("/api/admin/models/profile", dependencies=[Depends(auth)])
    def switch_profile(body: ProfileIn, actor: str = Depends(auth)):
        """Hot-swap the model profile. Chunks embedded with a different model are reported as stale."""
        try:
            new_settings = Settings.load(body.profile)
            new_state = AppState(new_settings)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f"could not activate profile '{body.profile}': {e}")
        app.state.rag_state = new_state
        new_state.store.log("profile_switch", actor, None, profile=body.profile, llm=new_state.llm.identity, embedding=new_state.embedder.identity)
        return new_state.describe()

    @app.post("/api/admin/reindex", dependencies=[Depends(auth)])
    def reindex(actor: str = Depends(auth)):
        return current().pipeline.reindex(actor)

    @app.post("/api/admin/sync/folder", dependencies=[Depends(auth)])
    def sync_folder(body: FolderSyncIn, actor: str = Depends(auth)):
        """Pull new or changed files from a client file share (or Drake DMS / OneDrive-synced folder) into the archive."""
        st = current()
        if not Path(body.root).is_dir():
            raise HTTPException(400, f"'{body.root}' is not a directory reachable from the server")
        conn = FolderConnector(body.root, client_depth=body.client_depth, source_prefix=body.source_prefix)
        r = run_sync(conn, st.store, st.pipeline, actor=actor, create_clients=body.create_clients)
        r["files"] = r["files"][:200]
        return r

    @app.get("/api/admin/sync", dependencies=[Depends(auth)])
    def sync_state():
        return current().store.list_sync_state()

    @app.get("/api/admin/audit", dependencies=[Depends(auth)])
    def audit(limit: int = 100):
        return current().store.recent_audit(limit)

    @app.exception_handler(Exception)
    async def unhandled(_, exc: Exception):  # pragma: no cover
        log.exception("unhandled error")
        return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


app = create_app()
