"""Voyage AI embeddings via plain HTTPS (no extra SDK)."""
from __future__ import annotations

import os

import httpx

from ..config import SlotConfig
from .base import EmbeddingProvider
from .registry import register_embedding


@register_embedding("voyage")
class VoyageEmbedding(EmbeddingProvider):
    def __init__(self, cfg: SlotConfig):
        self.model = cfg.model or "voyage-3.5"
        self.dimensions = int(cfg.options.get("dimensions", 1024))
        self.identity = f"{cfg.identity}:{self.dimensions}"
        self.api_key = os.environ.get(cfg.options.get("api_key_env", "VOYAGE_API_KEY"), "")
        self.base_url = cfg.options.get("base_url", "https://api.voyageai.com/v1")
        self.q_type = cfg.options.get("input_type_query", "query")
        self.d_type = cfg.options.get("input_type_document", "document")
        if not self.api_key:
            raise RuntimeError("VOYAGE_API_KEY is not set (required by the voyage embedding provider)")

    def _call(self, texts: list[str], input_type: str) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            batch = texts[i : i + 64]
            r = httpx.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": batch, "input_type": input_type, "output_dimension": self.dimensions},
                timeout=60,
            )
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            out.extend(d["embedding"] for d in data)
        return out

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._call(texts, self.d_type)

    def embed_query(self, text: str) -> list[float]:
        return self._call([text], self.q_type)[0]
