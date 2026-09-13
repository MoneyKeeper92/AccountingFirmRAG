"""IRS Wage and Income transcript parsing and request-list reconciliation.

Research (Prompt 8): the CPA path is the Transcript Delivery System with a Form 8821 / 2848 on
file. The wage-and-income (W&I) transcript lists every information return the IRS received for
the taxpayer (W-2, 1099-INT/DIV/B/NEC/R/G/K/MISC, 1098, SSA-1099, 5498...). Used here as an
independent check next to what the client uploaded: the request list stops asking for what is
already in hand and asks specifically for what the IRS shows but the firm has not received.

Caveats baked into the UI text: current-year W&I data is often incomplete until late March,
identifiers are masked, and there is no state withholding on an IRS transcript.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

FORM_HEADER = re.compile(r"^\s*Form\s+(W-?2G?|1099-?(?:INT|DIV|B|NEC|MISC|R|G|K|SA|S|Q|OID|PATR|C|LTC)|1098-?(?:T|E|C)?|SSA-?1099|5498(?:-SA)?|1042-?S|3921|3922)\b.*$",
                         re.I | re.M)
ID_LINE = re.compile(r"identification\s+number|\bEIN\b|\bFIN\b|social\s+security\s+number|\bSSN\b|\bTIN\b|account\s+number|^\s*\d{3}-\d{2}-\d{4}", re.I)
ROLE_LINE = re.compile(r"^\s*(Employer|Payer|Lender|Filer|Issuer|Recipient|Employee|Borrower|Student|Beneficiary|Trustee|Participant)\s*:?\s*$", re.I)
AMOUNT = re.compile(r"^\s*([A-Za-z][A-Za-z ,'/()&\-]+?)\s*:\s*\$?\s*(-?[\d,]+(?:\.\d{2})?)\s*$", re.M)

KEY_AMOUNT = {
    "W-2": ["Wages, Tips and Other Compensation", "Wages Tips and Other Compensation"],
    "1099-INT": ["Interest", "Interest Income"],
    "1099-DIV": ["Ordinary Dividend", "Ordinary Dividends", "Total Ordinary Dividends"],
    "1099-B": ["Proceeds", "Gross Proceeds"],
    "1099-NEC": ["Non-Employee Compensation", "Nonemployee Compensation"],
    "1099-MISC": ["Other Income", "Rents", "Royalties"],
    "1099-R": ["Gross Distribution", "Taxable Amount"],
    "1099-G": ["Unemployment Compensation", "State or Local Income Tax Refunds"],
    "1099-K": ["Gross Amount of Payment Card/Third Party Network Transactions", "Gross Amount"],
    "1099-SA": ["Gross Distribution"],
    "1098": ["Mortgage Interest Received from Payer(s)/Borrower(s)", "Mortgage Interest Received", "Mortgage Interest"],
    "1098-T": ["Payments Received for Qualified Tuition", "Amounts Billed"],
    "1098-E": ["Student Loan Interest Received"],
    "SSA-1099": ["Benefits Paid", "Benefits Paid for Year"],
    "5498": ["IRA Contributions", "Fair Market Value of Account"],
}

# transcript form -> request-list rule key of the generic item it makes specific
FORM_TO_ITEM_KEY = {
    "W-2": "w2", "1099-INT": "1099_int", "1099-DIV": "1099_div", "1099-B": "1099_b", "1099-NEC": "sched_c_income",
    "1099-K": "sched_c_income", "1099-MISC": "sched_c_income", "1099-R": "retirement", "5498": "retirement", "5498-SA": "hsa",
    "1099-SA": "hsa", "1098": "1098_mortgage", "1098-T": "1098_t", "1098-E": "student_loan", "SSA-1099": None, "1099-G": None, "W-2G": None,
}
FORM_CATEGORY = {"1098": "Deductions", "1098-T": "Credits", "1098-E": "Deductions", "1099-SA": "Deductions", "5498-SA": "Deductions"}


@dataclass
class TranscriptEntry:
    form: str
    payer: str
    amount: float | None
    amount_label: str | None
    amounts: dict[str, float] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"irs:{self.form.lower()}:{_slug(self.payer)}"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "unknown"


def _norm_form(raw: str) -> str:
    f = raw.upper().replace(" ", "")
    if f in ("W2", "W-2"):
        return "W-2"
    if f in ("W2G", "W-2G"):
        return "W-2G"
    if f.startswith("SSA"):
        return "SSA-1099"
    if f.startswith("1099") and "-" not in f:
        return "1099-" + f[4:]
    if f.startswith("1098") and "-" not in f and len(f) > 4:
        return "1098-" + f[4:]
    if f.startswith("5498") and "-" not in f and len(f) > 4:
        return "5498-" + f[4:]
    return f


def is_wage_income_transcript(text: str) -> bool:
    t = text.lower()
    return "wage and income transcript" in t or ("wage & income" in t and "transcript" in t) or ("transcript" in t and "form w-2" in t and "employer" in t)


def tax_period(text: str) -> int | None:
    m = re.search(r"Tax\s+Period\s+Requested\s*:?\s*[A-Za-z]*,?\s*(20\d\d)", text, re.I)
    return int(m.group(1)) if m else None


def parse_wage_income_transcript(text: str) -> list[TranscriptEntry]:
    heads = list(FORM_HEADER.finditer(text))
    entries: list[TranscriptEntry] = []
    for i, h in enumerate(heads):
        block = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        form = _norm_form(h.group(1))
        payer = _payer_name(block)
        amounts: dict[str, float] = {}
        for m in AMOUNT.finditer(block):
            label = " ".join(m.group(1).split())
            try:
                amounts[label] = float(m.group(2).replace(",", ""))
            except ValueError:
                continue
        amount, label = None, None
        for want in KEY_AMOUNT.get(form, []):
            for lab, val in amounts.items():
                if lab.lower().startswith(want.lower()):
                    amount, label = val, lab
                    break
            if amount is not None:
                break
        if amount is None and amounts:
            label, amount = next(iter(amounts.items()))
        entries.append(TranscriptEntry(form=form, payer=payer, amount=amount, amount_label=label, amounts=amounts))
    return entries


def _payer_name(block: str) -> str:
    lines = [ln.strip() for ln in block.splitlines()]
    payer_side = True
    for idx, ln in enumerate(lines):
        if not ln:
            continue
        rm = ROLE_LINE.match(ln)
        if rm:
            payer_side = rm.group(1).lower() in ("employer", "payer", "lender", "filer", "issuer", "trustee")
            continue
        if not payer_side:
            continue
        if ID_LINE.search(ln) or ":" in ln:
            continue
        if re.match(r"^\d", ln):                     # street address / zip
            continue
        return ln[:80]
    return "Unknown payer"


def reconcile(store, rl: dict, entries: list[TranscriptEntry], transcript_document_id: str | None, actor: str) -> dict:
    """Make the request list specific: one item per payer the IRS knows about, generic items retired,
    items already satisfied by a received document marked received."""
    by_key = store.items_by_key(rl["id"])
    docs = store.list_documents(rl["client_id"])
    year_docs = [d for d in docs if d.get("tax_year") == rl["tax_year"] and d["id"] != transcript_document_id]
    added = matched = retired = 0
    generic_hit: set[str] = set()
    details = []
    for e in entries:
        generic_key = FORM_TO_ITEM_KEY.get(e.form)
        amount_txt = f" (${e.amount:,.0f} per IRS wage & income transcript)" if e.amount is not None else " (per IRS wage & income transcript)"
        item_text = f"{e.form} from {e.payer}{amount_txt}"
        category = FORM_CATEGORY.get(e.form, "Income")
        existing = by_key.get(e.key)
        if not existing:
            existing = store.add_request_item(rl["id"], item_text, "Reported to the IRS by this payer", category, key=e.key)
            by_key[e.key] = existing
            added += 1
        if generic_key:
            generic_hit.add(generic_key)
        # already received? look for a document of the right form type mentioning the payer
        received_doc = _find_received(year_docs, e)
        if received_doc and existing["status"] != "received":
            store.set_request_item(existing["id"], "received", document_id=received_doc["id"])
            matched += 1
        details.append({"form": e.form, "payer": e.payer, "amount": e.amount, "item_id": existing["id"],
                        "status": "received" if received_doc else existing["status"], "document_id": received_doc["id"] if received_doc else None})
    for gk in generic_hit:
        g = by_key.get(gk)
        if g and g["status"] == "pending":
            store.set_request_item(g["id"], "not_applicable", note="Replaced by per-payer items from the IRS wage & income transcript")
            retired += 1
    result = {"entries": len(entries), "added": added, "matched_received": matched, "generic_retired": retired, "details": details,
              "caveats": ["Current-year wage & income data is often incomplete until late March; re-run after that.",
                          "IRS transcripts carry no state withholding and mask identifiers.",
                          "Payers that report late (K-1s, some brokerages) will not appear."]}
    store.log("transcript_reconcile", actor, rl["client_id"], list_id=rl["id"], transcript_document_id=transcript_document_id,
              entries=len(entries), added=added, matched_received=matched, generic_retired=retired)
    return result


_FORM_DOC_TYPES = {"W-2": {"w2"}, "1099-INT": {"1099_int"}, "1099-DIV": {"1099_div"}, "1099-B": {"1099_b"}, "1099-NEC": {"1099_nec"},
                   "1099-MISC": {"1099_misc"}, "1099-R": {"1099_r"}, "1099-G": {"1099_g"}, "1099-K": {"1099_k"}, "1098": {"1098_mortgage"},
                   "1098-T": {"1098_t"}, "1098-E": {"1098_e"}, "SSA-1099": {"ssa_1099"}}


def _find_received(year_docs: list[dict], e: TranscriptEntry) -> dict | None:
    words = [w for w in re.split(r"[^a-z0-9]+", e.payer.lower()) if len(w) > 2 and w not in ("inc", "llc", "corp", "the", "and", "bank", "company")]
    types = _FORM_DOC_TYPES.get(e.form, set())
    for d in year_docs:
        hay = f"{d.get('filename', '')} {d.get('summary', '')}".lower()
        form_ok = d.get("doc_type") in types or e.form.lower().replace("-", "") in hay.replace("-", "")
        payer_ok = any(w in hay for w in words) if words else False
        if form_ok and payer_ok:
            return d
    return None
