"""Claude adapter (official `anthropic` SDK).

Model, effort, max_tokens and thinking mode all come from models.yaml, so
moving to a newer Claude release is a one-line config change.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from ..config import SlotConfig
from .base import LLMProvider, LLMResponse, ToolCall, ToolSpec
from .registry import register_llm

log = logging.getLogger(__name__)


@register_llm("anthropic")
class AnthropicLLM(LLMProvider):
    def __init__(self, cfg: SlotConfig):
        import anthropic  # imported here so the offline profile never needs it

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()  # ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / `ant auth login`
        self.model = cfg.model or "claude-opus-5"
        self.identity = cfg.identity
        self.max_tokens = int(cfg.options.get("max_tokens", 16000))
        self.effort = cfg.options.get("effort", "high")
        self.thinking = cfg.options.get("thinking", "adaptive")

    # ------------------------------------------------------------------ chat
    def chat(self, system: str, messages: list[dict[str, Any]], tools: list[ToolSpec] | None = None) -> LLMResponse:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            # Stable system prompt first so it is cacheable across a session.
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            output_config={"effort": self.effort},
        )
        if self.thinking == "adaptive":
            kwargs["thinking"] = {"type": "adaptive"}
        if tools:
            kwargs["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema, "strict": True}
                for t in tools
            ]
        try:
            resp = self.client.messages.create(**kwargs)
        except self._anthropic.RateLimitError as e:
            raise RuntimeError(f"Claude rate limit hit ({e.message}). Try again shortly.") from e
        except self._anthropic.APIStatusError as e:
            raise RuntimeError(f"Claude API error {e.status_code}: {e.message}") from e
        except self._anthropic.APIConnectionError as e:
            raise RuntimeError("Could not reach the Claude API (network error).") from e

        if resp.stop_reason == "refusal":
            detail = getattr(resp, "stop_details", None)
            why = getattr(detail, "explanation", None) or "safety refusal"
            return LLMResponse(text=f"The model declined this request: {why}", stop_reason="refusal", model=resp.model)

        text_parts = [b.text for b in resp.content if b.type == "text"]
        calls = [ToolCall(id=b.id, name=b.name, input=dict(b.input)) for b in resp.content if b.type == "tool_use"]
        usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
        cached = getattr(resp.usage, "cache_read_input_tokens", None)
        if cached:
            usage["cache_read_input_tokens"] = cached
        return LLMResponse(
            text="\n".join(text_parts).strip(),
            tool_calls=calls,
            stop_reason=resp.stop_reason or "end_turn",
            model=resp.model,
            usage=usage,
            raw_content=resp.content,
        )

    # --------------------------------------------------------------- extract
    def extract_json(self, instructions: str, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=instructions,
            messages=[{"role": "user", "content": text}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError("Model refused extraction request")
        payload = next(b.text for b in resp.content if b.type == "text")
        return json.loads(payload)
