# Model, embedding and infrastructure recommendations (September 2026)

Verify pricing and retention terms on the vendors' pages before signing anything; this moves quickly.

## Guiding constraints for an accounting firm

1. **Zero data retention (ZDR) or equivalent contractual guarantee** that prompts and documents
   are not stored or used for training. Non-negotiable for client tax data.
2. **Data residency** in the firm's country. Most US practices are fine with US regions; Canadian
   and EU practices need in-region inference.
3. **Swappability.** Models are improving every few months. No model name belongs in code.
4. **Cost per client-year.** Ingesting a client's archive is a one-time cost; queries are cheap.

## Language models

| Slot | Recommendation | Why | Notes |
|---|---|---|---|
| `llm` (answers, forecasting narrative) | **Claude Opus 5** (`claude-opus-5`) | Strongest reasoning over long financial documents, 1M context, tool use with strict schemas, available under ZDR on the Claude API | Use adaptive thinking; effort `high`. Prompt caching cuts cost on repeated evidence |
| `extractor` (file → canonical JSON) | **Claude Sonnet 5** (`claude-sonnet-5`) | Structured-output extraction is a mid-tier job; 5× cheaper than Opus | Run through the Batch API for bulk onboarding (50% off) |
| Cheap classifier / router (optional) | Claude Haiku 4.5 | Doc-type triage before extraction | Only worth adding once volume is high |
| Alternative vendors | OpenAI GPT-5 family, Google Gemini 2.5/3 | Comparable capability; ZDR only on enterprise agreements or via Azure / Vertex | Wire in with a ~60-line adapter |
| Self-hosted | Llama 4 / Qwen 3 / Mistral Large behind vLLM | Only if a firm forbids any external inference | Expect a quality drop on multi-document reasoning; keep for extraction, not for partner-facing answers |

Where to buy the same models with different data terms:

| Route | ZDR / retention | Residency | When to choose |
|---|---|---|---|
| Claude API direct | ZDR available on request for Opus 5 / Sonnet 5; standard is 30-day retention | US by default; `inference_geo` pins region | Simplest; best for a US pilot |
| Amazon Bedrock | No retention by AWS or Anthropic; runs in your AWS account's region | Any Bedrock region | Firms already on AWS; strongest "it never leaves our cloud account" story |
| Google Vertex AI | Same idea, GCP project | Any Vertex region | Firms on Google Workspace |
| Microsoft Foundry | Same idea, Azure tenant | Azure regions | Firms on Microsoft 365 (most accounting firms). Also gives Entra SSO for free |

Note on top-tier models: Anthropic's highest tier requires 30-day retention and is not offered
under ZDR, so it is excluded here. Opus 5 is the ceiling for a ZDR deployment today.

## Account structure: one account for all firms, or one per firm?

Working hypotheses to verify with Prompt 5 in `docs/RESEARCH_BOT_PROMPTS.md`:

| Structure | How it works | Likely fit |
|---|---|---|
| **A. One account, ours** | You are the customer of the model vendor and the data processor for every firm. Each firm signs a DPA with you. Inside the account, one workspace or project and one API key per firm gives separate spend limits, rate limits and logs. ZDR is normally granted at the organisation level, so one grant should cover every workspace; confirm and get it in writing so you can show firms an attestation | Right starting point for 3–30 staff firms: one contract to negotiate, no per-firm minimums, fastest onboarding |
| **B. One account per firm, in the firm's name** | The firm is the vendor's customer; you hold delegated admin. Each firm would need its own ZDR request and DPA | Only when a firm's counsel insists; slow, and small firms will not want another vendor relationship |
| **C. In the firm's own cloud tenant** | Bedrock / Vertex / Foundry in the firm's AWS, Google or Microsoft account. Those routes do not retain prompts by default, so no separate ZDR request; the firm's existing cloud agreement and controls apply | What larger firms and any firm with an active IT provider will ask for; also your cleanest privacy story |

Expected cost picture (verify): ZDR itself is usually not a per-token surcharge on the Claude
API; it is a configuration granted on request, sometimes tied to an enterprise conversation.
Cloud routes charge the same per-token list prices as the platform, with no retention to opt
out of. The real costs of structure A are the DPA work and the attestation firms will ask for;
the real cost of structure C is deployment effort per firm.

Whatever the structure, IRC §7216 sits on the *firm*: they are the preparer disclosing return
information to a contractor. Your job is to make their compliance easy: a one-page description
of the processing, the sub-processor list (model vendor, embedding vendor, OCR vendor, cloud
host), the retention statement, and the paragraph for their engagement letter.

## Embedding models

| Option | Dimensions | Why | ZDR |
|---|---|---|---|
| **Voyage `voyage-3.5`** (default) | 1024 (Matryoshka; 512 works well too) | Anthropic's recommended embedding partner; strong on finance/legal text; `voyage-finance-2` exists for pure financial corpora | ZDR on request |
| OpenAI `text-embedding-3-large` | 1024–3072 | Ubiquitous, cheap, good | Enterprise / Azure for ZDR |
| Cohere `embed-v4` | 1024 | Good multilingual; available on Bedrock | Via Bedrock |
| Self-hosted `nomic-embed-text` / `bge-m3` / `gte-large` via Ollama or TEI | 768–1024 | Nothing leaves the firm; adequate quality for retrieval of financial statements | N/A |

Guidance: retrieval quality in this domain depends more on **chunk headers and metadata
filtering** (client, year, doc type) than on the last 5% of embedding quality. A self-hosted
embedding model plus Claude for answers is a perfectly defensible configuration and removes one
vendor from the data-processing agreement.

Add a **reranker** (Voyage `rerank-2.5` or Cohere `rerank-3.5`) once archives exceed a few
thousand documents per client. It is a 20-line addition in `RagEngine.retrieve`.

## Document parsing / OCR

Scanned PDFs are the biggest practical problem in a legacy archive.

| Option | Notes |
|---|---|
| `pypdf` text layer (built in) | Works for anything produced by tax software or Excel |
| Claude vision on page images | Send scanned pages as images to the extractor slot. Handles handwriting, stamps, rotated pages. Most accurate for 1040s and K-1s; cost is per page |
| Azure Document Intelligence | Excellent tables, prebuilt US tax form models (W-2, 1099, 1040) with field-level confidence |
| AWS Textract | Similar; natural on Bedrock deployments |
| Tesseract / OCRmyPDF | Free, on-prem, mediocre on forms |

Recommendation: text layer first, Claude vision as the fallback for the extractor slot, and a
prebuilt tax-form OCR service only if the pilot shows a large volume of scanned forms.

## Vector / document store

| Stage | Store |
|---|---|
| Pilot (this repo) | SQLite + numpy brute force. Zero ops |
| Single firm, production | Postgres + pgvector on the firm's VM or private cloud. One database for facts, documents, audit log and vectors |
| Multi-firm SaaS | Postgres per tenant (schema- or database-level), never a shared index |
| Very large archives | Qdrant or Weaviate self-hosted; only if pgvector latency becomes a problem |

## Application stack

- **Backend:** Python + FastAPI (this repo). Async, typed, small.
- **Front end:** the single-file UI is enough for a pilot. When you need roles, multi-firm admin,
  and a polished feel, move to Next.js or SvelteKit but keep the same REST API.
- **Auth:** Microsoft Entra ID via OIDC. Nearly every accounting firm is on Microsoft 365, and
  it gives you MFA, conditional access and offboarding for free.
- **Hosting per firm:** one small VM or container (2 vCPU / 8 GB) in the firm's cloud account or
  yours, disk encrypted, nightly encrypted backups, private network or VPN only.
- **Secrets:** cloud secret manager, never `.env` files in production.
- **Observability:** the built-in audit log plus structured logs; do not send prompts to a
  third-party LLM-observability SaaS without another DPA.

## Cost sketch (Claude API list prices, Sept 2026)

Assume a 300-client practice, 8 years of history, average 6 documents per client-year,
average 8k tokens per document.

- Extraction: 300 × 8 × 6 × 8k ≈ 115M input tokens with Sonnet 5 at $2/M ≈ $230 input plus
  ≈ $100 output; halve it with the Batch API. **One-time archive ingestion ≈ $200.**
- Embeddings: 115M tokens with Voyage 3.5 ≈ $7.
- Queries: a partner question with 8 retrieved chunks and a tool round ≈ 15k input / 1.5k output
  on Opus 5 ≈ $0.11. **1,000 questions a month ≈ $110**, less with prompt caching.

Model spend is not the cost driver of this business; onboarding effort and trust are.

## Keeping current

- Subscribe to the Claude API changelog and the Voyage release notes.
- Every quarter: add the new model to `models.yaml` as a new profile, run the evaluation question
  set against both profiles, compare answers and cost, then flip the default.
- Never delete an old profile until every firm has been migrated and re-embedded.
