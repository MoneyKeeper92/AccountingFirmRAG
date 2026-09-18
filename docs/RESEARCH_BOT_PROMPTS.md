# Instructions for an AI research agent: competitive landscape

Paste the block below into a research-capable agent (Claude with web search, a Managed Agent
with web tools, Perplexity, or a deep-research mode). It is written for accounting first; the
second section shows how to re-target it to law firms or any other profession by swapping a
few lines.

---

## Prompt 1: Accounting-firm AI archive / knowledge tools

```
You are a market research analyst. Your task is to map every product that lets an accounting,
tax or audit firm search, question, or analyse its own client records (tax returns, financial
statements, audit files, working papers) using AI, and to report what users say about them.

SCOPE
- Include: AI features inside practice-management and document-management suites used by
  accounting firms; standalone "chat with your documents" tools marketed to accountants; audit
  analytics platforms with natural-language query; tax research assistants that also index the
  firm's own files; vertical RAG startups targeting CPA firms; open-source projects aimed at
  this use case.
- Exclude: general-purpose chatbots with no firm-archive feature; bookkeeping automation that
  does not answer questions about historical records; consumer tax software.
- Geography: United States first, then Canada, United Kingdom, Australia. Note where a product
  is region-locked.

START LIST (verify each, then expand)
Thomson Reuters (CoCounsel, Checkpoint Edge with AI, GoFileRoom, Practice CS), Wolters Kluwer
(CCH Axcess with AI, CCH iFirm, TeamMate), Intuit (ProConnect / Lacerte / ProSeries AI, Intuit
Assist for accountants), Karbon AI, Canopy, TaxDome, Financial Cents, Keeper, Caseware (Caseware
AiDA, Cloud), MindBridge, DataSnipper, Fieldguide, AuditBoard, Inflo, Validis, Black Ore,
Blue J (tax research), Truewind, Basis, Docyt, Digits, Puzzle, Copilot for Microsoft 365 in
accounting firms, Harvey (check for accounting/tax use), Materia, Numeric, Bluecopa, and any
YC / a16z / Bessemer-backed "AI for accountants" startup from the last 24 months.

FOR EACH PRODUCT, RECORD
1. Vendor, product name, URL, founding year or feature launch date, target firm size.
2. Core capability: does it (a) index the firm's own historical client files, (b) answer
   natural-language questions with citations, (c) extract structured data from returns and
   statements, (d) do cross-year comparison or forecasting, (e) do risk / analytical review,
   (f) let clients upload directly, (g) integrate with tax software / DMS / QuickBooks / Xero,
   (h) work on scanned documents (OCR).
3. Architecture and data handling, as stated publicly: which LLM vendor(s), zero data retention
   or training opt-out, data residency, SOC 2 / ISO 27001 status, on-premises or single-tenant
   options, whether they say anything about IRC §7216 or GLBA.
4. Pricing: list prices, per-seat vs per-firm, minimums, whether AI features are an add-on.
5. Evidence of traction: customer counts, notable firms, funding, partnerships with state CPA
   societies or the AICPA.
6. User feedback: summarise reviews from G2, Capterra, Reddit (r/Accounting, r/taxpros,
   r/CPA), the TaxProTalk forum, Accounting Today, CPA Practice Advisor, Going Concern, LinkedIn
   posts by practitioners, YouTube demos. For each product give three recurring praises and
   three recurring complaints with a source link and date. Distinguish verified-user reviews
   from vendor marketing.
7. Gaps: what users ask for that the product does not do.

ALSO ANSWER
- Which products actually let a partner ask "what were client X's revenue and net income over
  the last three years and which areas looked risky" against the firm's own files, versus only
  searching a public tax-law corpus?
- Which vendors offer zero-data-retention with their AI provider, and how do they describe it?
- What do practitioners say about trust, hallucination, and whether they would upload client
  returns to a cloud AI tool? Quote them.
- What price points are firms with 3–25 staff actually paying for AI add-ons?
- Which open-source projects (GitHub) target this use case, and how active are they?

METHOD
- Use primary sources first: vendor documentation, security pages, pricing pages, release
  notes. Then reviews and forums. Then news.
- For every factual claim provide a URL and the date you accessed it. Mark anything you could
  not verify as "unverified".
- Do not rely on a single review site. Cross-check at least two sources per product for
  feedback.
- If a product has been discontinued or acquired, say so and by whom.

OUTPUT
1. A comparison table (product × capabilities a–h × data-handling × price band × firm-size fit).
2. A one-paragraph profile per product with feedback quotes and sources.
3. A "white space" section: capabilities nobody offers well, complaints nobody has fixed, and
   segments (firm size, specialty, geography) that are under-served.
4. A list of the 20 most useful source URLs.
5. Confidence notes: where the market is moving fast and the findings may be stale within months.
```

---

## Prompt 2: Re-targeting the same research to another profession

Replace the SCOPE, START LIST, and domain-specific questions. Example for law firms:

```
[Same role and method as above.]

SCOPE: products that let a law firm search, question or analyse its own matter files
(pleadings, contracts, discovery, memos, billing narratives) with AI. Include DMS-embedded AI
(iManage, NetDocuments), legal research tools that also index firm files, contract-analysis
platforms, and vertical legal RAG startups.

START LIST: Harvey, CoCounsel (Thomson Reuters), Lexis+ AI / Protégé, iManage Ask / Insight+,
NetDocuments ndMAX, Spellbook, Luminance, Robin AI, Kira, Everlaw AI, Relativity aiR, Clio
Duo, Legora, Hebbia, DeepJudge, Paxton, Alexi, Casetext legacy, and recent YC/a16z legal-AI
startups.

DOMAIN QUESTIONS: attorney-client privilege and work-product handling; state bar ethics opinions
on generative AI (ABA Formal Opinion 512 and state equivalents); conflict-check integration;
matter-level access control; whether tools support citation verification against primary law.

FEEDBACK SOURCES: G2, Capterra, r/Lawyertalk, r/LawFirm, Above the Law, Artificial Lawyer,
Legaltech News, LawSites (Bob Ambrogi), ILTA surveys, Legal IT Insider.
```

The same substitution works for wealth management (client files, IPS documents, account
statements; regulators FINRA/SEC), insurance brokers (policies, claims), architecture and
engineering firms (project records), and medical practices (with HIPAA replacing §7216). For
each: name the archive, name the regulator and the confidentiality rule, name the incumbent
DMS/practice-management vendors, name the forums where practitioners complain.

---

## Prompt 3: Where accounting firms keep their documents, and how to get them out

Run this before designing connectors. It answers two questions: what storage systems firms
actually use (by firm size), and for each one, the practical ways to extract documents in bulk
and keep new documents flowing.

```
You are a solutions engineer researching document storage in accounting, tax and audit firms so
that an integration team can plan how to extract documents in bulk and keep new documents
synchronised. Cover the United States first, then Canada, the UK and Australia.

PART A - WHERE DOCUMENTS LIVE
For each of these firm segments - solo/1-3 staff, 4-15 staff, 16-75 staff, 75+ staff - identify
the most common storage systems and, where any survey or vendor data exists, the approximate
share of firms using each. Categories to cover:
1. Plain file shares: Windows file server / NAS with a folder-per-client convention; what the
   typical folder structure looks like (client / year / engagement type).
2. General cloud drives: SharePoint / OneDrive, Google Drive, Dropbox, Box, Egnyte.
3. Accounting-specific document management systems: CCH Axcess Document, CCH ProSystem fx
   Document, Thomson Reuters GoFileRoom, FileCabinet CS, Onvio Documents, Doc.It, SmartVault,
   SuiteFiles, Virtual Cabinet, iChannel, IRIS, Karbon, Canopy, TaxDome, Financial Cents,
   Jetpack Workflow, Client Hub, Mango.
4. Client portals and secure file exchange used as de facto storage: ShareFile, SmartVault,
   SafeSend, Liscio, TaxCaddy, Suralink, Intuit Link.
5. Documents locked inside application binders: tax software (UltraTax, Lacerte, ProSeries,
   Drake, CCH Axcess Tax, ProConnect, TaxAct Pro, ATX), audit engagement software (CaseWare
   Working Papers and Cloud, CCH ProSystem fx Engagement, AdvanceFlow, Thomson Reuters
   Engagement Manager, Inflo, Suralink), bookkeeping platforms (QuickBooks Desktop/Online, Xero,
   Sage) with attached documents.
6. Email: attachments never filed anywhere else (Outlook/Exchange, Gmail).
7. Paper and scanned images: how common scan-only archives still are, typical scanners and
   OCR habits (Fujitsu ScanSnap, Adobe Acrobat OCR).
Sources: AICPA PCPS / CPA.com technology surveys, Accounting Today "Year Ahead" and top-firms
technology surveys, CPA Practice Advisor product reviews and reader surveys, Journal of
Accountancy technology roundups, Wolters Kluwer and Thomson Reuters customer counts, Reddit
r/Accounting and r/taxpros threads about file organisation, TaxProTalk, vendor case studies,
IT-provider (MSP) blogs that specialise in CPA firms, Karbon/Canopy/TaxDome practice reports.
For every figure give the source, its date, and the sample it came from.

PART B - HOW TO EXTRACT FROM EACH
For every storage system in Part A, document the realistic extraction paths, in this order of
preference: (1) supported API or SDK, (2) supported bulk export or sync client, (3) admin-side
migration tooling or vendor-assisted export, (4) filesystem or database-level access,
(5) manual print-to-PDF or download. For each path record:
- Authentication model (OAuth app registration, API key, service account, on-prem agent).
- Whether metadata comes with the file: client identifier, tax year, document type, engagement,
  version/final flag, last-modified, who filed it.
- Whether the API supports change notifications / webhooks / delta queries so new documents can
  be picked up automatically, and the polling alternative if not.
- Rate limits, file-size limits, and any licensing or partner-program requirement to get API
  access (name the program and its cost if known).
- Known pain points reported by integrators or users.
- For application binders (tax and audit software): how to batch-export the filed return or
  final statements as text-layer PDF, and whether a structured data export exists (e.g. tax
  return data reports, trial balance exports, CaseWare export formats).
- For email: the practical route (Microsoft Graph / Gmail API, mailbox rules, journaling) and
  the privacy considerations.
- For scans: which OCR options integrators actually use on tax forms and financial statements,
  and reported accuracy.
Specifically confirm for each of Microsoft Graph (SharePoint/OneDrive), Google Drive API, Box,
Dropbox, Egnyte, ShareFile, SmartVault, GoFileRoom, CCH Axcess (Document and Tax), Onvio,
Karbon, Canopy, TaxDome, CaseWare Cloud, QuickBooks Online and Xero: does a documented API for
listing and downloading documents exist today, and where is the documentation?

PART C - RECOMMENDATIONS
1. Rank the storage systems by (frequency among 3-30 staff firms) x (ease of extraction).
2. For the top five, sketch a connector: bulk backfill approach, incremental sync approach,
   how client and year would be inferred, and expected effort in engineer-days.
3. Identify the systems where the only realistic route is a watched folder or manual export,
   and say how firms using them typically cope.
4. Flag any legal or contractual constraint on extracting documents from a vendor system
   (terms of service that forbid bulk export, data egress fees, partner agreements).

METHOD AND OUTPUT
- Primary sources (vendor API docs, developer portals, help centres) before forum evidence.
- Provide a URL and access date for every claim; mark unverified items.
- Output: (1) a table of storage systems x firm size x adoption evidence; (2) a table of
  extraction paths per system with the fields above; (3) the ranked recommendations; (4) the
  30 most useful URLs.
```

## Prompt 4: Features worth borrowing from existing systems

Run this with the current feature list of this software so the agent can score gaps. Update the
"WHAT WE HAVE" block each quarter.

```
You are a product manager doing feature discovery for a private AI assistant that lets a small
accounting / tax / audit firm search and analyse its own client archive. Your job is to find
features in existing products - direct competitors and adjacent tools - that our users would
value and that we should consider integrating or building, and to say how each one works in
enough detail that an engineer could scope it.

WHAT WE HAVE TODAY
- Upload or connect a firm's client files (PDF, Excel, CSV, JSON, text); each becomes a
  standard record with document type, tax year, summary, key figures with source lines, and
  risk flags.
- Plain-English questions scoped to one client, answered with citations that open the source
  file at the cited page.
- Deterministic forecasting (trend, CAGR), ratio analysis and analytical-review flags exposed
  as tools the model must use for numbers.
- Tax-season request lists: read last year's return and the folder, draft the document request
  email, match returned attachments to items, keep an "items pending" list per client.
- Copy or pointer storage of originals; swappable models by configuration; audit log.

WHERE TO LOOK (verify, then expand)
Client document collection and organizers: TaxCaddy, SafeSend (Suite, Returns, Gather),
Liscio, Suralink, Canopy client requests, TaxDome organizers and pipelines, Karbon client
tasks and automatic reminders, SmartVault request lists, Intuit Link, Content Snare, Financial
Cents client tasks, Keeper client portal, Ignition.
Firm-archive AI and search: CCH Axcess with AI, Thomson Reuters CoCounsel / GoFileRoom,
Karbon AI, Canopy AI, iManage Ask, NetDocuments ndMAX (legal, but the pattern transfers).
Tax and audit analytics: MindBridge, DataSnipper, Fieldguide, Inflo, Caseware AiDA, Blue J,
Black Ore, TaxPlanIQ, Corvee, Holistiplan (financial planning from a 1040).
Adjacent professions with mature equivalents: legal (Harvey, Clio Duo, Spellbook), wealth
management (Holistiplan, FP Alpha, Jump), medical (Abridge, Nuance DAX) for document intake and
summarisation patterns.

FOR EACH FEATURE YOU FIND, RECORD
1. Product, feature name, link to documentation or demo video, date.
2. What the user does and what they get - walk through it step by step from the screenshots or
   video, including edge cases the vendor handles (client sends the wrong document, item no
   longer applies, multiple people at the client, reminders and escalation cadence).
3. The mechanism, as far as it is public: does it use OCR / classification to recognise a
   document type on arrival, does it pre-fill from last year, does it read tax software data,
   does it integrate with email, SMS, e-signature, payment collection.
4. Evidence users like it or complain about it: quotes with source and date from G2, Capterra,
   r/taxpros, r/Accounting, TaxProTalk, vendor community forums, YouTube comments, LinkedIn.
5. Whether it is available via API or webhook so we could integrate rather than rebuild, and
   the vendor's partner terms if known.
6. Effort to build an equivalent inside our system: small (days), medium (weeks), large
   (months), with the reasoning.
7. Fit score 1-5 for a 3-30 staff firm, with one sentence of justification.

SPECIFIC QUESTIONS
- How do the best client-request tools decide what to ask for? Do any of them derive the list
  from the prior-year return automatically, and how accurate do users say that is?
- How do they recognise an incoming document and match it to the request (file name, OCR,
  form-type classifier, client tagging)? What happens to unmatched uploads?
- What reminder cadences and channels (email, SMS, portal push) do they use, and what do
  practitioners say actually gets clients to respond?
- Which products let the client answer questions inline (organizer-style yes/no) instead of
  only uploading files, and do firms find that useful or ignored?
- What review and sign-off flows exist for AI-extracted figures ("verify before use" screens,
  tick marks, confidence indicators, side-by-side source view)?
- Which planning or forecasting outputs (tax projections, entity-choice comparisons, ratio
  dashboards, industry benchmarks) do firms report using in client meetings?
- What do firms say they wish these tools did, that none of them do?

OUTPUT
1. A ranked backlog of 15-25 features: name, source product(s), fit score, build-vs-integrate
   recommendation, effort, one-paragraph rationale with evidence links.
2. A short "do not build" list: features competitors ship that users do not value, with the
   evidence.
3. For the top five, a one-page mini-spec: user story, screens, data needed, integration points
   with our existing pieces (request lists, archive, citations, audit log).
4. Source list with URLs and access dates; mark anything unverified.
```

## Prompt 5: Zero-retention model costs, and one account vs. one per client firm

```
You are researching AI vendor terms and pricing for a company that will run a private
document-assistant service for many small accounting firms. Client tax data will pass through
large-language-model and embedding APIs. Answer two questions with sources and dates.

QUESTION 1 - WHAT DOES ZERO DATA RETENTION (ZDR) ACTUALLY COST, PER VENDOR AND ROUTE?
For each of: Anthropic Claude API (direct), Anthropic models on Amazon Bedrock, Google Vertex AI
and Microsoft Foundry; OpenAI API (direct) and Azure OpenAI; Google Gemini API and Vertex;
Voyage AI, Cohere and OpenAI embeddings; and the main OCR services (Azure Document
Intelligence, AWS Textract, Google Document AI), record:
- The default retention period for API inputs and outputs, and whether data is used for
  training by default.
- How ZDR (or "no retention", "no logging", "abuse-monitoring opt-out") is obtained: self-serve
  setting, request form, sales conversation, enterprise agreement, minimum spend or commitment.
- Any price difference for ZDR: per-token uplift, platform fee, committed-use requirement,
  minimum annual contract. If the answer is "no extra charge", cite where the vendor says so.
- Which models are excluded from ZDR (some top-tier models require retention), and which
  features stop working under ZDR (prompt caching, batch, fine-tuning, sticky fallbacks,
  abuse monitoring exemptions).
- Where ZDR is granted: organisation level, workspace/project level, or per API key.
- Data residency options and whether they cost extra.
- The exact contractual documents: DPA, BAA, commercial terms, and whether a small company can
  sign them online.
Then build a cost model for our workload: per firm, about 300 clients x 8 years x 6 documents
x 8k tokens for one-time ingestion, plus 1,000 questions a month at ~15k input / 1.5k output
tokens each, plus embeddings. Show monthly cost per firm at list prices for the two or three
most realistic ZDR-capable configurations, and the fixed costs (minimums, platform fees) that
would be shared across firms.

QUESTION 2 - CAN WE HOLD ONE VENDOR ACCOUNT AND SERVE ALL CLIENT FIRMS, OR DOES EACH FIRM
NEED ITS OWN ZERO-RETENTION ARRANGEMENT?
Consider three structures and, for each, report what the vendor terms allow, what the
accounting-profession rules require, and what firms actually accept:
  A. One account in our name; all firms' traffic flows through it; we are the data processor
     and each firm signs a DPA with us; per-firm isolation via separate workspaces / projects /
     API keys / spend limits inside our account.
  B. One account per firm, in the firm's name, that we administer (firm is the customer of the
     model vendor; we hold delegated admin).
  C. In-tenant deployment: the firm's own Bedrock / Vertex / Foundry / Azure OpenAI in their
     cloud account; we deploy software into it.
For each structure answer:
- Do the vendor's terms permit reselling or acting as an intermediary for third-party data
  (check "customer", "end user", "reseller" and "service provider" language)? Is a partner or
  reseller programme required?
- Does ZDR granted to our organisation automatically cover all workspaces and keys, or must it
  be requested per workspace? Can a firm verify ZDR independently (attestation letter, console
  setting they can see)?
- Under IRC section 7216 and the related regulations (Treas. Reg. 301.7216-2 and -3), when a
  tax return preparer uses a third-party contractor for processing, what disclosures or
  consents are required, and does having a further sub-processor (the model vendor) change
  anything? Cite the regulation text and any IRS guidance or Revenue Procedure on contractors
  and "auxiliary services".
- Under the FTC Safeguards Rule (16 CFR Part 314) and typical CPA-firm written information
  security plans, what must the firm document about us and about our sub-processors?
- What do state boards of accountancy and the AICPA Code (ET section 1.700.040, use of third-
  party service providers) say about client consent and confidentiality when a service provider
  is used?
- Liability and insurance: which structure puts the model-vendor relationship (and breach
  liability) on us versus the firm, and what cyber / E&O cover do comparable vendors carry?
- What do firms and their IT providers say they prefer in practice? Look for procurement
  questionnaires, MSP blog posts, and forum threads (r/taxpros, r/Accounting, TaxProTalk,
  Spiceworks) on AI vendor due diligence.
Conclude with a recommendation: the structure to start with for firms of 3-30 staff, the
structure larger firms will insist on, the minimum paperwork per firm under each, and the
break-even firm count at which per-firm minimums or platform fees stop mattering.

METHOD AND OUTPUT
Primary sources first: vendor trust centres, pricing pages, terms of service, DPAs, the
Federal Register and eCFR for regulations, IRS.gov for guidance. Provide a URL and access date
for every claim; mark anything unverified or inferred. Output: (1) a vendor x route table of
retention defaults, how ZDR is obtained, cost, exclusions; (2) the per-firm cost model;
(3) a structure comparison table (A/B/C x legal, vendor terms, firm acceptance, our liability,
paperwork per firm); (4) the recommendation; (5) the 25 most useful URLs.
```

## Prompt 6: Is a SOC 2 report necessary to win accounting-firm clients, and is it worth it?

```
You are advising a two-person software and services company that will host client tax and
audit documents for small accounting firms (3-30 staff at first, then larger). Determine
whether, when and at what cost the company should obtain a SOC 2 report, and what to do in
the meantime.

PART A - DO BUYERS ACTUALLY REQUIRE IT?
- Survey what accounting firms ask vendors for during due diligence, by firm size: security
  questionnaire, SOC 2 Type I or Type II, ISO 27001, penetration test report, cyber insurance
  certificate, WISP alignment letter, references. Sources: AICPA PCPS vendor-management
  resources, state CPA society guidance, IT providers (MSPs) that serve CPA firms and publish
  vendor checklists, procurement questionnaires posted publicly, forum threads from
  practitioners and from vendors selling into this market (r/taxpros, r/Accounting, r/msp,
  TaxProTalk, LinkedIn, vendor community forums).
- Find what comparable vendors show on their trust pages and at what stage they obtained SOC 2:
  TaxDome, Canopy, Karbon, Liscio, SafeSend, TaxCaddy, SmartVault, Financial Cents, Keeper,
  Truewind, and any small AI-for-accountants startup with public history. Note whether they
  started with Type I, how long after founding, and whether they also hold ISO 27001.
- Look for evidence (case studies, founder interviews, sales-engineering write-ups) of deals
  won or lost on the presence or absence of a SOC 2 report in this segment.
- Identify what the FTC Safeguards Rule requires a CPA firm to obtain from a service provider
  in practice: does a SOC 2 satisfy the "assess service providers" requirement, and what do
  firms use when a vendor has none?
- For the larger-firm segment (75+ staff) and for firms with peer review or PCAOB exposure,
  determine whether SOC 2 Type II is effectively mandatory.

PART B - WHAT DOES IT COST AND HOW LONG DOES IT TAKE?
For a small company on a cloud platform (AWS / Azure / GCP) with a handful of systems:
- Auditor fees for SOC 2 Type I and Type II, from at least five audit firms that publish or
  quote small-company pricing (include the audit-firm networks that partner with compliance
  platforms). Distinguish first-year from renewal.
- Compliance-automation platforms (Vanta, Drata, Secureframe, Thoropass, Sprinto, Scrut,
  Oneleet, Delve and similar): annual price for a company of 2-10 people, what is included,
  whether a bundled auditor is offered and at what price.
- Typical timeline: readiness to Type I, observation window to Type II (3, 6 or 12 months),
  total calendar time from start to a shareable report.
- Hidden costs: penetration test, background checks, MDM and endpoint tooling, policy work,
  founder time in hours.
- Cheaper interim signals and their cost: a completed CAIQ or SIG Lite questionnaire, a
  third-party penetration test with letter of attestation, cyber insurance, a vendor security
  whitepaper, using the cloud provider's own SOC reports, running inside the firm's tenant so
  the firm's existing controls apply.

PART C - COST-BENEFIT
Using Part A and B, model three paths for the first 24 months: (1) no SOC 2, questionnaire
plus pen test plus in-tenant deployment; (2) Type I at month 6, Type II at month 18;
(3) Type II as early as possible. For each: total cost, founder hours, which segments become
sellable and when, expected effect on sales cycle length and price. State the assumptions
and the firm count or annual revenue at which SOC 2 pays for itself. Give a recommendation
with the trigger conditions that should move the company from one path to the next (e.g.
first prospect over 30 staff, first procurement questionnaire that asks, first request from
a firm's IT provider).

METHOD AND OUTPUT
Primary sources first (AICPA SOC 2 guidance, auditor and platform pricing pages, the
Safeguards Rule text at 16 CFR 314), then practitioner and vendor evidence. URL and access
date for every claim; mark anything unverified. Output: (1) a buyer-requirements table by
firm size with evidence; (2) a cost table (auditor, platform, hidden costs, timeline) with
quotes and dates; (3) the three-path model; (4) the recommendation and triggers; (5) the 20
most useful URLs.
```

## Prompts 7–13: the next research pack

Shorter briefs. Each follows the same method rules as Prompt 1 (primary sources first, URL and
access date on every claim, mark unverified items).

### Prompt 7: Structured data straight from the tax software (the best source of facts)

```
For each of UltraTax CS, Lacerte, ProSeries, ProConnect, Drake, CCH Axcess Tax, CCH ProSystem fx
Tax, ATX and TaxAct Professional: (a) how to batch-export as-filed returns as text-layer PDF for
many clients at once; (b) every structured export that exists - client data reports, proforma /
organizer exports, K-1 export, "tax return data" CSV or XML, and above all whether the e-file
(MeF) XML for a filed return can be exported or retrieved, since it is a complete machine-readable
copy of the return; (c) any API, SDK or partner programme, with cost and eligibility; (d) where
the software stores files on disk (folder layout, naming) for a watched-folder approach.
Then: document the IRS MeF schemas for 1040, 1065, 1120-S and 1120 (where to download the
current schema packages, how line items are named, how they change year to year) and produce a
line-name map for the last three tax years for the key lines we extract. Output: a table per
package, and a recommendation of the cheapest reliable path to structured prior-year data.
```

### Prompt 8: IRS transcripts and third-party data as a second source

```
Research how a firm can pull IRS data for a client into a system like ours: Transcript Delivery
System via e-Services (Form 8821 / 2848 requirements, what transcript types exist - wage and
income, account, return), the IRS Income Verification Express Service, and third-party
transcript tools (Canopy Transcripts, Tax Help Software, THS, IRS Solutions, Pitbulltax). For
each: access requirements, cost, format (PDF vs structured), rate limits, automation options,
and terms on storing the data. Also cover Intuit Link / broker aggregators for 1099 data and
QuickBooks / Xero APIs for books. Recommend which sources are worth wiring in and in what order.
```

### Prompt 9: OCR and extraction accuracy on scanned tax forms

```
Compare Azure Document Intelligence prebuilt tax models (W-2, 1099 family, 1040, 1098), AWS
Textract, Google Document AI, and frontier-model vision (Claude, GPT) on scanned tax documents:
published accuracy, handling of handwriting and stamps, multi-page returns, cost per page, data
retention terms, and any independent benchmarks or practitioner reports. Include studies on LLM
extraction accuracy for tax and financial documents (field-level numbers, not just anecdotes).
Recommend a default path and a fallback, with expected accuracy and cost per 1,000 pages.
```

### Prompt 10: Compliance language and insurance

```
Collect: sample IRC 7216 consent and disclosure language for use of third-party contractors and
cloud/AI services (AICPA, state societies, insurers, law-firm client alerts); engagement-letter
clauses covering AI-assisted services; state board of accountancy positions on AI and outsourcing
(all 50 states, flag the strict ones); Circular 230 and IRS guidance touching AI use by preparers;
state AI laws affecting professional services (e.g. Colorado); what professional-liability (E&O)
carriers for CPA firms say about AI tools; and what cyber-insurance carriers require from a
vendor holding client tax data (controls, limits, typical premium for a company our size).
Output: a clause library with sources, a state risk table, and an insurance checklist.
```

### Prompt 11: Willingness to pay and the value of time saved

```
Find data to price the product and quantify the pitch: average revenue per tax client and per
1040 / 1065 / 1120-S return for firms of 3-30 staff (Rosenberg Survey, AICPA MAP, NSA fee
studies, state society surveys); partner and senior billing rates and realisation; time spent
per return on gathering documents and reviewing prior year; client document turnaround times and
response rates by channel (email vs SMS vs portal) from TaxDome, Liscio, SafeSend, Karbon
reports; small-firm SaaS spend per staff member and per-firm price points that sold well.
Output: a value-of-time model per firm size and a recommended price ladder with the evidence.
```

### Prompt 12: Go-to-market channels for small CPA firms

```
Map the channels that reach 3-30 staff US tax firms: state CPA society vendor programmes
(cost, reach, timing), conferences (AICPA Engage, Scaling New Heights, Drake and Intuit user
events, NATP, NAEA), IT providers that specialise in CPA firms (names, size, partner terms),
peer networks and mastermind groups, podcasts and newsletters practitioners actually read, and
the buying calendar (when firms evaluate tools). For each: cost to participate, evidence of
vendor results, and the first three we should try. Also list the partner programmes that gate
API access (Wolters Kluwer, Thomson Reuters, Intuit, TaxDome) with requirements and fees.
```

### Prompt 13: Model and vendor watch

```
Quarterly: list model releases from Anthropic, OpenAI and Google since the last run with
pricing, context window, structured-output and tool-use support, and retention terms; any
benchmark on tax or financial document tasks; embedding and reranker releases; changes to
Bedrock / Vertex / Foundry availability and residency; and any security incident or terms change
at a vendor we use. Output: a diff against the previous quarter and a recommendation on whether
to trial a new model profile.
```

## Prompt 14: Follow-ups the first pack left open

Specific, checkable items. Each unblocks a piece of code or a claim made to a firm. Same method
rules: primary sources, URL and access date, mark unverified.

```
A. MeF element names (unblocks replacing the alias table in app/ingest/mef.py)
   For tax years 2023, 2024 and 2025, from the IRS MeF schema packages: the exact element names
   for the core lines we extract on IRS1040 (wages, taxable interest, dividends, capital gain,
   total income, adjustments, AGI, deduction, QBI, taxable income, total tax, withholding,
   estimated payments, refund, owed, penalty), IRS1040ScheduleC net profit, IRS1040ScheduleSE
   tax, IRS1065 (gross receipts, COGS, guaranteed payments, ordinary income, Schedule L capital),
   IRS1120S (gross receipts, officer compensation, ordinary income, Schedule K distributions,
   Schedule L loans from shareholders and retained earnings, Schedule M-2 AAA), IRS1120 (taxable
   income, total tax, estimated payments, retained earnings, NOL), and Schedule K-1 per-owner
   elements. Note every rename between years. Also: does the UltraTax / Lacerte "View XML" file
   contain the accepted submission (post-acknowledgement) and the state return package, what is
   it named on disk, and is there any batch or macro path to save XML for many clients.

B. IRS transcript formats (unblocks hardening app/ingest/transcript.py)
   The exact layout of a Wage and Income transcript as delivered by the Transcript Delivery
   System (file type, field labels, section order, how multiple payers of the same form appear,
   how masked IDs are printed) and as exported by Canopy, Tax Help Software and THS; whether any
   machine-readable format exists; Form 8821 processing time; whether business account
   transcripts (1120 / 1065) and Form 941 filings can be pulled the same way; a redacted public
   sample if one exists.

C. Azure Document Intelligence specifics (unblocks per-form routing in the OCR slot)
   Exact model IDs and output field names for the US tax prebuilts (W-2, the 1099 variants, 1040
   and which schedules, 1098 family), whether a multi-form PDF is split automatically, page
   pricing tiers, US region availability, and Document Intelligence's own data-retention and
   no-training terms (they differ from Azure OpenAI's).

D. Connector shapes for the next three (unblocks Dropbox, SmartVault, ShareFile connectors)
   For each: auth flow suitable for a firm-installed app, list and download endpoints, change
   notification or delta mechanism, rate limits, and any partner or app-review requirement.
   For Microsoft Graph specifically: least-privilege application permissions for one SharePoint
   library (Sites.Selected), the admin-consent flow a firm's IT provider will run, and whether
   Business Standard licensing is enough.

E. Sending reminders from the firm's own mailbox (unblocks the reminder transport)
   On Microsoft 365: SMTP AUTH availability by tenant default in 2026 versus Graph sendMail with
   Mail.Send scoped to one shared mailbox; on Google Workspace the equivalent. For SMS: 10DLC
   registration requirements, cost and timeline for a small sender, and which gateways (Twilio,
   Telnyx, and any TaxDome / Liscio built-ins) small firms actually use.

F. Client-facing organizer identity (unblocks the magic-link page)
   Which small-firm portals (ShareFile, SmartVault, Liscio, TaxDome, SafeSend) allow an embedded
   or linked third-party page, what identity signal they pass, and what an acceptable magic-link
   pattern looks like under the firm's security expectations (expiry, single use, IP binding).

G. Consent mechanics (unblocks the compliance kit's consent template)
   The verbatim Rev. Proc. 2013-14 mandatory paragraphs for 1040 consents to disclose and to
   use; whether e-signature is acceptable; default and maximum duration; whether sub-processors
   can be named generically; any state-level consent rules that go beyond federal (California,
   New York, Massachusetts).

H. State withholding and state returns (unblocks estimates and withholding screens)
   Since IRS transcripts carry no state withholding: which states offer preparer transcript or
   account access, and whether state returns are included in the UltraTax / Lacerte XML.

I. Evaluation data (unblocks the evaluation harness)
   Any public or purchasable labelled datasets of tax documents (synthetic 1040 packages, W-2
   and 1099 images, K-1s) usable to measure extraction accuracy, with licence terms.

J. Archive composition (sizes the OCR budget)
   For small US firms, what share of the archive is scanned versus born-digital by year, and
   typical pages per return package; state board record-retention requirements by state (years),
   to set the deletion policy.

K. Firm IT baseline (validates the compliance kit's SSO / MDM claims)
   What Microsoft 365 Business Standard versus Business Premium includes for a 3-30 staff firm
   (Entra ID plan, Intune, Purview, Defender), and what CPA-focused MSPs deploy by default.
```

## Prompt 16: ATX import paths, exactly

```
For Wolters Kluwer ATX (the desktop professional tax program, tax years 2024-2026), document
every way data can enter a return without keying, from the vendor's own materials first (the
ATX User Guide PDF, the "ATXLP <year> - Importing Data" support PDF, files.cchsfs.com help pages,
support.atxinc.com knowledge base), then the ATX Community forum.
1. Returns > Import Data: list every menu item and what it imports.
2. Form 8949 / Schedule D CSV import: the exact column headers and order, date formats, how
   short/long term and wash sales are coded, row limits, and whether the same import exists for
   1099-DA digital-asset transactions.
3. W-2 and 1099 data: is there any way to import a W-2 into a 1040 other than from ATX's own
   payroll module? Any CSV or spreadsheet template?
4. K-1 import: confirm the ATX-to-ATX path and whether a K-1 from another program can be
   imported.
5. Accounting / trial balance import: supported sources (iFirm, CAS, QuickBooks Desktop or
   Online, CSV), the mapping file format, and whether the mapping can be reused year to year.
6. Client data: the CSV / XML conversion formats, and whether a client list or organizer
   answers can be imported.
7. Licence terms: any clause in the ATX EULA about automation, macros, screen scraping or
   third-party tools interacting with the program.
8. Any announced ATX API, integration marketplace, or scan-and-populate partnership, with date.
Output: a table of import paths with format specs, quotes from the guides with page numbers,
the EULA clause text if any, and a recommendation on which two imports to build exporters for.
```

## Prompt 15: Short weekly monitoring prompt

Run this every Monday to stay current:

```
Search for news, product launches, funding announcements, and practitioner discussions from the
last 7 days about AI tools that let accounting/tax/audit firms search or analyse their own client
records. Sources: Accounting Today, CPA Practice Advisor, Going Concern, Journal of Accountancy,
r/taxpros, r/Accounting, TaxProTalk, LinkedIn, Product Hunt, vendor blogs of [list from Prompt 1].
Return: a bulleted digest with links, a note on any change to a vendor's data-retention or
pricing terms, and any new competitor not on this list: [paste current list].
```

## Tips for getting good output

- Ask for the comparison table first; it forces the agent to be systematic.
- Give the agent your own product's capability list and ask it to score competitors against it.
- Ask for quotes with dates. Undated sentiment about AI tools is useless; the products change
  monthly.
- Re-run Prompt 1 quarterly and diff the tables.
