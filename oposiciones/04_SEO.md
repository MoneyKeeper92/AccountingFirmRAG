# 04 — SEO strategy

## 0. The one idea

Opositores Google **laws, articles, temas, official exams and news** ("test ley 39/2015",
"artículo 14 constitución", "nota de corte auxiliar administrativo", "convocatoria auxiliar
administrativo 2026"). Every one of those searches should land on a Tesón page that **lets them
answer real questions right there**, explains the law better than anyone, and offers "guarda tu
progreso gratis" → sign-up.

The best-ranking competitors (PreparaOposiciones, Vence, OpositaTest, Linceopositor) already use
**free interactive test pages per law/tema**. We match that format and beat it on
explanation depth, freshness ("vigente a fecha…") and tools.

## 1. Seasonality: the calendar that drives everything

| Window | What people search | What must already be indexed |
|---|---|---|
| **Oct–Nov 2026** | "plazas auxiliar administrativo 2026", "cuándo sale la convocatoria", "temario" | Hub, temario pages, tema tests, law tests |
| **Late Dec 2026 – Jan 2027** (convocatoria in BOE + ~20 working days of applications) | "convocatoria auxiliar administrativo estado 2026", "requisitos", "cómo inscribirse", "tasas" | Convocatoria page (**published in Oct as "pendiente" and updated at the same URL the day the BOE publishes**) |
| **Feb–Apr 2027** | "test tema X", "test ley 39/2015", "psicotécnicos", "simulacro" | Full tema/law coverage + simulacro + psicotécnicos |
| **Exam day (≈ May–Jun 2027) + 48 h** | "plantilla provisional auxiliar administrativo 2027", "corrección examen", "impugnar pregunta" | **Explained answer key within 48 h of INAP publishing the plantilla**. The biggest single traffic spike of the year |
| **+1–2 months** | "nota de corte auxiliar administrativo 2027" | Nota de corte page + *calculadora de nota* |

Google needs weeks to trust a new domain, so the domain and the first 50–100 pages must go live
**in October**, even before the app beta.

## 2. Site architecture (URL plan)

All in Spanish, lowercase, no accents in URLs.

```
/                                          Home
/auxiliar-administrativo-estado/           Exam hub (guide: what, plazas, requisitos, examen, temario, fechas)
  /temario/                                28 temas overview
  /temario/tema-1-constitucion-espanola/   Tema page: summary + 15–20 free questions + "practica este tema"
  ... (28)
  /test/                                   Test hub (by tema, by bloque, by law, simulacro)
  /simulacro/                              Official-format mock (app deep link)
  /examenes-oficiales/                     Index of INAP papers
  /examenes-oficiales/2026-modelo-a/       Explained official exam (interactive)
  ... (2019→2026)
  /convocatoria-2026/                      Live news page (plazas, BOE, plazos, tasas)
  /nota-de-corte/                          History table + estimate
  /psicotecnicos/                          Guide + free generator
  /ofimatica/                              Windows 11 / M365 guide + tests
  /sueldo/  /requisitos/  /destinos/       Informational
/administrativo-estado/                    Same skeleton for C1 (month 3+)
/leyes/                                    Law library
  /leyes/constitucion-espanola/            Law hub + test
  /leyes/constitucion-espanola/articulo-14/  Article page (programmatic, see §4)
  /leyes/ley-39-2015/ ... /ley-40-2015/ ... /trebep/ ... /ley-19-2013-transparencia/ ...
/herramientas/
  /calculadora-nota-oposiciones/           Enter aciertos/fallos/blancos → nota with −1/3; vs nota de corte
  /calculadora-plazos-administrativos/     Ley 39/2015 días hábiles/naturales calculator (national holidays + weekends)
/impugnaciones/                            Public error log (trust page)
/metodologia/                              How questions are made & reviewed (E-E-A-T)
/blog/                                     News + guides
/academias/                                B2B teaser (month 4+)
/sobre-teson/  /contacto/  /legal/...
```

## 3. Keyword clusters (priority order)

Search volumes are **not verified**. Kyle or Claude should run Google Keyword Planner (Spain,
Spanish) from the new Google Ads account (no spend needed) in week 1. The ranking below is a
relative estimate.

| Priority | Cluster | Example queries | Page type | Competition |
|---|---|---|---|---|
| **P1** | Law tests | test constitución española, test ley 39/2015, test ley 40/2015, test trebep, test ley 19/2013 | Law hub + test | High (Vence, PreparaOposiciones, OpositaTest) |
| **P1** | Exam hub/news | auxiliar administrativo del estado 2026, convocatoria, plazas, fecha examen, requisitos | Hub + convocatoria page | High but news-driven: freshness wins |
| **P1** | Official exams | exámenes anteriores auxiliar administrativo estado, examen auxiliar administrativo 2026 resuelto, plantilla | Explained exam pages | Medium: most only link PDFs, **nobody explains every question** |
| **P2** | Temario | temario auxiliar administrativo del estado gratis, tema 1 constitución auxiliar | Tema pages | High for "temario gratis" (PDF sellers); medium for per-tema |
| **P2** | Articles | artículo 14 constitución, artículo 21 ley 39/2015, artículo 103 constitución | Programmatic article pages | Low–medium, huge long tail (also used by students of law and the general public) |
| **P2** | Tools | calculadora nota oposiciones, calcular plazos administrativos días hábiles | Tools | Low. **Link magnets** |
| **P3** | Nota de corte | nota de corte auxiliar administrativo 2024/2026 | Data page | Medium |
| **P3** | Psicotécnicos / ofimática | psicotécnicos auxiliar administrativo, test ofimática oposiciones, test excel oposiciones | Guides + generators | Medium |
| **P3** | Comparisons (month 3+) | opositatest opiniones, mejor app test oposiciones, alternativa gratis opositatest | Honest comparison page | Medium. Keep it factual and fair, never disparage |

## 4. Programmatic pages done right (not thin content)

**Article pages** (`/leyes/<ley>/articulo-<n>/`) ≈ 560 pages for CE + 39/2015 + 40/2015 +
TREBEP. Each one is generated from the BOE corpus, then quality-gated. Every page contains:
1. The **official text** of the article (legislation has no copyright; cite the BOE with the
   version date).
2. **"En cristiano"**: a plain-language explanation (unique, ~120–250 words).
3. **"Cómo lo preguntan"**: which INAP exams asked about it (year, question number) + the trap.
4. **3–5 interactive questions** with full explanations.
5. Related articles + "practica todo el Título".
6. `Revisado: <date> · Vigente desde: <date>` + reviewer name.

Publish in waves (CE first, then 39/2015, then 40/2015, TREBEP), about 50–100 per week. Watch
GSC "Crawled – currently not indexed". If a wave doesn't index, improve it before adding more.

**Tema pages** (28) and **explained exam pages** (≈16 papers: C2+C1, modelos A/B, 2019–2026)
are hand-polished, not purely programmatic.

## 5. Technical SEO checklist

- [ ] Static HTML (Astro) → every question and explanation is in the HTML, not loaded by JS.
- [ ] `sitemap.xml` split by type (`/sitemaps/leyes.xml`, `/temario.xml`…), submitted in GSC + Bing.
- [ ] Canonicals; no duplicate URLs with/without trailing slash; `.com` → 301 → `.es`.
- [ ] Structured data: `Organization`, `WebSite` (sitelinks search), `BreadcrumbList`, `Article`
      (blog/news with `dateModified`), `Quiz`/education Q&A markup where Google still supports
      it (verify in Google's current docs), `Dataset` for nota de corte tables.
- [ ] Core Web Vitals green on mobile (Cloudflare CDN, no heavy JS on content pages, fonts
      self-hosted with `font-display: swap`).
- [ ] `hreflang` not needed (Spanish only). `lang="es-ES"`.
- [ ] Open Graph images auto-generated per page (question card style), which makes shares on
      Telegram/WhatsApp look good.
- [ ] `robots.txt` allows AI crawlers that send traffic (Google-Extended decision: allow;
      opositores increasingly ask ChatGPT/Perplexity "¿dónde hago tests gratis de la ley 39?").
      Add `/llms.txt` summarising the site.
- [ ] Internal linking: every question links to its article page; every article page links to
      its tema and law test; the hub links everything.
- [ ] Cookie banner must not block content or hurt LCP.

## 6. E-E-A-T (why Google and humans should trust a new site)

- **/metodologia/**: sources (BOE consolidated texts, INAP papers), review process, update
  policy, how AI is used ("la IA redacta, una persona revisa, la ley manda").
- **Named reviewer** with a short bio (e.g., "funcionaria del Cuerpo General Administrativo").
  Needs the reviewer's consent.
- **/impugnaciones/** public log.
- "Última revisión" dates on every page.
- Company data in the aviso legal (legally required anyway).

## 7. Link building (low effort, ranked by ROI)

1. **Tools** (calculadora de nota, calculadora de plazos) get linked by forums, Telegram
   admins, creators, and even law-school and gestoría blogs.
2. **Explained official exam pages**: pitch them to Telegram admins and creators on exam week.
3. **Creator collaborations** (see 07): a link in the description/bio.
4. **Directories/editorial pitches**: infoposiciones.net, opositoraenactivo.com, mundopositor.info,
   oposiciones.guru, grupostelegram.net listing for our channel, disboard.
5. **Data stories for press**: "Las preguntas que más fallan los opositores de Auxiliar",
   built from our own beta data (month 3+). Pitch to El Español / 20minutos / Newtral-type
   education and employment sections. This is the Maxwell "outcome data" play turned into PR.
6. **Unions' AGE channels** (CSIF, CCOO, UGT): offer the free tool to their members.

Never buy links. Never spin competitor content.

## 8. Measurement

| KPI | Month 1 | Month 3 | Month 6 |
|---|---|---|---|
| Indexed pages (GSC) | 100 | 600 | 1,000+ |
| Organic clicks / month | 200 | 5,000 | 25,000 (spike after the convocatoria) |
| Organic sign-ups / month | 20 | 400 | 1,500 |
| Referring domains | 5 | 30 | 80 |

These targets are directional. Claude produces a **weekly GSC + GA4 digest** (queries gaining,
pages losing, not-indexed report) and proposes the next 10 pages to write.

## 9. Who does what
- **Claude:** keyword research (with the Keyword Planner export), page generation, internal
  linking, schema, weekly digest, refreshes when laws change, outreach drafts.
- **Reviewer:** approves questions/explanations before they are published.
- **Kyle:** approves the brand/tone once, looks at the weekly digest (5 min), sends outreach
  emails only where a personal touch matters (or delegates).
