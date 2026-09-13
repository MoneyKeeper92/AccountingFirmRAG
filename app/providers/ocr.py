"""OCR providers for scanned PDFs and images.

Research (Prompt 9): Azure Document Intelligence prebuilt tax models for structured W-2 / 1099 /
1040 pages (about $10 per 1,000 pages); frontier-model vision for K-1s and messy layouts
(about $30 per 1,000 pages); always prefer an existing text layer. Google's legacy 1099 path
sunsets 2026-06-30. Vendor accuracy claims are directional only: spot-check on the firm's own
scans during onboarding.

The pipeline calls `extract_pages` only when the PDF has no usable text layer.
"""
from __future__ import annotations

import abc
import base64
import os
import time
from typing import Callable

import httpx

from ..config import SlotConfig

_OCR_FACTORIES: dict[str, Callable[[SlotConfig], "OCRProvider"]] = {}


def register_ocr(name: str):
    def deco(factory):
        _OCR_FACTORIES[name] = factory
        return factory
    return deco


def build_ocr_provider(cfg: SlotConfig | None) -> "OCRProvider | None":
    if cfg is None or cfg.provider in ("none", ""):
        return None
    try:
        return _OCR_FACTORIES[cfg.provider](cfg)
    except KeyError:
        raise ValueError(f"No OCR provider named '{cfg.provider}'. Known: {sorted(_OCR_FACTORIES)}")


class OCRProvider(abc.ABC):
    identity: str = "ocr"

    @abc.abstractmethod
    def extract_pages(self, data: bytes, filename: str) -> list[str]: ...


@register_ocr("azure_di")
class AzureDocumentIntelligence(OCRProvider):
    """Azure Document Intelligence via REST. model: prebuilt-layout (default), prebuilt-read,
    or a tax prebuilt such as prebuilt-tax.us.w2 / prebuilt-tax.us.1099 / prebuilt-tax.us.1040."""

    def __init__(self, cfg: SlotConfig, http: httpx.Client | None = None):
        self.endpoint = cfg.options.get("endpoint") or os.environ["AZURE_DI_ENDPOINT"]
        self.key = os.environ.get(cfg.options.get("api_key_env", "AZURE_DI_KEY"), "")
        self.model = cfg.model or "prebuilt-layout"
        self.api_version = cfg.options.get("api_version", "2024-11-30")
        self.identity = f"azure_di:{self.model}"
        self.http = http or httpx.Client(timeout=120)

    def extract_pages(self, data: bytes, filename: str) -> list[str]:
        url = f"{self.endpoint.rstrip('/')}/documentintelligence/documentModels/{self.model}:analyze?api-version={self.api_version}"
        r = self.http.post(url, headers={"Ocp-Apim-Subscription-Key": self.key, "Content-Type": "application/json"},
                           json={"base64Source": base64.b64encode(data).decode()})
        r.raise_for_status()
        op = r.headers.get("operation-location")
        if not op:
            raise RuntimeError("Azure DI did not return an operation-location header")
        for _ in range(120):
            time.sleep(1.0)
            s = self.http.get(op, headers={"Ocp-Apim-Subscription-Key": self.key})
            s.raise_for_status()
            body = s.json()
            if body.get("status") == "succeeded":
                result = body["analyzeResult"]
                pages = result.get("pages") or []
                if pages and all("lines" in p for p in pages):
                    return ["\n".join(ln.get("content", "") for ln in p["lines"]) for p in pages]
                return [result.get("content", "")]
            if body.get("status") == "failed":
                raise RuntimeError(f"Azure DI analysis failed: {body.get('error')}")
        raise TimeoutError("Azure DI analysis did not finish")


@register_ocr("anthropic_vision")
class ClaudeVisionOCR(OCRProvider):
    """Send the scanned PDF to Claude as a document block and ask for a faithful transcription,
    page by page. Uses the same credentials and data-retention terms as the LLM slot."""

    def __init__(self, cfg: SlotConfig, client=None):
        import anthropic

        self.client = client or anthropic.Anthropic()
        self.model = cfg.model or "claude-sonnet-5"
        self.identity = f"anthropic_vision:{self.model}"
        self.max_tokens = int(cfg.options.get("max_tokens", 16000))
        self.inference_geo = cfg.options.get("inference_geo")

    def extract_pages(self, data: bytes, filename: str) -> list[str]:
        media = "application/pdf" if filename.lower().endswith(".pdf") else "image/png"
        block = {"type": "document" if media == "application/pdf" else "image",
                 "source": {"type": "base64", "media_type": media, "data": base64.b64encode(data).decode()}}
        kwargs = dict(
            model=self.model, max_tokens=self.max_tokens,
            system="You transcribe scanned tax documents exactly. Output plain text. Keep every label and number as printed, "
                   "one field per line as 'Label: value'. Start each page with a line '=== PAGE n ==='. Do not summarise or infer.",
            messages=[{"role": "user", "content": [block, {"type": "text", "text": f"Transcribe {filename}."}]}],
            output_config={"effort": "low"},
        )
        if self.inference_geo:
            kwargs["inference_geo"] = self.inference_geo
        with self.client.messages.stream(**kwargs) as stream:
            resp = stream.get_final_message()
        text = "\n".join(b.text for b in resp.content if b.type == "text")
        pages = [p.strip() for p in text.split("=== PAGE") if p.strip()]
        return [p.split("===", 1)[-1].strip() if p[:1].isdigit() else p for p in pages] or [text]
