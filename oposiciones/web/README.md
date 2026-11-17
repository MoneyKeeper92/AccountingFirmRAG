# Tesón website (Astro)

Marketing and SEO site for `tesonopos.es`. Static Astro build, deployed on Netlify with **base directory
`oposiciones/web`** (it uses `oposiciones/web/netlify.toml`). The practice app in `../mvp/` is a separate
Netlify site.

| Command | What it does |
|---|---|
| `npm install` | Install (Node ≥ 22.23.4, see `.nvmrc`) |
| `npm run dev` | Local dev server at http://localhost:4321 |
| `npm run build` | Build to `dist/`, then `scripts/check-site.mjs` checks titles, descriptions, internal links, no third-party requests, and noindex while pre-launch |

**Settings live in `src/site.ts`:**
- contact email
- app URL. While it's empty, the buttons go to `/beta/`, which asks for a place by email.
- legal owner details
- `launch.public`

While `launch.public` is false, every page is `noindex` and `robots.txt` disallows crawling. Setting it to true with any legal field empty fails the build.

**Privacy by design:**
- no cookies and no analytics
- fonts are self-hosted (`@fontsource`), so there are no Google requests
- the contact is a `mailto:` link, not a form

**Pages:**
- `/`
- `/beta/`
- `/auxiliar-administrativo-estado/` and `/auxiliar-administrativo-estado/convocatoria-2026/`
- `/herramientas/calculadora-nota-oposiciones/`
- `/metodologia/`, `/impugnaciones/`, `/sobre-teson/`, `/contacto/`
- `/aviso-legal/`, `/privacidad/`, `/cookies/`
- 404

The copy follows `../05_WEBSITE.md`, trimmed to what the private beta really offers today.
