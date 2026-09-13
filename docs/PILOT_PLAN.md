# Busy-season pilot plan for a small tax practice

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
| Week 1 (now) | Install on a laptop or office VM with the offline profile; walk through sample data; agree pilot clients (10 individual 1040s, 3 S corps, 1 partnership, 1 C corp) | Staff have seen it; client list; security checklist started |
| Week 2 | Legal/security: DPAs, hosting route (recommend Microsoft Foundry or Claude API with ZDR, given most small firms are on Microsoft 365), WISP paragraph | Signed off, or a clear list of blockers |
| Week 3 | Switch to the real profile; ingest the 5 entity clients (last 3 years of 1120-S / 1065 / 1120 returns, K-1s, trial balances) | First real answers; note extraction misses |
| Week 4 | Ingest the 10 individual clients (last 2 years of returns plus preparer notes); tune fact vocabulary | Full pilot archive |
| Jan–Feb | Tax season: staff upload prior-year return when opening each engagement; ask "what changed, what to watch" | Question log grows; weekly fixes |
| Feb–Mar | Entity returns: "what should we watch", "reasonable compensation", "distributions vs basis", "what did we flag last year"; request lists sent to every client at engagement start | Compare with the partner's own review notes |
| Weekly hour | 20 min review audit log; 20 min fix/tune; 20 min plan next week | Steady improvement |
| After April 15 | Retrospective; decide on productising; write the case study | Go/no-go |

## Questions to seed the evaluation set

Individual clients:
- What changed between the 2024 and 2025 returns for this client?
- Which clients had Schedule C income last year and did not make estimated payments?
- Did we note anything last year to follow up on this year?
- What was the effective tax rate and how does it compare to the prior year?

Entity clients:
- Summarise last year's 1120-S / 1065 / 1120 and the schedules it included.
- Which lines moved more than 20% year over year?
- Based on the last three years, what should we expect gross receipts and ordinary income to be?
- Is officer compensation defensible against distributions? Do distributions exceed AAA or basis?
- Were owner or corporate estimates sufficient, and what should this year's instalments be?
- What did we note to follow up on last year, and is it in this year's folder yet?

## Metrics to track

- Minutes to answer a planning question with the tool vs. by opening folders (time three staff on
  three questions each, before and after).
- Share of answers where the citation was correct on first read.
- Extraction accuracy on a spot check of 30 facts per document type.
- Number of "not in the archive" answers per week (onboarding gap indicator).
- Staff satisfaction, one question, weekly.

## What "success" looks like in April

- Staff open the tool before opening the client folder.
- A partner used the planning screen or the forecast in at least one real client conversation.
- Extraction accuracy above 95% on structured exports and above 90% on PDFs.
- A list of ten features the firm would pay for, ranked.
