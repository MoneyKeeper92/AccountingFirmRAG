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

## Prompt 5: Short weekly monitoring prompt

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
