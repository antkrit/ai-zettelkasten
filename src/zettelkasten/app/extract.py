from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed

from zettelkasten.adapters.ai.protocol import AIProvider
from zettelkasten.models import MAX_ATOMIC_NOTES, AtomicNote, SourceText

DEFAULT_MAX_WORKERS = 3


def extract_atomic_notes(source: SourceText, ai: AIProvider) -> list[AtomicNote]:
    """Validate source, call the AI provider, and normalize the result list."""
    notes = ai.generate_atomic_notes(source)
    return list(notes[:MAX_ATOMIC_NOTES])


def iter_atomic_notes(
    sources: list[SourceText],
    ai: AIProvider,
    *,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> Iterator[AtomicNote]:
    """Yield notes as each source's AI call finishes (completion order).

    The per-call note cap applies to each source separately. A single source
    runs inline without a thread pool.
    """
    if not sources:
        return

    if len(sources) == 1:
        yield from extract_atomic_notes(sources[0], ai)
        return

    workers = max(1, min(max_workers, len(sources)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(extract_atomic_notes, source, ai) for source in sources]
        for future in as_completed(futures):
            yield from future.result()
