# 05 — Website: platform decision, sitemap and copy (Spanish)

## 1. Squarespace or code? (decision for Kyle)

| | Squarespace | Astro static site on Cloudflare Pages (in a GitHub repo) |
|---|---|---|
| Who updates it | Someone clicking in the Squarespace editor (Kyle, or Claude driving Chrome) | **Claude, by committing files**. No browser and no Kyle |
| 1,000+ programmatic SEO pages (articles, temas, explained exams) | Impractical: manual pages, blog-post hacks | Native: generated from the question DB and the BOE corpus |
| Interactive questions inside the page | Only via embedded code blocks | Native |
| Cookie consent (AEPD-compliant, Consent Mode v2) | The native banner doesn't send Consent Mode v2. You need a CMP via Code Injection (paid plan) | Any CMP |
| Speed / Core Web Vitals | OK | Excellent |
| Cost | ~€16–25/month website plan | €0 (Cloudflare Pages free tier) |
| Kyle's involvement | Recurring | Near zero |

**Recommendation:** buy the domain wherever is convenient (Squarespace is fine). Build the
**website in Astro on Cloudflare Pages** so Claude can operate SEO with no clicking. That fits
the "very little involvement" goal best. If Kyle prefers Squarespace anyway, use it for the
~8 core pages below and put the programmatic `/leyes/` + `/temario/` sections on the Astro
site. The copy below works in either case.

## 2. Launch sitemap (week 2–3)

| Page | URL | Goal |
|---|---|---|
| Home | `/` | Explain + "Empieza gratis" / join the beta |
| Beta landing (for community posts) | `/beta` | One CTA, UTM-tracked |
| Exam hub | `/auxiliar-administrativo-estado/` | SEO hub (see 04) |
| Convocatoria tracker | `/auxiliar-administrativo-estado/convocatoria-2026/` | Rank *before* the BOE publishes |
| Calculadora de nota | `/herramientas/calculadora-nota-oposiciones/` | Link magnet, useful on day 1 |
| Metodología | `/metodologia/` | Trust/E-E-A-T |
| Impugnaciones | `/impugnaciones/` | Trust (goes live with the app) |
| Sobre Tesón | `/sobre-teson/` | Who we are |
| Contacto | `/contacto/` | `hola@tesonopos.es` + form |
| Legal ×4 | `/aviso-legal/`, `/privacidad/`, `/cookies/`, `/condiciones/` | Required (see 09) |

Then add the SEO waves (temario → leyes → explained exams) from 04.

---

## 3. Copy

> Tone: tú, close, honest, no hype. Never promise to pass. Numbers only if true.

### 3.1 Home (`/`)

**Title tag:** Tesón · Tests gratis de Auxiliar Administrativo del Estado con explicaciones
**Meta description:** Practica por temas y con simulacros oficiales. Cada respuesta explicada con
el artículo exacto del BOE. Beta gratuita: sin tarjeta, sin letra pequeña.

**Hero**
> # Tu plaza, pregunta a pregunta.
> Tests de **Auxiliar Administrativo del Estado** con cada respuesta explicada —la correcta y
> las incorrectas— y el artículo exacto del BOE a un clic.
>
> **[Empieza gratis]**  ·  *Beta abierta: todo gratis durante 6 meses. Sin tarjeta.*

**Three blocks ("Por qué Tesón")**
1. **Entiende por qué fallas.** No te damos solo la letra correcta. Te explicamos por qué las
   otras tres son falsas y qué trampa te han puesto. Con el artículo de la ley enlazado.
2. **Sabes dónde estás.** Tu nota estimada con la penalización real (−1/3), tus temas débiles y
   —cuando seamos suficientes— en qué percentil estás frente al resto de opositores.
3. **Repasa lo que se te olvida.** Cada fallo vuelve a ti justo antes de que lo olvides.
   Cinco minutos al día en el metro cuentan.

**Block: "Preguntas que no te van a mentir"**
> La ley cambia. Las preguntas mal hechas cuestan plazas. En Tesón cada pregunta indica la ley
> vigente en la que se basa y la fecha de su última revisión. Si ves un error, pulsa
> **Impugnar**: lo revisamos en menos de 72 horas y lo publicamos en nuestro
> [registro de impugnaciones](/impugnaciones/). Sin esconder nada.

**Block: "Qué incluye la beta"**
- Tests por tema de los 28 temas (Bloque I y Bloque II)
- Simulacros con el formato oficial: 90 minutos, penalización incluida
- Exámenes oficiales del INAP resueltos y explicados
- Repaso inteligente de tus fallos
- Estadísticas por tema y nota estimada
- Psicotécnicos y ofimática (Windows 11 y Microsoft 365) — *en camino*

**Block: "¿Por qué gratis?"**
> Estamos construyendo Tesón **contigo**. Durante la beta todo es gratis. A cambio, te pedimos
> lo que más valor tiene para nosotros: que lo uses y nos digas qué mejorar. Quienes entren en
> la beta serán **Fundadores** y conservarán condiciones especiales cuando lancemos los planes
> de pago.

**FAQ**
- *¿Es realmente gratis?* Sí. Sin tarjeta, sin prueba que caduque a los 7 días. Toda la
  plataforma, durante la beta.
- *¿Quién hace las preguntas?* Se redactan a partir del texto oficial del BOE y de los
  exámenes oficiales del INAP. La IA nos ayuda a redactar; una persona con experiencia en la
  Administración revisa. Lo contamos todo en [Metodología](/metodologia/).
- *¿Sirve para Administrativo del Estado (C1)?* Gran parte del temario legal es común. Iremos
  añadiendo los bloques específicos del C1.
- *¿Estáis relacionados con el INAP o con alguna academia?* No. Tesón es un proyecto
  independiente. Los exámenes oficiales se citan con su fuente.
- *¿Funciona en el móvil?* Sí. Puedes instalarla como app desde el navegador.
- *¿Qué hacéis con mis datos?* Solo lo necesario para que la plataforma funcione y mejore.
  Servidores en la UE. Detalles en [Privacidad](/privacidad/).

**Footer:** Tesón · Oposiciones, pregunta a pregunta · hola@tesonopos.es · Aviso legal ·
Privacidad · Cookies · Condiciones · "Tesón no está vinculado al INAP ni a ninguna
Administración Pública."

### 3.2 Beta landing (`/beta`), used for every community post
> # Beta gratuita de Tesón para Auxiliar Administrativo del Estado
> Estamos buscando a los primeros 500 opositores que quieran probar una forma más clara de
> practicar tests. Todo gratis durante 6 meses. Solo te pedimos feedback sincero.
>
> ✔ Tests por tema con explicación de cada opción
> ✔ Simulacros con formato oficial y penalización
> ✔ Tus fallos, en repaso automático
> ✔ Estatus de **Fundador** para siempre
>
> **[Entrar en la beta]** (email → magic link)
> ☐ Quiero recibir novedades y avisos de la convocatoria por email *(unticked, optional)*

### 3.3 Calculadora de nota (`/herramientas/calculadora-nota-oposiciones/`)
> # Calculadora de nota: Auxiliar Administrativo del Estado
> Introduce tus aciertos, fallos y preguntas en blanco de cada parte. Aplicamos la penalización
> oficial (cada fallo resta un tercio de acierto) y te comparamos con las últimas notas de corte.
>
> *[Parte 1: aciertos / fallos / blancos] [Parte 2: aciertos / fallos / blancos] → Nota sobre 100*
>
> Última nota de corte publicada (cupo general, examen de diciembre de 2024): **56,33**.
> *Fuente: INAP. Las notas de corte cambian en cada convocatoria.*
>
> **¿Quieres saber tu nota real antes del examen?** Haz un simulacro gratis en Tesón →

*(Implementation: pure client-side JS, no login. Support custom question counts so it also works
for C1 and other −1/3 exams, which widens the link audience.)*

### 3.4 Convocatoria tracker (`/auxiliar-administrativo-estado/convocatoria-2026/`)
> # Convocatoria Auxiliar Administrativo del Estado 2026 (OEP 2026)
> **Estado: pendiente de publicación en el BOE.** Última actualización: <fecha>.
>
> - **Plazas aprobadas (OEP 2026, Real Decreto 387/2026):** 1.450 de acceso libre *(verificar
>   el desglose en el BOE)*.
> - **¿Cuándo se publica?** La OEP obliga a convocar dentro de 2026. La convocatoria anterior
>   se publicó el 22 de diciembre de 2025.
> - **¿Cuándo sería el examen?** El anterior fue el 23 de mayo de 2026, unos 5 meses después
>   de su convocatoria. *Estimación, no dato oficial.*
>
> 🔔 **Te avisamos el mismo día que salga en el BOE** → [email / canal de Telegram]

(Updated at the same URL on BOE day with plazas, plazos, tasa, requisitos and a link to the
BOE. Keeping one URL keeps the ranking.)

### 3.5 Metodología (`/metodologia/`)
> # Cómo hacemos las preguntas
> 1. **La fuente manda.** Partimos del texto consolidado del BOE y del temario oficial de la
>    convocatoria. Cada pregunta guarda el artículo exacto y la versión de la ley en la que se basa.
> 2. **La IA redacta, una persona revisa.** Usamos inteligencia artificial para proponer
>    preguntas y explicaciones. Un sistema automático comprueba que la cita existe literalmente
>    en la ley y que la respuesta es única. Después, una persona con experiencia en la
>    Administración revisa lo dudoso y una muestra de todo lo demás.
> 3. **Los datos vigilan.** Si una pregunta la falla quien mejor va, o una opción incorrecta
>    atrae casi tanto como la correcta, la retiramos para revisarla.
> 4. **Tú impugnas.** Cualquier opositor puede impugnar una pregunta. Respondemos en menos de
>    72 horas y lo publicamos en el [registro de impugnaciones](/impugnaciones/).
> 5. **La ley cambia, nosotros también.** Revisamos cada semana los cambios en el BOE. Si un
>    artículo cambia, las preguntas afectadas se ocultan hasta revisarlas.
>
> *Exámenes oficiales: fuente INAP (Instituto Nacional de Administración Pública). Tesón no
> está vinculado al INAP.*
> *Legislación: fuente Agencia Estatal Boletín Oficial del Estado. Los textos consolidados
> tienen carácter informativo.*

### 3.6 Sobre Tesón (`/sobre-teson/`)
> # Sobre Tesón
> Opositar es una carrera de fondo. Meses —a veces años— de temario, tests y dudas. Tesón nace
> para que ese esfuerzo rinda más: para que cada test te enseñe algo y sepas en todo momento
> dónde estás y qué hacer hoy.
>
> Detrás de Tesón hay un equipo con experiencia en plataformas de preparación de exámenes
> profesionales exigentes, que ahora trae ese método a las oposiciones. Y detrás de cada
> pregunta, una revisión humana.
>
> ¿Quieres ayudarnos? Entra en la beta, impugna todo lo que veas raro y cuéntanos qué echas de
> menos: **hola@tesonopos.es**

*(Mentions the exam-prep background without naming Maxwell or Kyle, as Kyle asked. Note that
the aviso legal must still name the legal owner. See 09.)*

### 3.7 Academias teaser (`/academias/`, month 4+)
> # Tesón para academias y preparadores
> ¿Tus alumnos hacen tests en PDF, Word o formularios? Te ayudamos a darles una plataforma de
> práctica moderna con tu marca, tus preguntas y estadísticas por alumno, sin cambiar tu forma
> de enseñar.
> **[Solicita una demo con tus propias preguntas]** (form with explicit consent; see 09 on cold email)

### 3.8 Legal pages
Generate with iubenda (≈€5–20/month; produces Spanish privacy, cookie and terms texts that stay
updated) or have a gestoría/lawyer draft them. Content requirements are in
[09_LEGAL_AND_COMPANY.md](09_LEGAL_AND_COMPANY.md).
