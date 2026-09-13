"""MeF (IRS Modernized e-File) XML ingest.

UltraTax and Lacerte let a preparer view and save the e-file XML for a return; when a firm
drops those files in the client folder we can read the return deterministically: no OCR, no
language model, every figure tied to a schema element name.

Research (Sept 2026): none of the major packages offers a documented batch MeF archive API, so
this is a short-circuit for firms that save the XML by hand or via a print-to-folder macro, not
a universal source. The PDF path stays the default.

Element names below are IRS schema names for the core lines and are stable across recent tax
years, but the IRS revises schemas annually. `MEF_FACT_MAP` lists aliases per fact; verify
against the schema package for each tax year (e-Services SOR, Software Developer role) and add
aliases rather than renaming. Unmapped `*Amt` elements are still indexed as text so they remain
searchable and citable.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

# fact name -> candidate element names (first match wins), searched within the main return form
MEF_FACT_MAP: dict[str, list[str]] = {
    # ---- 1040 (IRS1040 + schedules)
    "wages": ["WagesSalariesAndTipsAmt", "TotalWagesAmt", "WagesAmt"],
    "taxable_interest": ["TaxableInterestAmt"],
    "tax_exempt_interest": ["TaxExemptInterestAmt"],
    "ordinary_dividends": ["OrdinaryDividendsAmt", "TotalOrdinaryDividendsAmt"],
    "qualified_dividends": ["QualifiedDividendsAmt"],
    "ira_distributions_taxable": ["IRADistributionsTaxableAmt", "TaxableIRAAmt"],
    "pensions_taxable": ["PensionsAnnuitiesTaxableAmt", "TotalTaxablePensionsAmt"],
    "social_security_taxable": ["SocSecBnftTaxableAmt", "TaxableSocSecAmt"],
    "capital_gain_loss": ["CapitalGainLossAmt", "NetCapitalGainLossAmt"],
    "total_income": ["TotalIncomeAmt"],
    "adjustments_to_income": ["TotalAdjustmentsAmt", "TotalAdjustmentsToIncomeAmt"],
    "adjusted_gross_income": ["AdjustedGrossIncomeAmt"],
    "standard_or_itemized_deduction": ["TotalItemizedOrStandardDedAmt", "TotalDeductionsAmt"],
    "qbi_deduction": ["QualifiedBusinessIncomeDedAmt", "QBIDeductionAmt"],
    "taxable_income": ["TaxableIncomeAmt"],
    "income_tax_before_credits": ["TaxAmt", "TotalTaxBeforeCrAndOthTaxesAmt"],
    "child_tax_credit": ["CTCODCAmt", "ChildTaxCreditAmt"],
    "self_employment_tax": ["SelfEmploymentTaxAmt"],
    "total_tax": ["TotalTaxAmt"],
    "federal_withholding": ["WithholdingTaxAmt", "FormW2WithheldTaxAmt", "TotalWithholdingAmt"],
    "estimated_payments": ["EstimatedTaxPaymentsAmt", "EstimatedTaxPymtAmt"],
    "refund": ["RefundAmt", "OverpaidAmt"],
    "amount_owed": ["OwedAmt", "AmountOwedAmt", "BalanceDueAmt"],
    "underpayment_penalty": ["EsPenaltyAmt", "EstimatedTaxPenaltyAmt"],
    # ---- 1065 / 1120-S / 1120
    "gross_receipts": ["GrossReceiptsOrSalesAmt", "GrossReceiptsAmt"],
    "returns_and_allowances": ["ReturnsAndAllowancesAmt"],
    "cost_of_goods_sold": ["CostOfGoodsSoldAmt"],
    "gross_profit": ["GrossProfitAmt"],
    "officer_compensation": ["CompensationOfOfficersAmt"],
    "salaries_and_wages": ["SalariesAndWagesLessCreditsAmt", "SalariesAndWagesAmt"],
    "guaranteed_payments": ["GuaranteedPaymentsToPartnersAmt", "GuaranteedPymtToPartnersAmt", "GuaranteedPaymentsAmt"],
    "rent_expense": ["RentsAmt", "RentExpenseAmt"],
    "interest_expense": ["InterestDeductionAmt", "InterestAmt", "InterestExpenseAmt"],
    "taxes_and_licenses": ["TaxesAndLicensesAmt"],
    "depreciation": ["DepreciationAmt", "DepreciationNotClaimedElswhrAmt", "DepreciationDeductionAmt"],
    "section_179": ["Section179DeductionAmt", "Sect179DeductionAmt"],
    "total_deductions": ["TotalDeductionsAmt"],
    "ordinary_business_income": ["OrdinaryBusinessIncomeLossAmt", "OrdinaryIncomeLossAmt"],
    "net_rental_income": ["NetRentalRealEstateIncomeLossAmt", "NetRentalRealEstateIncomeAmt"],
    "distributions": ["TotalPropertyDistributionsAmt", "DistributionsAmt", "CashPropertyDistributionsAmt", "TotalDistributionsAmt"],
    "total_assets": ["TotalAssetsEOYAmt", "TotalAssetsAmt"],
    "cash": ["CashEOYAmt"],
    "accounts_receivable": ["TradeNotesAndAcctsRcvblEOYAmt", "AccountsReceivableEOYAmt"],
    "inventory": ["InventoriesEOYAmt"],
    "total_liabilities": ["TotalLiabilitiesEOYAmt"],
    "loans_from_shareholders": ["LoansFromShareholdersEOYAmt", "LoansFromShareholdersAmt"],
    "partners_capital": ["PartnersCapitalAccountsEOYAmt", "PartnersCapitalAcctEOYAmt"],
    "retained_earnings": ["RetainedEarningsEOYAmt", "RetainedEarningsApprEOYAmt", "RetainedEarningsUnapprEOYAmt"],
    "aaa_balance": ["AAAEndOfYearAmt", "AccumulatedAdjustmentsAcctEOYAmt", "BalanceAtEndOfTaxYearAmt"],
    "corporate_taxable_income": ["TaxableIncomeAmt"],           # only used for 1120, see below
    "corporate_total_tax": ["TotalTaxAmt"],                     # only used for 1120, see below
    "net_operating_loss": ["NetOperatingLossDeductionAmt", "NOLDeductionAmt"],
    "number_of_owners": ["NumberOfShareholdersCnt", "NumberOfPartnersCnt", "ShareholdersCnt", "PartnersCnt"],
}

ENTITY_ONLY = {"corporate_taxable_income", "corporate_total_tax"}
INDIVIDUAL_ONLY = {"taxable_income", "total_tax", "wages"}

RETURN_TYPE_CODES = {"1040": "1040", "1040SR": "1040", "1040NR": "1040", "1040X": "1040", "1065": "1065", "1120S": "1120-S", "1120": "1120",
                     "1041": "1041", "990": "990", "990EZ": "990", "990PF": "990"}
MAIN_FORM = {"1040": "IRS1040", "1065": "IRS1065", "1120-S": "IRS1120S", "1120": "IRS1120", "1041": "IRS1041", "990": "IRS990"}
DOC_TYPE = {"1040": "form_1040", "1065": "form_1065", "1120-S": "form_1120s", "1120": "form_1120", "1041": "form_1041", "990": "form_990"}


def is_mef_xml(data: bytes) -> bool:
    head = data[:4000]
    return b"ReturnHeader" in head and (b"ReturnData" in data[:200_000] or b"<Return" in head)


def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean(root: ET.Element) -> ET.Element:
    for el in root.iter():
        el.tag = _strip_ns(el.tag)
    return root


def _form_name(tag: str) -> str | None:
    """IRS1040ScheduleC -> 'Schedule C'; IRS8949 -> 'Form 8949'; IRS1120SScheduleK1 -> 'Schedule K-1'; IRS1120S -> '1120-S'."""
    if not tag.startswith("IRS"):
        return None
    body = tag[3:]
    m = re.match(r"^(1040(?:SR|NR|X)?|1065|1120S|1120|1041|990(?:EZ|PF)?)(?:Schedule([A-Z0-9]+))?$", body)
    if m:
        base, sched = m.groups()
        if sched:
            sched = sched.replace("K1", "K-1").replace("M1", "M-1").replace("M2", "M-2").replace("M3", "M-3").replace("8812", "8812")
            return f"Schedule {sched}"
        return {"1120S": "1120-S", "1040SR": "1040-SR", "1040NR": "1040-NR", "1040X": "1040-X"}.get(base, base)
    m = re.match(r"^(\d{4}[A-Z]{0,2})", body)
    if m:
        num = m.group(1)
        return f"Form {num[:4]}-{num[4:]}" if len(num) > 4 else f"Form {num}"
    return None


def _first_amount(scope: ET.Element, names: list[str]) -> tuple[float, str] | None:
    for name in names:
        el = scope.find(f".//{name}")
        if el is not None and el.text and el.text.strip():
            try:
                return float(el.text.strip()), name
            except ValueError:
                continue
    return None


def _mask(value: str | None) -> str:
    if not value:
        return ""
    digits = re.sub(r"\D", "", value)
    return f"***-**-{digits[-4:]}" if len(digits) >= 4 else "***"


def parse_mef(data: bytes, filename: str = "") -> dict[str, Any]:
    """Return {'record': canonical record, 'pages': [text], 'unmapped': [...]}."""
    root = _clean(ET.fromstring(data))
    header = root.find(".//ReturnHeader")
    rdata = root.find(".//ReturnData")
    if header is None or rdata is None:
        raise ValueError("Not an MeF return: ReturnHeader / ReturnData missing")

    code = (header.findtext(".//ReturnTypeCd") or "").strip().upper()
    return_type = RETURN_TYPE_CODES.get(code, "none")
    tax_year_txt = header.findtext(".//TaxYr") or header.findtext(".//TaxPeriodEndDt") or ""
    m = re.search(r"(20\d\d)", tax_year_txt)
    tax_year = int(m.group(1)) if m else None
    filer = header.find(".//Filer")
    names: list[dict[str, str]] = []
    if filer is not None:
        for tag, role in (("PersonFirstNm", "taxpayer"), ("BusinessNameLine1Txt", "entity"), ("SpouseFirstNm", "spouse")):
            el = filer.find(f".//{tag}")
            if el is not None and el.text:
                last = filer.findtext(".//PersonLastNm") if role == "taxpayer" else filer.findtext(".//SpouseLastNm") if role == "spouse" else None
                names.append({"name": f"{el.text.strip()} {last.strip()}" if last else el.text.strip(), "role": role})
        ssn = filer.findtext(".//PrimarySSN") or filer.findtext(".//EIN")
    else:
        ssn = None

    forms: list[str] = []
    for child in rdata:
        f = _form_name(child.tag)
        if f and f not in forms:
            forms.append(f)

    filing_status = None
    fs = rdata.find(".//IndividualReturnFilingStatusCd")
    if fs is not None and fs.text:
        filing_status = {"1": "single", "2": "married filing jointly", "3": "married filing separately", "4": "head of household",
                         "5": "qualifying surviving spouse"}.get(fs.text.strip(), fs.text.strip())

    main = rdata.find(f".//{MAIN_FORM.get(return_type, 'IRS1040')}")
    scope = main if main is not None else rdata
    facts: list[dict[str, Any]] = []
    used: set[str] = set()
    for fact_name, aliases in MEF_FACT_MAP.items():
        if return_type == "1120" and fact_name in INDIVIDUAL_ONLY:
            continue
        if return_type != "1120" and fact_name in ENTITY_ONLY:
            continue
        hit = _first_amount(scope, aliases)
        if hit is None and scope is not rdata:
            hit = _first_amount(rdata, aliases)          # schedules (Schedule L / K / M-2) live beside the main form
        if hit is None:
            continue
        value, element = hit
        unit = "count" if fact_name == "number_of_owners" else "USD"
        facts.append({"name": fact_name, "value": value, "period": tax_year, "unit": unit, "source_quote": f"MeF {element} = {value:,.0f}"})
        used.add(element)
    # Schedule C / SE from the 1040 package
    if return_type == "1040":
        sc = rdata.find(".//IRS1040ScheduleC")
        if sc is not None:
            hit = _first_amount(sc, ["NetProfitOrLossAmt", "NetProfitLossAmt"])
            if hit:
                facts.append({"name": "schedule_c_net_profit", "value": hit[0], "period": tax_year, "unit": "USD", "source_quote": f"MeF IRS1040ScheduleC {hit[1]} = {hit[0]:,.0f}"}); used.add(hit[1])
        se = rdata.find(".//IRS1040ScheduleSE")
        if se is not None and not any(f["name"] == "self_employment_tax" for f in facts):
            hit = _first_amount(se, ["SelfEmploymentTaxAmt"])
            if hit:
                facts.append({"name": "self_employment_tax", "value": hit[0], "period": tax_year, "unit": "USD", "source_quote": f"MeF IRS1040ScheduleSE {hit[1]} = {hit[0]:,.0f}"}); used.add(hit[1])

    # Render a readable, searchable text version: every amount element by form, SSN masked
    lines = [f"MeF e-file return {return_type} for tax year {tax_year} ({code})",
             f"Filer: {', '.join(n['name'] + ' (' + n['role'] + ')' for n in names) or 'n/a'}  ID {_mask(ssn)}",
             f"Filing status: {filing_status or 'n/a'}", f"Forms present: {', '.join(forms)}", ""]
    unmapped: list[str] = []
    for child in rdata:
        form = _form_name(child.tag) or child.tag
        lines.append(f"[{form}]")
        for el in child.iter():
            if el is child or not el.text or not el.text.strip():
                continue
            if el.tag.endswith(("Amt", "Cnt", "Pct")):
                label = re.sub(r"(?<!^)(?=[A-Z])", " ", el.tag)
                lines.append(f"{label}: {el.text.strip()}")
                if el.tag not in used and el.tag.endswith("Amt"):
                    unmapped.append(f"{form}:{el.tag}")
        lines.append("")
    text = "\n".join(lines)

    record = {
        "doc_type": DOC_TYPE.get(return_type, "other"), "return_type": return_type, "tax_year": tax_year, "filing_status": filing_status,
        "forms_present": forms, "entities": names, "facts": facts,
        "summary": f"{return_type} e-file XML for {tax_year}: {len(forms)} forms/schedules, {len(facts)} figures read directly from the MeF elements.",
        "risk_flags": [], "source": "mef_xml", "unmapped_amount_elements": unmapped[:200],
    }
    return {"record": record, "pages": [text], "unmapped": unmapped}
