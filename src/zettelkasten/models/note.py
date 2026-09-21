from pydantic import BaseModel, Field, field_validator

MAX_ATOMIC_NOTES = 20
MAX_TAGS_PER_NOTE = 8


class AtomicNote(BaseModel):
    """One atomic idea, suitable for a Zettelkasten knowledge base."""

    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)

    @field_validator("title", "content")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be non-empty")
        return stripped

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for tag in value:
            normalized = tag.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(normalized)
            if len(cleaned) >= MAX_TAGS_PER_NOTE:
                break
        return cleaned
