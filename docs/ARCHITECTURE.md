# Architecture

## One-paragraph version

Files come in through the UI or API, get parsed to text, and are sent to an **extractor** model
that returns a small canonical JSON record (document type, tax year, summary, entities,
`facts` triples, risk flags). The text is chunked and embedded with an **embedding** model and
stored next to the facts in SQLite. When someone asks a question, the question is embedded,
the closest chunks for that client are retrieved, and the **LLM** answers from that evidence,
calling deterministic tools for anything numeric. Every upload, query, model switch and delete
is written to an audit log.

```
              ┌────────────┐   parse    ┌──────────┐  extract JSON  ┌──────────────┐
 upload ────► │  parsers   │ ─────────► │ chunker  │ ─────┐         │  extractor   │
 (pdf/csv/    └────────────┘            └──────────┘      │         │  model slot  │
  xlsx/json)                                  │ embed     ▼         └──────────────┘
                                              ▼      ┌──────────┐          │ facts, summary
                                       ┌────────────┐│  facts   │◄─────────┘
                                       │  chunks +  ││  table   │
                                       │  vectors   │└──────────┘
                                       └────────────┘      ▲
 question ──► embed ──► top-k search ───────┘              │ get_client_facts /
                              │                            │ forecast_financials /
                              ▼                            │ assess_risk
                    ┌──────────────────┐   tool calls  ┌────┴─────┐
                    │  LLM model slot  │ ◄───────────► │  tools   │
                    └──────────────────┘               └──────────┘
                              │ answer + citations
                              ▼
                             UI
```

## Modules

| Module | Responsibility |
|---|---|
| `app/config.py` | Loads `.env` and `models.yaml`; produces one `SlotConfig` per model slot |
| `app/providers/base.py` | The two interfaces everything depends on: `LLMProvider` and `EmbeddingProvider` |
| `app/providers/registry.py` | Name → adapter class map. New vendors register here |
| `app/providers/anthropic_llm.py` | Claude adapter (chat with tools, JSON extraction via structured outputs, prompt caching) |
| `app/providers/mock_llm.py` | Offline stand-in used by tests and demos |
| `app/providers/{voyage,openai,hash}_embed.py` | Embedding adapters |
| `app/ingest/parsers.py` | PDF/CSV/XLSX/JSON/TXT → pages of text; flags scanned PDFs that need OCR |
| `app/ingest/chunker.py` | Page-aware chunking with headings and overlap |
| `app/ingest/extractor.py` | The canonical JSON schema and extraction prompt |
| `app/ingest/pipeline.py` | Orchestrates upload → parse → extract → chunk → embed → store; dedupes by SHA-256; reindex |
| `app/store.py` | SQLite tables: clients, documents, chunks (with float32 vectors), facts, audit_log |
| `app/forecast.py` | Linear trend + CAGR projections, ratio analysis, analytical-review flags |
| `app/rag.py` | Retrieval, system prompt, tool loop, citations |
| `app/main.py` | REST API and static UI; hot-swappable `AppState` |
| `app/static/index.html` | Single-file browser UI (no build step) |

## Canonical JSON record

Every document, regardless of source format, becomes:

```json
{
  "doc_type": "financial_statements",
  "tax_year": 2025,
  "summary": "Audited statements for ABC Company... covenant breach waived post year-end.",
  "entities": [{"name": "ABC Company, Inc.", "role": "entity"}, {"name": "First Regional Bank", "role": "bank"}],
  "facts": [
    {"name": "revenue", "value": 5610000, "period": 2025, "unit": "USD", "source_quote": "Revenue: 5,610,000"},
    {"name": "accounts_receivable", "value": 1180000, "period": 2025, "unit": "USD", "source_quote": "Accounts receivable, net: 1,180,000"}
  ],
  "risk_flags": ["Current-ratio covenant breached at year end; waiver obtained Feb 2026"]
}
```

Why this shape:

- `facts` are flat `(name, value, period)` triples, so a 1040, a set of statements and a trial
  balance all feed the same forecasting and ratio code.
- The fact vocabulary (`FACT_NAMES` in `extractor.py`) is an enum the extractor must pick from.
  That keeps "Sales", "Net sales" and "Revenues" from becoming three different series.
- `source_quote` makes each number auditable back to the line it came from.
- The whole record is also indexed as a chunk, so "what does the 2025 return say" questions hit
  the summary directly instead of a random page.

Extend the vocabulary as the practice needs (e.g. `qbi_deduction`, `payroll_tax`,
`fixed_assets_net`). Existing documents can be re-extracted by deleting and re-uploading, or by
adding a `reextract` admin route (straightforward: `pipeline.ingest_bytes` already does the work).

## Model hot-swapping

The application never names a model. `models.yaml` defines **profiles**; each profile fills
three **slots**:

| Slot | Used for | Typical choice |
|---|---|---|
| `llm` | Answering staff, forecasting narrative | Most capable model you can afford |
| `extractor` | Turning files into canonical JSON at ingest (batchable, high volume) | Mid-tier model |
| `embedding` | Vectorising chunks and queries | Domain-strong embedding model |

Swapping a model:

1. Edit `models.yaml` (change `model:` or add a new profile).
2. Restart, or call `POST /api/admin/models/profile` from the UI's **Models & audit** dialog.
3. If the *embedding* slot changed, the UI shows a "stale chunks" count. Click **Re-embed** (or
   `POST /api/admin/reindex`). Chunks store the embedding model identity, so mixed indexes are
   never searched together.

Adding a new vendor: subclass `LLMProvider` or `EmbeddingProvider`, decorate with
`@register_llm("name")` / `@register_embedding("name")`, and import it in
`registry._import_adapters`. Roughly 60 lines each; the Voyage adapter is a good template.

Every audit-log row records which model produced an answer or extraction, so you can compare
model versions on the same questions later (see the evaluation section below).

## Retrieval details

- Scoped by `client_id` first. Cross-client search is only possible when no client is selected,
  which is what a partner expects and what confidentiality demands.
- Chunks carry a header line (`[client_id=…] [file=…] [doc_type=…] [year=…]`) so a retrieved
  passage is self-describing to the model and in the citations panel.
- Brute-force cosine over float32 vectors in numpy. At 1,500 chars per chunk a small practice with
  500 clients × 10 years × 5 documents ≈ 250k chunks, which still searches in well under a second.
  Past that, move to pgvector (see below).
- Every citation carries `document_id` and `page`. The UI turns `[3]` and `[file.pdf p.3]`
  references in an answer, and each entry in the Citations panel, into a link that opens the
  stored original (`/api/documents/{id}/file`, PDFs open at the cited page via `#page=N`).
  For firms with a document management system, store the DMS deep link on the document record
  and point the citation there instead of at the stored copy.
- The LLM has a `search_documents` tool, so it can run a follow-up query (e.g. for a note
  disclosure) when the first retrieval did not contain what it needs.

## Forecasting and risk

`app/forecast.py` is deliberately boring arithmetic: least-squares linear trend, CAGR,
year-over-year deltas, current ratio, debt-to-equity, AR days, inventory days, margins, and a
set of analytical-review flags (receivables growing faster than revenue, large swings). The
model must call these tools and is told to explain method and assumptions. Thresholds are
generic starting points; tune them per industry with the engagement partner.

## Tax-season request lists

`app/checklist.py` turns the archive into a client to-do list at the start of an engagement.

1. **Context.** For the client, take the most recent year on file as the prior year, pull its
   extracted facts (wages, interest, dividends, Schedule C profit, estimated payments...), the
   lower-cased text of the folder, the extractor's risk flags, and any preparer notes.
2. **Rules.** Each rule is (condition, item, why, match words). Wages on the return produce
   "W-2 from each employer (wages of $142,500 on the 2025 return)"; the word "home office" in
   the folder produces the home-office item; a note containing "ask about" becomes a Follow-up
   item. Rules are plain Python and are meant to be edited with the firm; see `RULES`.
3. **Email.** A grouped, checkbox-style draft. With a real model profile the wording is
   polished by the LLM; it may not add or drop items.
4. **Tracking.** `request_lists` / `request_items` tables. Items are pending, received or not
   applicable; the list flips to complete when nothing is pending.
5. **Receiving.** Two routes file the client's documents into their folder through the normal
   ingestion pipeline (so they are indexed and searchable immediately) and tick the item:
   `POST /request-lists/{id}/items/{item}/upload` for a specific item, and
   `POST /request-lists/{id}/inbound` for a whole reply, where each attachment is matched to a
   pending item by filename and extracted text (specific tokens such as `1099-int` beat generic
   ones). Unmatched attachments are still filed and listed for staff to assign.

Wiring a mailbox: a Microsoft Graph or Gmail webhook (or the firm's portal) posts the
attachments to the inbound route with the sender address; map sender to client on the way in.
Reminder cadences (nudge after 7 and 14 days for pending items) are a small scheduled job on
top of `list_request_lists`.

## Security model of the prototype

- Single shared `X-API-Token`. Fine for a one-office pilot on a private network; replace with
  SSO (Microsoft Entra / Google Workspace) and per-user roles before anything else.
- Originals are stored on disk under `data/uploads/<client_id>/` in copy mode. In pointer mode
  (`FIRM_RAG_KEEP_ORIGINALS=false`) nothing is copied and the document record holds a `source_uri`;
  the file route redirects there. Encrypt the volume at rest either way.
- All model calls go out over HTTPS to the configured vendor; nothing else leaves the box.
- Audit log is append-only from the application's point of view.

## Scaling the vector store

`Store` is the only module that knows about SQLite. To move to Postgres + pgvector:

1. Keep the same tables; change `embedding BLOB` to `vector(N)`.
2. Replace `Store.search` with an SQL `ORDER BY embedding <=> $1 LIMIT k` query with the same
   filters.
3. Nothing above `Store` changes.

Managed alternatives (Qdrant Cloud, Pinecone, Weaviate) work the same way but push client data to
a third party, which means another data-processing agreement. For a firm-by-firm deployment
model, Postgres on the firm's own VM or private cloud project is the simplest story to tell a
client.

## Evaluation harness (next step)

Before swapping models in production, run a fixed question set against a fixed client archive and
compare. The pieces needed already exist:

- `tests/` shows how to spin up an app instance and seed it.
- The audit log stores `question`, `model`, `citations`, `tools`.
- Add a `evals/questions.jsonl` with `{question, client_id, expected_facts, expected_files}` and a
  script that scores citation recall and numeric agreement. Keep ten to twenty questions per
  client type; that is enough to catch regressions when a new model lands.
