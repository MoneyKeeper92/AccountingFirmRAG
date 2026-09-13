"""Page-aware chunking with overlap. Keeps a section heading with every chunk
so retrieved passages stay self-describing."""
from __future__ import annotations

import re

HEADING = re.compile(r"^(?:[A-Z][A-Z &/\-]{4,}|\[Sheet: .+\]|#+ .+|(?:Schedule|Form|Note|Part)\s+[A-Z0-9\-]+.*)$", re.M)


def chunk_pages(pages: list[str], target_chars: int = 1400, overlap_chars: int = 200) -> list[dict]:
    chunks: list[dict] = []
    for page_no, page in enumerate(pages, start=1):
        page = page.strip()
        if not page:
            continue
        section = None
        paras = re.split(r"\n\s*\n|\n(?=[A-Z][A-Z ]{4,}\n)", page)
        buf = ""
        for para in paras:
            para = para.strip()
            if not para:
                continue
            m = HEADING.match(para.split("\n", 1)[0])
            if m:
                section = m.group(0).strip()[:80]
            if len(buf) + len(para) + 2 > target_chars and buf:
                chunks.append({"page": page_no, "section": section, "text": buf.strip()})
                buf = buf[-overlap_chars:] + "\n" + para
            else:
                buf = (buf + "\n\n" + para) if buf else para
            while len(buf) > target_chars * 2:      # very long single paragraph
                chunks.append({"page": page_no, "section": section, "text": buf[:target_chars].strip()})
                buf = buf[target_chars - overlap_chars:]
        if buf.strip():
            chunks.append({"page": page_no, "section": section, "text": buf.strip()})
    return chunks
