# Evaluation

Run before and after any model profile change, and weekly during the pilot with the questions
staff actually asked.

## Harness

`scripts/run_eval.py` seeds a temporary archive from `sample_data/` (or points at an existing
database with `--db`) and runs `evals/questions.jsonl`:

- **question rows** score citation recall (expected files among the retrieved sources), tool
  use (expected tools called), and answer phrases (expected wording present);
- **facts rows** check extracted values against expected numbers per year.

Write results with `--out evals/results-<profile>.json` and diff two runs. The offline profile
scores about 0.9 on the seed set; a real model profile should reach 1.0 on it before it is
trusted with a firm's questions.

## Growing the set

Add ten to twenty real questions per client type from the audit log, with the file that
answered them and the number a partner confirmed. Keep expected phrases short and factual
("168,000", "Reasonable compensation"), not prose.

## Extraction accuracy on scans (research 14I)

Usable labelled data for measuring OCR plus extraction: NIST Special Database 2 (1988 1040
packages, free), the Kaggle synthetic W-2 set (CC0) and its Hugging Face mirror, and the
Symage coherent 1040 set (gated, no redistribution). Purchasable: SymageDocs W-2 and 1040
sets. There is no solid public labelled K-1 or 1099 corpus; build a small internal one from
the pilot firm's redacted scans with partner-confirmed values, and keep it out of the repo.
