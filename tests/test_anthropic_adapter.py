"""Shape tests for the Claude adapter using a stubbed SDK client (no network)."""
import json
from types import SimpleNamespace

import pytest

from app.config import SlotConfig
from app.providers.base import ToolSpec


@pytest.fixture()
def adapter(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    from app.providers.anthropic_llm import AnthropicLLM

    cfg = SlotConfig.from_dict({"provider": "anthropic", "model": "claude-opus-5", "effort": "high", "thinking": "adaptive", "max_tokens": 4096})
    a = AnthropicLLM(cfg)
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        if "format" in kwargs.get("output_config", {}):
            block = SimpleNamespace(type="text", text=json.dumps({"doc_type": "other", "tax_year": 2025, "summary": "s", "entities": [], "facts": [], "risk_flags": []}))
        else:
            block = SimpleNamespace(type="tool_use", id="tu_1", name="assess_risk", input={"client_id": "abc"})
        return SimpleNamespace(content=[block], stop_reason="tool_use", model="claude-opus-5",
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0), stop_details=None)

    a.client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
    return a, captured


def test_chat_request_shape(adapter):
    a, captured = adapter
    tool = ToolSpec(name="assess_risk", description="d", input_schema={"type": "object", "properties": {"client_id": {"type": "string"}}, "required": ["client_id"], "additionalProperties": False})
    r = a.chat("SYSTEM", [{"role": "user", "content": "hi"}], [tool])
    assert captured["model"] == "claude-opus-5"
    assert captured["thinking"] == {"type": "adaptive"}
    assert captured["output_config"] == {"effort": "high"}
    assert captured["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert captured["tools"][0]["strict"] is True
    assert "temperature" not in captured and "budget_tokens" not in json.dumps(captured, default=str)
    assert r.tool_calls[0].name == "assess_risk" and r.tool_calls[0].input == {"client_id": "abc"}
    assert r.stop_reason == "tool_use"


def test_extract_json_uses_structured_output(adapter):
    a, captured = adapter
    out = a.extract_json("instructions", "doc text", {"type": "object", "properties": {}, "additionalProperties": False})
    assert captured["output_config"]["format"]["type"] == "json_schema"
    assert out["tax_year"] == 2025
