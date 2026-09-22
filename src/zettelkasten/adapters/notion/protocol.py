from typing import Protocol, runtime_checkable

from zettelkasten.models import AtomicNote


@runtime_checkable
class NoteStore(Protocol):
    """Port for persisting atomic notes to an external knowledge base."""

    def create_notes(self, notes: list[AtomicNote]) -> list[str]:
        """Create notes and return their external ids (e.g. Notion page ids)."""
        ...
