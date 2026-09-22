from zettelkasten.adapters.notion.protocol import NoteStore
from zettelkasten.models import AtomicNote


def persist_notes(notes: list[AtomicNote], store: NoteStore) -> list[str]:
    """Persist atomic notes and return their external ids."""
    if not notes:
        return []
    return store.create_notes(notes)
