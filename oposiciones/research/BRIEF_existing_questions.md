# Research brief: where Spanish oposiciones practice questions already exist

> **How to use:** paste everything below the line into an AI research tool that can browse
> the web and open PDFs (ChatGPT Deep Research, Claude with web search, Perplexity Pro, Gemini
> Deep Research). If the tool can't produce files, ask it to put each table inline as CSV in a
> code block. Run Part A first; it's the most valuable. Parts B–G can be separate runs.

---

## Who you're working for and why

You are researching for **Tesón**, a new, free web app that helps people in Spain prepare for
*oposiciones* (public-sector entrance exams) by practising multiple-choice questions with detailed
explanations. The app starts with **Auxiliar Administrativo del Estado (C2)** and will expand to
related exams.

We need a complete, verified map of **where practice questions already exist**, so we can:

1. Add **official past exam questions** (written and published by the examining bodies) to the
   app, with their official answer keys and our own explanations, where reuse is legally allowed.
2. Understand what **free and paid question banks** already offer, so we can benchmark quality and
   coverage. This is for analysis only. We will **not** copy them.
3. Find any **openly licensed** question datasets we could legally reuse.

## Ground rules (read before searching)

- **Never copy, scrape or reproduce questions from commercial or user-generated banks** (academies,
  publishers, test apps, Daypo, Quizlet, etc.). They're protected by copyright and database rights.
  For those sources, record only metadata: name, URL, claimed question count, price, format, and
  how they say they source questions.
- **Don't bypass paywalls, logins, CAPTCHAs or robots.txt**, and don't download in bulk from
  commercial sites.
- **Official sources** (BOE, INAP, ministries, regional governments, city councils, police corps)
  can be opened and downloaded. Record their reuse terms exactly as written.
- **Verify everything.** Every row you report must have a URL you actually opened, with the date
  you opened it. If you couldn't open something, mark it `unverified` and say why. **Never
  invent a URL, date, count or legal clause.** If you are unsure, say so.
- Prefer the **official URL** over re-hosts. When an official PDF is only available on a
  third-party site (an academy blog, a forum), record both and mark `rehost_only`.
- Spanish exam documents use these terms: *cuestionario* (exam paper), *modelo A/B* (versions),
  *plantilla provisional* (provisional key), *plantilla definitiva* (final key), *preguntas de
  reserva* (reserve questions), *preguntas anuladas* (annulled questions), *turno libre*
  (open entry), *promoción interna* (internal promotion), *convocatoria* (call), *OEP*
  (oferta de empleo público), *ejercicio* (exam part).

---

## Part A: official past exams (highest priority)

For each exam below, find **every published convocatoria** (aim for 2010 → 2026; at minimum the
last 8 years), and for each one find the exam paper(s) and answer keys.

### Priority order
1. **Cuerpo General Auxiliar de la Administración del Estado (C2)**, turno libre, plus promoción interna if published
2. **Cuerpo General Administrativo de la Administración del Estado (C1)**: test part and supuesto práctico
3. **Justicia**: Auxilio Judicial, Tramitación Procesal y Administrativa, Gestión Procesal y Administrativa
4. **Policía Nacional**, Escala Básica (conocimientos test)
5. **Guardia Civil**, Cabos y Guardias (conocimientos + ortografía + gramática)
6. **Administrativo de la Seguridad Social** (C1) and **Auxiliar Administrativo de la Seguridad Social**, if separate
7. **Agentes de la Hacienda Pública** (AEAT)
8. Regional C2/C1 administrative exams: **Comunidad de Madrid**, **Junta de Andalucía**, **Generalitat Valenciana**, **Junta de Castilla y León**, **Xunta de Galicia**, **Gobierno de Canarias**
9. **Ayuntamiento de Madrid** (Auxiliar Administrativo) and **Ayuntamiento de Barcelona** (if test-based)

### Starting points (verify; these came from an earlier search)
- INAP C2 index: `https://sede.inap.gob.es/es/procedimientos-y-servicios/seleccion/procesos-selectivos-de-cuerpos-y-escalas-generales/cuerpo-general-auxiliar-de-la-administracion-del-estado`
- INAP C1 index: `https://sede.inap.gob.es/es/procedimientos-y-servicios/seleccion/procesos-selectivos-de-cuerpos-y-escalas-generales/cuerpo-general-administrativo-de-la-administracion-del-estado`
- INAP C2 convocatoria 2025 (exam held 23 May 2026): `…/cuerpo-general-auxiliar-de-la-administracion-del-estado-ingreso-libre-convocatoria-2025`
- Older INAP mirror: `https://www.inap.es/es/seleccion/…`
- Policía Nacional: `https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/empleo-publico/procesos-selectivos/policia-nacional/escala-basica/` and `policia.es` (oposiciones section)
- Guardia Civil: `guardiacivil.es` (sección de oposiciones / ingreso)
- Justicia: `mjusticia.gob.es` → Empleo público → Cuerpos generales de Justicia
- Seguridad Social: `seg-social.es` → Empleo público
- AEAT: `sede.agenciatributaria.gob.es` → Empleo público → Agentes

### Useful searches (Spanish)
- `"cuestionario" "plantilla definitiva" auxiliar administrativo del estado [AÑO] site:inap.gob.es`
- `examen auxiliar administrativo del estado [AÑO] pdf modelo A plantilla`
- `"plantilla de respuestas" tramitación procesal [AÑO] mjusticia`
- `cuestionario escala básica policía nacional [AÑO] plantilla respuestas`
- `examen guardia civil [AÑO] cuadernillo respuestas oficiales`
- `exámenes anteriores [cuerpo] site:gob.es`

### Record one row per document in `official_exams.csv`

| Column | Meaning |
|---|---|
| `exam_family` | AGE, Justicia, Policía Nacional, Guardia Civil, Seguridad Social, AEAT, CCAA-<name>, Ayto-<name> |
| `cuerpo` | Exact official name of the body/scale |
| `group` | A1/A2/C1/C2 |
| `access` | libre / promoción interna / estabilización / discapacidad (only if a separate paper) |
| `convocatoria_ref` | Official reference (e.g., "Resolución de 18 de diciembre de 2025", BOE-A-2025-xxxxx) |
| `oep_year` | OEP year(s) the convocatoria belongs to |
| `exam_date` | Date of the exam (YYYY-MM-DD) |
| `ejercicio` | Which part (primer ejercicio, segunda parte, supuesto práctico…) |
| `doc_type` | cuestionario / plantilla_provisional / plantilla_definitiva / acuerdo_anulacion / nota_de_corte / otro |
| `modelo` | A, B, único… |
| `n_questions` | Scored questions in the paper |
| `n_reserve` | Reserve questions |
| `n_annulled` | Questions annulled in the plantilla definitiva (and which numbers, in `notes`) |
| `penalty_rule` | e.g., "error resta 1/3", as stated in the convocatoria or paper |
| `official_url` | Direct URL to the PDF on the official site |
| `rehost_url` | Third-party copy, only if the official one is missing |
| `format` | Text PDF / scanned PDF (needs OCR) / HTML |
| `syllabus_version` | Which temario/annex the exam followed (link to the BOE annex if found) |
| `opened_on` | Date you opened the URL |
| `status` | verified / unverified / broken_link / rehost_only |
| `notes` | Anything notable (e.g., changes between provisional and definitive keys, appeals, linked "acuerdo del Tribunal") |

Also produce, per exam family, a short **coverage summary**:
- which years exist
- which are missing
- where provisional and definitive keys differ
- whether papers are text or scanned
- approximate total number of official questions available

---

## Part B: reuse terms for each official source

For every official website that hosts the papers (INAP, sede.inap.gob.es, interior.gob.es,
guardiacivil.es, mjusticia.gob.es, seg-social.es, AEAT, each CCAA and city council used):

1. Find its **aviso legal / condiciones de uso / reutilización** page.
2. Quote the exact clauses about reuse, reproduction, commercial use, attribution and
   modification. Keep the quote in Spanish and add a one-line English summary.
3. Note whether it points to **Ley 37/2007** (reuse of public-sector information) or
   **RD 1495/2011**, or to a Creative Commons licence, or whether it reserves all rights.
4. Note any **contact email or procedure** for requesting reuse authorisation.
5. Flag contradictions. For example, **inap.es** appears to allow reuse with attribution, while
   **sede.inap.gob.es** appears limited to private use. Confirm or correct this, quoting both.
6. Check **datos.gob.es** for any official open-data dataset of exam questions.

Output: `reuse_terms.md` with one section per source, plus a summary table:
`source | reuse allowed? (yes / yes with conditions / private use only / unclear) | attribution text required | commercial use allowed? | key quote | URL | opened_on`.

Also answer, citing sources, whether any Spanish court ruling, AEPD/Transparency Council
resolution or legal commentary discusses whether **exam questions written by a tribunal** are
protected by copyright or are "acts of public bodies" excluded under **Ley de Propiedad
Intelectual art. 13**. Report what you find; don't draw a legal conclusion.

---

## Part C: openly licensed question datasets

Search for datasets of Spanish oposiciones or Spanish legal multiple-choice questions with an
**explicit open licence**:

- **Hugging Face**: search "oposiciones", "spanish legal", "constitución española", "examen",
  "MCQ spanish", "INAP", "BOE".
- **GitHub**: search "oposiciones preguntas", "test oposiciones json", "auxiliar administrativo
  preguntas", "constitucion española test".
- **Kaggle**, **Zenodo**, **datos.gob.es**, university repositories.
- Academic papers that built Spanish legal or civil-service MCQ benchmarks. Look in
  SEPLN, ACL Anthology and arXiv for "Spanish legal benchmark", "oposiciones dataset", "exámenes MIR".
  MIR is medicine and out of scope, but it shows the pattern.

Record in `open_datasets.csv`:
`name | url | owner | licence (exact) | n_questions | exams/topics covered | source of the questions (official exams? generated? scraped from a commercial site?) | answer keys included? | explanations included? | last updated | quality notes`

**Flag any dataset that appears to be scraped from a commercial bank.** We won't use those,
whatever licence the uploader claims.

---

## Part D: the existing practice-question market (benchmark only, no copying)

Catalogue the sites and apps where opositores practise questions for the priority exams in
Part A. Include:
- **Paid platforms**: OpositaTest, PreparaOposiciones, GoKoan, ADAMS Test, MAD, InnoTest, OpoRuta, Testualia, Aprobado.app, Red Opositor, Vence…
- **Free sites**: Vence, oposicionesflou, hacertest, linceopositor, leyesparaoposiciones, opomania, josenrique.es, estudiafacil…
- **User-generated**: Daypo, Quizlet, and public Telegram test bots and channels.
- **App-store apps**: Google Play and the App Store in Spain.

Record in `market_banks.csv`:
`name | url | type (paid/freemium/free/UGC/app) | exams covered | claimed question count (and for which exam) | price | says it uses official exams? (quote) | explanations? (none/key only/short/detailed with article) | cites law articles? | shows "updated to" dates? | has error-reporting? | free access without login? | notable user complaints (with source links) | opened_on`

Observe only what any public visitor can see. Look at a few public sample questions to judge
explanation depth, and describe it in words. **Do not paste their questions or explanations
into your report.**

---

## Part E: official syllabi (for mapping questions to topics)

For each exam in Part A, find the **current official temario** (the annex of the latest
convocatoria in the BOE or the regional bulletin).

Record in `syllabi.csv`:
`exam | convocatoria_ref | bulletin URL | n_temas | list of temas (numbered, exact wording) | software versions named (Windows/Office/M365) | laws explicitly cited`

---

## Part G: who already does adaptive practice and visual explanations?

Tesón's planned edge is three things together: **practice-only** (no lessons or video), **visual
explanations** (comparison tables and diagrams that explain why each option is right or wrong) and
**adaptive review** (questions chosen from the student's weak concepts, review timing and
recurring confusions). Find out whether any Spanish oposiciones product already does all three
well.

For every product in Part D, plus any AI-first entrants you find (OpoRuta, Testualia,
PreparaOposiciones, Aprobado.app, InnoTest, Typed AI, Oposit.ai, OposiAI, opositest.ai, Red
Opositor…), record from public pages, demos, app-store screenshots and reviews:

| Column | Meaning |
|---|---|
| `adaptive_claim` | Exact quote of any "adaptive / personalised / IA / puntos débiles / repetición espaciada" claim |
| `adaptive_evidence` | What is visibly implemented: weak-topic tests, spaced repetition (SM-2/Leitner), concept-level tracking, confusion detection, predicted score… |
| `explains_wrong_options` | Do explanations cover why each wrong option is wrong? (yes / partly / no) |
| `visual_explanations` | Diagrams, comparison tables or esquemas inside explanations? Describe them; don't copy |
| `progress_view` | What the student sees: % by tema, ranking/percentile, predicted mark, trends |
| `practice_only` | Is it test-only, or bundled with temario/video/classes? |
| `price` | As in Part D |
| `top_complaints` | The 3 most common complaints in reviews (Google Play, App Store, Trustpilot, Reddit, forums), with links |
| `top_praise` | The 3 most common positives, with links |

Then answer in `summary.md`:
1. Does anyone already combine all three well? Who comes closest, and what is missing?
2. What do students most dislike about current apps' explanations and "adaptive" features?
3. Is there evidence that any of them measure real learning gains, rather than just engagement?

## Deliverables (in this order)

1. **`summary.md`** (1–2 pages). Cover:
   - total official questions found, by exam family and year
   - the legal picture for reusing them
   - the best openly licensed datasets, if any
   - the 5 most important gaps
   - your recommendation for what Tesón should ingest first
2. `official_exams.csv`
3. `reuse_terms.md`
4. `open_datasets.csv`
5. `market_banks.csv`
6. `syllabi.csv`
7. A list of every URL you could not open and why.

**Quality bar:** a smaller, fully verified result is far more useful than a long list with
guesses. Mark uncertainty explicitly.

---

## Optional Part F: extract official questions (only if B shows reuse is allowed)

If your environment can download and read PDFs, and the reuse terms from Part B for that source
allow it, extract the questions from **official INAP C2 papers** (most recent first) into JSON,
one object per question:

```json
{
  "source": "INAP",
  "exam": "Auxiliar Administrativo del Estado (C2), turno libre",
  "convocatoria_ref": "…",
  "exam_date": "2026-05-23",
  "modelo": "A",
  "question_number": 12,
  "is_reserve": false,
  "stem": "…",
  "options": {"a": "…", "b": "…", "c": "…", "d": "…"},
  "key_provisional": "b",
  "key_definitive": "b",
  "annulled": false,
  "official_url": "…",
  "page": 3,
  "extraction_notes": "OCR used / text PDF / unclear characters…"
}
```

Copy the text **exactly as printed**, without corrections or paraphrase. Use the definitive key
when it exists. Mark annulled questions. Note any page where OCR was needed or the text is
uncertain. Do **not** write explanations: Tesón writes its own.
