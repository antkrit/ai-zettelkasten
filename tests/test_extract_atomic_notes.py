from zettelkasten.adapters.ai.fake import FakeAIProvider
from zettelkasten.app.extract import extract_atomic_notes
from zettelkasten.models import SourceText


def test_extract_happy_path() -> None:
    source = SourceText(content="Spaced repetition strengthens long-term memory.")
    notes = extract_atomic_notes(source, FakeAIProvider())
    assert len(notes) == 1
    assert notes[0].title
    assert notes[0].content
