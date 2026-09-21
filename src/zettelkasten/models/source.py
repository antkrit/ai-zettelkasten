from pydantic import BaseModel, field_validator


class SourceText(BaseModel):
    """Raw material to extract atomic Zettelkasten notes from."""

    content: str

    @field_validator("content")
    @classmethod
    def content_must_be_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must be non-empty")
        return stripped
