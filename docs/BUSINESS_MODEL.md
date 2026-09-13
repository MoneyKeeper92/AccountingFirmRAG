# Business model notes

## The offer

"A private research assistant for your firm's own archive, installed in your environment,
maintained by a person you talk to every week."

Three components, priced separately so the firm sees where the money goes:

| Component | What it is | Pricing idea |
|---|---|---|
| Onboarding | Inventory, format conversion, bulk ingestion, extraction tuning, security setup | One-time, scaled by number of clients and years (e.g. $3–8k for a 5–15 person firm) |
| Platform | Hosting, updates, model upgrades, monitoring, backups, model API costs | Monthly per firm, tiered by client count rather than seats (e.g. $400–1,500/month). Research puts the underlying ZDR model + OCR + infra cost at roughly $180–230 per firm per month at steady state, so the platform line carries margin from the first firm |
| Fractional AI lead | The weekly hour: review usage, tune, train staff, evaluate new models, extend to new document types | Monthly retainer (e.g. $1–3k/month), can be dropped after year one |

Price per firm, not per user: the bundled practice-management AI tiers the same firms already
see are $59–149 per user per month, and Copilot is $30 per user. A per-firm price positions
this as an add-on to those tools rather than a replacement (see `docs/RESEARCH_FINDINGS.md`).

## Price ladder and the value model (from Prompt 11)

Value anchors the research found: partner time about $275/hour, associate about $127; document
chasing costs 1 to 3.5 hours per return. For an 8-person firm filing about 800 returns, a blended
$125/hour and conservative hours saved put the value on the order of $15k a year, which supports
a price around one seventh of that. Treat the figure as a model until the pilot measures it.

Adjacent price points the same firms already see: SmartRequestAI $12.50 per return, Canopy
$74–149 per user plus about $34 per client for tax AI, SafeSend often $13–17 per return.

| Tier | For | Price idea | Includes |
|---|---|---|---|
| Archive | Up to 300 clients | $350–500 / month | Archive, search with citations, planning screens, Verify, one connector |
| Season | Up to 800 clients | $700–1,100 / month | Everything above plus request lists, organizer, reminders, transcript reconciliation, all connectors |
| Practice | Larger or multi-office | $1,500+ / month, quoted | In-tenant deployment, SSO, SOC 2 evidence pack, priority model upgrades |
| Onboarding | All tiers | $3–8k one-time | Inventory, bulk load, extraction tuning, security setup |
| Fractional AI lead | Optional | $1–3k / month | The weekly hour |

Per-firm pricing keeps this an add-on under the per-user practice-management AI tiers. Model and
OCR cost per firm is roughly $30–80 a month at the margin (see `docs/RESEARCH_FINDINGS.md`).

## Why a small firm buys this instead of waiting for their DMS vendor

- Their data is spread across a file server, a DMS, tax software, and email. The vendor's AI
  only sees its own silo. This sees everything they choose to upload.
- Tax-planning screens across years (estimates, entity choice, reasonable compensation, basis)
  and request lists derived from the prior return are not something a document management
  vendor builds. Audit and review work is the natural second product once the tax version is
  proven.
- Vendor independence: model choice is a config line; if a better or cheaper model appears they
  get it next quarter.
- A human who knows their practice and shows up every week. Small firms buy relationships.

## Positioning

- Not "AI does the return". That is a liability magnet and the big vendors' territory.
- "Never dig through folders again, and walk into planning meetings with last year already
  summarised." Time saved for seniors and partners, whose hours are the scarce resource.

## Go-to-market

1. Pilot with the family practice; produce a one-page case study with time-saved numbers.
2. State CPA society affinity programmes (example: WICPA, $3k minimum ad spend), technology
   committees, peer-review networks. Partners trust other partners.
3. Conferences with the case study in hand: AICPA ENGAGE (June 8–11 2026), Scaling New Heights
   (June 14–17 2026), Digital CPA (December 6–9 2026).
4. CPA-focused IT providers (Rightworks, Cetrom, Boomer Consulting network); they get asked about
   AI constantly and have nothing to sell.
5. Tax API partner programmes last: Intuit tiers carry fees; Thomson Reuters and CCH are often
   closed or partner-gated; the Microsoft marketplace takes about 3%.
4. Later: the same product for law firms (matters instead of clients, pleadings and contracts
   instead of returns), wealth managers, and insurance agencies. The canonical-record idea
   transfers; the fact vocabulary and tools change.

## Expansion features (ordered by likely demand)

1. Watched-folder / DMS integration so nothing needs manual upload.
2. "Verify facts" screen with tick marks and reviewer sign-off.
3. Planning memo generator: drafts the analytical review section from the risk screen and
   prior-year memo, with citations, for the partner to edit.
4. Engagement-start brief: automatic "what to know before opening this file" when a return is
   assigned.
5. Firm-wide analytics: which clients have covenant issues, which are S-corp election candidates,
   which have not sent documents yet.
6. Multi-firm hosting with per-tenant isolation, once three or more firms are live.

## SOC 2: when, not whether

Working hypothesis to verify with Prompt 6 in `docs/RESEARCH_BOT_PROMPTS.md`:

- Firms of 3–30 staff rarely ask for a SOC 2 report. They ask "where is our data, who can see
  it, and can my IT person look at it?" A completed security questionnaire, a third-party
  penetration test letter, cyber insurance, and in-tenant deployment usually answer that.
- Firms above roughly 30–50 staff, firms with an outsourced IT provider that runs vendor
  reviews, and firms with peer-review or PCAOB exposure will ask, and a Type II is the
  expected answer.
- Research result (Prompt 6): not legally required by the FTC Safeguards Rule, but the sales
  gate from mid-market up and effectively mandatory at 75+ staff or PCAOB-adjacent firms.
  Recommended path: Type I around month 6, Type II around month 18, roughly $45–85k cash over
  24 months. Trigger: three or more mid-market opportunities or about $150–250k ARR.
- Until then: run the controls from day one (SSO, MDM, logging, policies, vendor list) so the
  audit is cheap later, and answer small-firm diligence with the data-handling sheet, a
  penetration-test letter, cyber insurance and the in-tenant deployment option.

## What could kill it

- A vendor incident (any AI vendor, not necessarily yours) that makes firms freeze AI adoption.
  Mitigation: in-tenant inference and self-hosted embeddings as the default pitch.
- Incumbents bundling "good enough" AI search for free. Mitigation: depth and service.
- Under-pricing the onboarding work. It is the hardest part; charge for it.
