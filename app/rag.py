"""Retrieval-augmented chat with tool use.

Flow per question:
  1. Embed the question, retrieve top-k chunks (scoped to the selected client).
  2. Build a system prompt with the evidence and the client profile.
  3. Let the model answer, calling deterministic tools for numbers
     (get_client_facts / forecast_financials / assess_risk / search_documents).
  4. Return the answer plus the citations that were actually retrieved.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from . import forecast
from .providers.base import EmbeddingProvider, LLMProvider, ToolSpec
from .store import SearchHit, Store

SYSTEM_TEMPLATE = """You are the tax research assistant for a CPA firm. You answer preparers' and partners' questions about
their own clients using ONLY the firm's archived records supplied below and the tools provided. The archive holds
individual returns (1040 and schedules), partnership returns (1065), S corporation returns (1120-S), C corporation
returns (1120), K-1s, source documents (W-2, 1099s, 1098s), books, notices and preparer notes.

Ground rules:
- Every number you state must come from the evidence or from a tool result. Cite the source file (and page) in
  brackets like [file.pdf p.3]. If the archive does not contain something, say so plainly and name the document
  that would answer it.
- For projections call `forecast_financials`; for planning, "what should we watch", entity-choice, estimated-payment
  or reasonable-compensation questions call `assess_risk`; to pull a specific figure call `get_client_facts`.
  Explain the method and the assumptions behind any projection.
- Refer to forms and lines by name (Form 1040 line 11, Schedule C line 31, Form 1120-S Schedule K line 16d) when the
  evidence shows them.
- You support a licensed preparer; you do not replace their judgement. Flag positions that need professional
  review (elections, basis, reasonable compensation, penalties) rather than concluding on them.
- Length: {style_rule}

Active client: {client_line}
Firm context: today's date is {today}. Retrieved evidence follows.

<evidence>
{evidence}
</evidence>
"""

TOOLS = [
    ToolSpec(
        name="get_client_facts",
        description="Return the structured tax facts (name, value, period, source line) extracted from a client's documents. "
                    "Use for exact figures such as wages, AGI, taxable income, total tax, gross receipts, officer compensation, distributions.",
        input_schema={"type": "object", "properties": {
            "client_id": {"type": "string"},
            "names": {"type": "array", "items": {"type": "string"}, "description": "Optional list of fact names to filter, e.g. ['revenue','net_income']"},
        }, "required": ["client_id", "names"], "additionalProperties": False},
    ),
    ToolSpec(
        name="forecast_financials",
        description="Project each available metric (AGI, total tax, Schedule C profit, gross receipts, ordinary business income...) forward "
                    "using linear trend and CAGR over the years on file. Returns history, year-over-year changes and both projections.",
        input_schema={"type": "object", "properties": {
            "client_id": {"type": "string"},
            "periods_ahead": {"type": "integer", "minimum": 1, "maximum": 5},
            "metrics": {"type": "array", "items": {"type": "string"}, "description": "Optional subset of metric names; empty means all available"},
        }, "required": ["client_id", "periods_ahead", "metrics"], "additionalProperties": False},
    ),
    ToolSpec(
        name="assess_risk",
        description="Run tax-planning screens over the client's facts: estimated-payment safe harbour, S-corp election candidates, "
                    "reasonable compensation, distributions vs basis, accumulated earnings, itemize-vs-standard, year-over-year swings. "
                    "Returns key figures and ranked flags for the latest year on file.",
        input_schema={"type": "object", "properties": {"client_id": {"type": "string"}}, "required": ["client_id"], "additionalProperties": False},
    ),
    ToolSpec(
        name="search_documents",
        description="Semantic search over the archive for a follow-up query (e.g. a note disclosure or a specific schedule).",
        input_schema={"type": "object", "properties": {
            "query": {"type": "string"},
            "client_id": {"type": ["string", "null"]},
            "tax_year": {"type": ["integer", "null"]},
        }, "required": ["query", "client_id", "tax_year"], "additionalProperties": False},
    ),
]


@dataclass
class ChatResult:
    answer: str
    citations: list[dict[str, Any]]
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


class RagEngine:
    def __init__(self, store: Store, llm: LLMProvider, embedder: EmbeddingProvider, top_k: int = 8, max_tool_rounds: int = 6):
        self.store = store
        self.llm = llm
        self.embedder = embedder
        self.top_k = top_k
        self.max_tool_rounds = max_tool_rounds

    # ------------------------------------------------------------ retrieval
    def retrieve(self, query: str, client_id: str | None, tax_year: int | None = None, top_k: int | None = None) -> list[SearchHit]:
        vec = self.embedder.embed_query(query)
        return self.store.search(vec, self.embedder.identity, client_id=client_id, top_k=top_k or self.top_k, tax_year=tax_year)

    @staticmethod
    def _format_evidence(hits: list[SearchHit]) -> str:
        blocks = []
        for i, h in enumerate(hits, 1):
            loc = f"{h.filename}" + (f" p.{h.page}" if h.page else "") + (f" ({h.section})" if h.section else "")
            blocks.append(f"[{i}] source: {loc} | year: {h.tax_year} | type: {h.doc_type} | score: {h.score:.2f}\n{h.text}")
        return "\n\n".join(blocks) if blocks else "(nothing retrieved)"

    # ----------------------------------------------------------------- tools
    def _run_tool(self, name: str, args: dict[str, Any]) -> str:
        try:
            if name == "get_client_facts":
                facts = self.store.facts_for_client(args["client_id"], args.get("names") or None)
                slim = [{k: f[k] for k in ("name", "value", "period", "unit", "source_quote", "filename")} for f in facts]
                return json.dumps(slim or {"note": "no structured facts for this client"}, default=str)
            if name == "forecast_financials":
                facts = self.store.facts_for_client(args["client_id"])
                return json.dumps(forecast.forecast_client(facts, int(args.get("periods_ahead", 1)), args.get("metrics") or None), default=str)
            if name == "assess_risk":
                return json.dumps(forecast.assess_risk(self.store.facts_for_client(args["client_id"])), default=str)
            if name == "search_documents":
                hits = self.retrieve(args["query"], args.get("client_id"), args.get("tax_year"), top_k=5)
                return self._format_evidence(hits)
            return json.dumps({"error": f"unknown tool {name}"})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"error": f"{type(e).__name__}: {e}"})

    # ------------------------------------------------------------------ chat
    STYLE_RULES = {
        "brief": "Answer in at most four short sentences in plain words, as if speaking to a colleague across the desk. "
                 "No headings, no bullet lists, no tables. Give the number and the source, then stop. If more detail exists, end with "
                 "'Say \"more\" for the detail.'",
        "detailed": "Be concise and structured. Short tables are welcome for year-over-year comparisons.",
    }

    def ask(self, question: str, client_id: str | None, history: list[dict[str, str]] | None = None,
            actor: str | None = None, today: str = "", style: str = "detailed") -> ChatResult:
        hits = self.retrieve(question, client_id)
        client = self.store.get_client(client_id) if client_id else None
        client_line = (f"client_id={client['id']} | {client['name']} | {client.get('entity_type') or 'n/a'} | "
                       f"industry: {client.get('industry') or 'n/a'} | FYE: {client.get('fiscal_year_end') or 'n/a'}") if client else "none selected (firm-wide search)"
        system = SYSTEM_TEMPLATE.format(client_line=client_line, today=today, evidence=self._format_evidence(hits),
                                        style_rule=self.STYLE_RULES.get(style, self.STYLE_RULES["detailed"]))

        messages: list[dict[str, Any]] = []
        for turn in (history or [])[-8:]:
            if turn.get("role") in ("user", "assistant") and turn.get("content"):
                messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append(self.llm.user_message(question))

        trace: list[dict[str, Any]] = []
        usage: dict[str, int] = {}
        response = self.llm.chat(system, messages, TOOLS)
        rounds = 0
        while response.tool_calls and rounds < self.max_tool_rounds:
            rounds += 1
            results = []
            for call in response.tool_calls:
                out = self._run_tool(call.name, call.input)
                trace.append({"tool": call.name, "input": call.input, "output_preview": out[:400]})
                results.append((call.id, out))
            messages.append({"role": "assistant", "content": response.raw_content if response.raw_content is not None else
                             [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.input} for c in response.tool_calls]})
            messages.append(self.llm.tool_result_message(results))
            for k, v in response.usage.items():
                usage[k] = usage.get(k, 0) + v
            response = self.llm.chat(system, messages, TOOLS)
        for k, v in response.usage.items():
            usage[k] = usage.get(k, 0) + v

        citations = [{"n": i, "document_id": h.document_id, "filename": h.filename, "page": h.page, "section": h.section,
                      "tax_year": h.tax_year, "doc_type": h.doc_type, "score": round(h.score, 3), "excerpt": h.text[:300]}
                     for i, h in enumerate(hits, 1)]
        self.store.log("query", actor, client_id, question=question, model=response.model or self.llm.identity,
                       tools=[t["tool"] for t in trace], citations=[c["document_id"] for c in citations], usage=usage)
        return ChatResult(answer=response.text, citations=citations, tool_trace=trace, model=response.model or self.llm.identity, usage=usage)
