# 02 — Brand: name, identity, domains, handles

## Recommendation: **Tesón**

*Tesón* (n.) = tenacity, perseverance, stubborn determination. It is the single word every
opositor uses about themselves ("hace falta mucho tesón"). The average candidate studies for
1–3 years, so the brand promise is not "pass fast". It is "we keep you going, question by
question, and show you it's working".

| Why it works | Detail |
|---|---|
| Emotional fit | Opositores' identity is built on constancy and sacrifice. The name flatters the user instead of the product. |
| Not tied to one exam | Works for AGE, Justicia, Policía, Guardia Civil, local exams, and later B2B ("Tesón para academias"). |
| Not crowded | Every competitor is `opo-`, `oposita-`, `test-`, `plaza-` or `aprueba-`. A web search found no oposiciones product called Tesón (Sept 2026). |
| Short and natively Spanish | Two syllables and easy to say. A Spaniard hears a real word, not an anglicism or a startup coinage. |
| Zero link to Kyle or Maxwell | No physicist, no English, no accounting connotation. |

**Full brand line:** **Tesón** · *Oposiciones, pregunta a pregunta*

**Domain plan** (DNS lookups on 2026-09-28 found no records. That usually means unregistered, but
**confirm at the registrar before paying**):

| Domain | Use | Status seen |
|---|---|---|
| `tesonopos.es` | **Primary.** Spaniards trust `.es`, and "opos" is how students actually say *oposiciones* ("estoy con las opos") | appears free |
| `tesonopos.com` | 301 redirect to `.es`; protects the brand | appears free |
| `teson.app` | Optional: short link for the app / QR codes | appears free (unverified; `.app` often has no A record even when registered) |
| `teson.es`, `teson.com` | Taken, don't chase | taken |

App URL: `app.tesonopos.es` (or `tesonopos.es/app` if we host everything on one stack; see
[05_WEBSITE.md](05_WEBSITE.md)).

**Social handle:** `@tesonopos` everywhere (Instagram, TikTok, YouTube, Telegram, X, Threads,
Reddit `u/tesonopos`). Kyle must check availability during account creation. Fallbacks:
`@teson.opos`, `@tesonoposiciones`, `@tesonapp`.

### Alternates, in order (if the trademark search or handles fail)

| Name | Domain seen free | Pros | Cons |
|---|---|---|---|
| **Plaza Plan** | `plazaplan.es` / `.com` | Clear promise: "your plan to get the *plaza*" | "Plaza" is crowded (Tu Plaza Oposiciones, Plaza Mayor CEP) |
| **Hincacodos** | `hincacodos.es` / `.com` | From *hincar los codos* (to cram), funny and memorable, great for TikTok | Informal, which hurts the later B2B sale to academies |
| **Mérito** (`meritoopos.es`) | `meritoopos.es` / `.com` | Art. 103.3 CE: public jobs are awarded by *mérito y capacidad*. Aspirational. | `merito.es` taken; the name is generic, so the trademark is weaker |
| **Aprobaya** | `aprobaya.es` / `.com` | Direct and SEO-friendly | Sounds like a promise we can't make ("aprobado ya") and pushes toward misleading advertising |
| **Método Cajal** | `metodocajal.es` / `.com` | The Maxwell-style "scientist" name: Ramón y Cajal wrote *Los tónicos de la voluntad*, literally about willpower | Using a famous person's name as a trademark is legally risky in Spain (Ley 17/2001 de Marcas, art. 9) and "Cajal" is everywhere |

### Before buying anything (Kyle, ~20 minutes)

1. **OEPM trademark search**: <https://consultas2.oepm.es/LocalizadorWeb/> → search "TESON" and
   "TESÓN" in classes **9, 41, 42**.
2. **EUIPO eSearch / TMview**: <https://www.tmdn.org/tmview/> → same search. An identical mark in
   class 41 (education) is a blocker, and so is one in class 9 (software).
3. Check handles on Instagram, TikTok and YouTube.
4. If all clear → buy domains → file the OEPM trademark (see [09_LEGAL_AND_COMPANY.md](09_LEGAL_AND_COMPANY.md)).

---

## Identity (deliberately unlike Maxwell)

Maxwell uses blues (#01506e / #207bb5 / #0099d4) and DM Sans. Tesón uses **none of those**.

### Palette

| Token | Hex | Use |
|---|---|---|
| `--teson-verde` | `#1F5E4A` | Primary (bottle green: calm, "state", serious without being bureaucratic) |
| `--teson-ambar` | `#E9A23B` | Accent / CTAs / streaks (warm, energy) |
| `--teson-papel` | `#FAF7F0` | Background (warm paper, like a notebook) |
| `--teson-tinta` | `#1D2320` | Text |
| `--teson-acierto` | `#3C9D6B` | Correct answer |
| `--teson-fallo` | `#C2412D` | Wrong answer |
| `--teson-blanco` | `#9AA39F` | Unanswered ("en blanco") |

Dark mode swaps paper for `#121715` and keeps green/amber.

### Type
- Headings: **Bricolage Grotesque** (Google Fonts): characterful and friendly.
- Body/UI: **Inter**: legible at small sizes on phones, which is where opositores study.

### Logo concept
Lowercase wordmark **tesón** where the acute accent on the *ó* is drawn as a small upward
**tick ✓**. It reads as "the correct answer" and as "progress". App icon: the *ó* + tick on bottle
green. (Claude can produce SVG drafts; alternatively ~€50–150 for a Fiverr/Malt designer to
polish.)

### Voice
- **Tú**, never *usted*. A study partner who has been there, not an academy.
- Honest numbers, no hype. **Never** "aprobado garantizado", "la mejor academia", or pass-rate
  claims we can't prove (misleading advertising rules; also opositores are allergic to it).
- Speaks their language: *tema, bloque, simulacro, nota de corte, plantilla, impugnar, penalización,
  convocatoria, OEP, plaza, preparador, "salir en la lista"*.
- Celebrates constancy (streaks, questions this week) more than scores.

### Taglines (test in posts, keep the winner)
1. **Tu plaza, pregunta a pregunta.** ← default
2. Estudia con tesón. Aprueba con datos.
3. Sabes qué has fallado. Ahora sabes por qué.
4. El test que te explica la ley, artículo por artículo.

### Product vocabulary (name features in their words)
| Feature | Tesón name |
|---|---|
| Report a wrong/ambiguous question | **Impugnar** (the word opositores use for challenging official answers) |
| Mistake notebook / spaced repetition | **Tus fallos** / **Repaso inteligente** |
| Mock exam in official format | **Simulacro oficial** |
| Past INAP exams with our explanations | **Exámenes oficiales explicados** |
| Readiness indicator | **Tu nota estimada** (always shown with the penalty formula applied) |
| Weekly progress email | **Tu semana de tesón** |
