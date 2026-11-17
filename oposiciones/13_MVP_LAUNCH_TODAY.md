# 13 — MVP launch: today's session

**Goal:** validate a free, working Tesón app with a **private, named cohort** before any
public launch. This runbook is the source of truth for the current release. Documents 01–12
describe the later full-product roadmap; they do not describe the current app.

**Private-beta scope:** 82 Tesón-authored questions on Constitución Española (I), local-only
progress, no registration, and optional pseudonymous analytics. No official-exam question is
included. Nothing is charged.

## Entry gates (all required)

- [ ] The 82-question bank has completed a named human legal/content review and
  `TESON_BANK.status` is updated from `pendiente_revision_humana`.
- [ ] `npm test` and `npm run check:production` pass, including question-bank,
  human-review and production-configuration checks.
- [ ] The legal controller fields contain the real owner name/entity, NIF/NIE, address and
  contact email; the privacy page matches the processors actually used.
- [ ] The Supabase EU project has `mvp/schema.sql` applied and the deployed public URL/key
  are configured. Reports are tested end to end.
- [ ] Consent refusal and withdrawal have been tested: no behavioral analytics are sent and
  queued analytics are removed.
- [ ] The beta owner has named the person who will triage reports and the realistic response
  target shown in the app.

Do not share a deployed URL outside the named cohort until every gate is checked.

## What already exists (built 29 Oct 2026)

| Piece | Where |
|---|---|
| Working app (static, no compilation; gated validation before deploy) | [`mvp/`](mvp/) |
| Live preview to try on your phone | https://claude.ai/artifact/24oDYJCJGYtzYK7xQ9JSMk (private until you share it) |
| Question bank: 82 questions on Constitución Española (I), each with the correct answer explained, why every wrong option is wrong, the typical trap, and a BOE link | [`mvp/questions.js`](mvp/questions.js) |
| Database setup (one paste) | [`mvp/schema.sql`](mvp/schema.sql) |
| Legal page templates (fill in the yellow fields) | `mvp/aviso-legal.html`, `mvp/privacidad.html` |

**What the app does:**
- Tests by block (10/20/30/all questions).
- **Estudio** mode corrects each question as you go and explains it.
- **Examen** mode corrects at the end, with a timer and the official −1/3 penalty.
- Results by block, with every question reviewable.
- **Tus fallos**: mistakes come back after 1, 3, 7 and 21 days.
- Progress page.
- **Impugnar** button on every question.
- "Danos tu opinión" button, plus a 0–10 recommendation question after the 2nd test.
- 4-question onboarding: which exam, when, which academy, how they found us.
- **"Me interesa"** votes on upcoming topics, which tell us what to build next.
- No registration. Installable on the phone.

**Data:** progress stays in the user's browser. If the user accepts (the choice is shown with
equal-weight buttons), pseudonymous usage events go to your Supabase database in the EU.
Impugnaciones and feedback are sent when the user submits them.

**Content caveat:** the bank is Tesón-authored from the consolidated constitutional text and
has automated structural checks. It remains `pendiente_revision_humana` until a named reviewer
checks every item against the linked BOE source. Automated or AI review does not satisfy the
human-review entry gate.

## Private-beta setup

Do these in a **new Chrome profile** called "Tesón" so nothing touches Maxwell.

### 1. Try it (10 min)
Open the preview link on your phone and do a 10-question test in Estudio mode, then one in
Examen mode. Note anything that feels off.

### 2. Tesón Google account (10 min)
Create `tesonopos@gmail.com` (or the closest available). Turn on 2FA. Recovery email: your
personal one, not Maxwell's. This account owns everything below.

### 3. Database: Supabase (15 min)
1. supabase.com → **Start your project** → sign up with the Tesón Gmail.
2. New organization "Tesón" (Free) → New project `teson-prod`, region **Central EU
   (Frankfurt)**. Save the DB password in your password manager.
3. When the project is ready: **SQL Editor** → New query → paste all of `mvp/schema.sql` → **Run**.
   It should say "Success".
4. **Project Settings → API** (or "Data API"): copy the **Project URL** and the **anon / public**
   key, and paste both to me in chat. The anon key is designed to be public: the database
   only accepts inserts from it, so no one can read data with it. **Never** paste the
   `service_role` key anywhere.

Note: free projects pause after about a week with no activity. Once real users are sending
events it stays awake. Upgrade to Pro ($25/month) only if it pauses or you want backups.

### 4. Hosting: Netlify private-beta deploy (15 min)
1. Connect the Tesón repository to Netlify under the Tesón account.
2. Netlify reads the root `netlify.toml`; it validates, then publishes `oposiciones/mvp`.
3. Before a production deploy, fill `mvp/config.js` and run `npm run check:production`. The production
   configuration check intentionally fails if legal identity or backend fields are missing.
4. Use the Netlify preview URL for the named cohort. Do not post it publicly during this phase.

### 5. Domain (10 min, optional today)
Buy `tesonopos.es` (+ `.com` if cheap). Squarespace if it offers `.es`, otherwise DonDominio.
Then in Netlify → **Domain management** → add `tesonopos.es` and follow the DNS instructions.
The Netlify preview URL is sufficient for the private beta.

### 6. Legal pages (10 min)
Spanish law requires the site owner's name, NIF/NIE, address and email in the aviso legal. Send me:
- the owner name (you as autónomo, or an existing company)
- the NIF/NIE
- a contact address
- the contact email (the Tesón Gmail is fine for now)

I'll fill both pages. A free beta is fine under your own name for now; switch to an SL later if
you want your name off it (see 09).

### 7. Private cohort (20 min)
Recruit **10–25 named participants** from Spanish advisors and trusted C1/C2 candidates. Use
individual links such as `?utm_source=advisor&utm_campaign=private_beta`; do not include names
or other personal data in UTM values.

1. Send the link directly with the scope and content-review caveat.
2. Ask each participant to complete at least two tests and submit one piece of feedback.
3. Do not use the public Reddit, Telegram-group or creator templates in [07](07_LAUNCH_CHANNELS.md)
   until the exit decision below is made.

## Private-beta decision criteria

Review after at least **10 participants or 50 completed tests**, whichever takes longer:

- **Release gate:** zero unresolved correctness reports rated severe; all upheld reports fixed.
- **Reliability:** at least 95% of started tests complete without a reported blocker.
- **Content signal:** median explanation rating is positive and fewer than 5% of attempted
  questions receive a correctness/ambiguity report.
- **Use signal:** at least 40% of participants complete a second test.
- **Operations:** every report receives an acknowledgement or resolution within the response
  target shown in the app.

**Proceed to public-launch planning** only if all release/reliability/operations gates pass and
the content/use signals are directionally positive. Otherwise revise the bank or UX and run
another private cohort. These criteria govern this release; the month-6/12 metrics govern later
business decisions.

## What I need from you to finish

| Item | Why |
|---|---|
| Supabase Project URL + anon key | Turns on data collection; I update `config.js` and send a new zip |
| Owner name / NIF / address / email | Legal pages |
| The Netlify preview URL (and the domain, once bought) | Private cohort links; SEO later |
| Anything that felt off when you tried it | Fix before posting |

## After today (what I do next, with little of your time)

| Cadence | What |
|---|---|
| Every 1–2 weeks | **One new tema** of ~60–80 explained questions. Order: "Me interesa" votes first, otherwise CE (II) → Ley 39/2015 → Ley 40/2015 → TREBEP |
| Weekly | A 5-minute digest from the Supabase views (`v_daily`, `v_feedback`, `v_reports`, `v_question_health`, `v_onboarding`, `v_tema_interest`). You paste the query results, or connect Supabase to the Tesón Claude account and I read them directly |
| Within 72 h | Fix every impugnación and log it |
| Late Dec 2026 | Convocatoria day: update the exam info and post in communities |
| By the exam (≈ May–Jun 2027) | Full Bloque I + key Bloque II temas, and a full-length simulacro |
| After the private-beta threshold | Written go/revise/stop decision against the criteria above |
| Month 6+ | Business decision memo using the fuller metrics in [08](08_METRICS.md) |

**Running cost for this MVP:** €0 today (Supabase Free + Netlify Free). Optional
domain ≈ €10–35 a year. Supabase Pro ($25/month) only when needed.
