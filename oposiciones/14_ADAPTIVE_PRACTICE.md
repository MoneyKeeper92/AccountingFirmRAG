# 14 — Adaptive practice: design, algorithm and experiment

**Promise to students:** *Practica lo que más necesitas mejorar.* We don't say "AI-powered"; the
selection is transparent rules, and every question shows why it was chosen.

**Product = Practice + Understand + Improve:**
- **Practice:** high-quality questions.
- **Understand:** explanations of all four options, comparison tables ("esquemas") and a link to the BOE article.
- **Improve:** adaptive review.

No lessons and no video.

Built in `mvp/` v0.2 (17 Nov 2026). Preview: https://claude.ai/artifact/24oDYJCJGYtzYK7xQ9JSMk

## 1. What the student sees

| Screen | Contents | Borrowed from the CPA app |
|---|---|---|
| **Inicio: "Tu Constitución"** | Mastery % per area (with a 7-day trend), a **recommended practice** card describing the real mix of the session it will serve, a **"Sueles confundir…"** card with a button to practise that confusion and a comparison table, stats, an **estimated mark if you sat a test on this tema today**, the diagnostic and progress-check cards | Topic list with % accuracy; "Predicted Exam Score (if you sat today)" |
| **Test personalizado** | Pick areas (each shows its question count and your %), number of questions, study or exam mode | "Create Test" page |
| **Question** | Dark top bar: **question timer with pause**, **Impugnar**, Entregar/Salir; **numbered navigator**; **question ID**; why-chosen pill (Refuerzo / Repaso / Nuevo / Cobertura / Tu confusión) | Timer bar, "Report Question Error", page numbers, question ID |
| **Results** | Score with the official penalty; correct/incorrect/blank/total; **"Repasar el test completo"** and **"Practicar tus puntos débiles"**; **Fortalezas / Áreas a mejorar**; table of Código · Pregunta · Resultado, with each row expanding to the full explanation | "Review Full Quiz", "Practice Weak Areas", Strengths / Areas for Improvement, question table |
| **Progreso** | Concept-by-concept mastery and next review date, frequent confusions, test history, privacy controls | — |

Layouts follow the CPA app. Colours, type and name stay Tesón's (no Maxwell blues or DM Sans),
so the brands stay separate.

## 2. Data model (built first, because lost learning data can't be recovered later)

Each question carries:
- **concepts**: 33 concepts in 6 areas (`tags.js`), e.g. `ref.ordinaria` (art. 167).
- **diff**: a 1–3 starting estimate, to be replaced by real accuracy.
- **mis**: for each wrong option, the **typical confusion** it represents. There are 12, e.g.
  "Alarma, excepción y sitio", "Art. 23.2 vs 103.3", "Quién autoriza: juez o Administración".
- **art** and a BOE link.

Every answer event stores the question ID, concepts, difficulty, result, chosen option, the
confusion triggered, time, answer changes, mode, session type, why the question was chosen,
and the experiment arm.

## 3. The four signals

| Signal | How it's computed |
|---|---|
| **Accuracy by concept** | Recency-weighted accuracy over the last 12 answers (each older answer counts ×0.75), with a prior worth one answer at 50%. One correct answer gives 75%, one wrong gives 25%. **Weak = below 70%.** |
| **Time since last successful recall** | Per-concept review interval: correct → 2 days, then ×2.5 each time (max 45). Wrong → back to 1 day. Per-question review: 1, 3, 7, 21 days in "Tus fallos". |
| **Repeated confusions** | A wrong pick on an option tagged with a confusion counts as a hit; getting right a question that offered that confusion counts as half a fix. A confusion is **active** with ≥2 hits in 30 days and a net score ≥1.5. |
| **Improvement over time** | A daily snapshot of area mastery; the dashboard shows the change against 7 days ago. Plus the diagnostic → progress-check comparison. |

## 4. Selection algorithm (recommended session of 20)

| Bucket | Share | Source |
|---|---|---|
| **Refuerzo** | 50% (10) | Weak concepts, weakest first. Concepts linked to an active confusion get priority. |
| **Repaso** | 30% (6) | Learned concepts whose review date has arrived |
| **Nuevo** | 20% (4) | Concepts never seen, in syllabus order |
| **Cobertura** | any shortfall | Concepts seen least recently, for broad coverage |

A shortfall in one bucket rolls into the next: refuerzo → repaso → nuevo → cobertura.

**Safeguards against blind spots:**
- At most **3 questions per concept** per session.
- At most **40% of a session from one area**, unless the student chose that area.
- Within a concept, prefer questions not answered in the last 24 hours, then unseen questions, then ones the student usually gets wrong.
- Order is shuffled.

Area practice (tapping an area) uses the same rules, limited to that area. "Practicar esta
confusión" gives up to 8 questions whose wrong options carry that confusion.

**Tested with a simulated student** who answers *Garantías* and *Reforma* wrong and everything
else right:
- By the third session the weak areas got the most questions the caps allow: Garantías 6–8, Reforma 4.
- Reforma is limited by its pool: only 4 of its questions remain once the progress-check questions are held back.
- No progress-check question ever appeared in practice.

## 5. Experiment `adapt-v1`: does adaptive practice actually help people learn?

**Design:** a randomised controlled trial among users who accept analytics.

| | Standard arm | Adaptive arm |
|---|---|---|
| "Practicar ahora" / tap an area | Random questions from the tema or area | §4 algorithm |
| Dashboard | Same area bars and stats; card says "Práctica del tema" | "Práctica recomendada" + "Sueles confundir" card |
| Explanations, esquemas, Tus fallos, custom tests | Identical | Identical |

**Measurement:**
- Two parallel **10-question forms (A and B)**, balanced by area, are held out of all practice.
- Each participant gets one form as the **diagnostic** (pre) and the other as the **progress check** (post). Which form comes first is randomised, so form difficulty cancels out across arms.
- The progress check is offered after 60 practice answers, or after 10 days with at least 30.
- Users who decline analytics get the adaptive version and are not analysed.

**Primary analysis:** post score ~ arm + pre score (ANCOVA), on everyone with both checkpoints.

**Do not adjust for practice volume in the primary model.** It's affected by the treatment
itself, because adaptive users may practise more or less. Report it separately, as a
secondary outcome alongside these:
- W4 retention
- answers per week
- recurrence of confusions
- the recommendation score (0–10)

**Supabase views:**
- `v_experiment`: one row per participant
- `v_experiment_summary`: by arm
- `v_concept_accuracy`
- `v_misconceptions`

**Be realistic about sample size:**
- With 10-question checkpoints, scores are noisy.
- To detect a 0.5-point difference out of 10 (gain SD ≈ 1.5, effect size ≈ 0.33, 80% power), we need **about 140 completers per arm**.
- If roughly 30% of participants reach the progress check, that means **about 1,000 consenting users**.
- Until then, treat results as directional.

As the bank grows, lengthen the forms to 15–20 questions, which makes the measurement much
sharper.

**Ethics and law:**
- Both arms get a complete, free product.
- Assignment happens only with consent; the consent screen and the privacy page say we may show
  one of two ways of choosing questions.
- No sensitive data is involved.

## 6. Known limitations / next steps
1. **More esquemas** (4 today: reforma, estados, Título I, suspensión): one per area as content grows. Esquemas are where "Understand" beats competitors.
2. **Concept tags and confusions are my first pass.** The reviewer should check them, as they check the questions.
3. **Difficulty**: replace the 1–3 seed with real accuracy once each question has 30+ answers. Later, a simple item-response (IRT) model can personalise difficulty.
4. **Progress is per device** (localStorage). An optional login (magic link) would carry it across devices and allow a weekly email. Add it once users ask.
5. **Competitive check** before heavy investment: do existing Spanish apps already combine practice-only + visual explanations + adaptive review, and what do students dislike about them? This is Part G of the research brief.
