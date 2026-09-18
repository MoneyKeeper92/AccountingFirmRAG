"""Deterministic offline LLM. No network, no keys.

It is deliberately simple: it echoes the retrieved evidence, calls the planning tools when the
question looks like a forecast / planning question, and formats a readable answer. For
extraction it uses label regexes tuned to tax-return layouts (1040, 1065, 1120-S, 1120) and
structured JSON exports. Its purpose is to let you exercise every part of the pipeline before
any client data is sent to a vendor.
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..config import SlotConfig
from ..ingest.extractor import FACT_NAMES, FORMS
from ..ingest import forms_catalog
from .base import LLMProvider, LLMResponse, ToolCall, ToolSpec
from .registry import register_llm


@register_llm("mock")
class MockLLM(LLMProvider):
    def __init__(self, cfg: SlotConfig):
        self.identity = cfg.identity

    def chat(self, system: str, messages: list[dict[str, Any]], tools: list[ToolSpec] | None = None) -> LLMResponse:
        last = messages[-1]
        # Second pass: tool results have come back -> compose the answer.
        if isinstance(last.get("content"), list) and last["content"] and last["content"][0].get("type") == "tool_result":
            parts = [_render_tool_result(r.get("tool_use_id", ""), r.get("content", "")) for r in last["content"]]
            question = _first_user_text(messages)
            evidence = _find(r"<evidence>(.*?)</evidence>", system, flags=re.S) or ""
            return LLMResponse(
                text=f"Offline answer to: _{question}_\n\n" + "\n\n".join(parts)
                + "\n\n" + _sources_line(evidence)
                + "\n\n_(offline mock model: numbers above come straight from the deterministic tools; "
                "switch FIRM_RAG_PROFILE to a real profile for narrative analysis and citations)_",
                model=self.identity,
            )

        question = _first_user_text(messages)
        client_id = _find(r"client_id[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_\-]+)", system) or _find(r"\[client_id=([^\]]+)\]", system)
        calls: list[ToolCall] = []
        tool_names = {t.name for t in (tools or [])}
        q = question.lower()
        if client_id and "forecast_financials" in tool_names and any(k in q for k in ("forecast", "expect", "project", "next year", "this year", "estimate")):
            calls.append(ToolCall(id="forecast", name="forecast_financials", input={"client_id": client_id, "periods_ahead": 1, "metrics": []}))
        if client_id and "assess_risk" in tool_names and any(k in q for k in ("risk", "risky", "planning", "plan", "opportunit", "s-corp", "s corp", "election", "underpay", "penalt", "review", "concern")):
            calls.append(ToolCall(id="risk", name="assess_risk", input={"client_id": client_id}))
        if calls:
            return LLMResponse(text="", tool_calls=calls, stop_reason="tool_use", model=self.identity)

        evidence = _find(r"<evidence>(.*?)</evidence>", system, flags=re.S) or "(no evidence retrieved)"
        excerpt = evidence.strip()[:2500]
        return LLMResponse(
            text=f"Offline answer to: _{question}_\n\nMost relevant retrieved passages:\n\n{excerpt}\n\n"
            + _sources_line(evidence)
            + "\n\n_(offline mock model: this shows what the real model would be given as evidence)_",
            model=self.identity,
        )

    def extract_json(self, instructions: str, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Regex-based fallback extractor for files with explicit labels or structured JSON."""
        out: dict[str, Any] = {}
        props = schema.get("properties", {})
        m = re.search(r"^Filename:\s*(.+)$", text, re.M)
        filename = m.group(1).strip() if m else ""
        text = _body(text)          # the prompt wrapper (hints) must not drive detection; the filename may
        doc_type = _guess_doc_type(text, filename)
        if "doc_type" in props:
            out["doc_type"] = doc_type
        if "return_type" in props:
            out["return_type"] = _return_type_for(doc_type, text)
        if "facts" in props:
            facts = _regex_facts(text)
            if doc_type == "form_1120":
                for f in facts:
                    if f["name"] == "taxable_income":
                        f["name"] = "corporate_taxable_income"
                    elif f["name"] == "total_tax":
                        f["name"] = "corporate_total_tax"
            out["facts"] = facts
        if "tax_year" in props:
            out["tax_year"] = _primary_year(text)
        if "filing_status" in props:
            out["filing_status"] = _filing_status(text)
        if "forms_present" in props:
            out["forms_present"] = _forms_present(text)
        if "summary" in props:
            out["summary"] = " ".join(text.split())[:300]
        if "entities" in props:
            out["entities"] = []
        if "risk_flags" in props:
            out["risk_flags"] = _regex_flags(text)
        return out


# --------------------------------------------------------------------------- rendering helpers

def _sources_line(evidence: str) -> str:
    refs = re.findall(r"^\[(\d+)\] source: ([^|]+?)\s*\|", evidence, flags=re.M)
    if not refs:
        return ""
    seen, items = set(), []
    for n, loc in refs:
        if loc not in seen:
            seen.add(loc)
            items.append(f"[{n}] {loc.strip()}")
    return "Sources: " + "; ".join(items[:6])


def _render_tool_result(tool_id: str, payload: str) -> str:
    try:
        data = json.loads(payload)
    except Exception:
        return f"**{tool_id}**\n{payload}"
    if tool_id == "forecast" and isinstance(data, dict):
        rows = ["| metric | history | linear projection | CAGR projection |", "|---|---|---|---|"]
        for metric, p in data.items():
            if not isinstance(p, dict) or "history" not in p:
                continue
            hist = ", ".join(f"{y}: {v:,.0f}" for y, v in p["history"].items())
            lin = f"{p['linear']:,.0f}" if p.get("linear") is not None else "n/a"
            cagr = f"{p['cagr']:,.0f}" if p.get("cagr") is not None else "n/a"
            rows.append(f"| {metric} | {hist} | {lin} | {cagr} |")
        target = next((p.get("target_year") for p in data.values() if isinstance(p, dict)), "next year")
        return f"**Projection for {target}** (linear trend and compound growth over the years on file)\n\n" + "\n".join(rows)
    if tool_id == "risk" and isinstance(data, dict):
        lines = [f"**Tax planning screen ({data.get('ratios', {}).get('year', 'latest year')}, {data.get('profile', '')})**"]
        for f in data.get("flags", []):
            lines.append(f"- [{f['severity'].upper()}] {f['area']}: {f['detail']}")
        if not data.get("flags"):
            lines.append("- No flags raised by the screens.")
        ratios = {k: v for k, v in data.get("ratios", {}).items() if k != "year" and v is not None}
        if ratios:
            lines.append("\nKey figures: " + ", ".join(f"{k} {v}" for k, v in ratios.items()))
        return "\n".join(lines)
    return f"**{tool_id}**\n```\n{json.dumps(data, indent=1)[:1500]}\n```"


def _body(text: str) -> str:
    if "<document>" in text:
        text = text.split("<document>", 1)[1]
    return text.replace("</document>", "")


def _first_user_text(messages: list[dict[str, Any]]) -> str:
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            return m["content"]
    return ""


def _find(pattern: str, text: str, flags: int = 0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- extraction helpers

# Label -> regex. Lines look like "11 Adjusted gross income: 190,020" or "Gross receipts or sales: 5,610,000".
_FACT_LABELS: dict[str, str] = {
    # 1040
    "wages": r"wages(?:,?\s+salaries,?\s+tips)?(?:[^:\n]*)?",
    "taxable_interest": r"taxable\s+interest",
    "tax_exempt_interest": r"tax[-\s]exempt\s+interest",
    "ordinary_dividends": r"ordinary\s+dividends",
    "qualified_dividends": r"qualified\s+dividends",
    "ira_distributions_taxable": r"(?:taxable\s+)?ira\s+distributions(?:[^:\n]*taxable)?",
    "pensions_taxable": r"(?:taxable\s+)?pensions\s+and\s+annuities(?:[^:\n]*taxable)?",
    "social_security_taxable": r"(?:taxable\s+)?social\s+security(?:\s+benefits)?(?:[^:\n]*taxable)?",
    "capital_gain_loss": r"capital\s+gain(?:s)?(?:\s+or\s+\(?loss\)?)?|net\s+capital\s+gain",
    "schedule_c_net_profit": r"schedule\s+c\s+net\s+profit|business\s+income\s+or\s+\(loss\)|net\s+profit\s+\(schedule\s+c\)",
    "schedule_e_net_income": r"schedule\s+e\s+net\s+income|rental\s+real\s+estate,?\s+royalties[^:\n]*",
    "total_income": r"total\s+income",
    "adjustments_to_income": r"adjustments\s+to\s+income",
    "adjusted_gross_income": r"adjusted\s+gross\s+income|agi",
    "standard_or_itemized_deduction": r"standard\s+deduction\s+or\s+itemized\s+deductions|standard\s+deduction",
    "itemized_deductions_total": r"total\s+itemized\s+deductions|itemized\s+deductions",
    "salt_deduction": r"state\s+and\s+local\s+taxes|salt",
    "mortgage_interest_deduction": r"(?:home\s+)?mortgage\s+interest",
    "charitable_contributions": r"charitable(?:\s+contributions)?|gifts\s+to\s+charity",
    "qbi_deduction": r"qualified\s+business\s+income\s+deduction|qbi\s+deduction",
    "taxable_income": r"taxable\s+income",
    "self_employment_tax": r"self[-\s]employment\s+tax",
    "child_tax_credit": r"child\s+tax\s+credit",
    "total_tax": r"total\s+tax",
    "federal_withholding": r"federal\s+income\s+tax\s+withheld|federal\s+withholding|withholding",
    "estimated_payments": r"(?:\d{4}\s+)?estimated\s+(?:tax\s+)?payments",
    "refund": r"refund|amount\s+(?:you\s+)?overpaid",
    "amount_owed": r"amount\s+you\s+owe|amount\s+owed|balance\s+due",
    "underpayment_penalty": r"(?:estimated\s+tax\s+|underpayment\s+)penalty",
    "dependents_count": r"dependents(?:\s+claimed)?",
    # entity returns
    "gross_receipts": r"gross\s+receipts(?:\s+or\s+sales)?",
    "returns_and_allowances": r"returns\s+and\s+allowances",
    "cost_of_goods_sold": r"cost\s+of\s+goods\s+sold|cogs",
    "gross_profit": r"gross\s+profit",
    "officer_compensation": r"compensation\s+of\s+officers|officer\s+compensation",
    "salaries_and_wages": r"salaries\s+and\s+wages(?:[^:\n]*)?",
    "guaranteed_payments": r"guaranteed\s+payments(?:\s+to\s+partners)?",
    "rent_expense": r"rents?(?:\s+expense)?(?:\s*-\s*related\s+party)?",
    "interest_expense": r"interest\s+expense",
    "taxes_and_licenses": r"taxes\s+and\s+licenses",
    "depreciation": r"depreciation(?:\s+expense)?(?:\s+\(form\s+4562\))?",
    "section_179": r"section\s+179(?:\s+(?:deduction|expense))?",
    "total_deductions": r"total\s+deductions",
    "ordinary_business_income": r"ordinary\s+business\s+income(?:\s+\(loss\))?",
    "net_rental_income": r"net\s+rental\s+real\s+estate\s+income(?:\s+\(loss\))?|net\s+rental\s+income",
    "interest_income": r"interest\s+income",
    "dividend_income": r"dividend\s+income|dividends",
    "total_assets": r"total\s+assets",
    "cash": r"cash(?:\s+and\s+cash\s+equivalents)?",
    "accounts_receivable": r"(?:trade\s+notes\s+and\s+)?accounts\s+receivable(?:,\s*net)?",
    "inventory": r"inventor(?:y|ies)",
    "fixed_assets_net": r"(?:buildings\s+and\s+other\s+depreciable\s+assets|fixed\s+assets|equipment)[^:\n]*net",
    "total_liabilities": r"total\s+liabilities",
    "loans_from_shareholders": r"loans\s+from\s+shareholders|shareholder\s+loans",
    "partners_capital": r"partners'?\s+capital(?:\s+accounts)?",
    "retained_earnings": r"retained\s+earnings(?:[^:\n]*)?",
    "aaa_balance": r"accumulated\s+adjustments\s+account|aaa(?:\s+balance)?",
    "distributions": r"(?:shareholder\s+|partner\s+|cash\s+)?distributions(?:[^:\n]*)?",
    "number_of_owners": r"number\s+of\s+(?:shareholders|partners)",
    "net_operating_loss": r"net\s+operating\s+loss(?:\s+(?:deduction|carryforward))?|nol\s+carryforward",
    "state_tax": r"state\s+(?:income\s+)?tax(?:es)?(?:\s+paid)?",
    "shareholder_health_insurance": r"shareholder\s+health\s+insurance|health\s+insurance\s+(?:for\s+)?(?:>\s*|more\s+than\s+)2%",
    "retirement_plan_contributions": r"(?:pension|profit[-\s]sharing|retirement)(?:\s+plan)?(?:\s+contributions)?",
    # books
    "revenue": r"(?:total\s+)?revenue[s]?|net\s+sales|sales",
    "operating_expenses": r"(?:total\s+)?operating\s+expenses",
    "net_income": r"net\s+income|net\s+profit|net\s+earnings",
    "total_equity": r"total\s+(?:stockholders'?|shareholders'?|owners'?)?\s*equity",
    "current_assets": r"(?:total\s+)?current\s+assets",
    "current_liabilities": r"(?:total\s+)?current\s+liabilities",
    "long_term_debt": r"long[-\s]term\s+debt|notes\s+payable|mortgages,?\s+notes",
}

_LINE_PREFIX = r"^\s*(?:(?:line\s+)?\d{1,2}[a-z]?\.?\s+)?"   # optional "11 " / "1a " / "line 11 " prefix
# optional "(Form 1125-E)" note, one or more ": - |" separators (trial-balance rows have two), then the amount;
# the lookbehind stops a greedy label from swallowing the leading digits of the number.
_AMOUNT = r"(?:\s*\([^)\n]*\))?(?:\s*[:\-|])*\s*\$?\s*(?<![\d,.])(\(?-?\d[\d,]*(?:\.\d+)?\)?)\s*(?:count)?\s*\|?\s*$"


def _regex_facts(text: str) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            facts.extend(_facts_from_json(json.loads(text[start : end + 1])))
            if facts:
                return facts
        except Exception:
            pass
    default_year = _primary_year(text)
    for name, pat in _FACT_LABELS.items():
        for m in re.finditer(_LINE_PREFIX + rf"(?:{pat})" + _AMOUNT, text, flags=re.I | re.M):
            raw = m.group(1)
            neg = raw.startswith("(") and raw.endswith(")")
            raw = raw.strip("()").replace(",", "")
            try:
                val = float(raw)
            except ValueError:
                continue
            if neg:
                val = -abs(val)
            unit = "count" if name in ("dependents_count", "number_of_owners") else "USD"
            facts.append({"name": name, "value": val, "period": default_year, "unit": unit, "source_quote": m.group(0).strip()[:140]})
            break
    return facts


def _facts_from_json(data: Any, period: int | None = None) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    names = set(FACT_NAMES)
    if isinstance(data, dict):
        period = data.get("period") or data.get("tax_year") or data.get("fiscal_year") or period
        try:
            period = int(period) if period is not None else None
        except (TypeError, ValueError):
            period = None
        for k, v in data.items():
            key = re.sub(r"[^a-z0-9]+", "_", str(k).lower()).strip("_")
            if isinstance(v, (int, float)) and not isinstance(v, bool) and key in names:
                unit = "count" if key in ("dependents_count", "number_of_owners") else "USD"
                facts.append({"name": key, "value": float(v), "period": period, "unit": unit, "source_quote": f"{k}: {v}"})
            elif isinstance(v, (dict, list)):
                facts.extend(_facts_from_json(v, period))
    elif isinstance(data, list):
        for item in data:
            facts.extend(_facts_from_json(item, period))
    return facts


def _primary_year(text: str) -> int | None:
    """The year a document reports on, not the latest year it mentions."""
    m = re.search(r"(?:year[s]?\s+ended|tax\s+year|fiscal\s+year|for\s+(?:the\s+)?(?:calendar\s+)?year|as\s+of)[^\n\d]{0,40}(20[0-4]\d)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"[\"']?(?:tax_year|fiscal_year|period)[\"']?\s*[:=]\s*[\"']?(20[0-4]\d)", text)
    if m:
        return int(m.group(1))
    years = re.findall(r"(?<!\d)(20[0-4]\d)(?!\d)", text)
    if not years:
        return None
    counts: dict[str, int] = {}
    for y in years:
        counts[y] = counts.get(y, 0) + 1
    best = max(counts.values())
    return int(max(y for y, c in counts.items() if c == best))


def _guess_doc_type(text: str, filename: str = "") -> str:
    spec = forms_catalog.detect(text, filename)
    if spec is not None:
        return spec.doc_type
    return _guess_doc_type_legacy(text, filename)


def _guess_doc_type_legacy(text: str, filename: str = "") -> str:
    t = text.lower().replace("_", " ")
    head = t[:600]
    if filename:
        # "ABC_Company_Trial_Balance_2025.csv" carries the type when the content does not
        head = filename.lower().replace("_", " ").replace("-", " ") + " " + head
    if re.search(r"schedule\s+k-?1", head):
        if "1120-s" in head or "1120s" in head:
            return "k1_1120s"
        if "1041" in head:
            return "k1_1041"
        return "k1_1065"
    if re.search(r"form\s+1120[-\s]?s\b|\b1120[-\s]?s\b|s\s+corporation", head):
        return "form_1120s"
    if re.search(r"form\s+1065\b|\b1065\b|partnership\s+return", head):
        return "form_1065"
    if re.search(r"form\s+1120\b|\b1120\b|corporation\s+income\s+tax\s+return", head):
        return "form_1120"
    if re.search(r"form\s+1041\b|\b1041\b", head):
        return "form_1041"
    if re.search(r"form\s+990\b", head):
        return "form_990"
    if re.search(r"form\s+1040|\b1040\b|individual\s+income\s+tax\s+return", head):
        return "form_1040"
    for pat, dt in [
        (r"\bw-?2\b", "w2"), (r"1099-?int", "1099_int"), (r"1099-?div", "1099_div"), (r"1099-?b\b", "1099_b"),
        (r"1099-?nec", "1099_nec"), (r"1099-?misc", "1099_misc"), (r"1099-?r\b", "1099_r"), (r"1099-?k\b", "1099_k"),
        (r"1099-?g\b", "1099_g"), (r"ssa-?1099", "ssa_1099"), (r"1098-?t\b", "1098_t"), (r"1098-?e\b", "1098_e"),
        (r"\b1098\b", "1098_mortgage"), (r"1095-?a", "1095_a"), (r"form\s+941|\b941\b", "form_941"),
        (r"trial\s+balance|\btb\b", "trial_balance"), (r"general\s+ledger", "general_ledger"), (r"depreciation\s+schedule", "depreciation_schedule"),
        (r"bank\s+statement", "bank_statement"), (r"payroll\s+(?:summary|report|register)", "payroll_report"),
        (r"organizer|questionnaire", "organizer"), (r"engagement\s+letter", "engagement_letter"),
        (r"(?:irs|internal\s+revenue\s+service).{0,80}(?:notice|letter)|notice\s+cp\d+", "irs_notice"),
        (r"extension|form\s+4868|form\s+7004", "extension"),
    ]:
        if re.search(pat, head):
            return dt
    if "balance sheet" in t and ("income statement" in t or "profit and loss" in t):
        return "financial_statements"
    if "balance sheet" in t:
        return "balance_sheet"
    if "income statement" in t or "profit and loss" in t:
        return "income_statement"
    return "other"


def _return_type_for(doc_type: str, text: str) -> str:
    mapping = {"form_1040": "1040", "form_1065": "1065", "k1_1065": "1065", "form_1120s": "1120-S", "k1_1120s": "1120-S",
               "form_1120": "1120", "form_1041": "1041", "k1_1041": "1041", "form_990": "990"}
    if doc_type in mapping:
        return mapping[doc_type]
    t = text.lower()
    for needle, rt in (("1120-s", "1120-S"), ("1120s", "1120-S"), ("1065", "1065"), ("1120", "1120"), ("1040", "1040")):
        if needle in t:
            return rt
    return "none"


def _forms_present(text: str) -> list[str]:
    t = text.lower()
    found: list[str] = []
    for form in FORMS:
        f = form.lower()
        if f.startswith("schedule "):
            tail = re.escape(f.split(" ", 1)[1]).replace("\\-", "-?")
            pat = rf"schedule\s+{tail}\b"
        elif f.startswith("form "):
            tail = re.escape(f.split(" ", 1)[1]).replace("\\-", "-?")
            pat = rf"form\s+{tail}\b"
        elif f == "1120":
            pat = r"form\s+1120(?!-?s)\b"
        elif f in ("1040", "1065", "1041", "990", "1120-s", "1040-sr", "1040-nr", "1040-x"):
            pat = rf"form\s+{re.escape(f).replace(chr(92) + '-', '-?')}\b"
        elif f == "w-3":
            pat = r"\bw-?3\b"
        else:
            pat = re.escape(f)
        if re.search(pat, t):
            found.append(form)
    return found


def _filing_status(text: str) -> str | None:
    m = re.search(r"filing\s+status[\"']?\s*[:=]\s*[\"']?([A-Za-z ]+)", text, re.I)
    if m:
        return m.group(1).strip().lower()
    m = re.search(r"married\s+filing\s+jointly|married\s+filing\s+separately|head\s+of\s+household|qualifying\s+surviving\s+spouse|\bsingle\b", text, re.I)
    return m.group(0).lower() if m else None


def _regex_flags(text: str) -> list[str]:
    flags = []
    for pat, msg in [
        (r"\bpenalt(?:y|ies)\b", "Penalty mentioned in the prior-year file"),
        (r"\b(?:paid|filed|were|was)\s+late\b|\blate\s+(?:payment|filing|estimate)", "Late payment or filing noted in the prior-year file"),
        (r"\b(?:irs|state)\s+notice\b|\bnotice\s+cp\d+|\bcp2000\b", "IRS/state notice referenced"),
        (r"\bamended\s+return\b|\b1040-x\b", "Amended return referenced"),
        (r"distributions?\s+exceed|in\s+excess\s+of\s+basis", "Distributions in excess of basis referenced"),
        (r"no\s+officer\s+compensation|reasonable\s+compensation", "Reasonable compensation question noted"),
    ]:
        if re.search(pat, text, re.I):
            flags.append(msg)
    return flags[:5]
