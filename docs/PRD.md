# Firm Archive Assistant — prototype PRD (one page)

**Product.** A private assistant for small tax practices (3–30 staff) that indexes the firm's
own client archive (1040, 1065, 1120-S, 1120 returns, K-1s, source documents, books, notes),
answers plain-English questions with citations to the form and line, runs tax-planning screens
and projections from extracted figures, and runs the tax-season document request loop end to
end. Delivered with a weekly hour of hands-on refinement.

**Users.** Preparers and reviewing partners (primary); admin staff who run the request loop;
clients only through the firm's portal or email (never the search UI).

**Problem.** Partner and senior time is spent opening folders to re-learn last year before
planning or preparing this year; chasing client documents is manual; extracted numbers from AI
tools are not trusted without a way to check them.

**Jobs the prototype does today**
1. Ingest: upload, folder sync (NAS / Drake DMS / OneDrive-synced), SharePoint via Graph.
   Each file → return type, forms present, tax year, facts with source line, flags. Pointer or
   copy storage. Duplicate detection.
2. Ask: client-scoped retrieval; deterministic tools for numbers; citations open the source at
   the cited page; thumbs up/down on citations to the audit log.
3. Plan: estimated-payment safe harbour, S-corp candidates, reasonable compensation,
   distributions vs basis, accumulated earnings, itemize vs standard, year-over-year swings;
   trend and CAGR projections.
4. Request loop: prior-year → request list with reasons → edited email → mark sent →
   organizer yes/no opens or retires items → inbound attachments filed and matched → reminders
   on a schedule until nothing is pending → items-pending view.
5. Verify: accept / reject / edit every extracted figure; rejected facts leave the planning
   and answer paths; all decisions logged with who and when.
6. Operate: swappable model profiles by config, re-embed on change, audit log of every upload,
   query, file open, verification, reminder and sync.

**Non-goals (from research).** Practice-management suite, e-sign/payments, tax-prep autopilot,
public tax-law research, DMS replacement, training on client data.

**Privacy posture.** One vendor account with per-firm workspaces to start; zero-retention model
and embedding vendors only; in-tenant deployment (Bedrock / Foundry) for firms that require it;
§7216 disclosure paragraph and data-handling sheet supplied to each firm; SOC 2 Type I at the
mid-market trigger.

**Success metrics for the pilot season.** Minutes to answer a planning question before vs
after; share of citations judged correct on first read; extraction accuracy on a 30-fact spot
check per document type (target >95% structured, >90% PDF); request-list completion time vs
last season; staff open the tool before the folder.

**Open risks.** Scanned archives need OCR; TaxDome has no public bulk API; reminder delivery
needs the firm's SMTP or portal; single shared token must become SSO before multi-user use.

**Milestones.** Pilot install (offline profile) → security sign-off → real profile and archive
load → request lists sent at engagement start → verify and planning in reviews → April
retrospective and case study.
