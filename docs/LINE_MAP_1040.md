# Form 1040 line map, tax years 2023–2025

Why this exists: the fact vocabulary is concept-based (`adjusted_gross_income`, not "line 11")
precisely because the IRS renumbers. Extraction is told to map by label and quote the line it
saw. This table records the moves the research agent verified so reviewers know what a quoted
line number should look like for each year. Source: `side_1040_line_map.md` (research pack).

| Concept (fact name) | TY2023 | TY2024 | TY2025 |
|---|---|---|---|
| wages | 1a / 1z | 1a / 1z | 1a / 1z |
| taxable_interest | 2b | 2b | 2b |
| ordinary_dividends / qualified_dividends | 3b / 3a | 3b / 3a | 3b / 3a |
| capital_gain_loss | 7 | 7 | **7a** |
| total_income | 9 | 9 | 9 |
| adjustments_to_income | 10 | 10 | 10 |
| adjusted_gross_income | 11 | 11 | **11a / 11b** |
| standard_or_itemized_deduction | 12 | 12 | **12e** |
| qbi_deduction | 13 | 13 | **13a** |
| Schedule 1-A deduction (new) | – | – | **13b** |
| taxable_income | 15 | 15 | 15 |
| total_tax | 24 | 24 | 24 |
| federal_withholding | 25d | 25d | 25d |
| estimated_payments | 26 | 26 | 26 |
| earned income credit | 27 | 27 | **27a** |
| line 30 | (reserved) | (reserved) | **refundable adoption credit** |
| refund / amount_owed | 35a / 37 | 35a / 37 | 35a / 37 |

Notes
- 2023 → 2024: core fact lines stable.
- TY2025 renumbering is baked into `EXTRACTION_INSTRUCTIONS` in `app/ingest/extractor.py`.
- Schedule 1-A (line 13b) is a new deduction line; add a `schedule_1a_deduction` fact when the
  first TY2025 returns arrive and it proves useful for planning.
- Re-run the line-map research each January and update this table before the season.
