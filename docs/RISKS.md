# Risks and mitigations

Ordered roughly by how badly they could hurt the business.

## 1. Confidentiality and legal exposure

| Risk | Detail | Mitigation |
|---|---|---|
| **IRC §7216 (US)** | A tax return preparer who discloses or uses tax return information other than to prepare the return can face criminal penalties. Sending return data to an AI vendor is a disclosure to a "contractor" and requires the firm to have proper safeguards and, in some situations, written consent | Get the firm's own counsel to sign off on the vendor arrangement; keep processing strictly for preparation/advisory purposes; sign DPAs with every vendor; prefer cloud routes (Bedrock/Foundry) that keep data inside the firm's own tenant |
| **GLBA Safeguards Rule / FTC** | CPA firms are "financial institutions" and must have a written information security plan (WISP) covering vendors | Give the firm a vendor-risk section for their WISP describing this system; document encryption, access control, and retention |
| **AICPA / state board confidentiality rules** | Client consent may be required before sharing confidential client information with third-party service providers | Add a one-paragraph disclosure to the firm's engagement letter template |
| **Vendor retains or trains on data** | Standard consumer AI terms allow this | Only use enterprise/API terms with zero data retention; verify in writing; never use consumer chat products for client data |
| **Cross-client leakage** | A query for one client surfacing another client's document | Retrieval is scoped by `client_id`; firm-wide search is an explicit choice; add per-user client permissions before multi-user rollout |
| **Data breach of the archive itself** | One database now holds the firm's most sensitive data in a very searchable form | Full-disk encryption, network isolation (VPN only), SSO with MFA, short-lived tokens, rate limiting, immutable audit log, encrypted off-site backups, quarterly access review |
| **Right to deletion / retention limits** | Firms have retention policies (often 7 years) and clients may request deletion | `DELETE /api/documents` and `/api/clients` remove originals, chunks and facts; add scheduled retention jobs |

## 2. Accuracy and professional liability

| Risk | Detail | Mitigation |
|---|---|---|
| **Hallucinated numbers** | The single fastest way to lose a CPA's trust | All figures come from extracted `facts` with `source_quote`, or from deterministic tools. The system prompt forbids un-cited numbers. Show citations in the UI |
| **Extraction errors** | Wrong sign, wrong year, "in thousands" not scaled, subtotal mistaken for total | Enum-constrained fact names; quotes back to the source line; reviewer sees the canonical JSON on upload; add a "verify facts" screen where staff tick-mark extracted figures for high-value clients |
| **Forecasts taken as advice** | Linear/CAGR projections are planning aids, not predictions | Tools return both methods and the history; prompt tells the model to state assumptions; UI labels projections as deterministic arithmetic |
| **Over-reliance by junior staff** | Answers that sound confident replace reading the file | Position the tool as "find and summarise", require the source to be opened for anything going into a deliverable; training in the pilot |
| **Model drift after a swap** | A newer model answers differently | Evaluation question set run before every profile change; keep old profile until validated |
| **Stale data** | Question answered from the prior year because this year's file was not uploaded | UI shows latest year per client; answers state the years on file |

## 3. Security of the prototype (must fix before real use)

- Single shared API token → replace with OIDC (Entra/Google) and per-user roles.
- No rate limiting or upload virus scanning → add both.
- Originals stored unencrypted on local disk → encrypted volume plus per-file encryption keys.
- No TLS termination in the app → run behind a reverse proxy with TLS, private network only.
- Prompt injection via uploaded documents (a PDF containing "ignore previous instructions") →
  documents are placed inside `<evidence>` tags and the system prompt names them as data; keep
  tool set read-only (no tool can send email, modify records or browse the web).
- SQLite is single-writer → fine for one office; move to Postgres for concurrency.
- Citation links open the original via `GET /api/documents/{id}/file?token=…` so a browser tab can
  fetch it. A long-lived token in a URL ends up in browser history and proxy logs → replace with
  short-lived signed URLs minted per click (or serve through the SSO session cookie).

## 4. Operational

| Risk | Mitigation |
|---|---|
| Scanned archives with no text layer | OCR step in onboarding; the parser flags these on upload |
| Bulk onboarding cost/time | Batch API for extraction; run overnight; start with the top 20% of clients by fee |
| Vendor outage during busy season | Second profile pointing at a different route (e.g. Bedrock) that can be activated from the UI in seconds; the archive itself still works for search with no LLM |
| Key person risk (you) | Everything is config and documented; the firm can run it without you, which is also the sales pitch for trust |

## 5. Business

| Risk | Mitigation |
|---|---|
| Incumbents (Thomson Reuters, Wolters Kluwer, Intuit, Karbon, Canopy) ship "AI search" in the DMS the firm already pays for | Compete on depth (forecasting, risk screens, cross-year analysis across tax + audit), vendor independence, and hands-on service; sell to firms that are unhappy with their DMS vendor's AI or have data spread across folders |
| Firms hesitant to send data anywhere | Offer the self-hosted-embeddings plus in-tenant-inference (Bedrock/Foundry) configuration; do the demo with the offline profile on their own machine |
| Long sales cycles, seasonal buyers | Sell in May–November; pilot during busy season only with a friendly firm |
| Scope creep into "do the return" | Stay in research/planning/review; that is where liability is manageable and value is obvious |

## Data-handling checklist to give a firm

1. Where is data stored? (their VM / their cloud account / your cloud account, region)
2. Which vendors see it, under what terms? (model vendor, embedding vendor, OCR vendor; DPAs attached)
3. Retention: originals, chunks, logs, backups, vendor side.
4. Who can log in and what can they see? Offboarding procedure.
5. Encryption at rest and in transit; key management.
6. Incident response: who is called, within what time.
7. How to get everything out (export) and how to delete everything.
