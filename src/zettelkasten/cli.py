from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from zettelkasten.adapters.ai.deepseek import DeepSeekProvider
from zettelkasten.adapters.ai.fake import FakeAIProvider
from zettelkasten.adapters.ai.protocol import AIProvider
from zettelkasten.adapters.notion.notion import NotionNoteStore
from zettelkasten.adapters.pdf import extract_pdf_chunks
from zettelkasten.app.extract import iter_atomic_notes
from zettelkasten.app.persist import persist_notes
from zettelkasten.config import Settings, load_settings
from zettelkasten.models import AtomicNote, SourceText

logger = logging.getLogger("zettelkasten")


class _StderrHandler(logging.Handler):
    """Write to the current ``sys.stderr`` (safe across pytest capture resets)."""

    terminator = "\n"

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            stream = sys.stderr
            stream.write(msg + self.terminator)
            stream.flush()
        except Exception:
            self.handleError(record)


def _configure_logging() -> None:
    package_logger = logging.getLogger("zettelkasten")
    if package_logger.handlers:
        return
    handler = _StderrHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    package_logger.addHandler(handler)
    package_logger.setLevel(logging.INFO)
    package_logger.propagate = False


def main(argv: list[str] | None = None) -> None:
    _configure_logging()
    parser = argparse.ArgumentParser(
        description="Extract atomic Zettelkasten notes from text.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Input file path. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--fake",
        action="store_true",
        help="Use the deterministic fake AI provider (no network).",
    )
    parser.add_argument(
        "--notion",
        action="store_true",
        help="Persist extracted notes to the configured Notion database.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown). json streams one object per line.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    ai = _build_provider(fake=args.fake, settings=settings)
    store = _build_notion_store(settings) if args.notion else None

    try:
        sources = _load_sources(args.path)
        _run(sources, ai, store=store, fmt=args.format)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"Extraction failed: {exc}") from exc


def _load_sources(path: str | None) -> list[SourceText]:
    if path is not None and Path(path).suffix.lower() == ".pdf":
        file_path = Path(path)
        try:
            chunks = extract_pdf_chunks(file_path)
        except Exception as exc:
            raise SystemExit(f"Failed to read PDF {file_path}: {exc}") from exc
        if not chunks:
            raise SystemExit(f"Failed to read PDF {file_path}: no extractable text")
        try:
            return [SourceText(content=chunk) for chunk in chunks]
        except ValidationError as exc:
            raise SystemExit(f"Invalid PDF content from {file_path}: {exc}") from exc

    content = _read_text_input(path)
    try:
        return [SourceText(content=content)]
    except ValidationError as exc:
        raise SystemExit(f"Invalid source text: {exc}") from exc


def _run(
    sources: list[SourceText],
    ai: AIProvider,
    *,
    store: NotionNoteStore | None,
    fmt: str,
) -> None:
    note_count = 0
    page_ids: list[str] = []
    markdown_sep = False

    for note in iter_atomic_notes(sources, ai):
        note_count += 1
        _emit_note(note, fmt=fmt, markdown_sep=markdown_sep)
        markdown_sep = True

        if store is not None:
            created = persist_notes([note], store)
            page_ids.extend(created)

    if note_count == 0 and fmt == "markdown":
        print("_No atomic notes extracted._")

    if store is not None:
        logger.info("Created %d Notion page(s).", len(page_ids))


def _emit_note(note: AtomicNote, *, fmt: str, markdown_sep: bool) -> None:
    if fmt == "json":
        print(json.dumps(note.model_dump(), ensure_ascii=False), flush=True)
        return

    if markdown_sep:
        print("\n---\n", flush=True)
    print(_format_one_note(note), flush=True)


def _read_text_input(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _build_provider(*, fake: bool, settings: Settings) -> AIProvider:
    if fake:
        return FakeAIProvider()
    return DeepSeekProvider(
        settings.deepseek.api_key,
        model=settings.deepseek.api_model,
    )


def _build_notion_store(settings: Settings) -> NotionNoteStore:
    try:
        return NotionNoteStore(
            settings.notion.api_key,
            database_id=settings.notion.database_id,
            title_property=settings.notion.title_property,
            tags_property=settings.notion.tags_property,
        )
    except ValueError as exc:
        raise SystemExit(
            "Notion requires NOTION_API_KEY and NOTION_DATABASE_ID in the environment."
        ) from exc


def _format_one_note(note: AtomicNote) -> str:
    tags = ", ".join(f"`{tag}`" for tag in note.tags) if note.tags else "_none_"
    return f"# {note.title}\n\n{note.content}\n\nTags: {tags}"


if __name__ == "__main__":
    main()
