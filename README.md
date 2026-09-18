# Firm Archive Assistant

A working prototype of a private, model-agnostic "ask your archive" system for tax practices.
Staff upload years of client records (1040s with their schedules, 1065 partnership returns, 1120-S
and 1120 corporate returns, K-1s, W-2s and 1099s, books, notices, preparer notes); the system
recognises the return type and the forms present, normalises each file into a canonical JSON record,
indexes it for retrieval, and lets a preparer ask questions in plain English:

> "Pull up ABC Company's 1120-S from last year. What should we watch when preparing this year's
> return, and what should we expect the 2026 figures to look like?"

The first release is tax-only. Audit and review engagements are a later expansion; the architecture
does not change, only the fact vocabulary and the screens.

The answer cites the source files, and every number comes from deterministic tools (ratio screens,
trend projections) rather than from the language model's imagination.

Beyond search, the prototype does two engagement-level jobs: **tax-planning screens and projections**
per client (estimated-payment safe harbour, S-corp election candidates, reasonable compensation,
distributions versus basis, accumulated earnings, itemize-versus-standard, year-over-year swings), and
**tax-season request lists** that read last year's return, draft the document request email, file the
client's replies into their folder, and keep an "items pending" list. Request lists know the difference
between a 1040 client and a 1065 / 1120-S / 1120 client, carry a conditional organizer whose yes/no answers open or
retire items, and send scheduled reminders until nothing is pending. A **Verify** tab lets staff accept, reject or
correct every extracted figure before it is used; rejected figures drop out of planning and answers.

## The MVP screen

`http://127.0.0.1:8000/` opens the preparer's view, built for someone who does not want to learn
software: pick a client on the left, see last year's return, what is still needed from the
client and what has come in, then press one of four buttons.

| Button | What happens |
|---|---|
| **Start this year's return** | Drafts the document request from last year's return, writes a one-page brief (figures, forms to expect, watch items), and lists the next steps |
| **Review a return** | Compares a draft or filed return (the PDF from the tax software) with last year: what moved, which forms are missing, what to check |
| **Financial statements** | Builds a balance sheet and income statement from the trial balance or the return, with an Excel download |
| **Keying sheet for ATX** | Every figure from this year's source documents and the IRS transcript, grouped by the ATX input worksheet, with an Excel download |

The chat below the buttons answers in a few plain sentences; "more" expands. Files are added
with one button or by dropping them anywhere on the page, and the archive recognises the major
IRS forms on the way in (W-2, the 1099 and 1098 families, K-1s, 1095s, 5498s, the 1040 schedules,
1065 / 1120-S / 1120 and their schedules, payroll filings, notices, transcripts; see
`app/ingest/forms_catalog.py`). The earlier working screen is still at `/workbench` for the
checklist, verification, reminders and model settings.

ATX has no API; the keying sheet and ATX's own CSV / K-1 / trial-balance imports are the bridge.
See `docs/ATX_INTEGRATION.md`.

## What is in this repository

| Path | What it is |
|---|---|
| `app/` | FastAPI backend, ingestion pipeline, RAG engine, provider adapters, browser UI |
| `models.yaml` | The model registry. Swapping LLM / extractor / embedding model is a config edit |
| `sample_data/` | Synthetic returns: a 1040 client, an 1120-S, a 1065 and an 1120, two years each, plus MeF e-file XML samples, for demos and tests |
| `docs/LINE_MAP_1040.md` | Form 1040 line renumbering TY2023–2025 and how extraction handles it |
| `scripts/seed_demo.py` | Loads the sample clients into a fresh database |
| `tests/` | Pytest suite that runs fully offline |
| `docs/ARCHITECTURE.md` | How the pieces fit, the canonical JSON schema, how model hot-swapping works |
| `docs/MODEL_RECOMMENDATIONS.md` | Which LLMs, embedding models and vector stores to use, and the zero-retention options |
| `docs/RISKS.md` | Legal, security, accuracy and business risks with mitigations |
| `docs/ONBOARDING_PLAYBOOK.md` | How to onboard a firm and get files into the right format, including client self-upload |
| `docs/PILOT_PLAN.md` | A busy-season pilot plan for a small tax/audit practice, with a weekly one-hour cadence |
| `docs/BUSINESS_MODEL.md` | Pricing, positioning and the "remote fractional AI lead" service model |
| `docs/ATX_INTEGRATION.md` | What ATX can import, why the MVP does not automate its screens, and the keying-sheet bridge |
| `docs/GRAPH_SETUP.md` | Least-privilege Microsoft 365 setup for a firm's IT provider (SharePoint read, shared-mailbox send) |
| `docs/EVALUATION.md` | How to run and grow the evaluation set; labelled datasets for OCR accuracy |
| `docs/COMPLIANCE_KIT.md` | Engagement-letter paragraph, §7216 consent approach, sub-processor list, questionnaire answers (drafts for counsel) |
| `docs/ROADMAP.md` | Feature status against the research backlog, next steps, do-not-build list |
| `docs/PRD.md` | One-page prototype PRD |
| `docs/RESEARCH_FINDINGS.md` | What the research agent found and the decisions taken |
| `docs/RESEARCH_BOT_PROMPTS.md` | Copy-paste instructions for an AI research agent to map competing products (accounting first, then law and other professions) |

## Quick start (no API keys needed)

```bash
pip install -r requirements.txt
cp .env.example .env            # defaults to the offline profile
python scripts/seed_demo.py     # loads the two sample clients
uvicorn app.main:app --reload   # open http://127.0.0.1:8000 (preparer view) or /workbench
```

The default access token is `change-me` (set in `.env`). The UI stores it in the browser after
you paste it into **Models & audit**.

In the offline profile the "LLM" is a deterministic stand-in: it retrieves evidence, calls the
forecasting and risk tools, and shows you exactly what a real model would be given. That lets you
demo the whole workflow to a firm before a single client document leaves their network.

## Switching on a real model

1. Put `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` in `.env`.
2. Set `FIRM_RAG_PROFILE=anthropic_voyage` (or pick the profile from the UI's **Models & audit** dialog).
3. Click **Re-embed stale chunks** so every chunk shares the new embedding space.

Adding a newer model later is one edit to `models.yaml`. See `docs/ARCHITECTURE.md`.

By default a copy of each uploaded original is kept so citations can open it. Set
`FIRM_RAG_KEEP_ORIGINALS=false` and pass a source link on upload to store only the index and
point citations at the firm's own file share or document management system.

## Running the tests

```bash
python -m pytest -q
```

## Status

This is a prototype built for a pilot with a small practice. It is not yet hardened for
multi-tenant production use. `docs/RISKS.md` lists what has to change before a paying firm relies on it.
