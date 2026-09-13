"""Provider interfaces.

The rest of the application only ever talks to these two abstract classes.
Adding a new vendor (or a newer model from the same vendor) means writing one
small adapter class and registering it in registry.py. No other code changes.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    """A tool the LLM may call. Schema is plain JSON Schema."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    # Opaque provider-native content blocks, echoed back on the next turn so
    # multi-step tool use works. The application never inspects these.
    raw_content: Any = None


class LLMProvider(abc.ABC):
    """Chat + structured extraction."""

    identity: str = "unknown"

    @abc.abstractmethod
    def chat(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse: ...

    @abc.abstractmethod
    def extract_json(self, instructions: str, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON object that validates against `schema`."""

    # Helpers for building provider-neutral message history -----------------

    @staticmethod
    def user_message(text: str) -> dict[str, Any]:
        return {"role": "user", "content": text}

    @staticmethod
    def tool_result_message(results: list[tuple[str, str]]) -> dict[str, Any]:
        """results: list of (tool_call_id, result_text). One message, all results."""
        return {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": call_id, "content": text}
                for call_id, text in results
            ],
        }


class EmbeddingProvider(abc.ABC):
    identity: str = "unknown"
    dimensions: int = 0

    @abc.abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abc.abstractmethod
    def embed_query(self, text: str) -> list[float]: ...
