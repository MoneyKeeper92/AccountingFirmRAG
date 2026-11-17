# Question-bank review gate

The 82 questions are Tesón-authored from the consolidated Spanish Constitution. Automated
checks verify structure, provenance fields, source URLs and internal answer/explanation shape;
they do not replace legal/content review.

Before changing `TESON_BANK.status` to `revisado_humano`:

1. A named reviewer opens every question in study mode and the linked BOE source.
2. They verify the stem, four options, key, explanation, each wrong-option explanation, trap
   and source destination.
3. They update that question in `review.json` from `pending` to `approved`, adding a short note
   for any correction made.
4. Once all 82 ledger entries are approved, change the uniform `q.reviewStatus` assignment in
   `questions.js` to `approved`, set `TESON_BANK.status` to `revisado_humano`, and fill
   `reviewer` and `completedAt` in both `review.json` and `TESON_BANK.humanReview`.
5. Run `npm run check:production`. It must reject missing or partial review records.

Do not approve a range by sampling. Every ID from CE-001 through CE-082 must be approved.
