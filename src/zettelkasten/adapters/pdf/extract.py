from pathlib import Path

import pymupdf
import pymupdf4llm

PAGES_PER_CHUNK = 6


def extract_pdf_chunks(
    path: Path,
    *,
    pages_per_chunk: int = PAGES_PER_CHUNK,
) -> list[str]:
    """Extract markdown text from a PDF as page-based chunks."""
    if pages_per_chunk < 1:
        raise ValueError("pages_per_chunk must be >= 1")

    doc = pymupdf.open(path)
    try:
        page_count = doc.page_count
        chunks: list[str] = []
        for start in range(0, page_count, pages_per_chunk):
            pages = list(range(start, min(start + pages_per_chunk, page_count)))
            markdown = pymupdf4llm.to_markdown(doc, pages=pages)
            if not isinstance(markdown, str):
                raise TypeError(
                    f"Expected str from pymupdf4llm.to_markdown, got {type(markdown)!r}"
                )
            stripped = markdown.strip()
            if stripped:
                chunks.append(stripped)
        return chunks
    finally:
        doc.close()
