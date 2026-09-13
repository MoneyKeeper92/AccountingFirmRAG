"""Offline embedding: hashed bag-of-words + character trigrams, L2-normalised.

Good enough to demonstrate retrieval on the sample data with no network.
Not for production - replace via models.yaml.
"""
from __future__ import annotations

import hashlib
import math
import re

import numpy as np

from ..config import SlotConfig
from .base import EmbeddingProvider
from .registry import register_embedding

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


@register_embedding("hash")
class HashEmbedding(EmbeddingProvider):
    def __init__(self, cfg: SlotConfig):
        self.dimensions = int(cfg.options.get("dimensions", 384))
        self.identity = f"{cfg.identity}:{self.dimensions}"

    def _vec(self, text: str) -> list[float]:
        v = np.zeros(self.dimensions, dtype=np.float32)
        tokens = _TOKEN.findall(text.lower())
        feats = list(tokens)
        for t in tokens:
            if len(t) > 4:
                feats.extend(t[i : i + 3] for i in range(len(t) - 2))
        for f in feats:
            h = int.from_bytes(hashlib.blake2b(f.encode(), digest_size=8).digest(), "little")
            idx = h % self.dimensions
            sign = 1.0 if (h >> 63) & 1 else -1.0
            v[idx] += sign * (1.0 + math.log(1 + len(f)))
        n = float(np.linalg.norm(v))
        return (v / n).tolist() if n else v.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)
