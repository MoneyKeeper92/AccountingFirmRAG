"""Any OpenAI-compatible /v1/embeddings endpoint (OpenAI, Azure, Ollama, TEI...)."""
from __future__ import annotations

import os

import httpx

from ..config import SlotConfig
from .base import EmbeddingProvider
from .registry import register_embedding


@register_embedding("openai_compatible")
class OpenAICompatibleEmbedding(EmbeddingProvider):
    def __init__(self, cfg: SlotConfig):
        self.model = cfg.model or "text-embedding-3-large"
        self.dimensions = int(cfg.options.get("dimensions", 1024))
        self.identity = f"{cfg.identity}:{self.dimensions}"
        self.base_url = cfg.options.get("base_url", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.environ.get(cfg.options.get("api_key_env", "OPENAI_API_KEY"), "local")
        self.send_dimensions = bool(cfg.options.get("send_dimensions", "openai.com" in self.base_url))

    def _call(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            body = {"model": self.model, "input": texts[i : i + 64]}
            if self.send_dimensions:
                body["dimensions"] = self.dimensions
            r = httpx.post(f"{self.base_url}/embeddings", headers={"Authorization": f"Bearer {self.api_key}"}, json=body, timeout=120)
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            out.extend(d["embedding"] for d in data)
        return out

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._call(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._call([text])[0]
