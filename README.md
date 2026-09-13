# Firm Archive Assistant

A working prototype of a private, model-agnostic "ask your archive" system for accounting firms.
Staff upload years of client records (tax returns, financial statements, trial balances, audit
files); the system normalises each file into a canonical JSON record, indexes it for retrieval, and
lets a partner ask questions in plain English:

> "Pull up ABC Company's financial statements from last year's audit. For planning this year, which
> areas look riskiest, and what should we expect the 2026 figures to look like?"

The answer cites the source files, and every number comes from deterministic tools (ratio screens,
trend projections) rather than from the language model's imagination.

## What is in this repository

| Path | What it is |
|---|---|
| `app/` | FastAPI backend, ingestion pipeline, RAG engine, provider adapters, browser UI |
| `models.yaml` | The model registry. Swapping LLM / extractor / embedding model is a config edit |
| `sample_data/` | Synthetic client files (an S-corp audit client and a 1040 client) for demos and tests |
| `scripts/seed_demo.py` | Loads the sample clients into a fresh database |
| `tests/` | Pytest suite that runs fully offline |
| `docs/ARCHITECTURE.md` | How the pieces fit, the canonical JSON schema, how model hot-swapping works |
| `docs/MODEL_RECOMMENDATIONS.md` | Which LLMs, embedding models and vector stores to use, and the zero-retention options |
| `docs/RISKS.md` | Legal, security, accuracy and business risks with mitigations |
| `docs/ONBOARDING_PLAYBOOK.md` | How to onboard a firm and get files into the right format, including client self-upload |
| `docs/PILOT_PLAN.md` | A busy-season pilot plan for a small tax/audit practice, with a weekly one-hour cadence |
| `docs/BUSINESS_MODEL.md` | Pricing, positioning and the "remote fractional AI lead" service model |
| `docs/RESEARCH_BOT_PROMPTS.md` | Copy-paste instructions for an AI research agent to map competing products (accounting first, then law and other professions) |

## Quick start (no API keys needed)

```bash
pip install -r requirements.txt
cp .env.example .env            # defaults to the offline profile
python scripts/seed_demo.py     # loads the two sample clients
uvicorn app.main:app --reload   # open http://127.0.0.1:8000
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

## Running the tests

```bash
python -m pytest -q
```

## Status

This is a prototype built for a pilot with a small practice. It is not yet hardened for
multi-tenant production use. `docs/RISKS.md` lists what has to change before a paying firm relies on it.
