from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from zettelkasten.adapters.ai.deepseek import DeepSeekProvider
from zettelkasten.adapters.ai.fake import FakeAIProvider
from zettelkasten.adapters.ai.protocol import AIProvider
from zettelkasten.app.extract import extract_atomic_notes
from zettelkasten.config import load_settings
from zettelkasten.models import AtomicNote, SourceText


def main(argv: list[str] | None = None) -> None:
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
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args(argv)

    content = _read_input(args.path)
    source = SourceText(content=content)
    ai = _build_provider(fake=args.fake)
    notes = extract_atomic_notes(source, ai)

    if args.format == "json":
        print(
            json.dumps(
                [note.model_dump() for note in notes], indent=2, ensure_ascii=False
            )
        )
    else:
        print(_format_markdown(notes))


def _read_input(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _build_provider(*, fake: bool) -> AIProvider:
    if fake:
        return FakeAIProvider()

    settings = load_settings()
    return DeepSeekProvider(
        settings.deepseek.api_key,
        model=settings.deepseek.api_model,
    )


def _format_markdown(notes: list[AtomicNote]) -> str:
    if not notes:
        return "_No atomic notes extracted._"

    blocks: list[str] = []
    for note in notes:
        tags = ", ".join(f"`{tag}`" for tag in note.tags) if note.tags else "_none_"
        blocks.append(f"# {note.title}\n\n{note.content}\n\nTags: {tags}")
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    main()
