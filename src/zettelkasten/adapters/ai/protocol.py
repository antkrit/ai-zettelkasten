from typing import Protocol, runtime_checkable

from zettelkasten.models import AtomicNote, SourceText


@runtime_checkable
class AIProvider(Protocol):
    """Port for turning source text into atomic notes."""

    def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
        """Extract zero or more atomic notes from source material."""
        ...
