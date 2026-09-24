import io
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zettelkasten.adapters.pdf.extract import extract_pdf_chunks
from zettelkasten.app.extract import iter_atomic_notes
from zettelkasten.cli import main
from zettelkasten.models import MAX_ATOMIC_NOTES, AtomicNote, SourceText


def test_extract_pdf_chunks_splits_by_page_ranges() -> None:
    doc = MagicMock()
    doc.page_count = 13
    doc.close = MagicMock()

    def fake_to_markdown(_doc, pages=None):
        assert pages is not None
        return f"chunk pages {pages[0]}-{pages[-1]}"

    with (
        patch("zettelkasten.adapters.pdf.extract.pymupdf.open", return_value=doc),
        patch(
            "zettelkasten.adapters.pdf.extract.pymupdf4llm.to_markdown",
            side_effect=fake_to_markdown,
        ),
    ):
        chunks = extract_pdf_chunks(Path("paper.pdf"), pages_per_chunk=6)

    assert chunks == [
        "chunk pages 0-5",
        "chunk pages 6-11",
        "chunk pages 12-12",
    ]
    doc.close.assert_called_once()


def test_extract_pdf_chunks_skips_empty_ranges() -> None:
    doc = MagicMock()
    doc.page_count = 6
    doc.close = MagicMock()

    def fake_to_markdown(_doc, pages=None):
        if pages == [0, 1, 2]:
            return "  keep me  "
        return "   "

    with (
        patch("zettelkasten.adapters.pdf.extract.pymupdf.open", return_value=doc),
        patch(
            "zettelkasten.adapters.pdf.extract.pymupdf4llm.to_markdown",
            side_effect=fake_to_markdown,
        ),
    ):
        chunks = extract_pdf_chunks(Path("paper.pdf"), pages_per_chunk=3)

    assert chunks == ["keep me"]


def test_extract_chunked_calls_ai_per_chunk_and_yields_all() -> None:
    class RecordingAI:
        def __init__(self) -> None:
            self.seen: list[str] = []

        def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
            self.seen.append(source.content)
            return [
                AtomicNote(
                    title=source.content,
                    content=f"body for {source.content}",
                    tags=["chunk"],
                )
            ]

    ai = RecordingAI()
    sources = [
        SourceText(content="first"),
        SourceText(content="second"),
        SourceText(content="third"),
    ]
    notes = list(iter_atomic_notes(sources, ai, max_workers=3))
    assert {note.title for note in notes} == {"first", "second", "third"}
    assert set(ai.seen) == {"first", "second", "third"}


def test_iter_chunked_yields_as_chunks_complete() -> None:
    class TimedAI:
        def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
            time.sleep(0.08 if source.content == "slow" else 0.01)
            return [
                AtomicNote(
                    title=source.content,
                    content=source.content,
                    tags=["t"],
                )
            ]

    sources = [
        SourceText(content="slow"),
        SourceText(content="fast"),
    ]
    titles = [
        note.title for note in iter_atomic_notes(sources, TimedAI(), max_workers=2)
    ]
    assert titles == ["fast", "slow"]


def test_extract_chunked_caps_per_call_not_globally() -> None:
    class FloodAI:
        def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
            return [
                AtomicNote(
                    title=f"{source.content}-{i}",
                    content=f"content {source.content} {i}",
                    tags=["t"],
                )
                for i in range(MAX_ATOMIC_NOTES + 5)
            ]

    sources = [
        SourceText(content="a"),
        SourceText(content="b"),
    ]
    notes = list(iter_atomic_notes(sources, FloodAI(), max_workers=2))
    assert len(notes) == MAX_ATOMIC_NOTES * 2
    titles = {note.title for note in notes}
    assert len(titles) == MAX_ATOMIC_NOTES * 2
    assert all(t.startswith("a-") or t.startswith("b-") for t in titles)


def test_extract_chunked_overlaps_ai_calls() -> None:
    lock = threading.Lock()
    in_flight = 0
    max_in_flight = 0

    class SlowAI:
        def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
            nonlocal in_flight, max_in_flight
            with lock:
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
            time.sleep(0.05)
            with lock:
                in_flight -= 1
            return [
                AtomicNote(
                    title=source.content,
                    content=source.content,
                    tags=["slow"],
                )
            ]

    sources = [SourceText(content=f"c{i}") for i in range(3)]
    notes = list(iter_atomic_notes(sources, SlowAI(), max_workers=3))
    assert len(notes) == 3
    assert max_in_flight >= 2


def test_cli_pdf_path_continues_pipeline(tmp_path: Path, capsys) -> None:
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"%PDF-1.4")
    with patch(
        "zettelkasten.cli.extract_pdf_chunks",
        return_value=["Spaced repetition strengthens long-term memory."],
    ) as extract:
        main(["--fake", str(path)])
    extract.assert_called_once_with(path)
    captured = capsys.readouterr()
    assert captured.out.startswith("# ")
    assert "Spaced repetition" in captured.out


def test_cli_pdf_multiple_chunks(tmp_path: Path, capsys) -> None:
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"%PDF-1.4")
    with patch(
        "zettelkasten.cli.extract_pdf_chunks",
        return_value=[
            "First chunk about memory.",
            "Second chunk about attention.",
        ],
    ):
        main(["--fake", str(path)])
    captured = capsys.readouterr()
    assert "First chunk" in captured.out
    assert "Second chunk" in captured.out


def test_cli_pdf_multi_chunk_json_is_ndjson(tmp_path: Path, capsys) -> None:
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"%PDF-1.4")
    with patch(
        "zettelkasten.cli.extract_pdf_chunks",
        return_value=["First chunk about memory.", "Second chunk about attention."],
    ):
        main(["--fake", "--format", "json", str(path)])
    out = capsys.readouterr().out
    lines = [line for line in out.strip().splitlines() if line]
    assert len(lines) == 2
    assert lines[0].startswith("{")
    assert not out.lstrip().startswith("[")


def test_cli_pdf_suffix_is_case_insensitive(tmp_path: Path, capsys) -> None:
    path = tmp_path / "paper.PDF"
    path.write_bytes(b"%PDF-1.4")
    with patch(
        "zettelkasten.cli.extract_pdf_chunks",
        return_value=["Active recall beats rereading."],
    ) as extract:
        main(["--fake", str(path)])
    extract.assert_called_once_with(path)
    assert "Active recall" in capsys.readouterr().out


def test_cli_non_pdf_path_unchanged(tmp_path: Path, capsys) -> None:
    path = tmp_path / "source.txt"
    path.write_text("Spaced repetition strengthens long-term memory.", encoding="utf-8")
    with patch("zettelkasten.cli.extract_pdf_chunks") as extract:
        main(["--fake", str(path)])
    extract.assert_not_called()
    assert "Spaced repetition" in capsys.readouterr().out


def test_cli_stdin_remains_text_only(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("Plain stdin source text."))
    with patch("zettelkasten.cli.extract_pdf_chunks") as extract:
        main(["--fake"])
    extract.assert_not_called()
    assert "Plain stdin source text" in capsys.readouterr().out


def test_cli_empty_pdf_extraction_fails(tmp_path: Path) -> None:
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"%PDF-1.4")
    with (
        patch("zettelkasten.cli.extract_pdf_chunks", return_value=[]),
        pytest.raises(SystemExit, match="no extractable text"),
    ):
        main(["--fake", str(path)])


def test_cli_whitespace_only_chunk_fails_with_system_exit(tmp_path: Path) -> None:
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"%PDF-1.4")
    with (
        patch("zettelkasten.cli.extract_pdf_chunks", return_value=["   "]),
        pytest.raises(SystemExit, match="Invalid PDF content"),
    ):
        main(["--fake", str(path)])


def test_cli_missing_pdf_raises_system_exit(tmp_path: Path) -> None:
    path = tmp_path / "missing.pdf"
    with pytest.raises(SystemExit, match="Failed to read PDF") as exc_info:
        main(["--fake", str(path)])
    assert str(path) in str(exc_info.value)


def test_cli_unreadable_pdf_raises_system_exit(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-1.4")
    with patch(
        "zettelkasten.cli.extract_pdf_chunks",
        side_effect=OSError("permission denied"),
    ):
        with pytest.raises(SystemExit, match="Failed to read PDF") as exc_info:
            main(["--fake", str(path)])
    assert "permission denied" in str(exc_info.value)


def test_cli_streams_notion_per_note_for_multi_chunk(tmp_path: Path, capsys) -> None:
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"%PDF-1.4")
    store = MagicMock()
    store.create_notes.side_effect = lambda notes: [f"id-{notes[0].title}"]

    with (
        patch(
            "zettelkasten.cli.extract_pdf_chunks",
            return_value=["Note alpha body here.", "Note beta body here."],
        ),
        patch("zettelkasten.cli._build_notion_store", return_value=store),
        patch("zettelkasten.cli.load_settings"),
    ):
        main(["--fake", "--notion", str(path)])

    assert store.create_notes.call_count == 2
    for call in store.create_notes.call_args_list:
        assert len(call.args[0]) == 1
    err = capsys.readouterr().err
    assert "Created 2 Notion page(s)." in err


def test_cli_streams_notion_per_note_for_single_source(tmp_path: Path, capsys) -> None:
    path = tmp_path / "source.txt"
    path.write_text("Single source about memory.", encoding="utf-8")
    store = MagicMock()
    store.create_notes.side_effect = lambda notes: [f"id-{notes[0].title}"]

    with (
        patch("zettelkasten.cli._build_notion_store", return_value=store),
        patch("zettelkasten.cli.load_settings"),
    ):
        main(["--fake", "--notion", str(path)])

    assert store.create_notes.call_count == 1
    assert len(store.create_notes.call_args.args[0]) == 1
    assert "Created 1 Notion page(s)." in capsys.readouterr().err


def test_iter_single_source_skips_thread_pool() -> None:
    class RecordingAI:
        def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
            return [
                AtomicNote(title="t", content=source.content, tags=["x"]),
            ]

    with patch("zettelkasten.app.extract.ThreadPoolExecutor") as pool_cls:
        notes = list(
            iter_atomic_notes(
                [SourceText(content="only one")],
                RecordingAI(),
            )
        )
    pool_cls.assert_not_called()
    assert len(notes) == 1
