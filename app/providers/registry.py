"""Maps provider names in models.yaml to adapter classes."""
from __future__ import annotations

from typing import Callable

from ..config import SlotConfig
from .base import EmbeddingProvider, LLMProvider

_LLM_FACTORIES: dict[str, Callable[[SlotConfig], LLMProvider]] = {}
_EMBED_FACTORIES: dict[str, Callable[[SlotConfig], EmbeddingProvider]] = {}


def register_llm(name: str):
    def deco(factory):
        _LLM_FACTORIES[name] = factory
        return factory
    return deco


def register_embedding(name: str):
    def deco(factory):
        _EMBED_FACTORIES[name] = factory
        return factory
    return deco


def build_llm_provider(cfg: SlotConfig) -> LLMProvider:
    _import_adapters()
    try:
        factory = _LLM_FACTORIES[cfg.provider]
    except KeyError:
        raise ValueError(f"No LLM provider named '{cfg.provider}'. Known: {sorted(_LLM_FACTORIES)}")
    return factory(cfg)


def build_embedding_provider(cfg: SlotConfig) -> EmbeddingProvider:
    _import_adapters()
    try:
        factory = _EMBED_FACTORIES[cfg.provider]
    except KeyError:
        raise ValueError(f"No embedding provider named '{cfg.provider}'. Known: {sorted(_EMBED_FACTORIES)}")
    return factory(cfg)


def known_providers() -> dict[str, list[str]]:
    _import_adapters()
    return {"llm": sorted(_LLM_FACTORIES), "embedding": sorted(_EMBED_FACTORIES)}


def _import_adapters() -> None:
    # Imported lazily so an adapter with a missing optional dependency does
    # not break profiles that never use it.
    from . import anthropic_llm, mock_llm, hash_embed, voyage_embed, openai_embed  # noqa: F401
