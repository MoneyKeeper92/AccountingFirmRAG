# Business model notes

## The offer

"A private research assistant for your firm's own archive, installed in your environment,
maintained by a person you talk to every week."

Three components, priced separately so the firm sees where the money goes:

| Component | What it is | Pricing idea |
|---|---|---|
| Onboarding | Inventory, format conversion, bulk ingestion, extraction tuning, security setup | One-time, scaled by number of clients and years (e.g. $3–8k for a 5–15 person firm) |
| Platform | Hosting, updates, model upgrades, monitoring, backups | Monthly per firm, tiered by staff seats (e.g. $400–1,500/month) |
| Fractional AI lead | The weekly hour: review usage, tune, train staff, evaluate new models, extend to new document types | Monthly retainer (e.g. $1–3k/month), can be dropped after year one |

Model API costs are passed through or bundled; they are small (see `docs/MODEL_RECOMMENDATIONS.md`).

## Why a small firm buys this instead of waiting for their DMS vendor

- Their data is spread across a file server, a DMS, tax software, and email. The vendor's AI
  only sees its own silo. This sees everything they choose to upload.
- Forecasting and risk screens across years and across tax + audit are not something a document
  management vendor builds.
- Vendor independence: model choice is a config line; if a better or cheaper model appears they
  get it next quarter.
- A human who knows their practice and shows up every week. Small firms buy relationships.

## Positioning

- Not "AI does the return". That is a liability magnet and the big vendors' territory.
- "Never dig through folders again, and walk into planning meetings with last year already
  summarised." Time saved for seniors and partners, whose hours are the scarce resource.

## Go-to-market

1. Pilot with the family practice; produce a one-page case study with time-saved numbers.
2. Local CPA society chapters, state society technology committees, peer-review networks.
   Partners trust other partners.
3. Referrals from IT MSPs that serve accounting firms; they get asked about AI constantly and
   have nothing to sell.
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
- Ballpark cost for a company this size: a compliance-automation platform at roughly $8–20k a
  year plus an auditor at roughly $8–20k for a Type I and $15–40k for a Type II, plus a
  penetration test at $5–15k and real founder hours. Type I is reachable in two to three months;
  Type II needs a three- to twelve-month observation window on top.
- Suggested path: run the controls from day one (SSO, MDM, logging, policies, vendor list) so a
  later audit is cheap; start Type I when the first prospect over 30 staff or the first formal
  procurement questionnaire appears; move to Type II once three or more firms are paying. A
  single mid-size firm at typical pricing covers the annual cost, which is why it is a timing
  question rather than a yes/no question.

## What could kill it

- A vendor incident (any AI vendor, not necessarily yours) that makes firms freeze AI adoption.
  Mitigation: in-tenant inference and self-hosted embeddings as the default pitch.
- Incumbents bundling "good enough" AI search for free. Mitigation: depth and service.
- Under-pricing the onboarding work. It is the hardest part; charge for it.
