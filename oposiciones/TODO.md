# Tesón: to-do for tomorrow (Wed 18 Nov 2026)

**✅ Unblocked:** `tesonopos.es` was registered on 17 Nov 2026 and the registrant email is verified. `tesonopos.com` is also registered. Nothing below waits on IONOS any more.

Do these in the separate "Tesón" Chrome profile, with the Tesón accounts, not Maxwell's.

## Start of the day (5 min)
- [x] `tesonopos.es` active (17 Nov) and IONOS contact email verified.

## Accounts and backend (about 45 min, steps in [16_ACCOUNTS_AND_AI_PLAN.md](16_ACCOUNTS_AND_AI_PLAN.md))

1. [ ] **Postmark**
   - Create a server.
   - Add and verify the sender domain `tesonopos.es`. Postmark gives you DKIM and Return-Path records; add them in IONOS → Dominios → tesonopos.es → DNS.
   - Copy the server token.
2. [ ] **Supabase Auth**
   - Connect Postmark as the email sender (custom SMTP) *(needs item 1)*.
   - Paste the Spanish code email into the "Magic Link" and "Confirm signup" templates.
3. [ ] **Database**
   - Re-run `mvp/schema.sql`.
   - Deploy the two server functions (`focus-plan`, `delete-account`) with the Supabase CLI.
4. [ ] **Anthropic**
   - Set `ANTHROPIC_API_KEY` as a Supabase secret.
   - Put a monthly spend limit on the Tesón organisation.
5. [ ] **Release gates** (see [15_PRIVATE_BETA_HANDOFF.md](15_PRIVATE_BETA_HANDOFF.md))
   - Legal details (owner name, NIF/NIE, address, date) in `mvp/config.js` **and** `web/src/site.ts`. Send them to Claude, who will fill in both.
   - Named human approval of all 82 questions.
   - The 10–25 private-beta participants.

## 6. Website (Astro on Netlify, code in [`web/`](web/))

The site is built and pushed. These steps put it online.

- [x] **6a. Create the Netlify site** (done 17 Nov: project `tesonopos`, live at tesonopos.netlify.app) (10 min, can be done today; no domain needed)
  1. Netlify → **Add new project → Import an existing project → GitHub**.
  2. Authorise Netlify on GitHub if asked. Pick the repo `MoneyKeeper92/AccountingFirmRAG`.
  3. Branch to deploy: `claude/oposiciones-platform-plan-z1bf01`.
  4. **Base directory: `oposiciones/web`** (important: the repo root holds the *app's* config).
  5. Build command `npm run build` and publish directory `oposiciones/web/dist` should fill in automatically from `oposiciones/web/netlify.toml`. If not, type them.
  6. Deploy. Project name: `teson-web`, giving the test address `teson-web.netlify.app`.
  7. Check the deploy log ends with `Site check passed: 13 pages. PRE-LAUNCH…`.
- [ ] **6b. Look at the site** on your phone and laptop. Note anything to change.
- [x] **6c. Connect the domains** (DNS done 17 Nov: IONOS `A @` and `A www` → 75.2.60.5 on both .es and .com. IONOS drops a `www` CNAME when `@` changes, so use A records. Remaining: add the `tesonopos.com` alias in Netlify, then HTTPS → Verify DNS configuration)
  1. Netlify → teson-web → **Domain management → Add a domain** → `tesonopos.es` and set it as primary.
  2. Add `tesonopos.com` as a domain alias. The netlify.toml already 301-redirects `.com` and `www` to `tesonopos.es`.
  3. Netlify then shows the DNS records to create. Use **exactly what Netlify shows**. It is normally:
     - an `A` record on `@` pointing to Netlify's load-balancer IP
     - a `CNAME` on `www` pointing to `teson-web.netlify.app`
  4. In IONOS → **Dominios y SSL → tesonopos.es → DNS**:
     - **delete IONOS's default `A` and `AAAA` records** for `@` and `www`. They point to the IONOS parking page, and a leftover `AAAA` breaks HTTPS on IPv6.
     - add Netlify's records.
  5. Repeat step 4 for `tesonopos.com`.
  6. Back in Netlify: **HTTPS → Verify DNS configuration**. It issues the free certificate automatically, usually within an hour.
- [ ] **6d. Email `hola@tesonopos.es`**
  - The website, app and legal pages all use this address.
  - In IONOS → **E-Mail**, check whether the domain includes a mailbox or forwarding. If yes, forward it to the Tesón Gmail.
  - If not, use a free forwarder.
  - Send a test email.
- [ ] **6e. Go public (later, not tomorrow)**
  - Once the legal details are in, Claude sets `launch.public: true` in `web/src/site.ts`. Until then every page is `noindex`, so Google ignores the site.
  - Then submit `https://tesonopos.es/sitemap-index.xml` in Google Search Console (Tesón Google account).

## Later
- [ ] App on its own Netlify site at `app.tesonopos.es`. This uses the repo-root `netlify.toml`, which stays blocked until item 5 is done.
  - Once it's live, Claude sets `appUrl` in `web/src/site.ts` so the website buttons open the app.
- [ ] OEPM / TMview trademark search for TESÓN (classes 9, 41, 42). Grab `@tesonopos` on Instagram, TikTok, YouTube and X.
- [ ] Move the Tesón code to its own GitHub repo, under a Tesón GitHub account.
