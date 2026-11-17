# Question banks (official exam papers only)

Added 2026-11-17. These JSON files were copied unchanged from Laura's
biblioteca quiz project. Every record comes from a public competitive-exam
paper for archive and library posts (Ayuntamiento de Madrid, Comunidad de
Madrid, Ministerio de Cultura). No academy, student or uncertain-source
material is included, per the provenance rule in [`../README.md`](../README.md).

| File | Records | Contents |
|---|---|---|
| `bibliotecas_official_exams.json` | 1,940 | 26 exam papers, 2006 to 2026: Ayuntamiento de Madrid 758, Ministerio de Cultura 675, Comunidad de Madrid 507 |
| `ministerio_cultura_2023-2024_turno_libre_modelo_a.json` | 150 | One paper by section, including 20 reserve questions |
| `ministerio_cultura_2020-2022_modelo_a_official_key.json` | 150 | One paper by section, answers from the definitive official key; 7 annulled questions are flagged in `status` and `notes` |
| `ministerio_cultura_2020-2022_modelo_b.json` | 100 | First part of one paper |

The three Ministerio files overlap heavily with the combined file. They are
kept because they preserve the original question numbers, sections, reserve
questions and annulments, which the combined file does not.

## Formats

- `bibliotecas_official_exams.json`: list of
  `{id, question, options[], correct_option, source, topic, original_id, original_topic}`.
  `correct_option` is a zero-based index into `options`. `source` is the
  original exam file name, `topic` is the administration, and `original_id`
  is the position within that source's extraction.
- `ministerio_cultura_2023-2024_*` and `ministerio_cultura_2020-2022_modelo_a_*`:
  `{exam, sections: [{section, questions: [{number, question, options{A..D}, correct_answer}]}]}`.
- `ministerio_cultura_2020-2022_modelo_b.json`: list of
  `{id, question, options{A..D}, answer}`.

## Known issues

- Answers were extracted by scripts from the answer keys or highlighted
  documents and have not been re-checked against the official keys here,
  except for the 2020-2022 Modelo A file.
- The sources `C.2023-Examen Ayudantes archivos bibliotecas y museos` and
  `C.2026-Examen-Ayudantes-Bibliotecas-Comunidad-Madrid-2026` share 75 of
  their 85 questions word for word. One of the two is probably mislabelled.
- The combined file has no official question numbers, model or exam date.
- Reuse terms for these administrations are in [`../reuse_terms.md`](../reuse_terms.md).
  Comunidad de Madrid and Ayuntamiento de Madrid terms were not confirmed to
  cover exam papers.

## Left out on purpose

Text for these stays out of the repo; counts and IDs are in
[`../student_exam_sources.md`](../student_exam_sources.md).

- Laura IMED bank, 1,939 records: academy tests for enrolled students.
- Maria social-work bank, 663 records (and the older 477-record version):
  academy preparation material.
- CCSE-style bank, 279 records: nationality-test material, not an oposición,
  source unknown.
- Laura veterinary bank, 817 records: no source recorded.
