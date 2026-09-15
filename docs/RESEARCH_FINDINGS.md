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

## 7. IRS transcripts (Prompt 8) and the OCR bake-off (Prompt 9)

**Transcripts:** the CPA path is the Transcript Delivery System with Form 2848 / 8821 on file,
not IVES (that is the lender path at $4 per 4506-C). The wage-and-income transcript can seed
"ask only for what is missing", with caveats: current-year data is often incomplete until late
March, identifiers are masked, and there is no state withholding. Canopy auto-pulls transcripts;
TaxCaddy Smart Links are bank links, not IRS. Product wedge: the IRS W&I transcript as an
independent check alongside portal uploads.
**Decision (built):** `app/ingest/transcript.py` parses W&I transcripts deterministically and
`POST /request-lists/{id}/reconcile-transcript` turns the generic list into one item per payer
the IRS knows about, retires the generic items, and marks items already satisfied by a received
document. The transcript is filed under the client but contributes no facts to the return
series. Caveats are shown in the UI.

**OCR:** structured W-2 / 1099 / 1040 pages → Azure Document Intelligence tax prebuilts (about
$10 per 1,000 pages); K-1s and messy layouts → frontier-model vision or custom Azure (about $30
per 1,000 pages); born-digital PDFs → text layer first. Google's legacy 1099 path sunsets
2026-06-30. Vendor accuracy SLAs are thin; treat third-party benchmarks as directional.
**Decision (built):** an optional `ocr` slot in `models.yaml` with `azure_di` and
`anthropic_vision` providers, used only when a PDF has no usable text layer; the Verify tab is
the accuracy check. Spot-check on the firm's own scans during onboarding.

## 8. Compliance and insurance (Prompt 10)

Generative AI over identifiable tax return information is generally a §7216 disclosure; do not
lean on the domestic auxiliary-services exception when the model summarises or reasons.
Conservative path: named-vendor written consent (Rev. Proc. 2013-14 mandatory language for
1040s) plus a DPA for AICPA ET 1.700.040; prefer US-only inference. Carriers (CAMICO, AICPA MIP,
CNA) show no public blanket AI exclusion; they expect governance, human review and vendor
diligence. Cyber questionnaires ask for MFA, encryption, SOC 2 (market expectation), incident
SLA, Publication 4557 / Safeguards §314.4(f) alignment.
**Decision (built / written):** `inference_geo: us` pinned in production profiles;
`docs/COMPLIANCE_KIT.md` with the engagement-letter paragraph, consent approach, sub-processor
list, data-handling sheet, questionnaire answers and governance statement, all marked as drafts
for counsel.

## 9. Willingness to pay (Prompt 11) and go-to-market (Prompt 12)

Anchors: partner median about $275/hour, associate about $127; document chasing 1 to 3.5
hours per return. Adjacent prices: SmartRequestAI $12.50 per return, Canopy $74–149 per user
plus about $34 per client for tax AI, SafeSend often $13–17 per return. Heuristic pitch figure
for an 8-person, 800-return firm: on the order of $15k a year of value at about 7x ROI. Treat as
a model, not survey fact.
GTM priority for 3–30 staff: state society affinity programmes → Scaling New Heights and
Digital CPA → CPA-focused MSPs (Rightworks, Cetrom, Boomer) → AICPA ENGAGE → tax API partners.
Dates: ENGAGE June 8–11 2026; Scaling New Heights June 14–17 2026; Digital CPA December 6–9
2026. Affinity example: WICPA $3k minimum ad spend. Intuit partner tiers carry fees; Microsoft
marketplace about 3%; Thomson Reuters and CCH programmes often closed or partner-gated.
**Decision:** price ladder and value model updated in `docs/BUSINESS_MODEL.md`; the season
after the pilot targets the June events with the case study in hand.

## 10. Monitoring (Prompt 13)

The Monday 09:00 watch now also catches pricing, zero-retention, model and OCR benchmark
changes, with a deeper quarterly pass on the first Monday of January, April, July and October.

## 11. Follow-ups (Prompt 14 A–K)

**A. MeF element names.** Public MeF stylesheets for TY2023–2025 cover the core lines; full SOR
XSDs need the e-Services Software Developer role. Core `*Amt` tags are mostly stable. Notable:
TY2025 adds `TotalAdditionalDeductionsAmt`; 1120-S uses `OfficersCompensationAmt`,
`RetainedEarningEOYAmt` (singular) and AAA `BalanceEOYAccumAdjAcctAmt`; K-1 ordinary income is
`OrdinaryIncomeLossAmt`. View XML can be post-acknowledgement if the local XML was kept; no batch
export or standard filename. **Built:** alias table updated, K-1 per-owner parsing, Schedule 1-A
fact `additional_deductions`.

**B. Transcript layouts.** W&I from TDS is a masked PDF-style product with repeating form
sections; no IRS XML/CSV. Canopy stores the IRS PDFs; THS produces analysis reports. Form 8821
takes about 8 business days. 1120 / 1065 / 941 share the TDS/CAF path, but W&I is individual
(IMF) only. **Decision:** parser stays text-based over the PDF text layer; file 8821s in the
autumn; entity clients get account transcripts, not W&I.

**C. Azure Document Intelligence.** v4.0 model IDs for W-2 / W-4, 1095, 1098, the 1099 variants
and 1040 with schedules (field names from the `2024-11-30-ga` schemas). Multi-form PDFs split
logically via `documents[]`. Prebuilt about $10 per 1,000 pages; Read $1.50 falling to $0.60.
**DI retains data about 24 hours**, unlike the no-train story for Azure OpenAI. **Decision:**
W-2 / 1099 pages → DI prebuilt; K-1 → custom model or layout plus LLM; DI listed as a
sub-processor with its retention window.

**D. Connectors.** Dropbox (team OAuth, list_folder / download, webhooks with cursor),
SmartVault (developer signup, OAuth tokens, nodes / files, poll only), ShareFile (OAuth by
subdomain, Items / Children / Download, webhooks), Graph (`Sites.Selected` plus site permission
grant plus admin consent; Business Standard is enough for one library). **Built:**
`docs/GRAPH_SETUP.md` for firm IT.

**E. Mail and SMS.** SMTP AUTH off by default for tenants created after January 2020; Basic Auth
for SMTP disable-by-default after December 2026. Prefer Graph `sendMail` on one shared mailbox
under an Exchange application access policy, not tenant-wide Mail.Send; Google: Gmail API with
domain-wide delegation. TaxDome has SMS but no automated reminders; Liscio does two-way SMS.
**Built:** `GraphMailNotifier`, preferred over SMTP when `GRAPH_MAIL_FROM` is set.

**F. Organizer identity.** ShareFile and SmartVault are link-only (SmartVault forbids iframes);
Liscio uses ~15-minute single-use magic links plus SSO; TaxDome uses password plus email OTP;
SafeSend uses email link plus partial SSN or access code. **Built:** single-use magic link with a
15-minute open window and a bounded working session; IP recorded, not enforced; the page shows
only the questions and upload slots.

**G. Consent.** Rev. Proc. 2013-14 §5.04(1)(a–d) blocks are quoted verbatim in the research
file; never paraphrase them in the kit. E-signature is acceptable (PIN of 5+ digits, typed
name, or 5+ unique characters). Default duration one year if unspecified, no federal maximum.
1040 disclosures need named recipients (generic classes only for non-1040). Watch CA BPC
§17530.5, NY 8 NYCRR §29.10(c), MA 252 CMR 3.03. **Written:** compliance kit updated.

**H. State withholding.** IRS transcripts are federal only. Preparer portals: CA MyFTB, NY
TR-2000, MA MassTaxConnect, plus IL, WI, IN, PA, NJ and others. UltraTax / Lacerte View XML is
per e-file package: state XML exists when that state e-file exists. **Decision:** withholding
screen is labelled federal; state portals are a playbook item per firm.

**I. Evaluation datasets.** NIST SD2 (free), Kaggle synthetic W-2 (CC0), Symage coherent 1040
(gated), purchasable SymageDocs sets; no solid public K-1 / 1099 corpus. **Built:**
`docs/EVALUATION.md` and `scripts/run_eval.py` with a seed question set.

**J. Archive composition and retention.** Scan-to-digital timeline proxies from CPAFMA and JoA
(2003–2023): older years are scan-heavier, budget OCR accordingly. Retention: IRC §6107 three
years; many state boards five to seven (CA and WA 7, MN 6, AL / AR / MI / TN / TX / NH 5; FL FAQ
3). **Decision:** deletion policy = the stricter of federal and the state of practice, set per
firm in onboarding.

**K. Microsoft 365 baseline.** Business Standard: Entra Free, Basic Mobility only, EOP.
Premium: Entra P1, Intune P1, Defender for Business, Defender for Office P1, DLP. Rightworks
often deploys E3 or Apps plus MSP layers, not always Premium; Boomer is consulting, not a
deployer. **Decision:** do not claim SSO or MDM as defaults for Standard shops; the compliance
kit's questionnaire answers now say which controls depend on the firm's licence.

## Still open

- Full SOR XSDs (Software Developer role) to confirm the element set beyond the core lines.
- TaxDome private-beta API terms once available.
- A survey-based check on the willingness-to-pay model before pricing is published.

- Weekly landscape monitor is running (Monday 09:00); it reports only material changes.
