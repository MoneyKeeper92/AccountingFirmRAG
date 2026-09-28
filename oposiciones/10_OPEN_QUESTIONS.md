# 10 — Open questions for Kyle

## A. Blocking decisions (answer before the Chrome session)

| # | Question | My recommendation | Why it matters |
|---|---|---|---|
| A1 | **Name:** go with **Tesón** (`tesonopos.es`)? | Yes, if the OEPM/TMview and handle checks are clean | Everything downstream uses it |
| A2 | **Is your name allowed to appear in the aviso legal?** Spanish law requires the legal owner's name + NIF on the site | If you want *zero* public link to you → SL. If you only care that the *brand* is separate → your autónomo registration is fine | Decides autónomo vs SL (09 §1–2) |
| A3 | **Are you currently registered as autónomo in Spain** (e.g., for Maxwell), or is Maxwell a US entity? Are you tax-resident in Spain? | — | Decides whether Tesón is a new epígrafe or a new registration, and the US reporting load |
| A4 | **Website:** Squarespace (your idea) or code on Cloudflare Pages (Claude operates it)? | Code (05 §1). Domain can still be bought on Squarespace | Programmatic SEO + near-zero involvement |
| A5 | **Who posts in communities and runs interviews?** You, a paid community helper, or both? How is your written Spanish for community posts? | Hire a helper who is an opositor | Credibility, native tone, your time |
| A6 | **Monthly budget ceiling** for the beta (reviewer, helper, tools, Claude Max)? | €600–1,000/month | Sizes the team and content pace |
| A7 | **Phone number for Tesón:** personal or a new prepaid eSIM? | New eSIM (~€5–10/mo) | WhatsApp/Telegram public contact without your number |

## B. Research Kyle should do (quick, needs a human or a login)

| # | Task | Time | Notes |
|---|---|---|---|
| B1 | OEPM Localizador + TMview search for "TESON"/"TESÓN" (classes 9/41/42) | 10 min | Links in 02 |
| B2 | Check `@tesonopos` on Instagram, TikTok, YouTube, X; check `tesonopos.es/.com` at checkout | 10 min | Fallback handles in 02 |
| B3 | Confirm Squarespace sells `.es` (else DonDominio) | 2 min | `.es` needs your NIE or a CIF |
| B4 | Ask your gestoría: autónomo epígrafe 933.9 vs SL; €80 flat rate eligibility; 036 "actividad preparatoria" during a free beta | 30-min call | Bring 09 |
| B5 | US cross-border CPA: implications of an SL (Form 5471 / GILTI) vs autónomo for you | 30-min call | Only if A2 → SL |
| B6 | How does Maxwell get Google reviews: Google Business Profile? Does it have a physical address? | 2 min | Decides whether GBP is viable for Tesón (03 F1) |
| B7 | Do you know any recent C1/C2 funcionarios, law grads or current opositores (Madrid network) who could be the reviewer or community helper? | — | Fastest hiring path |
| B8 | Open the three largest Telegram groups / Facebook groups in 07 from your phone and note member counts and rules | 15 min | Our research couldn't open Telegram/Facebook |
| B9 | Run Google Keyword Planner (Spain, Spanish) once the Tesón Google Ads account exists; Claude interprets the export | 10 min | Needs a logged-in Ads account (no spend) |
| B10 | Check r/oposiciones rules and size | 5 min | Reddit was blocked for our research |

## C. Strategy questions (answer any time in the first month)

1. **Pricing posture after the beta:** subscription (€8–15/month, like the market) vs one-off
   per convocatoria (€40–60, like OpoRuta/ADAMS and their "no auto-renewal" pitch)? *We'll
   let the month-5 willingness-to-pay survey decide. Say now if you have a strong prior.*
2. **Fundador perk:** lifetime discount (e.g., 50%) or X free months? *Recommend: 50% lifetime
   for anyone active ≥4 weeks during the beta.*
3. **Maxwell reuse:** are there Maxwell components (quiz UI patterns, question-health SQL,
   explanation rewriter prompts) you're comfortable re-implementing for Tesón? *Recommend
   re-implementing patterns, not copying code or data.*
4. **Ambition for B2B:** do you want to talk to academies yourself in month 4–6 (in Madrid,
   in person, which works better than email and avoids the LSSI cold-email issue), or delegate?
5. **Second exam:** after C2/C1, Justicia (Tramitación/Auxilio) or Policía/Guardia Civil?
   *Recommend Justicia: more legal-core overlap, MCQ-heavy, and its OEP-2026 convocatoria is
   also due by end-2026.*
6. **Visibility:** is it OK for you to appear as "founder" anywhere (e.g., LinkedIn, press), or
   should the public face be the team/the reviewer?
7. **Ads:** allow a €150–300 paid-social test in month 2 to measure CAC?

## D. Things we still need to verify (Claude will re-check once network access allows)

- Exact C2 temario (28 temas) and software version in the **OEP-2026 convocatoria annex** (late Dec 2026)
- Official nota de corte for the 23-May-2026 exam
- Current OEPM and CMP prices; Squarespace plan needed for Code Injection
- Whether Google still supports Quiz/education Q&A structured data
- Google Business Profile eligibility for online-only businesses in Spain
- r/oposiciones size/rules; Telegram group sizes
- INAP's answer on reuse (email below)

## E. Draft email to INAP (Kyle or the helper sends it from `hola@`)

> **Asunto:** Consulta sobre reutilización de cuestionarios de procesos selectivos
>
> Buenos días:
>
> Somos Tesón, un proyecto de plataforma educativa para personas que preparan oposiciones a los
> Cuerpos Generales de la Administración del Estado.
>
> Querríamos publicar en nuestra web los cuestionarios y plantillas definitivas de procesos
> selectivos anteriores de los Cuerpos General Auxiliar y General Administrativo, acompañados de
> explicaciones propias de cada pregunta, citando expresamente la fuente ("Fuente: Instituto
> Nacional de Administración Pública"), la fecha y la convocatoria, sin alterar el contenido
> original ni sugerir vinculación alguna con el INAP.
>
> Hemos consultado los avisos legales de www.inap.es y de sede.inap.gob.es y, dado que sus
> redacciones difieren, les agradeceríamos que nos confirmaran si esta reutilización es conforme
> a la Ley 37/2007 y al Real Decreto 1495/2011, o si requiere alguna autorización o condición
> adicional.
>
> Muchas gracias de antemano.
>
> Un saludo,
> Equipo de Tesón · hola@tesonopos.es
