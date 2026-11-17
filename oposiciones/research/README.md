# Tesón constitutional-question research

This folder is the canonical handoff for any AI or person continuing the
Spanish *oposiciones* Constitution-law question-bank work.

## Start here

1. [`summary.md`](summary.md) — findings, legal risk categories, coverage gaps,
   and recommended ingestion order.
2. [`student_audit_addendum.md`](student_audit_addendum.md) — Maria and Laura
   bank conclusions.
3. [`student_exam_sources.md`](student_exam_sources.md) — detailed provenance,
   active/inactive files, overlap analysis, and safe-use rules.
4. [`constitution_question_map.csv`](constitution_question_map.csv) — verified
   official exam/question-number mappings.
5. [`student_question_map.csv`](student_question_map.csv) — record-level IDs
   for the Maria and Laura constitutional subsets, without reproducing stems.

## Structured deliverables

- [`official_exams.csv`](official_exams.csv): 52 verified or explicitly
  qualified official source records.
- [`constitution_question_map.csv`](constitution_question_map.csv): 45
  official constitutional-question mappings.
- [`reuse_terms.md`](reuse_terms.md): source-by-source reuse clauses and
  operational conclusions.
- [`open_datasets.csv`](open_datasets.csv) and
  [`open_datasets_detailed.csv`](open_datasets_detailed.csv): licence and
  provenance review.
- [`market_banks.csv`](market_banks.csv): public competitor metadata only.
- [`syllabi.csv`](syllabi.csv): only syllabus facts supported by the research.
- [`unopened_urls.md`](unopened_urls.md): broken, gated, or unresolved sources.
- [`notes/`](notes/): source-linked research notes by exam family.
- [`question_banks/`](question_banks/): question text as JSON, official exam
  papers only (1,940 archive and library records from Laura's bank).
- [`official_exams_pdfs/`](official_exams_pdfs/): 49 of the 52 PDFs listed in
  `official_exams.csv`; `official_exams_downloads.csv` maps lines to files.
- [`BRIEF_existing_questions.md`](BRIEF_existing_questions.md): governing
  research brief and copyright constraints.

## Existing local-bank conclusions

- Tesón has 82 original Constitution questions (`CE-001`–`CE-082`) in
  `oposiciones/mvp/questions.js`; they remain pending human review.
- Maria's active bank contains 64 constitutional records out of 663. Its
  separate inactive CCSE-style bank contains 86 out of 279.
- Laura's active biblioteca bank contains 53 constitutional records out of
  1,940.
- Laura's historical aggregate contains 515 constitutional records: 39 mapped
  to identified official exams and 476 from private/student/academy material.
- The inactive Laura CCSE files are exact copies of Maria's 279-record set and
  must not be counted twice.

## Non-negotiable provenance rule

Public access is not permission to republish. Keep commercial, academy,
student, UGC, and uncertain-source question text **metadata-only** unless a
compatible licence or written permission is documented. Preserve source,
question number, final answer-key status, reuse terms, and review date for
every item considered for ingestion.
