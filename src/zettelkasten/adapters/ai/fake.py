from zettelkasten.models import AtomicNote, SourceText


class FakeAIProvider:
    """Deterministic stand-in for tests and offline CLI smoke."""

    def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
        text = source.content

        first_line = text.splitlines()[0].strip()
        title = first_line[:80] if first_line else "Untitled note"
        return [
            AtomicNote(
                title=title,
                content=text if len(text) <= 280 else f"{text[:277].rstrip()}…",
                tags=_simple_tags(text),
            )
        ]


def _simple_tags(content: str) -> list[str]:
    words = {
        word.strip("#.,!?;:()[]{}\"'").lower()
        for word in content.split()
        if len(word.strip("#.,!?;:()[]{}\"'")) > 4
    }
    return sorted(words)[:5]
