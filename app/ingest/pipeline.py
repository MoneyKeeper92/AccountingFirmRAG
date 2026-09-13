"""upload -> parse -> extract -> chunk -> embed -> store."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from ..providers.base import EmbeddingProvider, LLMProvider
from ..store import Store
from .chunker import chunk_pages
from .extractor import extract_canonical
from .mef import is_mef_xml, parse_mef
from .transcript import is_wage_income_transcript, parse_wage_income_transcript, tax_period
from .parsers import parse_file

log = logging.getLogger(__name__)


class IngestPipeline:
    def __init__(self, store: Store, extractor: LLMProvider, embedder: EmbeddingProvider, uploads_dir: Path, keep_originals: bool = True, ocr=None):
        self.store = store
        self.keep_originals = keep_originals
        self.ocr = ocr
        self.extractor = extractor
        self.embedder = embedder
        self.uploads_dir = uploads_dir

    def ingest_bytes(self, *, client_id: str, filename: str, data: bytes, uploaded_by: str | None,
                     engagement: str | None = None, tax_year: int | None = None, keep_original: bool | None = None,
                     source_uri: str | None = None) -> dict[str, Any]:
        """`source_uri` is where the file already lives (UNC path, SharePoint/DMS link). When the
        deployment runs in pointer mode (keep_originals=False) nothing is copied: the index and the
        extracted facts are stored, and citations open the file at its source."""
        if keep_original is None:
            keep_original = self.keep_originals
        sha = hashlib.sha256(data).hexdigest()
        dup = self.store.find_duplicate(client_id, sha)
        if dup:
            return {"document_id": dup["id"], "status": "duplicate", "message": f"Identical file already ingested as {dup['filename']}"}

        doc_id = self.store.create_document(client_id, filename, sha, len(data), uploaded_by, engagement, tax_year, source_uri)
        try:
            parsed = parse_file(filename, data)
            if keep_original:
                # Originals are kept so a reviewer can always open the source. Encrypt this
                # directory at rest in production (see docs/RISKS.md).
                dest = self.uploads_dir / client_id
                dest.mkdir(parents=True, exist_ok=True)
                (dest / f"{doc_id}__{Path(filename).name}").write_bytes(data)

            if parsed.needs_ocr and self.ocr is not None:
                try:
                    pages = self.ocr.extract_pages(data, filename)
                    if pages and sum(len(pg.strip()) for pg in pages) > 40:
                        parsed.pages, parsed.needs_ocr = pages, False
                        parsed.warnings = [w for w in parsed.warnings if "text layer" not in w] + [f"Scanned document transcribed by {self.ocr.identity}; spot-check figures in Verify"]
                except Exception as e:  # noqa: BLE001
                    parsed.warnings.append(f"OCR failed ({type(e).__name__}: {e}); text layer only")

            hints = {"client_id": client_id, "engagement": engagement, "tax_year": tax_year}
            extractor_identity = self.extractor.identity
            if parsed.kind == "xml" and is_mef_xml(data):
                # e-file XML saved from the tax software: deterministic, no model call
                mef = parse_mef(data, filename)
                record, parsed.pages = mef["record"], mef["pages"]
                extractor_identity = "mef_xml:deterministic"
            elif is_wage_income_transcript(parsed.text):
                # IRS wage & income transcript: deterministic; entries feed request-list reconciliation, not the facts series
                entries = parse_wage_income_transcript(parsed.text)
                period = tax_period(parsed.text) or tax_year
                record = {"doc_type": "irs_transcript_wage_income", "return_type": "1040", "tax_year": period, "filing_status": None,
                          "forms_present": sorted({e.form for e in entries}), "entities": [{"name": e.payer, "role": "payer"} for e in entries],
                          "facts": [], "risk_flags": [],
                          "summary": f"IRS wage & income transcript for {period}: {len(entries)} information returns ({', '.join(sorted({e.form for e in entries}))}).",
                          "transcript_entries": [{"form": e.form, "payer": e.payer, "amount": e.amount, "amount_label": e.amount_label} for e in entries]}
                extractor_identity = "irs_transcript:deterministic"
            elif parsed.text.strip():
                record = extract_canonical(self.extractor, parsed.text, filename, hints)
            else:
                record = {"doc_type": "other", "tax_year": tax_year, "summary": "Empty or unreadable document", "entities": [], "facts": [], "risk_flags": []}
            if parsed.needs_ocr:
                record["risk_flags"].append("Scanned PDF without text layer - run OCR and re-upload")
            record["warnings"] = parsed.warnings

            # Prefix every chunk with a header so a retrieved passage is self-describing.
            header = (f"[client_id={client_id}] [file={filename}] [doc_type={record.get('doc_type')}] "
                      f"[return={record.get('return_type', 'none')}] [year={record.get('tax_year') or tax_year}]")
            chunks = chunk_pages(parsed.pages)
            for c in chunks:
                c["text"] = f"{header}\n{c['text']}"
            # The canonical JSON summary is itself a chunk, so 'what does the return say' questions hit it directly.
            chunks.insert(0, {"page": None, "section": "canonical_record", "text": header + "\nSUMMARY: " + record.get("summary", "") +
                              ("\nFORMS: " + ", ".join(record.get("forms_present", [])) if record.get("forms_present") else "") +
                              (f"\nFILING STATUS: {record['filing_status']}" if record.get("filing_status") else "") +
                              "\nFACTS: " + "; ".join(f"{f['name']}({f.get('period')})={f['value']}" for f in record.get("facts", [])) +
                              ("\nRISK FLAGS: " + "; ".join(record.get("risk_flags", [])) if record.get("risk_flags") else "")})
            vectors = self.embedder.embed_documents([c["text"] for c in chunks]) if chunks else []
            n_chunks = self.store.add_chunks(doc_id, client_id, chunks, vectors, self.embedder.identity)
            n_facts = self.store.add_facts(client_id, doc_id, record.get("facts", []))
            self.store.finish_document(doc_id, doc_type=record.get("doc_type"), tax_year=record.get("tax_year") or tax_year,
                                       summary=record.get("summary"), page_count=len(parsed.pages),
                                       extractor_model=extractor_identity, canonical=record)
            self.store.log("upload", uploaded_by, client_id, document_id=doc_id, filename=filename, chunks=n_chunks, facts=n_facts,
                           extractor=extractor_identity, embedding=self.embedder.identity)
            return {"document_id": doc_id, "status": "ready", "doc_type": record.get("doc_type"), "return_type": record.get("return_type"),
                    "forms_present": record.get("forms_present", []), "tax_year": record.get("tax_year") or tax_year,
                    "original_stored": keep_original, "source_uri": source_uri,
                    "summary": record.get("summary"), "chunks": n_chunks, "facts": n_facts, "risk_flags": record.get("risk_flags", []),
                    "warnings": parsed.warnings}
        except Exception as e:  # noqa: BLE001
            log.exception("ingest failed for %s", filename)
            self.store.fail_document(doc_id, f"{type(e).__name__}: {e}")
            self.store.log("upload_failed", uploaded_by, client_id, document_id=doc_id, filename=filename, error=str(e))
            return {"document_id": doc_id, "status": "failed", "error": f"{type(e).__name__}: {e}"}

    def reindex(self, actor: str | None) -> dict[str, Any]:
        """Re-embed every chunk with the currently configured embedding model."""
        chunks = self.store.all_chunks()
        todo = [c for c in chunks if c["embedding_model"] != self.embedder.identity]
        for i in range(0, len(todo), 128):
            batch = todo[i : i + 128]
            vecs = self.embedder.embed_documents([c["text"] for c in batch])
            self.store.replace_embeddings([c["id"] for c in batch], vecs, self.embedder.identity)
        self.store.log("reindex", actor, None, reembedded=len(todo), embedding=self.embedder.identity)
        return {"reembedded": len(todo), "embedding_model": self.embedder.identity}
