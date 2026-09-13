"""Runtime configuration. Everything comes from environment variables or models.yaml."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Tiny .env loader so the prototype has no python-dotenv dependency."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(ROOT / ".env")


@dataclass
class SlotConfig:
    """Configuration for one model slot (llm / extractor / embedding)."""

    provider: str
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SlotConfig":
        raw = dict(raw)
        provider = raw.pop("provider")
        model = raw.pop("model", None)
        return cls(provider=provider, model=model, options=raw)

    @property
    def identity(self) -> str:
        """Stable identifier used to version embeddings and audit which model answered."""
        return f"{self.provider}:{self.model or 'default'}"


@dataclass
class Settings:
    db_path: Path
    uploads_dir: Path
    models_path: Path
    profile_name: str
    api_token: str
    keep_originals: bool
    llm: SlotConfig
    extractor: SlotConfig
    embedding: SlotConfig
    ocr: SlotConfig | None
    available_profiles: list[str]

    @classmethod
    def load(cls, profile: str | None = None) -> "Settings":
        models_path = Path(os.environ.get("FIRM_RAG_MODELS", ROOT / "models.yaml"))
        registry = yaml.safe_load(models_path.read_text())
        profiles = registry["profiles"]
        profile_name = profile or os.environ.get("FIRM_RAG_PROFILE") or registry.get("default_profile", "offline")
        if profile_name not in profiles:
            raise ValueError(f"Unknown model profile '{profile_name}'. Known: {sorted(profiles)}")
        p = profiles[profile_name]
        db_path = Path(os.environ.get("FIRM_RAG_DB", ROOT / "data" / "firm_rag.db"))
        uploads_dir = Path(os.environ.get("FIRM_RAG_UPLOADS", ROOT / "data" / "uploads"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        uploads_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            db_path=db_path,
            uploads_dir=uploads_dir,
            models_path=models_path,
            profile_name=profile_name,
            api_token=os.environ.get("FIRM_RAG_API_TOKEN", "change-me"),
            keep_originals=os.environ.get("FIRM_RAG_KEEP_ORIGINALS", "true").lower() in ("1", "true", "yes"),
            llm=SlotConfig.from_dict(p["llm"]),
            extractor=SlotConfig.from_dict(p.get("extractor", p["llm"])),
            embedding=SlotConfig.from_dict(p["embedding"]),
            ocr=SlotConfig.from_dict(p["ocr"]) if p.get("ocr") else None,
            available_profiles=sorted(profiles),
        )
