# ATX integration

The pilot firm prepares returns in ATX (Wolters Kluwer). This page records what could be
verified about getting data into ATX, what could not, and the path the MVP takes. Sources are
listed at the end; the vendor's own documents were not fetchable from this environment, so the
research agent should confirm the specifics in Prompt 16.

## What ATX can import today (verified from public sources)

| Data | ATX path | Format | Notes |
|---|---|---|---|
| Schedule D / Form 8949 transactions | Open the return, Form 8949 Detail worksheet, Returns → Import Data | CSV; columns can be omitted, rows unchecked before import | Third parties (form8949.com and broker converters) produce ATX-ready CSVs; this is the one broadly documented CSV import into a return |
| Schedule K-1 from a 1041 / 1065 / 1120-S prepared in ATX | Returns → Import Data → K-1 Data → Import Data For Marked Returns | ATX-to-ATX, matched by SSN / EIN | Only when the pass-through return is also prepared in ATX |
| Trial balance / accounting data | Returns → Import Data (Accounting Import) | iFirm, CAS Trial Balance / Client Write-Up; QuickBooks-style GL mapping to tax lines | Requires account-to-line mapping once per client |
| W-2 / 1099 data | From ATX's own Payroll Compliance Reporting module | Internal | Applies when the firm prepares the payroll forms in ATX |
| Client conversions | Wolters Kluwer conversion tools | CSV / XML from Drake, Lacerte, ProSeries | Onboarding only |

## What ATX does not offer

- **No public API** and no command-line or scripting interface. Every path above is a menu
  action inside the desktop program.
- **No scan-and-populate partner.** GruntWorx Populate lists Drake, UltraTax, Lacerte, CCH
  Axcess and ProSystem fx; SurePrep's list does not include ATX. ATX users on the ATX Community
  forum discuss this gap. Wolters Kluwer's own scan-and-populate investment sits in CCH Axcess.
- **No MeF XML import** of a return prepared elsewhere.

## Could a bot key data into ATX?

Technically yes, with Windows UI automation (the accessibility tree, keystroke replay), because
ATX is a standard Windows desktop application. Practically, for this firm and this MVP:

1. The licence terms would need checking before any automation touches the program.
2. ATX's input worksheets change with each annual release; a keystroke robot breaks every
   January and needs the preparer to sit with it.
3. A robot that keys wrong numbers into a return is exactly the failure mode a 60-year-old CPA
   will not forgive, and there is no undo across forms.

So the MVP does not automate ATX's screens. It makes keying fast and checkable instead, and
uses ATX's real import paths where they exist.

## The MVP bridge

1. **Keying sheet.** For each client and year, one spreadsheet listing every figure from the
   source documents and the IRS transcript, grouped by the ATX input worksheet it belongs to
   (W-2 input, 1099-INT input, Schedule C income, Schedule A mortgage interest...), with the
   payer, the amount, the source file and a "Keyed?" column. The preparer keys down the list
   with ATX on the other monitor. Route: `GET /api/clients/{id}/keying-sheet?tax_year=…&format=xlsx`.
2. **Form 8949 CSV.** Where a client's 1099-B detail has been extracted, produce the CSV in the
   layout ATX's Detail-worksheet import accepts, so hundreds of trades are never keyed. Layout to
   be confirmed against the "ATXLP – Importing Data" guide (Prompt 16); the exporter is a small
   addition once the column order is known.
3. **K-1 chain.** For a 1040 whose 1065 or 1120-S the firm also prepares in ATX, the request
   list reminds the preparer to use ATX's K-1 import instead of keying.
4. **Trial balance.** For entity returns, the financial statements built here (from the trial
   balance the client sends) are the numbers that go into ATX's accounting import or straight
   onto the return lines; the statement lines already carry the account groupings.
5. **Review.** After the return is prepared, the ATX PDF is uploaded and the "Review a return"
   action compares it line by line with the prior year and with the source documents.

## What would change the picture

- Wolters Kluwer opening an ATX API or adding ATX to a scan-and-populate partner: revisit
  automation immediately.
- The firm moving to CCH Axcess: Axcess has spreadsheet imports, a 1040 pass-through import
  utility and APIs, and GruntWorx and SurePrep both populate it.

## Sources

- Wolters Kluwer, ATX product page: https://www.wolterskluwer.com/en/solutions/atx
- Wolters Kluwer, ATX K-1 data import help (2023): https://files.cchsfs.com/doc/atx/2023/Help/Content/Both-SSource/K-1%20and%20CSV%20Files/Importing%20K-1%20Data.htm
- Wolters Kluwer, ATX Accounting Import help: https://files.cchsfs.com/doc/atx/2015/Help/15.9/Content/Both-SSource/Accounting%20Import.htm
- CCH support, "ATXLP 2026 – Importing Data" (PDF; not fetchable here, confirm in Prompt 16): https://support.cch.com/apioss/Knowledge/GetAttachement?AttachementId=068Vt00001P53T7IAJ&AttachementName=ATXLP+2026+-+Importing+Data.pdf
- form8949.com, Form 8949 reporting for ATX users (CSV import into the Detail worksheet): https://www.form8949.com/atx-form-8949.html
- GruntWorx Populate supported software: https://www.gruntworx.com/features/populate.php
- SurePrep, scan and populate products on the market: https://corp.sureprep.com/learning-center/scan-and-populate/on-the-market/
- ATX Community, "Scan & Populate" thread: https://www.atxcommunity.com/topic/17663-scan-populate/
- ATX Community, "Import Schedule D data from csv file": https://www.atxcommunity.com/topic/6547-import-schedule-d-data-from-csv-file/
- Ace Cloud Hosting, ATX integrations overview: https://www.acecloudhosting.com/integrations/software/atx-tax-software/
