"""Deterministic offline LLM. No network, no keys.

It is deliberately simple: it echoes the retrieved evidence, calls the
financial tools when the question looks like a forecast/risk question, and
formats a readable answer. Its purpose is to let you exercise every part of
the pipeline (upload -> parse -> extract -> embed -> retrieve -> tools -> UI)
before any client data is sent to a vendor.
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..config import SlotConfig
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
        if client_id and "forecast_financials" in tool_names and any(k in q for k in ("forecast", "expect", "project", "next year", "this year")):
            calls.append(ToolCall(id="forecast", name="forecast_financials", input={"client_id": client_id, "periods_ahead": 1}))
        if client_id and "assess_risk" in tool_names and any(k in q for k in ("risk", "risky", "audit", "concern")):
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
        """Regex-based fallback extractor for demo files that contain explicit labels."""
        out: dict[str, Any] = {}
        props = schema.get("properties", {})
        if "facts" in props:
            out["facts"] = _regex_facts(text)
        if "doc_type" in props:
            out["doc_type"] = _guess_doc_type(text)
        if "tax_year" in props:
            out["tax_year"] = _primary_year(text)
        if "summary" in props:
            body = text.split("<document>", 1)[1] if "<document>" in text else text
            out["summary"] = " ".join(body.replace("</document>", "").split())[:300]
        if "entities" in props:
            out["entities"] = []
        if "risk_flags" in props:
            out["risk_flags"] = []
        return out


def _sources_line(evidence: str) -> str:
    """Cite the retrieved evidence blocks the way the real model is instructed to: [n]."""
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
    """Turn raw tool JSON into readable markdown so the offline demo looks like a real answer."""
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
        lines = [f"**Risk screen ({data.get('ratios', {}).get('year', 'latest year')})**"]
        for f in data.get("flags", []):
            lines.append(f"- [{f['severity'].upper()}] {f['area']}: {f['detail']}")
        if not data.get("flags"):
            lines.append("- No flags raised by the ratio screens.")
        ratios = {k: v for k, v in data.get("ratios", {}).items() if k != "year" and v is not None}
        if ratios:
            lines.append("\nKey ratios: " + ", ".join(f"{k} {v}" for k, v in ratios.items()))
        return "\n".join(lines)
    return f"**{tool_id}**\n```\n{json.dumps(data, indent=1)[:1500]}\n```"


def _first_user_text(messages: list[dict[str, Any]]) -> str:
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            return m["content"]
    return ""


def _find(pattern: str, text: str, flags: int = 0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


_FACT_LABELS = {
    "revenue": r"(?:total\s+)?revenue[s]?|net\s+sales|sales",
    "cost_of_goods_sold": r"cost\s+of\s+(?:goods\s+sold|sales)|cogs",
    "gross_profit": r"gross\s+profit",
    "operating_expenses": r"(?:total\s+)?operating\s+expenses",
    "net_income": r"net\s+income|net\s+profit|net\s+earnings",
    "total_assets": r"total\s+assets",
    "current_assets": r"(?:total\s+)?current\s+assets",
    "cash": r"cash(?:\s+and\s+cash\s+equivalents)?",
    "accounts_receivable": r"accounts\s+receivable(?:,\s*net)?",
    "inventory": r"inventor(?:y|ies)",
    "total_liabilities": r"total\s+liabilities",
    "current_liabilities": r"(?:total\s+)?current\s+liabilities",
    "long_term_debt": r"long[-\s]term\s+debt|notes\s+payable",
    "total_equity": r"total\s+(?:stockholders'?|shareholders'?|owners'?)?\s*equity",
    "wages": r"wages|salaries(?:\s+and\s+wages)?",
    "adjusted_gross_income": r"adjusted\s+gross\s+income|agi",
    "taxable_income": r"taxable\s+income",
    "total_tax": r"total\s+tax",
    "interest_income": r"interest\s+income",
    "dividend_income": r"(?:ordinary\s+)?dividends?",
    "schedule_c_net_profit": r"schedule\s+c\s+net\s+profit|net\s+profit\s+\(schedule\s+c\)",
}


def _regex_facts(text: str) -> list[dict[str, Any]]:
    facts = []
    # Try structured JSON first (the text may be wrapped in a prompt, so find the outermost object).
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
        for m in re.finditer(rf"(?im)^\s*(?:{pat})\s*[:\-|]?\s*\$?\s*\(?(-?[\d,]+(?:\.\d+)?)\)?", text):
            raw = m.group(1).replace(",", "")
            try:
                val = float(raw)
            except ValueError:
                continue
            if m.group(0).strip().endswith(")"):
                val = -abs(val)
            facts.append({"name": name, "value": val, "period": default_year, "unit": "USD", "source_quote": m.group(0).strip()[:120]})
            break
    return facts


def _primary_year(text: str) -> int | None:
    """The year a document reports on, not the latest year it mentions.
    Prefers explicit 'year ended ... 2025' / 'tax year 2025' phrasing, then the most frequent year."""
    m = re.search(r"(?:year[s]?\s+ended|tax\s+year|fiscal\s+year|for\s+the\s+year|as\s+of)[^\n\d]{0,40}(20[0-4]\d)", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"[\"']?(?:tax_year|fiscal_year|period)[\"']?\s*[:=]\s*[\"']?(20[0-4]\d)", text)
    if m:
        return int(m.group(1))
    years = re.findall(r"(?<!\d)(20[0-4]\d)(?!\d)", text)
    if not years:
        return None
    counts = {}
    for y in years:
        counts[y] = counts.get(y, 0) + 1
    best = max(counts.values())
    return int(max(y for y, c in counts.items() if c == best))


def _facts_from_json(data: Any, period: int | None = None) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    if isinstance(data, dict):
        period = data.get("period") or data.get("tax_year") or data.get("fiscal_year") or period
        try:
            period = int(period) if period is not None else None
        except (TypeError, ValueError):
            period = None
        for k, v in data.items():
            key = re.sub(r"[^a-z0-9]+", "_", str(k).lower()).strip("_")
            if isinstance(v, (int, float)) and not isinstance(v, bool) and key in _FACT_LABELS:
                facts.append({"name": key, "value": float(v), "period": period, "unit": "USD", "source_quote": f"{k}: {v}"})
            elif isinstance(v, (dict, list)):
                facts.extend(_facts_from_json(v, period))
    elif isinstance(data, list):
        for item in data:
            facts.extend(_facts_from_json(item, period))
    return facts


def _guess_doc_type(text: str) -> str:
    t = text.lower().replace("_", " ")
    if "form 1040" in t or "1040" in t and "tax" in t:
        return "individual_tax_return"
    if "1120" in t or "1065" in t:
        return "business_tax_return"
    if "balance sheet" in t and ("income statement" in t or "profit and loss" in t):
        return "financial_statements"
    if "balance sheet" in t:
        return "balance_sheet"
    if "income statement" in t or "profit and loss" in t:
        return "income_statement"
    if "trial balance" in t:
        return "trial_balance"
    if "audit" in t and ("opinion" in t or "finding" in t or "workpaper" in t):
        return "audit_workpaper"
    if "engagement letter" in t:
        return "engagement_letter"
    return "other"
