"""Turn uploaded files into plain text pages.

Supported: PDF (text layer), CSV, XLSX, JSON, TXT/MD. Scanned PDFs with no
text layer are flagged so the onboarding checklist can route them to OCR
(see docs/ONBOARDING_PLAYBOOK.md).
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedFile:
    pages: list[str]                 # one entry per page / sheet / logical section
    kind: str                        # pdf | csv | xlsx | json | text
    needs_ocr: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(self.pages)


def parse_file(filename: str, data: bytes) -> ParsedFile:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(data)
    if ext == ".csv":
        return _parse_csv(data)
    if ext in (".xlsx", ".xlsm"):
        return _parse_xlsx(data)
    if ext == ".json":
        return _parse_json(data)
    if ext in (".txt", ".md", ".qbo", ".iif", ".ofx", ".tsv", ""):
        return ParsedFile(pages=[data.decode("utf-8", errors="replace")], kind="text")
    raise ValueError(f"Unsupported file type '{ext}'. Supported: pdf, csv, xlsx, json, txt, md")


def _parse_pdf(data: bytes) -> ParsedFile:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages, warnings = [], []
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            warnings.append("PDF is password protected")
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception as e:  # pragma: no cover
            pages.append("")
            warnings.append(f"page extraction failed: {e}")
    total_chars = sum(len(p.strip()) for p in pages)
    needs_ocr = total_chars < 40 * max(1, len(pages))
    if needs_ocr:
        warnings.append("Little or no text layer found - this looks like a scanned PDF and needs OCR before it is useful.")
    return ParsedFile(pages=pages, kind="pdf", needs_ocr=needs_ocr, warnings=warnings)


def _parse_csv(data: bytes) -> ParsedFile:
    text = data.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    return ParsedFile(pages=[_rows_to_text(rows)], kind="csv")


def _parse_xlsx(data: bytes) -> ParsedFile:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    pages = []
    for ws in wb.worksheets:
        rows = [[("" if c is None else str(c)) for c in row] for row in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(cell.strip() for cell in r)]
        if rows:
            pages.append(f"[Sheet: {ws.title}]\n" + _rows_to_text(rows))
    return ParsedFile(pages=pages or [""], kind="xlsx")


def _parse_json(data: bytes) -> ParsedFile:
    obj = json.loads(data.decode("utf-8", errors="replace"))
    # Pretty JSON is both embeddable and readable in citations.
    return ParsedFile(pages=[json.dumps(obj, indent=2)], kind="json")


def _rows_to_text(rows: list[list[str]]) -> str:
    lines = []
    for r in rows:
        cells = [c.strip() for c in r]
        if not any(cells):
            continue
        if len(cells) == 2 and cells[1]:
            lines.append(f"{cells[0]}: {cells[1]}")        # label/value layouts read naturally
        else:
            lines.append(" | ".join(cells))
    return "\n".join(lines)
