# Tesón MVP

A static web app with no build step. Deploy the folder as-is to any static host (Cloudflare
Pages, Netlify, GitHub Pages).

| File | What it is |
|---|---|
| `index.html`, `styles.css`, `app.js` | The app |
| `questions.js` | Question bank (`window.TESON_BANK`). Add temas here, or in more files loaded from `index.html` |
| `config.js` | Supabase URL + anon key (public by design) + contact email. Empty = no data sent |
| `schema.sql` | Run once in Supabase: an insert-only `events` table + review views |
| `privacidad.html`, `aviso-legal.html`, `legal.css` | Legal pages (fill in the yellow placeholders) |
| `manifest.webmanifest`, `icon.svg` | Install-to-home-screen |

Local run: `python3 -m http.server` in this folder, then open http://localhost:8000.

Preview build for claude.ai: `python3 ../tools/build_preview.py <out_dir>`.

Event types: `consent_given`, `session_start`, `onboarding_completed`, `test_started`,
`question_answered`, `test_completed`, `test_abandoned`, `explanation_rated`,
`boe_link_clicked`, `question_reported`, `feedback_sent`, `nps_submitted`, `tema_interest`,
`progress_wiped`.
