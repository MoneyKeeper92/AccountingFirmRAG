# Maria and Laura question-source audit

Audit date: 2026-11-17. Source repositories were read only.

## Executive findings

- Maria's live React code loads `public/spanish_quiz_combined.json`: **663 records**, of which **64** are constitutional-law records under the scope below.
- Maria's separate CCSE-style set has **279 records**: Tema 1 **99**, Tema 2 **36**, Tema 3 **24**, Tema 4 **36**, and Tema 5 **84**. The combined set contains **86** constitutional-law records.
- Laura's current React code loads `public/biblioteca_questions.json`, not the older all-in-one file. The runtime biblioteca bank has **1,940 records**, including **53** constitutional-law records.
- `public/all_biblioteca_quiz_combined.json` is a stale historical aggregate of **3,492 records**, including **515** constitutional-law records. It is not referenced by current runtime configuration.
- Laura's other configured runtime bank is `public/vet_questions.json`: **817 records** and **0** constitutional-law records. References to `Reglamento (CE)` were correctly treated as European Community citations, not Constitución Española records.

Constitution classification was done record by record from normalized question text and metadata. It includes the CE, Crown, Cortes, constitutionally defined Government, judiciary/CGPJ, Constitutional Court, territorial organization and autonomous institutions, constitutional rights, and constitutional reform. Mere appearances of words such as “rey”, “corona”, “comunidad autónoma”, or “Defensor del Pueblo” in historical, cataloguing, employment-status, or library-service questions were excluded.

## Exact bank totals and status

### Maria

- **Runtime active:** `public/spanish_quiz_combined.json` — **663**.
- **Present but not loaded by current source code:** `public/combined_quiz.json` — **279**; `tema1_quiz.json` — **99**; `tema2_quiz.json` — **36**; `tema3_quiz.json` — **24**; `tema4_quiz.json` — **36**; `tema5_quiz.json` — **84**.
- `combined_quiz.json` is exactly the concatenation of the five Tema files by count (99+36+24+36+84=279).
- `jan2026/` is a compiled/deployment copy. `jan2026_old_backup/` is explicitly a backup. Neither is the editable runtime source selected by `src/pages/HomePage.js` and `src/pages/QuizPage.js`.

### Laura

- **Runtime active biblioteca:** `public/biblioteca_questions.json` — **1,940**.
- **Runtime active veterinary:** `public/vet_questions.json` — **817**; `public/vet_temario.json` has **90** syllabus entries, not quiz questions.
- **Inputs used to build the runtime biblioteca bank:** `public/comunidad_madrid_questions.json` — **337**; `public/ayuntamiento_madrid_quiz.json` — **758**; root `ministerio_cultura_questions.json`, plus the 2023 and 2026 Comunidad de Madrid JSON inputs listed in `scripts/build-biblioteca-questions.js`.
- **Historical/inactive aggregates:** `public/all_biblioteca_quiz_combined.json` — **3,492**; `public/biblioteca_quiz_combined.json` — **1,081**; `public/imed_quiz.json` — **1,939**.
- **Inactive Maria copies in Laura:** `public/combined_quiz.json` and `public/spanish_quiz_combined.json` — **279** each; Tema 1–5 — **99/36/24/36/84**. Current Laura configuration does not reference them.

The older Laura summaries that call the all-in-one file “main” describe a previous app version. Current `src/config/quizConfig.js` is controlling evidence.

## Constitutional-law record map

### Maria runtime bank — 64 / 663

- Topic 2: IDs **44–61, 73–79, 89–97** (34).
- Topic 3: IDs **98–105** (8).
- Topic 5: IDs **107–114** (8).
- Other topic-coded sources: **145, 188, 196, 310, 319, 322, 324, 368, 370, 426, 435, 468, 517, 592** (14).

### Maria CCSE-style combined bank — 86 / 279

- Tema 1 (49): **1001, 1002, 1003, 1005, 1006, 1009, 1010, 1014–1019, 1021, 1024–1027, 1035, 1041, 1042, 1046, 1048, 1049, 1052, 1054, 1056–1058, 1060, 1063–1065, 1069–1075, 1082, 1084, 1085, 1092, 1094–1097, 1099**.
- Tema 2 (34): **2001–2022, 2024–2034, 2036**.
- Tema 3 (3): **3013, 3014, 3016**.
- Tema 4: **0**. Tema 5: **0**.

The individual Tema-file constitutional counts are therefore **49, 34, 3, 0, 0**.

### Laura current runtime biblioteca bank — 53 / 1,940

- C.2008-B Comunidad Madrid: **1, 2, 3, 17**.
- C.2021 Ayudantes Comunidad Madrid: **61, 62**.
- C.2021 Técnico Auxiliar Comunidad Madrid: **144, 145, 149**.
- C.2006 Comunidad Madrid: **204, 206, 207**.
- C.2008 Ayudante Comunidad Madrid: **260, 268, 269**.
- A.2006 Ayuntamiento: **429, 433, 435**.
- A.2010 Ayudantes Ayuntamiento: **543**.
- A.2010 Técnico Auxiliar Ayuntamiento: **623**.
- A.2019 Auxiliar Ayuntamiento: **796, 797**.
- A.2019 Ayudante Ayuntamiento: **877, 878**.
- A.2021 Ayuntamiento: **967, 968, 970, 971**.
- Ministerio 2023–2024 Modelo A: **1172, 1173, 1177–1180, 1202**.
- Ministerio 2023–2024 Modelo B: **1240–1242, 1332, 1333, 1346**.
- Ministerio 2020–2022 Modelo A: **1469**.
- Ministerio 2020–2022 Modelo B: **1538**.
- Ministerio 2018–2019: **1667, 1676, 1686, 1706, 1716, 1746**.
- C.2026 Comunidad Madrid: **1771, 1772**.
- C.2023 Comunidad Madrid: **1856, 1857**.

Source-specific counts: Ayuntamiento **13/758**; Comunidad Madrid **15/337**; legacy Comunidad+Ministerio aggregate **39/1,081**.

### Laura historical all-in-one bank — 515 / 3,492

Official-exam subset (39):

- Ministerio 2018–2019: **576, 585, 594, 613, 623, 651**.
- A.2006: **767, 771, 773**; A.2010 Ayudantes: **881**; A.2010 Técnico Auxiliar: **961**; A.2019 Auxiliar: **1134, 1135**; A.2019 Ayudante: **1215, 1216**; A.2021: **1305, 1306, 1308, 1309**.
- C.2008-B: **3373, 3374, 3375, 3389**; C.2021 Ayudantes: **3433, 3434**; C.2021 Técnico Auxiliar: **3517, 3521**; C.2006: **3576, 3578, 3579**; C.2008 Ayudante: **3632, 3640, 3641**.
- Ministerio 2020–2022 Modelo B: **3723**; Modelo A: **3887**; Ministerio 2023–2024 Modelo A: **4018, 4019, 4024, 4025**.

Private/student/academy subset (476):

- `TEST COMPETENCIAS ALUMNOS FEBRERO 2026`: **2480–2531** (52).
- `TEST IGUALDAD TEMA 7 ALUMNOS FEBRERO 2026`: **2635, 2636, 2660, 2661, 2664** (5).
- `TEST TEMA 2 Y 3 ALUMNOS FEBRERO 2026`: **2684–2746** (63).
- `TITULO I ALUMNOS FEBRERO 2026`: **3017–3163** (147).
- `TITULO PRELIMINAR ALUMNOS FEBRERO 2026`: **3164–3233** (70).
- `TITULO VIII ALUMNOS FEBRERO 2026`: **3234–3372** (139).

Laura `public/imed_quiz.json` contains those same **476 constitutional records** within its 1,939-record private-material bank, under different global IDs.

## Duplication and overlap

- Maria and Laura have **zero meaningful normalized-stem overlap between their current runtime banks**.
- The only literal normalized collision is a generic instruction-only stem. Maria IDs **461, 562, 581** collide with Laura runtime ID **476** (historical all-in-one ID **814**). Because the text is only a generic “select the correct statement” instruction, it is not evidence that one substantive question bank copied the other.
- No near match at token-Jaccard **0.88 or higher** was found between either Maria bank and Laura's runtime or historical aggregate after excluding exact matches.
- Laura contains byte-for-byte copies of Maria's dormant CCSE-style files: both `combined_quiz.json` files, Laura's `spanish_quiz_combined.json`, and all five Tema files. The 279 normalized stems overlap **279/279**. These are obvious copied-bank artifacts, but they are not loaded by Laura's current app.
- Maria's 663-record social-work bank and Laura's 279-record file named `spanish_quiz_combined.json` have **0** normalized-stem overlap; the shared filename is misleading.

## Provenance and notices

- Maria's 663-record bank traces by topic number to local `TEMAS GENERALES/` and `TEMAS ESPECÍFICOS/` PDFs. Extracted text contains the footer/watermark “Preparación oposición trabajo social Comunidad de Madrid”; extraction scripts also explicitly filter `vatea`. Classify this material as **private/academy preparation**, not an official exam, unless the owner supplies permission.
- Maria's Tema 1–5 PDFs produce the 279-record CCSE-style set. Their exact publisher/original edition is not established from the retained metadata. The content appears CCSE-derived, but that is not proof of an official reusable source. Classify as **unknown / likely derived test material** pending title-page and licence evidence.
- Laura Ayuntamiento, Comunidad de Madrid, and Ministerio de Cultura sources are named as public competitive-exam papers and are classified **official exam**. The original DOCX/PDF directories referenced in extraction summaries are no longer present in the current repository snapshot, so provenance is supported by filenames, retained metadata, scripts, and prior extraction notes rather than a complete local source-document set.
- Laura IMED, Yolanda, Ángel, Fátima, and `ALUMNOS FEBRERO 2026` sources are **private/student/academy tests**. Prior notes say DOCX answers were indicated by highlighting and PDF answers appeared on final pages. No reuse permission was found.
- One extracted Ministerio record in the historical all-in-one JSON contains the explicit notice **“©COPYRIGHT2021 PROHIBIDA LA REPRODUCCIÓN TOTAL O PARCIAL.”** Its metadata label says `2018-2019 Libres`, while the embedded exam header refers to a 2021 process; that mismatch should be resolved before any reuse.
- No explicit reuse licence or permission was found for private/student/academy material.

The requested Laura transcript was useful for reconstructing extraction history. Conversation IDs `c0372c08-78ca-47c7-8a6a-6c1522c36f18` and `1cc7f9ce-b542-40c5-b248-62857ec5673c` were not available as standalone local transcripts in the searched project stores.

## Safe-use recommendation

Treat all private, student, academy, IMED, Yolanda, Ángel, Fátima, `ALUMNOS`, VATEA/watermarked, and uncertain CCSE-derived material as **metadata-only**: retain counts, IDs, source labels, and hashes, but do not republish stems or options unless written reuse permission or a compatible licence is documented. For official exam material, keep source-agency, year, exam/model, and original question number, link to the agency publication where possible, and review each source's notice and applicable public-sector reuse terms before redistribution. Quarantine the record carrying the explicit prohibition and resolve its mislabeled provenance.
