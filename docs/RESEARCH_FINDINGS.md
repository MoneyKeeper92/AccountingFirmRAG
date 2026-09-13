# Research findings and the decisions they drove

Results from the research agent runs (Prompts 1, 3, 5 and 6 in `docs/RESEARCH_BOT_PROMPTS.md`),
as reported on 2026-09-13. Full write-ups live outside this repo:
`prompt1_competitive_landscape.md`, `prompt3_document_storage.md`,
`prompt5_zdr_and_accounts.md`, `prompt6_soc2.md`. Prompt 4 (feature backlog) is still running.
Figures below are the agent's; verify the cited sources before quoting them to a firm.

## 1. Competitive landscape

**Who actually answers "client X, last three years, what looked risky?" against the firm's own
files:** Fieldguide, Basis, Caseware AiDA, CoCounsel (with workspace uploads), DataSnipper
DocuMine, TaxGPT Client Intelligence, and Microsoft 365 Copilot where the file permissions
allow it. Not that: Blue J and Checkpoint research alone (public corpus); Karbon Kai and Canopy
Coworker (practice-operations Q&A, not multi-year return archives).

**Price reality for 3 to 25 staff firms:** practice-management AI is bundled at roughly $59 to
$149 per user per month; Copilot about $30 per user per month; DataSnipper starts around
$3.8k to $10.5k a year; Cranston about $30 per book and $40 per return; Fieldguide, Basis and
Black Ore are quote-only enterprise.

**White space:** an affordable automatic index of the legacy archive (GoFileRoom, SmartVault,
file shares) for small US CPA firms is still largely missing. True zero data retention is rarer
than "we don't train on your data", and IRC §7216 is almost never named on product pages.

**Decisions**
- Positioning stays "index the archive you already have, privately, with numbers that trace to
  the form and line", aimed at 3 to 30 staff firms. Name §7216 and zero data retention
  explicitly on the product page and in the firm-facing data-handling sheet.
- Price the platform per firm, not per user, and below the bundled practice-management AI tiers
  so it is an add-on rather than a replacement: see `docs/BUSINESS_MODEL.md`.

## 2. Where documents live and how to get them out

**US adoption, mid and large firms (CPAFMA 2026):** CCH Axcess Document 29%, GoFileRoom 16%,
Windows file shares or none about 13%; portals: SafeSend 47%, ShareFile 25%.
**Small-firm skew (Readers' Choice 2025):** Drake DMS 39%, TaxDome 28%, plus OneDrive /
SharePoint, Dropbox and SmartVault.

**API status today:** ready: Microsoft Graph, Google Drive, Box, Dropbox, Egnyte, ShareFile,
SmartVault, Karbon, QuickBooks Online, Xero. Partner-gated: CCH Axcess, GoFileRoom, SafeSend.
Watched folder or export only: FileCabinet CS, TaxDome without a partner agreement, most audit
engagement binders.

**Connector order for 3 to 30 staff firms:** 1. Microsoft Graph (SharePoint / OneDrive),
2. NAS / Windows watched folder, 3. Dropbox, 4. SmartVault or the Drake filesystem,
5. ShareFile or Karbon.

**Decisions (built)**
- `app/connectors/`: a connector interface, a **folder connector** (covers the NAS, mapped
  drives, OneDrive-synced folders, Drake DMS and FileCabinet CS storage) and a **Microsoft
  Graph connector** using the drive delta API. Client, year and engagement are inferred from
  the path; every file is stored in pointer mode with a `source_uri` so citations open the file
  where it lives. `POST /api/admin/sync/folder` and `scripts/sync_folder.py --watch` run it.
- Dropbox, SmartVault and ShareFile are next and follow the same interface; each is a listing
  call plus a download call.
- TaxDome's 28% share with no public bulk API is a real gap: use its export folder through the
  folder connector, and put a partner-API request on the backlog.

## 3. Zero data retention and account structure

- Zero retention itself is usually a $0 list uplift. What costs money: model tier, OCR packs,
  and data residency (about +10%).
- Steady state for the assumed firm (about 300 clients, 8 years, 1,000 questions a month):
  roughly $180 to $230 per firm per month on a Sonnet-class ZDR stack (Anthropic direct or
  Bedrock with no retention, Voyage with the retention opt-out, Azure Document Intelligence or
  Textract for OCR), including about $150 of shared infrastructure.
- Account structure: start with **A**, one vendor account you own with a workspace per firm
  and a DPA with each firm, for 3 to 30 staff. Larger and PCAOB-adjacent firms will push toward
  **C**, in-tenant Bedrock or Azure. §7216 still requires firm-side notices under A; legal
  review is required.

**Decisions**
- `models.yaml` default production profile stays Anthropic direct with Voyage; the Bedrock route
  is the documented alternative for structure C.
- The per-firm cost line in `docs/BUSINESS_MODEL.md` uses the $180 to $230 figure. Note the
  $150 shared-infrastructure component is per firm only at one firm; it amortises quickly.
- The answer slot stays on Opus-class for quality; the extractor slot is Sonnet-class. The
  agent's cost figure assumed Sonnet-class throughout, so budget the answer slot separately.

## 4. SOC 2

- Not legally required by the FTC Safeguards Rule (firms need evidence of safeguards, not a
  specific report), but it is the sales gate from mid-market up and effectively mandatory at
  75+ staff or PCAOB-adjacent firms.
- Recommended path: Type I around month 6, Type II around month 18; about $45k to $85k cash
  over 24 months. Start readiness when there are three or more mid-market opportunities or
  roughly $150k to $250k ARR.

**Decisions**
- Run the controls from day one (SSO, MDM, logging, policies, vendor list) so the audit is
  cheap later; do not buy the audit before the trigger. Interim evidence for small firms: the
  data-handling sheet, a penetration-test letter, cyber insurance, in-tenant deployment option.

## 5. Feature backlog (Prompt 4)

**Build next, top five:** (1) prior-year → editable request list with a human gate before send;
(2) auto-classify uploads and match to pending items (Liscio Speed Match pattern); (3) citation
and figure Accept / Reject / Edit with audit trail (DocuMine-style trust); (4) configurable
reminders, email plus optional SMS, stopping on completion; (5) conditional organizer, yes/no
answers opening upload slots.

**Do not build:** full practice-management suite, e-sign and payments, bank smart links,
tax-prep autopilot, public-law research, Excel snipper, ambient meeting AI, DMS replacement,
training on client data.

**Sequencing for 3–30 staff:** harden the request-list loop and verify-before-use first; partner
for tax-software proforma lists and planning decks (Holistiplan, TaxPlanIQ); Graph and NAS
connectors feed the archive.

**Decisions (built):** all five are in the prototype; see `docs/ROADMAP.md` for status and
what follows. Items 1 and 2 already existed; 3, 4 and 5 were added on the strength of this
report: a Verify tab with accept / reject / edit / undo on every extracted figure and thumbs
up/down on citations, a per-list reminder schedule and channel with a cron-ready job that stops
at zero pending, and a per-return-type organizer whose answers add, reopen or retire items.

## 6. Structured returns from the tax software (Prompt 7) and two side briefs

**MeF / e-file XML:** no documented batch MeF XML archive API from UltraTax, Lacerte, Drake or
CCH Axcess. UltraTax (Utilities → Electronic Filing Status → View XML) and Lacerte (E-file →
E-file Support Tools → View E-file) let a preparer view and save the XML per return. Drake
exports CSV/TXT e-file database and transfer packs, not MeF. CCH TaxTransfer / OIK is
proprietary worksheet XML under licence. ProConnect has admin CSV only. IRS schemas come via
e-Services SOR (Software Developer role); public XSL stylesheets on IRS.gov.

**Decision (built):** dual ingest. PDF plus OCR stays the default; an `.xml` file that is an MeF
return is parsed deterministically in `app/ingest/mef.py` (return type, forms present, filing
status, facts by schema element, SSN masked in the indexed text, unmapped amounts reported).
No model call, no OCR. Firms on UltraTax or Lacerte can save the XML into the client folder
and the folder connector picks it up. The element alias table must be re-checked against each
tax year's schema package.

**TaxDome:** no public REST bulk list/download; Zapier is CRM-only; the spring 2026 API is a
sales-gated private beta; the "partner program" is referral payouts, not technical access.
Practical path today: Drive copy or UI zip export into a watched folder.
**Decision:** target Microsoft 365 / SharePoint and SmartVault firms first; TaxDome shops via
the export folder until the beta opens.

**Form 1040 line map TY2023–2025:** 2023→2024 stable; TY2025 renumbers capital gain to 7a, AGI
to 11a/11b, deduction to 12e, QBI to 13a, adds 13b (Schedule 1-A), EIC to 27a, and line 30
becomes the refundable adoption credit. **Decision:** concept-based fact names unchanged; the
renumbering is in the extraction instructions and `docs/LINE_MAP_1040.md`.

## Still open

- IRS transcripts (TDS / wage-and-income seeding) and the OCR bake-off (Azure vs Textract vs vision).
- Then compliance and insurance, willingness to pay, go-to-market channels.

- Weekly landscape monitor is running (Monday 09:00); it reports only material changes.
