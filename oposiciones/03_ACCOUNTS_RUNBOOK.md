# 03 — Accounts & stack runbook (the Chrome session)

Goal: every service belongs to **Tesón**, not Kyle or Maxwell. Nothing shares a login, a
recovery email, a payment card label, an analytics property or a browser cookie jar with Maxwell.

Kyle opens Chrome and Claude walks through these in order. **Order matters**: each step
supplies the identity the next one needs. Kyle does anything involving passwords, 2FA codes,
phone verification, ID documents and payment details. Claude fills forms, names things and
configures settings.

Estimated session length: **2–3 hours** for Blocks A–D. Blocks E–F can happen in week 2–3.

---

## Block A — Isolation hygiene (15 min, do first)

| # | Step | Detail |
|---|---|---|
| A1 | **New Chrome profile** "Tesón" | Chrome → profile icon → *Add* → "Continue without an account" (the Tesón Google account gets attached in B1). Different color theme so Kyle never posts from the wrong profile. Never log into Maxwell tools in this profile. |
| A2 | **Password manager vault** | New Bitwarden account (free) *or* a separate vault in Kyle's existing 1Password, named "Tesón". Every credential below goes here. |
| A3 | **Authenticator** | Use the same authenticator app, but label every entry `Tesón · <service>`. Save backup codes into the vault. |
| A4 | **Phone number** (decide) | Google, Meta, TikTok and WhatsApp Business all want a phone. Options: (a) Kyle's personal number, simplest and invisible to users; (b) a **prepaid Spanish eSIM** (e.g., Digi/Lowi, ≈€5–10/month, verify current offers) so WhatsApp Business/Telegram for Tesón never shows Kyle's personal number. **Recommended: (b)** if Tesón will run a public WhatsApp/Telegram. |
| A5 | **Payment card** | A separate card used only for Tesón: a virtual card from Kyle's bank, or Revolut/Wise, or the SL's account once it exists. It makes the eventual accounting clean and keeps Maxwell's statements separate. |

## Block B — Core identity (30–40 min)

| # | Service | Account / setting | Notes |
|---|---|---|---|
| B1 | **Gmail ("root" account)** | `tesonopos@gmail.com` (fallbacks: `hola.tesonopos`, `teson.opos`) | Owner and recovery account for every Google property. Recovery email: Kyle's personal email (not Maxwell's). Turn on 2FA. |
| B2 | **Domain** | `tesonopos.es` + `tesonopos.com` | **Squarespace Domains** if it sells `.es` (check in the checkout. If it doesn't, use **DonDominio**, a Spanish registrar that is cheap for `.es`). `.es` for a person or company requires an NIE/NIF or company CIF. WHOIS privacy on. Auto-renew on. |
| B3 | **Google Workspace** (Business Starter, ~€7/user/month) | `hola@tesonopos.es` (primary), aliases `soporte@`, `prensa@`, `academias@`, `no-reply@` | Gives a professional address for community posts, creator outreach and support. Buy through Squarespace (bundled) or directly from Google. Add the B1 Gmail as recovery. **Cheaper alternative:** Cloudflare Email Routing (free) forwarding to the Gmail, but "send as" is clunkier. Recommended: Workspace. |
| B4 | **New Claude account + Max plan** | Sign up with `hola@tesonopos.es` | Kyle's plan. Then connect *this* account's connectors (Gmail/Workspace, Mixpanel, Supabase, Make, Cloudflare, GitHub) to the new Tesón accounts, never Maxwell's. |
| B5 | **GitHub** | New user `tesonopos` (email `hola@`) + org `teson` | Copy this plan folder into a new private repo `teson/plan`. The app code goes in `teson/app` and the website in `teson/web`. |
| B6 | **Anthropic Console (API)** | New org "Tesón" on `hola@` | Separate from Maxwell's API key. Used for question generation / explanation rewriting pipelines. Set a monthly spend limit (start at $100). |

## Block C — Website, analytics & search (40 min)

| # | Service | Setting |
|---|---|---|
| C1 | **Cloudflare** | Account on `hola@`. Add the `tesonopos.es` zone (change nameservers at the registrar). Gives free DNS, SSL, Pages hosting, Turnstile (anti-bot for sign-up) and Web Analytics (cookieless). |
| C2 | **Website host** | **Recommended:** Cloudflare Pages from `teson/web` (Astro static site): free, fast, and Claude can publish SEO pages by committing, with no clicking. **Alternative (Kyle's original idea):** Squarespace Website (Personal/Business plan) with the copy from [05_WEBSITE.md](05_WEBSITE.md). See the trade-off table in 05. |
| C3 | **Google Analytics 4** | New GA **account** "Tesón" (not a property under Maxwell's account!). Property "tesonopos.es", time zone Europe/Madrid, currency EUR, **data retention 14 months**, Google Signals **off**, IP/granular location: default EU handling. Web stream for the site + app. Consent Mode v2 wired to the cookie banner. |
| C4 | **Google Search Console** | Domain property `tesonopos.es` verified by DNS TXT in Cloudflare. Submit `sitemap.xml`. Add the `.com` too. |
| C5 | **Bing Webmaster Tools** | Import from GSC (2 min). Bing also powers ChatGPT search / DuckDuckGo results, which is increasingly relevant. |
| C6 | **Mixpanel** | New **organization** "Tesón", project "Tesón Prod" + "Tesón Dev", **EU data residency** (choose EU at project creation; it cannot be changed later). Free plan. Timezone Europe/Madrid. Add the event plan from [08_METRICS.md](08_METRICS.md) to Lexicon. |
| C7 | **Cookie consent (CMP)** | CookieYes or Cookiebot free tier (or Squarespace's built-in banner if on Squarespace, but check it blocks GA before consent). Must have an equal-weight **"Rechazar"** button (AEPD). |
| C8 | **Microsoft Clarity** *(optional)* | Free heatmaps and session recordings. Only behind consent. Mixpanel's session replay may be enough; skip if so. |

## Block D — App backend & email (40 min)

| # | Service | Setting |
|---|---|---|
| D1 | **Supabase** | New org "Tesón" on `hola@`. Project `teson-prod`, region **EU (Frankfurt `eu-central-1` or Paris `eu-west-3`)**, strong DB password in the vault. Start Free, move to **Pro ($25/mo) before public launch**: free projects pause when inactive and have no backups. Auth: email magic link + Google sign-in. Project `teson-dev` for testing. |
| D2 | **Transactional email** | **Resend** or **Brevo SMTP** on `hola@`. Verify `tesonopos.es` (SPF, DKIM, DMARC records in Cloudflare). Plug into Supabase Auth → custom SMTP, so magic links come from `no-reply@tesonopos.es` and not a Supabase address. |
| D3 | **Email marketing** | **Brevo** (French, EU-hosted, free up to 300 emails/day) *or* **MailerLite** (EU). Lists: *Lista de espera*, *Beta*, *Academias*. Double opt-in on. Recommended: Brevo (one vendor for D2 + D3). |
| D4 | **Forms / surveys** | **Tally** (EU company, free, unlimited responses) for the onboarding survey, monthly feedback survey, PMF survey and academy contact form. Webhook → Make → Supabase. |
| D5 | **Make.com** | New account on `hola@` (Free → Core ~€9/mo when needed). Scenarios: Tally → Supabase; new user → Brevo; weekly metrics digest → email. |
| D6 | **Booking user interviews** | Google Calendar **appointment schedule** (included in Workspace), 20-min slots. (Calendly free is the alternative, but it would be a second Calendly identity.) |

## Block E — Social & community (week 1–2, ~60 min, Kyle on phone for verification)

Create all with `hola@` (or an alias) and the Tesón phone number. Profile photo = the *ó✓* icon.
Bio (Spanish): *"Tests gratis para oposiciones con explicaciones artículo a artículo. Auxiliar
Administrativo del Estado 📚 Beta gratuita →"* + link.

| # | Platform | Handle | Purpose |
|---|---|---|---|
| E1 | Instagram (Professional → Creator) | `@tesonopos` | Opostagram: carousels "pregunta del día", reels |
| E2 | TikTok (Business) | `@tesonopos` | #opotok: 30–45 s "¿Sabrías responder?" videos |
| E3 | YouTube (brand channel under B1) | `@tesonopos` | Shorts + "examen oficial explicado" long-form (SEO asset) |
| E4 | Telegram | channel `t.me/tesonopos` + bot later | Daily question channel; opositores live on Telegram |
| E5 | Reddit | `u/tesonopos` (brand) + Kyle's human account for honest participation | r/oposiciones: see [07_LAUNCH_CHANNELS.md](07_LAUNCH_CHANNELS.md) |
| E6 | X / Threads | `@tesonopos` | Low priority: reserve the handles only |
| E7 | WhatsApp Business + Channel | Tesón phone number | Support and a broadcast channel (optional) |
| E8 | LinkedIn Company Page | "Tesón" | Month 4+: B2B credibility for academies |
| E9 | Discord | reserve "Tesón" server name | Only if the community asks for it |

## Block F — Reviews, payments, later (month 3+)

| # | Service | When | Note |
|---|---|---|---|
| F1 | **Google Business Profile** | ⚠️ **Probably skip** | Google's guidelines exclude online-only businesses without in-person customer contact. Maxwell's reviews strategy works via GBP, but a Tesón profile risks suspension. *Kyle to confirm Maxwell's setup; verify the current guideline.* Use Trustpilot + in-app testimonials instead. |
| F2 | **Trustpilot** (free business) | Month 2 | Invite beta users who rate the app 9–10 |
| F3 | **Stripe** | Month 4–5 | Only when a paid plan is decided; needs the legal entity (see 09) |
| F4 | **Apple / Google developer accounts** | Month 6+ | Launch as a PWA first; native store listings only if metrics justify them |
| F5 | **Canva** (free) | Week 1 | Social templates in the Tesón palette |

---

## Naming conventions (so Claude can operate everything later)

- Everything is named `Tesón` / `teson` with no reference to Maxwell or Kyle.
- Environments: `teson-prod`, `teson-dev`.
- UTM scheme: `utm_source={reddit|telegram|instagram|tiktok|youtube|foro|email|creator-<name>}` ·
  `utm_medium={organic|post|bio|dm|newsletter}` · `utm_campaign={beta-launch|pregunta-dia|examen-explicado|...}`.
- Keep a live **`accounts.md`** in the private repo listing every service, login email, plan,
  monthly cost, owner and renewal date. **No passwords**: those stay in the vault.

## Monthly running cost (beta, before any revenue)

| Item | €/month (approx.) |
|---|---|
| Google Workspace (1 user) | 7 |
| Supabase Pro | ~23 ($25) |
| Domains (`.es` + `.com`) | ~3 (≈€35/yr) |
| Claude Max (Kyle's new plan) | ~90–180 depending on tier |
| Anthropic API (question generation) | 30–150 (front-loaded in months 1–2) |
| Human legal reviewer (see 06) | 200–600 |
| Cloudflare, GA4, GSC, Mixpanel, Brevo, Tally, Make, CMP | 0 (free tiers) |
| Optional paid social tests | 0–300 |
| **Total** | **≈ €350–1,250 / month** |

One-offs: OEPM trademark (~€150–250 for 1–2 classes), optional logo polish (€50–150),
SL incorporation if chosen (see 09).
