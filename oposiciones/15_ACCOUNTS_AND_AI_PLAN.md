# 15 — Accounts (email + code) and the AI focus plan

*Built 17 Nov 2026 (app v0.3). Design notes, plus the setup Kyle does in Supabase, Postmark and
Anthropic.*

## 1. What changed for students

- **Sign-in with email, no password.**
  - The student types their email and gets a **6-digit code**, sent through Postmark.
  - They type the code and they're in.
  - They stay signed in on that device until they sign out.
- **Progress lives in their account.**
  - Answers, mastery, mistakes, history, experiment arm and plan sync to Supabase within 3 seconds, and again when the page is hidden or closed.
  - Signing in on another device merges both; per question, the record with more answers wins.
- **"Tu plan para hoy".** Students in the adaptive arm see a card with:
  - a coaching sentence
  - 2–5 focus concepts, each with a reason using their own numbers ("Has fallado 3 de tus últimas 4 respuestas sobre esto")
  - a button that starts a session built around the plan.
- **"Lo que ya has estudiado"** (on Progreso): recommended practice and the plan only use the areas the student marks. This is the Tesón version of the `from` dates in the CPA app's personal quizzes.
- **Easiest first** within each session, the CPA-app house rule.
- **The intake** asks hours per week, which sets plan session size: 10 questions for under 5 h/week, otherwise 15–20.
- **"Tu cuenta"** on Progreso:
  - shows the email
  - weekly-summary opt-in checkbox
  - Cerrar sesión
  - **Borrar mi cuenta**: deletes the email, progress, plans and analytics events (RGPD art. 17).

## 2. How the AI plan works (and what stays deterministic)

```
student answers ──► profiles.state (Supabase, synced)
                        │
 home screen, plan stale (>20 h or ≥40 answers since the last one)
                        ▼
      POST /functions/v1/focus-plan   (student's session token)
                        │ reads profiles.state, builds an anonymised summary:
                        │ per concept: answers, recent wrong/total, mastery, days since seen,
                        │ review due; active confusions; recent sessions; studied areas;
                        │ exam, exam date, hours/week (no email, no free text)
                        ▼
      Claude (claude-opus-5-5, JSON-schema output, concept IDs restricted to the catalog)
                        │ → focus [concept, weight 3/2/1, reason], review [...], session size, coach message
                        ▼
      validated server-side (unknown/duplicate/unstudied concepts dropped, text cleaned and capped)
                        │ falls back to rules: importance × weakness × evidence
                        ▼
      stored in plans + profiles.plan  ──► app: weighted slots (3:2:1), then review, new and
                                           coverage, with the usual per-concept and per-area caps
```

| Who decides what | |
|---|---|
| **The AI decides** | Which concepts matter most today, how to weight them, the wording of the reasons and the coaching line |
| **The rules always decide** | Which questions are shown, held-out progress-check questions, at most 3 questions per concept (4 for weight 3), at most 40% of a session from one area, easiest-first order, and safety-net coverage |
| **The AI never sees** | The email, the name, the academy name, or any text the student typed |

**When the rules plan is used instead of the AI:**
- the student has fewer than 10 answers
- the AI is unavailable, refuses, or returns something unusable
- the daily cap is reached

Students in that case still get a plan. The card says "Preparado a partir de tus resultados"
instead of "Preparado por un asistente de IA…". `plans.source` records which one was used, so
AI and rules plans can be compared later in experiment `adapt-v2`.

**Refusal fallback.** The function uses Anthropic's server-side refusal fallback (beta
`server-side-fallback-2026-07-01`, `fallbacks: "default"`). If the main model declines, the
request is re-run on a fallback model inside the same call. Any remaining refusal falls back to
the rules plan.

## 3. Cost and guardrails

| Setting (Edge Function env) | Default | Meaning |
|---|---|---|
| `TESON_PLAN_MODEL` | `claude-opus-5-5` | Model for plans |
| `TESON_PLAN_EFFORT` | `medium` | Thinking effort |
| `TESON_PLANS_PER_USER_DAY` | 3 | Above this, the stored plan is returned again (free) |
| `TESON_PLANS_PER_DAY` | 300 | Global daily cap on AI plans. Above it, rules plans (free) |
| `TESON_ALLOWED_ORIGINS` | `*` | Set to `https://tesonopos.es,https://teson.pages.dev` when live |

**Estimate:** about $0.03–0.06 per AI plan: roughly 3–4k input tokens, about 0.5k output, plus thinking.
- 200 weekly active students × ~4 plans/week ≈ 3,500 plans/month ≈ **$100–200/month**.
- The worst case is capped by the defaults at 300/day (about $15/day).
- `v_plan_costs` in Supabase shows tokens per day.
- To spend less, the planner can run on a smaller model, e.g. `TESON_PLAN_MODEL=claude-sonnet-5-5` or `claude-haiku-5-5`. That is your call; I haven't switched it.

## 4. Setup (Kyle, ~45 minutes, in the Tesón accounts)

### 4.1 Postmark (sends the login codes)
1. Create a Postmark account with `hola@tesonopos.es`.
2. Create a server "Tesón" and keep the default **Transactional** stream ("outbound").
3. **Sender Signatures → Domain** `tesonopos.es`: add the DKIM and Return-Path DNS records Postmark shows (in Cloudflare DNS), then verify.
4. New accounts start in test mode until Postmark approves them: request approval and describe "login codes for an education web app".
5. Copy the **Server API token**. It is both the SMTP username and password. Paste it only into Supabase, never into chat.
6. Weekly-summary emails later go in a separate **Broadcast** stream (or Brevo), never the transactional one.

### 4.2 Supabase Auth
1. **Authentication → Emails → SMTP Settings → enable custom SMTP:**
   - host `smtp.postmarkapp.com`, port `587`
   - username = password = the Postmark Server API token
   - sender `Tesón <no-reply@tesonopos.es>`

   Supabase's built-in email only reaches your own team's addresses, so custom SMTP is required for real students.
2. **Email Templates.** Edit **Magic Link** and **Confirm signup** (new students get the second one) to send the code, not a link. Subject: `Tu código de acceso a Tesón`. Body:
   ```html
   <h2>Tu código para entrar en Tesón</h2>
   <p style="font-size:28px;font-weight:700;letter-spacing:6px">{{ .Token }}</p>
   <p>Escríbelo en la app. Caduca en 1 hora. Si no lo has pedido tú, ignora este email.</p>
   ```
3. **Authentication → Providers → Email:** enabled. Email OTP length 6, expiry 3600 s (1 hour, which the app copy says).
4. **Rate limits:** raise "emails per hour" from the default to about 100 for launch week.
5. **Sessions:** sessions renew automatically, so students stay signed in until they sign out. For a forced re-login after 90 days without use, set **Inactivity timeout = 90 days** (Pro plan).
6. **URL configuration:** Site URL `https://tesonopos.es` (or `https://teson.pages.dev`).

### 4.3 Database
- Run `mvp/schema.sql` again in the SQL editor. It's safe to re-run, and adds `profiles` and `plans` with row-level security plus the new views.

### 4.4 Edge Functions
Install the Supabase CLI on your laptop, then from `oposiciones/mvp`:
```bash
supabase login
supabase link --project-ref <your project ref>
supabase secrets set ANTHROPIC_API_KEY=<key from the Tesón Anthropic Console org>   # paste into your terminal, not chat
supabase secrets set TESON_ALLOWED_ORIGINS=https://tesonopos.es,https://teson.pages.dev
supabase functions deploy focus-plan
supabase functions deploy delete-account
```
- Set an Anthropic **spend limit** for the Tesón org in the Anthropic Console (e.g. $100/month to start).
- After editing questions or tags, regenerate the catalog: `node tools/export_catalog.cjs`, then redeploy `focus-plan`.

### 4.5 App
- `config.js`: fill `supabaseUrl` and `supabaseAnonKey`, keep `demoAuth: false`, redeploy to Cloudflare Pages.
- `index.html` loads `@supabase/supabase-js@2.119.0` from jsDelivr.

## 5. Ideas carried over from the CPA app (`how-the-practice-app-works.md`)

| CPA app | Tesón |
|---|---|
| Personal quiz: topic **weights** 3/2/1, slots ∝ weight | AI plan focus weights 3/2/1, slots ∝ weight (largest-remainder rounding) |
| Within a topic: wrong/looked → unseen → just-missed held back → right | Within a concept: unseen first; answered in the last 24 h pushed back; questions with the student's active confusion first |
| `from` dates so the quiz follows a study plan | "Lo que ya has estudiado": unmarked areas stay out of recommendations and plans |
| Easiest first (difficulty 1–3) | Sessions sorted by difficulty (1–3), random within ties |
| Picker: importance × miss rate | Rules plan: importance × weakness × evidence (1–2 answers count as weak evidence) |
| Seeding from course history or a diagnostic | 10-question diagnostic feeds the learner model; the AI plan reads the diagnostic score |
| Email → slug, no verification | Email → **verified with a code** (needed under Spanish data-protection law, for sending emails, and so nobody can open someone else's progress) |
| Mixpanel keyed by slug, never email | Events keyed by account ID (or a random ID before sign-in), never email |
| Study-plan windows / focus pin (tutor-set) | **Not yet.** Becomes useful for B2B, when an academy sets the week's temas for its students |

## 6. Testing done (17 Nov)
- **Planner logic:** unit tests on `core.ts` cover:
  - no email in the summary
  - unknown confusions dropped
  - ranking by importance × weakness × evidence
  - validation dropping unknown, duplicate and unstudied concepts, clamping bad weights, stripping HTML and capping text
- **Typecheck:** both Edge Functions pass `tsc` against `@anthropic-ai/sdk@1.9.0` and `@supabase/supabase-js@2.119.0` types.
- **Preview mode (demo sign-in):**
  - invalid-email and wrong-code messages
  - diagnostic, practice, plan card, plan session
  - studied areas
  - sign-out wipes the device
- **Simulated Supabase, two devices:**
  - device A answers 20 and gets an AI plan with the right token
  - the account holds 20 answers and no email
  - device B sees 20 answers and the same experiment arm
  - a second user on device B starts empty
  - account deletion called with that user's token
  - all events keyed by account ID, never the email
- **Not tested** (it needs your accounts): real Postmark delivery, the real Supabase project, a live Claude call, and `supabase functions deploy`. The first real plan should be checked in `plans` (source `ai`, sensible reasons).

## 7. To do before launch
- [ ] Steps 4.1–4.5 above.
- [ ] Privacy page: name the owner (see 09). Confirm the processor list (Supabase, Postmark, Anthropic, Cloudflare) and their DPAs.
- [ ] Privacy page promises deletion after 24 months without use. Add a monthly job: Make scenario, or `pg_cron` deleting `auth.users` with `last_sign_in_at` older than 24 months.
- [ ] Decide when to ask for the email. Now it's **before the first question**. If sign-up drop-off is high, moving it to after the diagnostic is a small change.
