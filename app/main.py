"""FastAPI application: REST API + static UI."""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import forecast
from .config import Settings
from .ingest import IngestPipeline
from .providers import build_embedding_provider, build_llm_provider
from .providers.registry import known_providers
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



class AppState:
    """Everything that depends on the model profile lives here so it can be hot-swapped."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = Store(settings.db_path)
        self.llm = build_llm_provider(settings.llm)
        self.extractor = build_llm_provider(settings.extractor)
        self.embedder = build_embedding_provider(settings.embedding)
        self.pipeline = IngestPipeline(self.store, self.extractor, self.embedder, settings.uploads_dir)
        self.rag = RagEngine(self.store, self.llm, self.embedder)

    def describe(self) -> dict[str, Any]:
        return {
            "profile": self.settings.profile_name,
            "available_profiles": self.settings.available_profiles,
            "llm": self.llm.identity,
            "extractor": self.extractor.identity,
            "embedding": self.embedder.identity,
            "embedding_dimensions": self.embedder.dimensions,
            "stale_chunks": self.store.stale_chunk_count(self.embedder.identity),
            "known_providers": known_providers(),
            "stats": self.store.stats(),
        }


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

    # --------------------------------------------------------- documents
    @app.post("/api/documents", dependencies=[Depends(auth)])
    async def upload(client_id: str = Form(...), engagement: str | None = Form(None), tax_year: int | None = Form(None),
                     files: list[UploadFile] = File(...), actor: str = Depends(auth)):
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
                                         engagement=engagement, tax_year=tax_year)
            r["filename"] = f.filename
            results.append(r)
        return {"results": results}

    @app.get("/api/documents/{doc_id}", dependencies=[Depends(auth)])
    def get_document(doc_id: str):
        d = current().store.get_document(doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        return d

    @app.delete("/api/documents/{doc_id}", dependencies=[Depends(auth)])
    def delete_document(doc_id: str, actor: str = Depends(auth)):
        s = current().store
        d = s.get_document(doc_id)
        if not d:
            raise HTTPException(404, "document not found")
        s.delete_document(doc_id)
        s.log("document_delete", actor, d["client_id"], document_id=doc_id, filename=d["filename"])
        return {"deleted": doc_id}

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
