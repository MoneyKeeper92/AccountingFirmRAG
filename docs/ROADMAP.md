# Roadmap

Sequenced from the research pack (`docs/RESEARCH_FINDINGS.md`) for 3–30 staff tax practices.
Principle from Prompt 4: harden the request-list loop and verify-before-use first, because
those are where this product is already ahead; connectors feed the archive; partner for the
things adjacent vendors do well.

## Top five from the feature backlog, and where they stand

| # | Feature | Pattern borrowed from | Status |
|---|---|---|---|
| 1 | Prior-year return → editable document request list with a human gate before send | TaxCaddy / SafeSend Gather proforma lists | **Built.** Rules read last year's facts, folder text and preparer notes; the preparer edits the email and marks it sent |
| 2 | Auto-classify uploads and match them to pending items | Liscio Speed Match | **Built.** Inbound attachments are filed through the pipeline, classified, and matched by form tokens; unmatched files are surfaced for a person |
| 3 | Accept / Reject / Edit on extracted figures and citations, written to the audit log | DataSnipper DocuMine trust flow | **Built.** Verify tab per client; rejected facts drop out of planning and answers, edited values replace them, undo restores; thumbs up/down on citations |
| 4 | Configurable reminders, email plus optional SMS, stop on complete | Karbon / TaxDome reminder cadences | **Built.** Per-list schedule (default 7, 14, 21 days), channel, client contact; due-reminder job; log-only when no SMTP/SMS is configured; stops at zero pending |
| 5 | Conditional organizer: yes/no answers open upload slots | TaxDome / Intuit Link organizers | **Built.** Question set per return type; yes adds or reopens items, no retires them; answers logged |

## Next

- **Connectors** (Prompt 3 order): Graph and folder are built; Dropbox, SmartVault, ShareFile,
  Karbon next. TaxDome export folder via the folder connector; partner API request on the list.
- **Client-facing organizer page.** Today the preparer records answers. A per-client magic
  link with only the questions and upload slots (no search) is about a day on the existing
  routes and belongs behind the firm's portal identity where one exists.
- **Reminder job scheduling.** `scripts/send_reminders.py` is cron-ready; add a settings page
  for firm-wide defaults and quiet hours.
- **Evaluation set.** Ten to twenty real questions per client type with expected facts and
  files, run before every model profile change.
- **Verify-before-use, second pass.** Side-by-side source view (PDF page next to the figure)
  and a "must be verified before it appears in an answer" firm setting for high-stakes facts.
- **Partner, don't build:** tax-software proforma lists (UltraTax / Lacerte organizers),
  planning decks (Holistiplan, TaxPlanIQ), e-signature and payments, client portal identity.

## Do not build

Full practice-management suite; e-sign and payment collection; bank "smart links";
tax-prep autopilot; public tax-law research (Blue J / Checkpoint territory); Excel snipping
tools; ambient meeting AI; a document-management-system replacement; anything that trains on
client data.

## Sequencing for the pilot season

1. Weeks 1–4: archive loaded via folder sync; request lists sent for every pilot client;
   staff use Verify on the entity clients.
2. Jan–Feb: reminders running daily; organizer answers captured on intake calls; question log
   feeds the evaluation set.
3. Feb–Apr: planning screens in entity reviews; weekly hour spent on rule and threshold tuning.
4. Post-season: case study, SOC 2 readiness controls confirmed, connector work for the next
   firm's storage system.
