# 15 — Private-beta handoff (17 Nov 2026)

This is the current source of truth for other people and AIs working on Tesón.
Read this before changing the app, question bank, database, or launch copy.

## Where this lives

- Repository: `MoneyKeeper92/AccountingFirmRAG`
- Branch: `claude/oposiciones-platform-plan-z1bf01`
- Product folder: `oposiciones/`
- The repository default branch is a different project. Work only on this branch and in this folder.

## Current decision

The release is a **private beta**, not a public launch and not the full product described in documents 01–12.

Current product:

- 82 Tesón-authored Constitución Española (I) questions, IDs `CE-001` through `CE-082`
- Adaptive recommended practice and the `adapt-v1` experiment, documented in [`14_ADAPTIVE_PRACTICE.md`](14_ADAPTIVE_PRACTICE.md)
- no accounts
- progress stored only in the browser
- pseudonymous analytics only after explicit consent
- reports and free-text feedback sent only when the user submits them, and only when legal identity and Supabase are configured
- no official past-exam questions ingested

## What changed in this pass

- Documents 01, 08, 13, and the folder index now distinguish the private beta from the later roadmap.
- Consent withdrawal removes queued analytics and aborts an in-flight analytics flush. Explicit user submissions already queued are preserved.
- Onboarding, ratings, topic interest, and recommendation scores are consent-only.
- Reports and feedback cannot show a false success when the backend is not configured.
- Legal pages render from `mvp/config.js` and show a blocking warning while owner identity is missing.
- Google Fonts were removed. Netlify headers are in the repository-root `netlify.toml`.
- Every question has provenance fields: Tesón-authored, source `BOE-A-1978-31229`, content date `2026-11-17`, and `pending_human` review status.
- Broad structure questions no longer link to an unrelated constitutional article.
- `mvp/schema.sql` allowlists event types and separates consent events from user-requested submissions.
- `mvp/review.json` and `mvp/REVIEW.md` require named approval of every question.

## Verification already run

- `npm test`: passed
- `npm run test:e2e`: passed in headless Chrome for consent refusal, answering a question, opening the explanation, and keeping an offline report disabled
- `npm run check:production`: fails on purpose

## Do not do these things yet

1. Do not mark the bank `revisado_humano` or mark any question `approved` without a named human reviewer and a completed date. Automated or AI review does not satisfy `mvp/REVIEW.md`.
2. Do not deploy. Netlify runs `npm run check:production`, which must fail until the gates below are real.
3. Do not put another product's Supabase URL or key in `mvp/config.js`. Tesón needs its own empty EU project. Never commit a `service_role` key.
4. Do not copy questions from commercial banks, user-generated banks, or datasets flagged in the research files.
5. Do not treat a public PDF or a GitHub/Hugging Face licence as permission to reproduce official exam text. Follow the green/amber/red lanes in [`research/summary.md`](research/summary.md).

## Release gates still open

- Real controller name, tax ID, address, update date, and contact email in `mvp/config.js`
- A new Tesón-only Supabase project in the EU, with `mvp/schema.sql` applied and its public URL and anon/publishable key configured
- Named human approval of all 82 questions in both `questions.js` and `review.json`
- A named person and realistic response target for impugnaciones
- A private cohort of 10–25 named participants, using the decision criteria in [`13_MVP_LAUNCH_TODAY.md`](13_MVP_LAUNCH_TODAY.md)

## Research for the next AI

The research brief has been executed into:

| File | Contents |
|---|---|
| [`research/summary.md`](research/summary.md) | Findings and recommended ingestion order |
| [`research/official_exams.csv`](research/official_exams.csv) | Official papers and keys found |
| [`research/constitution_question_map.csv`](research/constitution_question_map.csv) | Question numbers and constitutional topics, without copied stems |
| [`research/reuse_terms.md`](research/reuse_terms.md) | Source reuse terms |
| [`research/open_datasets.csv`](research/open_datasets.csv) | Concise dataset register |
| [`research/open_datasets_detailed.csv`](research/open_datasets_detailed.csv) | Longer dataset notes |
| [`research/market_banks.csv`](research/market_banks.csv) | Competitor metadata only |
| [`research/syllabi.csv`](research/syllabi.csv) | Syllabus coverage and gaps |
| [`research/unopened_urls.md`](research/unopened_urls.md) | URLs that could not be verified |
| [`research/notes/`](research/notes/) | Working notes by exam family |

Those files are research conclusions. They are not authorization to import their referenced questions into `mvp/questions.js`.
