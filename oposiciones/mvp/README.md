# Tesón MVP

A static web app with no compilation step. Netlify runs the repository validation gate before
publishing the folder; other static hosts must run `npm run check:production` explicitly.

| File | What it is |
|---|---|
| `index.html`, `styles.css`, `app.js` | The app |
| `questions.js` | Question bank (`window.TESON_BANK`). Add temas here, or in more files loaded from `index.html` |
| `tags.js` | Areas, concepts, typical confusions per wrong option, difficulty seeds, experiment control forms |
| `esquemas.js` | Visual comparison tables shown in explanations |
| `config.js` | Supabase URL + anon key (public by design) + contact email. Empty = no data sent |
| `schema.sql` | Run once in Supabase: an insert-only `events` table + review views |
| `privacidad.html`, `aviso-legal.html`, `legal.js`, `legal.css` | Legal pages populated from `config.js`; missing identity is shown as a deployment blocker |
| `review.json`, `REVIEW.md` | Per-question human-review gate |
| `manifest.webmanifest`, `icon.svg` | Install-to-home-screen |

Local run: `python3 -m http.server` in this folder, then open http://localhost:8000.

Preview build for claude.ai: `python3 ../tools/build_preview.py <out_dir>`.

Repository checks:

- `npm test` validates the bank, provenance, consent protections and legal-page gates.
- `npm run test:e2e` runs the refusal → quiz → explanation → disabled-report flow in headless Chrome.
- `npm run check:production` additionally requires real legal/Supabase configuration and
  human approval of all 82 questions. It is expected to fail until those release gates are met.

Event types: `consent_given`, `session_start`, `onboarding_completed`, `test_started`,
`question_answered`, `test_completed`, `test_abandoned`, `explanation_rated`,
`boe_link_clicked`, `question_reported`, `feedback_sent`, `nps_submitted`, `tema_interest`,
`progress_wiped`, `exp_assigned`, `checkpoint_completed`, `checkpoint_skipped`, `esquema_viewed`, `test_paused`.

Behavioral events are consent-only. `question_reported` and `feedback_sent` are explicit
user-request events and are sent without the analytics identifier. If the legal or Supabase
configuration is incomplete, their controls are disabled rather than claiming an unsent success.

Adaptive logic and the experiment are documented in `../14_ADAPTIVE_PRACTICE.md`.
If you already ran `schema.sql`, run it again: it's idempotent and adds the v0.2 views.
