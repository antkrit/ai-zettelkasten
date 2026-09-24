import logging

from zettelkasten.adapters.notion.protocol import NoteStore
from zettelkasten.models import AtomicNote

logger = logging.getLogger(__name__)


def persist_notes(notes: list[AtomicNote], store: NoteStore) -> list[str]:
    """Persist atomic notes and return their external ids."""
    if not notes:
        return []
    page_ids = store.create_notes(notes)
    for page_id in page_ids:
        logger.info("%s", page_id)
    return page_ids
