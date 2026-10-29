# 13 — MVP launch: today's session

**Goal:** a free, working Tesón app online that real opositores can use, collecting how they
use it and what they think, at minimum cost and effort. Tesón is a **backup revenue stream** with
a **12-month learning horizon**. Nothing gets charged until the data says it's worth it.

## What already exists (built 29 Oct 2026)

| Piece | Where |
|---|---|
| Working app (static, no build step) | [`mvp/`](mvp/) |
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

**Content caveat:** I wrote the questions from the constitutional text. This session couldn't
reach boe.es to cross-check every quote, so the app shows them as "Beta: preguntas en revisión".
Before a wide launch, ask one of your Spanish advisors (ideally someone who opposed or studied
law) to do a 1-hour skim of the bank in Estudio mode, and impugnar anything off.

## Your steps today (~90 minutes)

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

### 4. Hosting: Cloudflare Pages (15 min)
1. dash.cloudflare.com → sign up with the Tesón Gmail.
2. **Workers & Pages → Create → Pages → Upload assets** (Cloudflare moves this button
   around; look for "deploy static files / drag and drop").
3. Project name `teson` → drag in the **`teson-mvp` folder** (unzip the file I sent) → **Deploy**.
   It works without the Supabase keys, but sends no data until they're in. Once you send me the
   keys, I'll give you an updated `config.js`: replace that one file and redeploy.
4. You get `https://teson.pages.dev` (or similar). That's the live app.

Later, connect Cloudflare Pages to a new Tesón GitHub repo, so every update I commit
deploys automatically and you don't have to drag anything.

### 5. Domain (10 min, optional today)
Buy `tesonopos.es` (+ `.com` if cheap). Squarespace if it offers `.es`, otherwise DonDominio.
Then in Cloudflare Pages → your project → **Custom domains** → add `tesonopos.es` and follow
the DNS instructions. Running on `teson.pages.dev` for the first weeks is fine.

### 6. Legal pages (10 min)
Spanish law requires the site owner's name, NIF/NIE, address and email in the aviso legal. Send me:
- the owner name (you as autónomo, or an existing company)
- the NIF/NIE
- a contact address
- the contact email (the Tesón Gmail is fine for now)

I'll fill both pages. A free beta is fine under your own name for now; switch to an SL later if
you want your name off it (see 09).

### 7. First users (20 min)
Use links with a source tag so we know where people came from. For example:
`https://teson.pages.dev/?utm_source=reddit&utm_campaign=beta`
1. Send the link to the Spanish advisors, with the Consulta Tesón questionnaire.
2. Post the r/oposiciones template from [07](07_LAUNCH_CHANNELS.md) §4.2. Read the subreddit rules first.
3. DM one Telegram group admin with template §4.1.

## What I need from you to finish

| Item | Why |
|---|---|
| Supabase Project URL + anon key | Turns on data collection; I update `config.js` and send a new zip |
| Owner name / NIF / address / email | Legal pages |
| The Cloudflare URL (and the domain, once bought) | Links, UTMs, SEO later |
| Anything that felt off when you tried it | Fix before posting |

## After today (what I do next, with little of your time)

| Cadence | What |
|---|---|
| Every 1–2 weeks | **One new tema** of ~60–80 explained questions. Order: "Me interesa" votes first, otherwise CE (II) → Ley 39/2015 → Ley 40/2015 → TREBEP |
| Weekly | A 5-minute digest from the Supabase views (`v_daily`, `v_feedback`, `v_reports`, `v_question_health`, `v_onboarding`, `v_tema_interest`). You paste the query results, or connect Supabase to the Tesón Claude account and I read them directly |
| Within 72 h | Fix every impugnación and log it |
| Late Dec 2026 | Convocatoria day: update the exam info and post in communities |
| By the exam (≈ May–Jun 2027) | Full Bloque I + key Bloque II temas, and a full-length simulacro |
| Month 12 (≈ Oct 2027) | Decision memo: users, retention, the recommendation score, willingness to pay, and whether to add a paid tier or license to academies |

**Running cost for this MVP:** €0 today (Supabase Free + Cloudflare Pages Free). Optional
domain ≈ €10–35 a year. Supabase Pro ($25/month) only when needed.
