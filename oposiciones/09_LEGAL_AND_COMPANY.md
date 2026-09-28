# 09 — Legal, company & compliance (Spain)

> Research summary, **not legal advice**. Direct access to boe.es/aepd.es/oepm.es was blocked
> during research, so items are from search summaries. Confirm with a **gestoría** (Spanish tax
> and admin accountant), and with a **US–Spain cross-border tax adviser** because Kyle is a US person.

## 1. The big catch: "separate brand" ≠ "anonymous owner"

Spanish law (**LSSI art. 10**) requires the website's **aviso legal** to show the **legal owner's
name, NIF/NIE, address and email**. So:

- As **autónomo**: *Kyle's full name and NIE appear in the aviso legal.* The brand is still
  Tesón everywhere else, but anyone who looks can connect it to Kyle.
- As an **SL** (e.g., "Tesón Formación Digital, S.L."): the aviso legal shows the **company**
  name, CIF and registered address. Kyle's name appears only in the public Registro Mercantil
  (as director/shareholder).

**If keeping Kyle's name off the site matters, an SL is the way.** That is a decision for Kyle
(see [10](10_OPEN_QUESTIONS.md)).

## 2. Structure options

| | Autónomo (new or existing) | SL |
|---|---|---|
| Setup | Modelo 036 (+ RETA), same day, €0 | CIRCE/PAE online with *estatutos tipo*: ~€150–300 official costs, ~1–2 weeks |
| Capital | — | €1 minimum (Ley 18/2022); 20% of profits to reserve until €3,000 |
| Social security | €200–590/mo by income; **€80/mo flat rate** for new autónomos (12 months) | Director with control = *autónomo societario*: higher minimum base [verify 2026 figure] |
| Tax on profit | IRPF (up to ~45%) | IS 19% on first €50k / 21% rest (2026; lower in 2027) |
| Liability | Unlimited | Limited |
| Ongoing admin | Quarterly 303/130; gestoría ~€40–80/mo | Accounts, IS return, annual accounts filing; gestoría ~€100–200/mo |
| US side | Schedule C + self-employment tax (totalization agreement decides which social security) | **Form 5471** (controlled foreign corporation reporting) + possibly GILTI/NCTI; check-the-box option. Needs a cross-border CPA |
| Name on website | **Kyle's** | **Company's** |

**Free beta (no revenue):** a no-revenue beta is arguably "actos preparatorios". You can file
the 036 early as preparatory activity to deduct VAT on setup costs, but it's not clearly required
until revenue. **RGPD and LSSI apply from day one regardless** (the site collects personal data
and is part of a planned economic activity).

**Recommended path**
1. **Now:** decide the name-visibility question.
   - If Kyle is fine with his name in the aviso legal → run Tesón under his existing (or a new)
     autónomo registration, adding IAE epígrafe **933.9** (other teaching activities; DGT
     V3016-23 covers oposiciones preparation) and a software/IT epígrafe as the gestoría advises.
   - If not → incorporate the SL before the site goes live (≈2 weeks), knowing the US
     5471 cost.
2. **Before charging (month 5–6):** revisit. Profits over ~€40–60k/year, B2B contracts with
   academies, or investors all favour an SL anyway.
3. **Don't** run it through a US LLC while living in Madrid (permanent-establishment and
   transparency issues).

Also: **ENISA "empresa emergente" certification** (Ley 28/2022 Startups Law) could give 15% IS
for 4 years and other perks if Tesón is an innovative SL. Worth a gestoría question later.

## 3. Trademark

- **OEPM** marca, classes **9** (software/app), **41** (education, exam preparation, online
  publications), **42** (SaaS). About €125 for the first class + ~€81 per extra class online
  (≈ €290 for three; **verify the current OEPM fee table**). 4–8 months if nobody opposes; 10-year term.
- File in the name of whoever will own Tesón long-term (Kyle or the SL; it can be assigned later).
- **EUIPO** (EU-wide) later if expanding: €850 for 1 class, €1,050 for 3. Use the 6-month priority
  from the OEPM filing.
- Pre-check: OEPM Localizador, TMview, Registro Mercantil Central (company names), domains.

## 4. Website legal texts (must exist at launch)

| Text | Must include |
|---|---|
| **Aviso legal** (LSSI art. 10) | Legal owner name/company, NIF/CIF, address, email, registry data (if SL); later prices incl. taxes |
| **Privacidad** (RGPD art. 13 + LOPDGDD art. 11) | Layered format. Controller, purposes, legal bases, recipients/processors (Supabase, Mixpanel, Google, Brevo, Anthropic), international transfers (EU–US Data Privacy Framework + standard contractual clauses fallback), retention, rights, AEPD complaint |
| **Cookies** (LSSI art. 22.2 + AEPD guide 2023/24) | "Rechazar" at the **same level and visibility** as "Aceptar" in the first layer; no "seguir navegando = aceptar"; easy withdrawal (persistent icon); list of cookies |
| **Condiciones** (beta terms) | Free beta "tal cual"; right to change/end it; not official content, may contain errors; acceptable use; anti-scraping; IP/database right; impugnación process |
| **Disclaimer** | "Tesón no está vinculado al INAP ni a ninguna Administración Pública." |

Tooling: **iubenda** (~€5–20/mo) generates and maintains Spanish privacy, cookie and terms texts,
and includes a CMP. Or have the gestoría/lawyer review a Claude draft.

## 5. Analytics & consent

- **GA4:** Consent Mode v2 in **Basic** mode (no Google tags before consent). Google Signals
  off, ad personalisation off, 14-month retention, accept Google's data processing terms.
- **Mixpanel:** **EU data residency** (choose at project creation); SDK
  `opt_out_tracking_by_default: true`, `opt_in_tracking()` after consent; session replay only with
  consent and input masking; sign the DPA.
- **Squarespace (if used):** its native banner doesn't send Consent Mode v2. Disable it and inject a
  CMP (Cookiebot / CookieYes / iubenda) via Code Injection (needs a plan that includes it).
- **Cookieless aggregate stats** (Cloudflare Web Analytics) can run without consent if they meet the
  AEPD audience-measurement exemption. Disclose them in the cookie policy.

## 6. Student data (RGPD)

- Legal bases: account + learning features = **contract**; analytics cookies = **consent**;
  service emails = contract/legitimate interest; marketing = **consent** (unticked box, double
  opt-in).
- **Don't ask about disability quota** (health data, art. 9) unless it is truly needed and explicit
  consent is collected.
- **DPAs:** Supabase (EU region), Mixpanel, Google, Brevo/Resend, Tally, Make, Anthropic (send
  no personal data to the model; use zero-retention settings where available).
- **Registro de actividades de tratamiento:** required (continuous processing). Generate it with
  the AEPD's free **Facilita RGPD** tool.
- DPO not required at this scale.
- Minors: oposiciones allow 16+. The Spanish digital-consent age is 14, so a free account is OK.
  For **paid** plans: 18+ or parental consent.
- B2B later: when academies bring their students, Tesón is their **processor**. Prepare a
  processor DPA template.

## 7. Marketing rules that affect the plan

- **No cold commercial emails**, including to **academies** (LSSI art. 21 covers business
  recipients too). For B2B outreach use: contact forms on their sites, phone, LinkedIn,
  in-person visits in Madrid, or inbound via `/academias/`. Check the Robinson list for any
  non-consented campaigns.
- Every email has an unsubscribe link.
- No "aprobado garantizado" or unprovable success claims (misleading advertising).
- **EU AI Act art. 50** (from Aug 2026): disclose AI use (the Metodología page does; add "IA"
  labels on any AI tutor/chat feature).

## 8. Content reuse

| Source | Rule |
|---|---|
| **Legislation (BOE)** | No copyright (LPI art. 13). BOE reuse conditions: cite the source, keep the update date, don't distort, don't imply official status; consolidated texts are "carácter meramente informativo" |
| **INAP past exams** | Reuse allowed under Ley 37/2007 + RD 1495/2011 with source citation, update date and no distortion. **But** the sede.inap.gob.es notice appears more restrictive ("private use"). **Action:** email INAP to confirm that republishing the questions with our own explanations and a source citation is fine. Use *plantillas definitivas*. Don't use INAP logos |
| **Other bodies' exams** (CCAA, ayuntamientos, universities) | Check each one's terms |
| **Commercial temarios / competitor banks** | **Never** ingest, copy or paraphrase. Protected by copyright (LPI art. 10), database right (art. 133) and unfair competition law. Our generation pipeline includes a similarity check against public competitor stems |
| **AI output** | Likely not copyrightable by itself. Protect the bank with the **database right** (substantial investment), terms and anti-scraping |

## 9. Before charging (month 5–6 checklist)
- 21% **IVA** (automated e-learning is an "electronically supplied service", not VAT-exempt
  education; DGT V0282/2026). EU consumers: OSS above €10k.
- 14-day **withdrawal** flow + the EU **withdrawal button** (Directive 2023/2673, since June 2026).
- **Law 10/2025**: renewal notice ≥15 days before auto-renewal charges; easy cancellation
  (applies from ~Dec 2026, verify).
- **Verifactu**-ready invoicing: mandatory from 1 Jan 2027 (companies) / 1 Jul 2027
  (autónomos). Or use a merchant of record (Paddle/Lemon Squeezy): verify the Spanish treatment.
- Many academies are VAT-exempt and can't recover the 21%. Factor that into B2B pricing.

## Key sources
- LSSI: https://www.boe.es/buscar/act.php?id=BOE-A-2002-13758
- LOPDGDD: https://www.boe.es/buscar/act.php?id=BOE-A-2018-16673
- AEPD cookie guide: https://www.aepd.es/guias/guia-cookies.pdf
- AEPD Facilita RGPD: https://www.aepd.es/guias-y-herramientas/herramientas/facilita-rgpd
- Ley 18/2022 (Crea y Crece): https://www.boe.es/buscar/act.php?id=BOE-A-2022-15818
- CIRCE/PAE: https://paeelectronico.es/es-es/CreaEmpresaPorTiMismo/Paginas/CIRCE.aspx
- Ley 28/2022 (Startups): https://www.boe.es/buscar/act.php?id=BOE-A-2022-21739
- OEPM fees: https://www.oepm.es/es/tasas-y-precios-publicos/tasas-de-marcas-y-nombres-comerciales/
- EUIPO fees: https://www.euipo.europa.eu/en/trade-marks/before-applying/fees-payments
- LPI: https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930
- Ley 37/2007: https://www.boe.es/buscar/act.php?id=BOE-A-2007-19814
- INAP aviso legal: https://www.inap.es/aviso-legal · https://sede.inap.gob.es/es/aviso-legal
- BOE aviso legal: https://www.boe.es/informacion/aviso_legal/index.php
- Mixpanel privacy: https://docs.mixpanel.com/docs/privacy
- Supabase DPA: https://supabase.com/legal/dpa
- Verifactu: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html
