# 06 — Product (free beta) & content engine

## 1. What we are testing in the 6-month beta

The long-term business in the research notes is **B2B**: a white-label test engine for small
academies and preparadores. The 6-month plan is **B2C and free** on purpose, because a
student-facing beta produces the three things the B2B pitch needs and cannot be bought:

1. **Proof students use it**: retention curves, questions/week, streaks.
2. **A calibrated question bank**: real difficulty and discrimination data per question, and a
   public track record of fixing *impugnaciones*.
3. **A map of the academies**: onboarding asks "¿Preparas con academia? ¿Cuál?" Every answer
   is a qualified B2B lead, with student satisfaction data attached.

So the beta answers: *Will opositores come back to Tesón weekly without being paid or chased, and
what do they value enough to pay for (or ask their academy to adopt)?*

## 1b. Differentiation (the competitive reality in Sept 2026)

"AI explanations + spaced repetition + weak-topic stats" is **no longer rare**:

- PreparaOposiciones: SM-2 flashcards, AI explanations citing articles, €6.66–12.90/mo
- OpoRuta: C2-specific, "citations verified against BOE", €49.99/yr
- Testualia, Aprobado.app (weekly leagues), InnoTest, Vence (free tests by law)
- OpositaTest (≈15k Auxiliar questions, €7.99–15.99/mo) is the incumbent

Full list in [11_COMPETITORS.md](11_COMPETITORS.md). So Tesón must win on things that are hard to
copy quickly:

| Wedge | What it means | Why it's defensible |
|---|---|---|
| **1. Honest about errors, in public** | Public **"Registro de impugnaciones"** page: every reported question, status, resolution and response time (target <72 h). Each question shows "revisada el …, ley vigente a …" | The #1 complaint about every competitor is wrong/outdated questions. Nobody publishes their error log. Trust compounds. |
| **2. Where you stand against the competition** | The oposición is a **ranking, not a pass mark**: ~13 candidates sit per plaza (22,412 sat for 1,700 C2 plazas in May 2026). Tesón shows **your percentile among Tesón opositores** + estimated nota vs last nota de corte ("hoy estarías en el top 18%; necesitas el top ~8%") | Needs a large calibrated user base, which the free beta builds. It is the UWorld/Maxwell percentile insight applied to a competitive exam |
| **3. Fully free for 6 months, no card, no paywalled "demo"** | Everything unlocked for the beta; "Fundador" users keep a lifetime discount | Competitors' free tiers are demos. Opositores hate bait-and-switch |
| **4. Explained official exams, every single one** | Every INAP C2/C1 paper 2019–2026, every question with a distractor-level explanation + BOE article link | Heavy editorial work that, once done, is a permanent SEO + trust asset |
| **5. Built with the community** | Monthly public changelog "Lo que habéis pedido este mes" | Feedback loop is the beta's purpose anyway |

## 2. MVP scope (launch around mid-November 2026)

Target exam: **Auxiliar Administrativo del Estado (C2)**. Its format: 90 min; part 1 = ~30 Bloque I
+ ~30 psychometric questions; part 2 = 50 Bloque II questions; each wrong answer subtracts 1/3; 28
temas (16 in Bloque I + 12 in Bloque II); Windows 11 + Microsoft 365 desktop per the Dec-2025
convocatoria. **Verify against the BOE annex of the OEP-2026 convocatoria when it is
published (expected late Dec 2026).**

Because ~70% of the C1 (Administrativo) legal content overlaps, C1 users can use the
Bloque I/II legal banks from day one, labelled "también útil para Administrativo (C1)".

### In the MVP

| # | Feature | Why | Maxwell equivalent |
|---|---|---|---|
| 1 | **Test por tema**: pick temas, 10/25/50 questions, "con penalización" toggle | Core loop | Custom quiz |
| 2 | **Corrección explicada**: why the key is right, why *each* distractor is wrong, the exact article **with a deep link to the BOE consolidated text** (e.g., `…/buscar/act.php?id=BOE-A-2015-10565#a21`), and a common-trap note | The differentiator. Official papers give only the key, and many free sites give only the key too | Explanation rewriter |
| 3 | **Simulacro oficial**: 110 questions, 90 min, official scoring (+1, −1/3, 0 blank), part-by-part score vs last year's nota de corte (56.33 in the Dec-2024 round) | Opositores obsess over "¿me llega para la nota de corte?" | Simulated exam |
| 4 | **Exámenes oficiales explicados**: INAP past papers (2019→2026) with our explanations | Biggest SEO magnet + trust anchor. **Subject to the reuse check in 09** | — |
| 5 | **Tus fallos + Repaso inteligente**: every wrong/blank question goes into a spaced-repetition queue (SM-2 style: 1, 3, 7, 21 days) | Retention, and the daily reason to open the app | Mistake review |
| 6 | **Tu progreso**: accuracy by tema/bloque, "nota estimada" with penalty applied, **percentile among Tesón users** (shown once ≥200 users have done a simulacro), questions this week, streak | "Where do I stand, what do I do today" (Maxwell North Star) | Dashboard |
| 6b | **Registro de impugnaciones** (public page): every reported question, status, fix, response time | Trust wedge (see 1b) | — |
| 7 | **Impugnar**: one-tap report on any question (reason: wrong key / ambiguous / outdated law / typo / other + free text). Users are notified when their report is resolved | Quality loop + community goodwill ("they actually fix things") | Question feedback |
| 8 | **Onboarding survey** (5 questions, skippable): target exam, expected exam date, academy (yes/no/which), hours/week, how you found us | Segmentation + B2B lead map | Student survey |
| 9 | **Magic-link / Google login**, PWA installable on phone | Most opositores study on their phones and on public transport | — |
| 10 | **Feedback widget + monthly 3-question survey** | The 6-month objective *is* feedback | — |

### Phase 2 (weeks 8–16, driven by data)
- **Psicotécnicos** generator (series, verbal, data comparison): parametric, so questions can be generated without legal review. Half of part 1 is psychometric.
- **Ofimática** question bank (Windows 11 / Word / Excel / Outlook / Microsoft 365).
- **Plan de estudio**: "your exam is in N weeks, do this today" (exam weight × personal weakness, the Maxwell North Star).
- **Weekly email** "Tu semana de tesón".
- **Telegram bot**: daily question in the channel, answer → deep link to the explanation.
- **Administrativo (C1)**: add Bloques III–VI + the supuesto práctico format.

### Explicitly NOT in the beta
Payments, video, forums/chat, native apps, teacher dashboards, white-label. (The B2B
instructor dashboard gets built only after 2–3 academy conversations in month 4–6.)

## 3. Architecture (reuse the Maxwell approach, new codebase)

```
tesonopos.es (marketing + SEO pages)      app.tesonopos.es (PWA)
   Astro static on Cloudflare Pages   ─►   React/TS SPA on Cloudflare Pages
                                              │
                                              ▼
                                   Supabase (EU): Postgres + Auth + Edge Functions
                                   tables: questions, question_versions, sources,
                                   temas, exams, attempts, answers, review_queue,
                                   reports (impugnaciones), surveys, users_profile
                                              │
               Mixpanel EU ◄── events ────────┤──── Brevo (email)  ◄── Make
               GA4 (consented, site only)     │
                                              ▼
                         Content pipeline (offline, Claude Code + Anthropic API)
                         BOE consolidated-law corpus → generate → verify → review → publish
```

- **New repo, new code.** Rebuild the Maxwell *patterns* (quiz engine, explanation format,
  question-health SQL, spaced review). Don't copy Maxwell code or data, which keeps the
  separation clean and avoids IP entanglement.
- Supabase Row-Level Security on every user table; questions are public-read only when
  `status='published'`.
- Question IDs are stable, and every edit creates a new `question_versions` row (the "version
  everything" lesson from Maxwell), so the before/after impact of fixes is measurable.

### Question record (extends the schema from the research notes)
`id, exam_codes[] (AUX-AGE, ADM-AGE, …), bloque, tema_code, subtema, learning_objective, stem,
options[4], key, explanation_correct, distractor_rationales[3], trap_note, law_id (BOE-A-…),
article, source_url (BOE ELI + #anchor), source_quote (verbatim snippet), law_version_date,
effective_from, effective_to, difficulty_seed, origin (generated|official_inap|official_adapted),
official_ref (convocatoria, modelo, nº), status (draft|verified|reviewed|published|retired),
reviewer, reviewed_at, version`
Computed nightly: `attempts, p_correct, discrimination (point-biserial), distractor_pull[],
report_count, median_time_ms`.

## 4. Content engine (how ~1,500 questions get made with little of Kyle's time)

### 4.1 Legal corpus (source of truth = BOE, never model memory)
Download consolidated texts via the **BOE open-data API for consolidated legislation**
(`boe.es/datosabiertos`) and store article-level chunks with version dates. Legislation
itself is not protected by copyright in Spain (Ley de Propiedad Intelectual, art. 13). Minimum
corpus for the C2 temario:

- Constitución Española (1978)
- Ley 39/2015 (procedimiento administrativo común)
- Ley 40/2015 (régimen jurídico del sector público)
- Ley 50/1997 (del Gobierno)
- TREBEP (RDL 5/2015)
- LO 3/2007 (igualdad)
- LO 1/2004 (violencia de género)
- Ley 4/2023 (LGTBI)
- RDL 1/2013 (discapacidad)
- Ley 19/2013 (transparencia)
- LO 3/2018 (LOPDGDD) + RGPD
- Ley 47/2003 (General Presupuestaria), for the budget temas
- TFUE/TUE extracts, for the EU tema
- RD on electronic administration (RD 203/2021)
- Plus the exact list in the temario annex of the convocatoria

A weekly job diffs the BOE consolidated versions. When an article changes, every question
citing it is flagged **"ley actualizada: revisar"** and hidden from simulacros until re-verified.

### 4.2 Generation → verification → review
| Step | Who | Detail |
|---|---|---|
| 1. Blueprint | Claude | Per tema: learning objectives weighted by how often they appeared in INAP papers 2019–2026 |
| 2. Generate | Anthropic API (strongest current Claude model) | RAG on the article chunks; output JSON in the schema; must include `source_quote` copied verbatim |
| 3. Auto-verify | Scripts + a second independent model call | (a) the quote exists verbatim in the cited article version; (b) a blind model re-solves the question without seeing the key, and any disagreement goes to the human queue; (c) near-duplicate check (embeddings) against our bank **and** against scraped public competitor stems (so we never accidentally mirror them); (d) style lints (no "todas/ninguna de las anteriores" overuse, balanced key positions, similar option lengths) |
| 4. Human review | **Paid reviewer** (see below) | Reviews only what the auto-verifier flags + a 10% random sample of passed items. Target error rate on published items: <2% |
| 5. Publish | Claude | `status=published`, `version=1` |
| 6. Learn | Nightly SQL | Maxwell question-health logic: discrimination <0.15 or negative, a distractor chosen as often as the key, report_count ≥2 → "revisar esta semana" list (10–15 max) |

**The reviewer.** Kyle is not a Spanish-law expert and wants low involvement, so hire a
**recently-appointed C1/C2 funcionario or a law graduate/opositor** as a part-time freelance
reviewer. Sources: Malt.es, LinkedIn, or a trusted beta user. Pay per reviewed batch; budget
€200–600/month. **This person is the quality moat. Do not skip it.** Kyle's time: one
30-minute weekly check-in, or none if Claude's weekly report looks clean.

### 4.3 Content targets
| Milestone | Questions published | Notes |
|---|---|---|
| Closed beta (≈ Nov 10) | 400 | Bloque I temas 1–8 (Constitution, Crown, Cortes, Gobierno, TC, organización territorial, UE) |
| Public beta (≈ Nov 24) | 1,000 | All 16 Bloque I temas + Bloque II legal temas (Ley 39/40, TREBEP, igualdad, transparencia, datos) |
| Convocatoria published (≈ late Dec) | 1,500 + ≥3 explained official papers | Psicotécnicos generator live |
| Month 4 | 2,500 + ofimática | C1 extension started |
| Month 6 | 3,500+ | Every item has ≥30 attempts → calibrated difficulty |

API cost estimate: generating + double-verifying ≈ 3,500 items is on the order of **$150–$500**
total at current Claude API prices (estimate; depends on model and retries).

## 5. Feedback system (the other half of the 6-month goal)

| Channel | Cadence | Tool |
|---|---|---|
| Impugnar button | Always on | In-app → Supabase `reports` |
| "¿Te ha servido la explicación?" 👍/👎 | Every explanation view | Mixpanel event |
| Onboarding survey | Signup | Tally or in-app |
| Monthly 3-question survey (NPS + "¿qué echas de menos?" + "¿qué quitarías?") | Day 30, 60, 90… | Tally → Make → Supabase |
| **Sean Ellis PMF survey** ("¿Cómo te sentirías si Tesón dejara de existir?") | Users with ≥3 active weeks, at month 3 and month 5 | Tally |
| **Willingness to pay** (Van Westendorp 4 questions + "¿pagaría tu academia?") | Month 5 | Tally |
| **User interviews** (20 min, Google Meet) | 2–4 per month, recruited in-app; offer a thank-you (e.g., "Fundador" badge + free premium months later) | Google Calendar booking page. Claude drafts the script and summarises recordings. If Kyle doesn't want to run them in Spanish, hire the reviewer or a UX freelancer for them |
| Community listening | Weekly | Claude reads r/oposiciones + public Telegram mentions → weekly digest |
