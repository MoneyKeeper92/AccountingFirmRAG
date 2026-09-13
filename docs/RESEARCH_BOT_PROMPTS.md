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

## Prompt 3: Short weekly monitoring prompt

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
