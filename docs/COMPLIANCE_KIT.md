# Compliance kit (drafts for counsel, not legal advice)

Built from the research agent's Prompt 10 brief (`prompt10_compliance_insurance.md`). Everything
here is a starting draft for the firm's own counsel and insurer to review.

## The position to take

- Running a language model over identifiable **tax return information** (TRI) is, conservatively,
  a **disclosure** under IRC §7216. Do not rely on the domestic "auxiliary services" exception
  when the model summarises, classifies or reasons over the return; that looks like a substantive
  determination.
- Conservative path: **named-vendor written consent** using the Rev. Proc. 2013-14 mandatory
  language for 1040 taxpayers (copy the required blocks verbatim from the Revenue Procedure; do
  not paraphrase them), plus a **data processing agreement** covering AICPA ET section 1.700.040
  (use of a third-party service provider).
- **US-only inference.** Offshore processing adds mandatory consent language and SSN-masking rules.
  The production profiles pin `inference_geo: us`; keep it that way for US firms.
- Human review is part of the service, not a disclaimer: extracted figures are verified in the
  Verify tab before use, every answer cites its source, and nothing is filed from the tool.

## What ships with every firm

1. **Engagement-letter paragraph** (draft):

   > In preparing your return we use software that stores your documents and prior returns in a
   > private archive operated for our firm, and that may use artificial-intelligence services from
   > named providers [list sub-processors] to read, organise and summarise those documents. Those
   > providers process your information in the United States, do not retain it after processing
   > and do not use it to train their systems. All figures produced by the software are reviewed
   > by a member of our staff before they are relied on. You may decline this processing by
   > telling us in writing; we will prepare your return without it.

2. **§7216 consent** for 1040 clients naming the processors, using the Rev. Proc. 2013-14
   mandatory paragraphs, duration and signature block. Keep the signed consent in the client
   folder (it is a document type the archive recognises: `engagement_letter` / `correspondence`).
3. **Sub-processor list**: model vendor, embedding vendor, OCR vendor, cloud host, mail provider
   for reminders, SMS gateway if used. Region, retention, DPA reference, date reviewed.
4. **Data-handling sheet** for the firm's WISP (FTC Safeguards Rule, 16 CFR 314.4(f) service
   provider oversight; IRS Publication 4557): where data lives, encryption, access, retention,
   deletion, incident-response contact and SLA.
5. **Cyber questionnaire answers**, ready to paste: MFA for all staff logins; encryption in
   transit and at rest; per-client access scoping; audit log of every query, file open and
   verification; SOC 2 status and plan; incident-response SLA; backups and restore test dates.

## Insurance

- Professional liability (CAMICO, AICPA Member Insurance Program, CNA): no public blanket
  exclusion for AI use was found. Carriers look for governance, human review and vendor
  diligence. Give the firm the one-page governance statement below to attach to renewals.
- For this company: cyber insurance is a prerequisite for holding client tax data. Expect
  questionnaires to ask for MFA, encryption, SOC 2 or equivalent evidence, incident-response
  plan, and backup practices. Keep the answers current in this document.

## Governance statement (one paragraph, for the firm)

> The firm uses [product] to index its own client records and to draft document requests and
> planning notes. The software runs in [firm tenant / vendor account, US region]; AI providers
> are contractually bound to zero data retention and no training. Staff verify extracted figures
> before use, every output cites its source document, and the firm retains an audit log of all
> access. Client consent is obtained under IRC §7216 where required, and the firm's written
> information security plan lists the vendor and its sub-processors.

## Product-side controls that back these statements

| Statement | Where it is enforced |
|---|---|
| US-only inference | `inference_geo: us` in `models.yaml`; Bedrock / Foundry US regions in structure C |
| Zero retention, no training | Vendor terms per profile; documented in `docs/MODEL_RECOMMENDATIONS.md` |
| Human review | Verify tab; rejected facts leave the planning and answer paths |
| Access scoping | Retrieval is scoped per client; firm-wide search is explicit |
| Audit trail | `audit_log`: uploads, queries, file opens, verifications, feedback, reminders, syncs |
| Deletion | Client and document delete routes remove originals, chunks, facts and lists |
| Masking | SSNs and EINs masked in indexed MeF text; IRS transcripts arrive masked |
