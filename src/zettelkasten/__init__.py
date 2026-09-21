"""AI-assisted Zettelkasten library."""

from zettelkasten.app.extract import extract_atomic_notes
from zettelkasten.models import AtomicNote, SourceText

__all__ = ["AtomicNote", "SourceText", "extract_atomic_notes"]
