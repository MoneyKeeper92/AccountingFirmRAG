# 01 — Master plan: Tesón (oposiciones), Oct 2026 → Apr 2027

## Executive summary

- **What:** *Tesón* (tesonopos.es), a free web app for Spanish opositores. It has tests by tema and
  law, official-format simulacros, INAP past exams explained question by question, spaced review
  of mistakes, and "where you stand" analytics.
- **First exam:** **Auxiliar Administrativo del Estado (C2)**. The legal core overlaps heavily with
  **Administrativo (C1)**, which is added from month 3.
- **Why now:** the OEP 2026 approved **1,450 C2 + 2,300 C1** turno-libre plazas. The
  convocatoria must be published by 31 Dec 2026, and the exam will likely be ≈ May–June 2027.
  A **mid-November beta launch** catches the whole study ramp: new candidates flood in after the
  convocatoria (late Dec/Jan) and study hardest Feb–May.
- **Six-month goal (to ≈ end of April 2027):** not revenue. It is **usage and feedback data**:
  - 3,000+ registered users (6,000 stretch)
  - W4 retention ≥20%
  - PMF survey ≥30% "muy decepcionado"
  - a calibrated question bank
  - a willingness-to-pay range
  - a list of the academies our users attend (the B2B lead list)
- **How it wins (it's a crowded category):**
  1. Public honesty about errors (a *registro de impugnaciones* with a <72 h fix target).
  2. "Where you stand among opositores" percentiles. The exam is a ranking, with ~13
     candidates sitting per plaza.
  3. Truly free for 6 months.
  4. Every official exam explained.
  5. Built in public with the community.
- **How Kyle stays low-involvement:** Claude runs content, SEO, analytics and drafting from a
  dedicated repo with skills and scheduled routines. A paid part-time **legal reviewer** and a
  **community helper** (both ideally opositores or recent funcionarios) cover what must be
  human and Spanish-native. Kyle: ~5 h in week 1, then ~1–2 h/week (decisions + weekly digest).
- **Cash:** roughly **€350–1,250/month** during the beta (details in 03), plus one-offs of about
  €300–600 (trademark, logo, optional SL).

## Documents

| # | File | What's in it |
|---|---|---|
| 01 | this file | Strategy, timeline, roles, risks |
| 02 | [02_BRAND.md](02_BRAND.md) | Name, alternates, domains, identity, voice |
| 03 | [03_ACCOUNTS_RUNBOOK.md](03_ACCOUNTS_RUNBOOK.md) | Step-by-step account creation for the Chrome session + costs |
| 04 | [04_SEO.md](04_SEO.md) | Keyword clusters, site architecture, programmatic pages, calendar |
| 05 | [05_WEBSITE.md](05_WEBSITE.md) | Squarespace vs code decision, sitemap, Spanish copy |
| 06 | [06_PRODUCT_AND_CONTENT.md](06_PRODUCT_AND_CONTENT.md) | MVP scope, differentiation, architecture, question pipeline, feedback system |
| 07 | [07_LAUNCH_CHANNELS.md](07_LAUNCH_CHANNELS.md) | Where opositores are, ranked channels, post templates, rules |
| 08 | [08_METRICS.md](08_METRICS.md) | Event plan, weekly digest, targets, month-6 decision |
| 09 | [09_LEGAL_AND_COMPANY.md](09_LEGAL_AND_COMPANY.md) | Autónomo vs SL, trademark, RGPD/cookies, content reuse |
| 10 | [10_OPEN_QUESTIONS.md](10_OPEN_QUESTIONS.md) | What Kyle needs to decide or research |
| 11 | [11_COMPETITORS.md](11_COMPETITORS.md) | Market facts, competitors, prices, name collisions |

## Strategy in one page

1. **B2C free beta now, B2B later.** The research thesis (a white-label engine for small
   academies) stays the long-term play. But you can't sell academies an engine with no data,
   no calibrated bank and no proof students use it. Six months of free B2C creates all three,
   and onboarding asks each user which academy they attend.
2. **Start narrow:** one exam (C2), with its 28 temas, the official format and its community.
   Expand along the shared legal core: C2 → C1 → Seguridad Social/Hacienda → Justicia → Policía/GC.
3. **Content is the product; data is the moat.** RAG over BOE consolidated law, AI drafting,
   automated verification, human review, and Maxwell-style question-health analytics.
4. **SEO is the long game; communities are the short game.** Communities bring the first 500
   users. SEO (law tests, article pages, explained exams, calculators) brings the next thousands
   when the convocatoria lands.
5. **Build it the Maxwell way, with a clean separation:** same patterns, new code, new accounts,
   new brand. No Maxwell data, code or identity.

## Roles

| Who | Does | Time |
|---|---|---|
| **Claude** (new Tesón Claude account, Claude Code + Anthropic API) | App build, content generation, verification, SEO pages, analytics digests, drafts of every post/email/outreach, community listening, month-6 memo | Continuous |
| **Kyle** | Decisions (10), account creation session (identity/2FA/payments), weekly 5-min digest review, approves anything public-facing in week 1–2 (then spot checks), optional: interviews and posting | ~5 h week 1, then 1–2 h/week |
| **Legal reviewer** (freelance; recent C1/C2 funcionario or law grad) | Reviews flagged questions + 10% sample, resolves impugnaciones, signs off explained exams | ~5–10 h/week; €200–600/mo |
| **Community helper** (an opositor, optional but recommended) | Posts in communities from a genuine account, answers comments, runs 2–4 interviews/month | ~5 h/week; €200–400/mo or perks |
| **Gestoría** | Autónomo/SL registration, taxes, legal-text review | €40–200/mo |

## Timeline

Week 1 starts **Mon 28 Sep 2026**.

### Phase 0: Decide & set up (Weeks 1–2, 28 Sep – 11 Oct)
- [ ] Kyle answers the blocking questions in [10](10_OPEN_QUESTIONS.md) (name, structure, website platform, who posts)
- [ ] Send the Consulta Tesón feedback app to 8–15 Spanish advisors ([12](12_ADVISOR_FEEDBACK.md)); paste replies to Claude for synthesis
- [ ] Trademark + handle check for "Tesón" (OEPM, TMview, Instagram/TikTok/YouTube)
- [ ] **Chrome session**: Blocks A–D of [03](03_ACCOUNTS_RUNBOOK.md) (isolation, Gmail, domain, Workspace, new Claude account, GitHub, Anthropic API, Cloudflare, GA4, GSC, Mixpanel EU, Supabase EU, Brevo, Tally, Make)
- [ ] File the OEPM trademark (classes 9, 41, 42)
- [ ] Gestoría appointment: autónomo epígrafe vs SL (bring 09)
- [ ] Move this plan into the new private repo `teson/plan`. Create the `CLAUDE.md` + skills (`teson-todo`, `teson-content`, `teson-seo-wave`, `teson-weekly-digest`) mirroring the Maxwell skill setup
- [ ] Post the reviewer job (Malt / LinkedIn / InfoJobs); interview 2–3 candidates
- [ ] Email INAP to confirm reuse of past exam questions (draft in 10)
- [ ] Run Google Keyword Planner (Spain) for the clusters in 04; adjust priorities

### Phase 1: Foundations live (Weeks 2–4, 5 Oct – 25 Oct)
- [ ] Website v1 live: home, /beta waitlist, exam hub, convocatoria tracker, **calculadora de nota**, metodología, legal pages, CMP
- [ ] GSC + Bing sitemap submitted; Cloudflare analytics on
- [ ] Telegram channel `t.me/tesonopos` starts a **daily question** (builds history before approaching admins)
- [ ] BOE corpus ingested (CE, 39/2015, 40/2015, 50/1997, TREBEP, igualdad, transparencia, LOPDGDD, etc.)
- [ ] Question schema + generation/verification pipeline running; reviewer onboarded with a 50-question calibration batch
- [ ] App MVP build: auth, test engine, explanations with BOE deep links, impugnar, review queue, dashboard, onboarding survey, Mixpanel (consented) + server-side events
- [ ] SEO wave 1: 8 tema pages + Constitución article pages (~50–100)
- [ ] Creators and admins: first friendly DMs (no ask yet; "we're building this, would love your opinion")

### Phase 2: Closed beta (Weeks 5–7, 26 Oct – 15 Nov)
- [ ] 400 reviewed questions (Bloque I temas 1–8) + simulacro v1
- [ ] INAP May-2026 C2 exam explained (if reuse is confirmed)
- [ ] **Closed beta ≈ 10 Nov**: 50 users (Reddit post, 2 small Telegram groups, community helper's network)
- [ ] 5 user interviews; fix the top 5 issues
- [ ] SEO wave 2: Ley 39/2015 article pages + law tests

### Phase 3: Public beta (Weeks 8–13, 16 Nov – 27 Dec)
- [ ] 1,000 questions (all Bloque I + legal Bloque II temas)
- [ ] **Public beta ≈ 24 Nov**: big Telegram group (admin deal), forum answers, Facebook groups, creator collabs, directory pitches
- [ ] Public **Registro de impugnaciones** page live
- [ ] Psicotécnicos generator v1
- [ ] **BOE-day playbook ready**: convocatoria page update + posts drafted in advance, published within hours
- [ ] Weekly digest running every Monday

### Phase 4: Convocatoria surge (Weeks 14–22, 28 Dec – 28 Feb 2027)
- [ ] Convocatoria published → update the exam format/temario from the BOE annex (verify Windows 11 / M365, tema list)
- [ ] 1,500 → 2,500 questions; ofimática bank; all past INAP C2 papers explained
- [ ] "Tu semana de tesón" weekly email
- [ ] Percentile feature on (once ≥200 users have done a simulacro)
- [ ] Start C1 (Administrativo) extension
- [ ] **Month-3 check (≈ mid-Feb):** first PMF survey, cohort retention review, fix-or-cut list
- [ ] First data story for press/SEO ("Las preguntas que más falláis")

### Phase 5: Deepen & measure (Weeks 23–31, 1 Mar – 30 Apr 2027)
- [ ] Study plan ("tu examen es en N semanas: hoy toca…")
- [ ] Analyse `academy_name` answers → the top academies; 2–5 exploratory conversations (no cold email, see 09)
- [ ] Willingness-to-pay survey + PMF survey #2
- [ ] Legal entity/payments readiness checklist (09 §9) if going paid before the exam
- [ ] **Month-6 memo (≈ 30 Apr):** go B2C+B2B / pivot B2B-first / stop (criteria in 08)

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Wrong/outdated questions damage trust | Medium | High | BOE-grounded generation, verbatim-quote check, blind re-solve, human reviewer, public impugnación log, weekly BOE diff |
| Crowded market (OpositaTest, PreparaOposiciones, OpoRuta…) | High | Medium | Differentiators in 06 §1b; free period; community-first; SEO long tail competitors ignore (article pages, explained exams) |
| New domain is slow to rank | High | Medium | Go live in **October**; communities cover the gap; link-magnet tools |
| Community bans for self-promotion | Medium | Medium | Rules in 07 §1; ask admins first; disclose |
| Kyle's name appears in the aviso legal | Certain if autónomo | Low–Medium | SL option (09 §1) |
| Kyle's attention: **Maxwell's November pricing update and REG simulated exam land in the same weeks as the Tesón beta launch** | High | Medium | Tesón's November work is mostly Claude + helpers; Kyle's Tesón asks in Nov ≤1 h/week; Chrome session done in week 1–2 |
| Reviewer quits or is unavailable | Medium | High | Recruit 2 from day one (1 primary, 1 backup); keep a style guide and calibration batch |
| INAP says no to republishing questions | Low–Medium | Medium | Link to INAP PDFs + publish our own explanations referencing question numbers, or write "estilo INAP" questions |
| Exam date moves / convocatoria delayed | Medium | Low | The beta metrics don't depend on the exam date; the content is reusable |
| Brand/trademark conflict found | Low | Medium | Alternates in 02 |
| Spend creeps | Low | Low | Anthropic API spend cap; monthly cost table in `accounts.md` |

## What Claude will do right after the Chrome session (no Kyle needed)
1. Create the `teson/web` repo and ship website v1 (Astro), the calculators and the legal-page drafts.
2. Create `teson/app` and scaffold Supabase schema + auth + quiz engine.
3. Build the BOE ingestion + question pipeline; generate the first 50-question calibration batch
   for the reviewer.
4. Set up Mixpanel Lexicon, GA4 consent mode, GSC sitemap.
5. Draft all admin/creator DMs and the Reddit post for Kyle or the helper to send.
6. Schedule routines: Monday digest, weekly BOE diff, weekly community listening.
