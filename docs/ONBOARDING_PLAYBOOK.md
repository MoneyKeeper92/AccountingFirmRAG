# Onboarding playbook

How to take a firm from "folders full of PDFs" to a searchable archive, and how to keep it current
with as little staff effort as possible.

## Phase 0 – Before any data moves (week 0)

1. **Security and legal sign-off.** Walk the managing partner through `docs/RISKS.md` and the
   data-handling checklist. Get the vendor DPAs signed. Add the engagement-letter disclosure.
2. **Decide the hosting route.** Default: a VM in the firm's own Microsoft/AWS/Google account,
   inference through that cloud's Claude offering, embeddings self-hosted or via Voyage under ZDR.
3. **Install with the offline profile** and demo with the sample data on their machine. No
   client data involved. This is where staff learn the UI.
4. **Agree the client list for the pilot.** Start with 10–25 clients: the entity returns
   (1120-S, 1065, 1120) and the top individual returns by fee. Don't try to ingest the whole archive.

## Phase 1 – Inventory and triage (week 1)

For each pilot client, list what exists and where. A simple sheet:

| Client | Year | Engagement | Document | Format | Location | Text layer? |
|---|---|---|---|---|---|---|
| ABC Company | 2024 | Audit | Financial statements (final) | PDF | S:\Clients\ABC\2024\Audit\Final | yes |
| ABC Company | 2024 | Audit | Trial balance | XLSX | same | n/a |
| John Doe | 2024 | Tax | Form 1040 (as filed) | PDF from UltraTax | S:\Clients\Doe\2024 | yes |

Rules of thumb for what to ingest first, in order of value per hour:

1. **Final deliverables**: filed returns (1040, 1065, 1120-S, 1120 with all schedules), K-1s
   issued, and the preparer's notes. These have the numbers and the conclusions.
2. **Structured exports**: trial balances, general ledgers, fixed-asset registers as CSV/XLSX.
   Best source of facts and cheapest to extract.
3. **Planning memos, review notes and prior-year organizers**: high value for "what did we worry
   about last year".
4. **Source documents** (bank statements, 1099s, W-2s): usually skip in the pilot; large volume,
   low query value. Add later, selectively.
5. **Tax workpapers with tick marks**: last. Often scanned, often noisy.

Skip entirely: drafts superseded by finals, duplicate copies, email dumps.

## Where firms keep documents, and how we get them out

A starting map based on what small and mid-size practices typically run. Treat it as a hypothesis
to validate with Prompt 3 in `docs/RESEARCH_BOT_PROMPTS.md` and with each firm's own inventory.

| Where the documents live | Typical in | Bulk backfill | Keeping it current | Metadata you get for free |
|---|---|---|---|---|
| Windows file server / NAS, folder per client per year | Most firms under ~30 staff, often alongside everything below | Walk the share with a small on-prem agent; infer client and year from the path | Watched-folder agent posts new finals to the API | Path (client, year, engagement), modified date |
| SharePoint / OneDrive (Microsoft 365) | Firms that moved the file server to the cloud; growing fast | Microsoft Graph API: list drive items, download | Graph delta queries or change notifications | Path, author, modified, custom columns if the firm uses them |
| Google Drive / Dropbox / Box / Egnyte | Smaller and newer firms | Vendor API | Change events / webhooks | Path, owner, modified |
| Accounting DMS (CCH Axcess Document, GoFileRoom, FileCabinet CS, Onvio, Doc.It, SuiteFiles, SmartVault) | Firms 10–200 staff on a Wolters Kluwer or Thomson Reuters stack | Vendor API where offered (varies; some need partner-program access), otherwise bulk export tooling | API polling or export schedules | Best metadata: client ID, year, document type, final/draft flag |
| Practice-management suites with built-in docs (Karbon, Canopy, TaxDome, Financial Cents) | Cloud-first small firms | Vendor API (Karbon and Canopy publish APIs; check the rest) | Webhooks or polling | Client, job/engagement, year |
| Client portals used as storage (ShareFile, SmartVault, Liscio, SafeSend, TaxCaddy) | Everywhere; often the only place client-provided source docs exist | Portal API or sync client | Portal events | Client, upload date |
| Tax software binders (UltraTax, Lacerte, ProSeries, Drake, CCH Axcess Tax) | Every tax practice | Batch print/export the filed return to text-layer PDF; export client data reports where available | Add "export as-filed PDF to the client folder" to the filing checklist | Client, year, form set |
| Audit engagement binders (CaseWare, ProSystem fx Engagement, AdvanceFlow) | Audit practices | Publish final statements and adjusted trial balance out of the binder (PDF + XLSX) | Same, at sign-off | Client, period, account mapping |
| Email attachments | Everywhere, and never filed | Microsoft Graph / Gmail API search on client domains; low priority for the pilot | Mailbox rule that files into the client folder | Sender, date |
| Paper and scan-only PDFs | Legacy years in almost every firm | OCR first (Acrobat, OCRmyPDF, cloud OCR), then treat as PDF | Scan-to-folder with OCR enabled on the scanner | Little; rely on filename and extraction |

Research result (Prompt 3, Sept 2026): among mid and large US firms CCH Axcess Document (29%)
and GoFileRoom (16%) lead, with SafeSend (47%) and ShareFile (25%) as portals; among small firms
Drake DMS (39%) and TaxDome (28%) lead, alongside OneDrive/SharePoint, Dropbox and SmartVault.
API-ready today: Microsoft Graph, Google Drive, Box, Dropbox, Egnyte, ShareFile, SmartVault,
Karbon, QuickBooks Online, Xero. Partner-gated: CCH Axcess, GoFileRoom, SafeSend. Export or
watched folder only: FileCabinet CS, TaxDome without a partner agreement, most engagement binders.

Connector order for 3–30 staff firms, and what exists in this repo:

1. **Microsoft Graph (SharePoint / OneDrive)**: built, `app/connectors/graph.py`, drive delta API.
2. **Watched folder on the NAS / file server**: built, `app/connectors/folder.py`. Also covers
   Drake DMS and FileCabinet CS (both store files on the filesystem) and OneDrive-synced folders.
   Run `python scripts/sync_folder.py "S:\Clients" --watch 300` on a machine that sees the share.
3. Dropbox, 4. SmartVault (or the Drake filesystem via 2), 5. ShareFile or Karbon: same
   interface, listing call plus download call each. TaxDome: use its export folder through 2.

Every synced file is stored in pointer mode with the share path or SharePoint URL as its source,
so citations open the file where it already lives and nothing is duplicated.

### Copies or pointers?

The system does not need to duplicate the archive. Two modes, set per deployment:

- **Copy mode** (`FIRM_RAG_KEEP_ORIGINALS=true`, default): the original is stored next to the
  index. Simplest, and needed when the app cannot reach the source (files emailed in, client
  uploads, one-off drops).
- **Pointer mode** (`FIRM_RAG_KEEP_ORIGINALS=false`): only the index, the extracted facts and a
  `source_uri` (UNC path, SharePoint or DMS link) are stored. Citations open the file where it
  already lives. No second copy to secure, back up or delete. This is the right default for a
  firm with a file share or DMS, and it is what a connector should use.

Storage is small either way. Tax returns and statements are mostly 0.5–3 MB of PDF; a 300-client
practice with eight years and six documents per client-year is roughly 20–25 GB of originals and
about 1 GB of index and vectors. On any cloud object store that is a few dollars a month. The cost
that matters is governance, not gigabytes, which is the argument for pointer mode.

## Phase 2 – Format guidance ("best format")

The system accepts PDF, CSV, XLSX, JSON and plain text. What to prefer:

| If you have… | Do this |
|---|---|
| Tax software (UltraTax, Lacerte, ProSeries, Drake, CCH Axcess) | Export the filed return as PDF **with text** (not "print to image"). Most also export a client summary or "tax return data" report; export that too, it extracts cleanly |
| QuickBooks / Xero / Sage | Export Trial Balance, P&L and Balance Sheet by year as **XLSX or CSV**, not PDF |
| Audit software (CaseWare, Engagement, AdvanceFlow) | Export the final statements PDF and the adjusted trial balance as XLSX |
| Excel workpapers | Upload the XLSX directly; each sheet is indexed separately |
| Scanned paper | Run OCR first (Adobe Acrobat "Recognize Text", OCRmyPDF, or the cloud OCR chosen in Phase 0). The uploader flags scans that have no text layer |
| Existing structured data | Send JSON that matches the canonical record; see `docs/ARCHITECTURE.md`. The sample 1040 summaries in `sample_data/john_doe/` show a good shape |

Naming convention that helps the extractor and the humans:

```
<ClientName>_<Year>_<Engagement>_<DocType>.<ext>
ABC_Company_2025_Audit_Financial_Statements.pdf
Doe_John_2025_Tax_1040_as_filed.pdf
```

Year in the filename is used as a fallback when the document itself is ambiguous.

## Phase 3 – Bulk load (weeks 1–2)

- Create the pilot clients (name, entity type, industry, fiscal year end). Industry matters:
  the risk thresholds will be tuned per industry later.
- Upload per client per year. The upload form takes `engagement` and `tax_year` hints; use them,
  they are passed to the extractor.
- Review the canonical JSON for the first two or three documents of each type with a senior.
  If the extractor consistently misses something (a fund accounting line, a state form), extend
  `FACT_NAMES` and the extraction instructions, then re-upload.
- Use the **Risk & forecast** tab as an instant sanity check: if revenue shows as 5,610 instead of
  5,610,000, the statement was "in thousands" and the extraction prompt needs the hint.

For large archives, script it: `scripts/seed_demo.py` shows the loop; point it at the inventory
sheet. Run overnight. Use the Batch API for extraction when a real model is configured.

## Phase 4 – Keeping it current: the "start of engagement" habit

The workflow you described is the right one and should become the firm's standard:

> Before starting John's 2026 return, upload John's 2025 return (and anything new: the 2026
> organizer, K-1s that arrived) to his client record.

Three ways to make that happen, in increasing order of automation:

1. **Manual, in the UI.** Staff drag the prior-year return and this year's source documents in
   when they open the engagement. Takes a minute. Sufficient for the pilot.
2. **Watched folder.** A small agent on the file server watches `S:\Clients\<Client>\<Year>\`
   and posts new finals to `POST /api/documents` with the client and year inferred from the
   path. Zero staff effort once folder discipline exists.
3. **DMS / practice-management integration.** Pull from SharePoint, Karbon, Canopy, CCH
   Document, or ShareFile via their APIs when a document is marked "final". Do this once a firm
   is paying.

### The request list: turning last year's return into this year's to-do list

Once last year's return is in the folder, the **Checklist** tab drafts the document request in
one click: every item says why it is being asked for, grouped income / business / deductions /
credits / payments / follow-ups / admin. The preparer edits the email, sends it from their own
mailbox (copy, or "open in email app"), and marks the list sent. As documents arrive, staff drop
the whole reply on the list: attachments are filed into the client's folder, matched to items,
and the "items pending" count updates. Anything unrecognised is filed and flagged for a person
to assign. Reopen, add or mark items not applicable at any time.

Firms using a portal keep using it: point the portal's upload webhook at the inbound route and
the matching happens without anyone touching the files.

### Client self-upload

For clients uploading their own documents (organizers, bank statements, 1099s), do **not** give
them access to this UI. Instead:

- Use the firm's existing client portal (ShareFile, SmartVault, TaxDome, Liscio, SafeSend).
  Clients already trust it and it already handles identity.
- Add a tiny bridge: when a client uploads to the portal, the file lands in the client's folder,
  and the watched-folder agent (option 2 above) ingests it with `engagement=tax`,
  `tax_year=current`.
- If a firm has no portal, a minimal upload-only page with a per-client magic link is about a
  day's work on top of this API: create `POST /api/intake/<token>` that maps the token to a
  `client_id`, accepts files, and nothing else. Never expose search to clients.

## Phase 5 – Quality loop (ongoing, the weekly hour)

- Review the audit log: what did staff ask, what did the model cite, where did it say "not in the
  archive"? Those gaps are your onboarding backlog.
- Collect five to ten real questions per week into the evaluation set with the expected answer.
- Tune: risk thresholds per industry, fact vocabulary, chunk size, top-k, system prompt wording.
- Once a quarter: trial a newer model profile against the evaluation set; switch if better.

## Onboarding checklist (copy into the engagement)

- [ ] DPAs signed; hosting route chosen; WISP updated; engagement letter disclosure added
- [ ] VM provisioned, disk encrypted, VPN/SSO in place, backups tested
- [ ] Offline demo done with staff; access tokens issued
- [ ] Pilot client list agreed; inventory sheet complete
- [ ] OCR route chosen for scanned files
- [ ] Bulk load done; canonical JSON spot-checked by a senior
- [ ] "Upload prior year at engagement start" written into the firm's tax and audit checklists
- [ ] Watched-folder agent or portal bridge live (post-pilot)
- [ ] Evaluation question set started; weekly review scheduled
