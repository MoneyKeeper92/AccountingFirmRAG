# Busy-season pilot plan for a small tax/audit practice

A concrete plan for testing this with a small practice (your dad's) between now and the end of the
2026 filing season, on a one-hour-per-week cadence.

## Goals

1. Prove the workflow "upload last year → ask questions → plan this year" saves time on real
   engagements.
2. Learn which questions staff actually ask. That defines the product.
3. Produce a reference story and metrics you can show the next firm.

## Ground rules

- Real client data only after the security steps in `docs/ONBOARDING_PLAYBOOK.md` Phase 0 are done.
  Until then, use the offline profile and synthetic data.
- The system is a research assistant. Nothing it produces goes into a deliverable without the
  source being opened.
- Keep a shared notes doc; every weekly session ends with three lines: what worked, what broke,
  what to change.

## Timeline

| When | Hour spent on | Outcome |
|---|---|---|
| Week 1 (now) | Install on a laptop or office VM with the offline profile; walk through sample data; agree pilot clients (5 business, 10 individual) | Staff have seen it; client list; security checklist started |
| Week 2 | Legal/security: DPAs, hosting route (recommend Microsoft Foundry or Claude API with ZDR, given most small firms are on Microsoft 365), WISP paragraph | Signed off, or a clear list of blockers |
| Week 3 | Switch to the real profile; ingest the 5 business clients (last 3 years of statements/returns/trial balances) | First real answers; note extraction misses |
| Week 4 | Ingest the 10 individual clients (last 2 years of returns plus preparer notes); tune fact vocabulary | Full pilot archive |
| Jan–Feb | Tax season: staff upload prior-year return when opening each engagement; ask "what changed, what to watch" | Question log grows; weekly fixes |
| Feb–Mar | Audit planning for the business clients: "riskiest areas", "expected figures", "what did we flag last year" | Compare with the partner's own planning memo |
| Weekly hour | 20 min review audit log; 20 min fix/tune; 20 min plan next week | Steady improvement |
| After April 15 | Retrospective; decide on productising; write the case study | Go/no-go |

## Questions to seed the evaluation set

Individual clients:
- What changed between the 2024 and 2025 returns for this client?
- Which clients had Schedule C income last year and did not make estimated payments?
- Did we note anything last year to follow up on this year?
- What was the effective tax rate and how does it compare to the prior year?

Business clients:
- Summarise the most recent financial statements and any emphasis-of-matter paragraphs.
- Which balances moved more than 20% year over year?
- Based on the last three years, what should we expect revenue, gross margin and net income to be?
- What covenants exist and were they met?
- What did the management letter say last year, and does this year's trial balance suggest it was fixed?

## Metrics to track

- Minutes to answer a planning question with the tool vs. by opening folders (time three staff on
  three questions each, before and after).
- Share of answers where the citation was correct on first read.
- Extraction accuracy on a spot check of 30 facts per document type.
- Number of "not in the archive" answers per week (onboarding gap indicator).
- Staff satisfaction, one question, weekly.

## What "success" looks like in April

- Staff open the tool before opening the client folder.
- A partner used the risk screen or the forecast in at least one real planning memo.
- Extraction accuracy above 95% on structured exports and above 90% on PDFs.
- A list of ten features the firm would pay for, ranked.
