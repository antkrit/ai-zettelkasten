import pytest
from pydantic import ValidationError

from zettelkasten.models import AtomicNote, SourceText


def test_source_text_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        SourceText(content="   ")


def test_source_text_strips_whitespace() -> None:
    source = SourceText(content="  hello world  ")
    assert source.content == "hello world"


def test_atomic_note_requires_title_and_content() -> None:
    with pytest.raises(ValidationError):
        AtomicNote(title=" ", content="body", tags=["idea"])
    with pytest.raises(ValidationError):
        AtomicNote(title="Title", content="", tags=["idea"])


def test_atomic_note_normalizes_tags() -> None:
    note = AtomicNote(
        title="Title",
        content="Body",
        tags=[
            "  Alpha ",
            "alpha",
            "Beta",
            "",
            "gamma",
            "delta",
            "epsilon",
            "zeta",
            "eta",
            "theta",
        ],
    )
    assert note.tags == [
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
    ]
