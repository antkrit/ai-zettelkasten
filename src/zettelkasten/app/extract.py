from zettelkasten.adapters.ai.protocol import AIProvider
from zettelkasten.models import MAX_ATOMIC_NOTES, AtomicNote, SourceText


def extract_atomic_notes(source: SourceText, ai: AIProvider) -> list[AtomicNote]:
    """Validate source, call the AI provider, and normalize the result list."""
    notes = ai.generate_atomic_notes(source)
    return list(notes[:MAX_ATOMIC_NOTES])
