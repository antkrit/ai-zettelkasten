from typing import Any

from notion_client import Client

from zettelkasten.models import AtomicNote

# Notion rich_text content chunks are capped at 2000 characters.
_MAX_RICH_TEXT = 2000


class NotionNoteStore:
    """Persist atomic notes as rows in a Notion database."""

    def __init__(
        self,
        api_key: str,
        *,
        database_id: str,
        title_property: str = "Name",
        tags_property: str = "Tags",
    ) -> None:
        if not api_key:
            raise ValueError("Notion api_key is required")
        if not database_id:
            raise ValueError("Notion database_id is required")
        self._client = Client(auth=api_key)
        self.database_id = database_id
        self.title_property = title_property
        self.tags_property = tags_property

    def create_notes(self, notes: list[AtomicNote]) -> list[str]:
        page_ids: list[str] = []
        for note in notes:
            page_ids.append(self._create_note(note))
        return page_ids

    def _create_note(self, note: AtomicNote) -> str:
        payload: dict[str, Any] = {
            "parent": {"database_id": self.database_id},
            "properties": build_properties(
                note,
                title_property=self.title_property,
                tags_property=self.tags_property,
            ),
        }
        blocks = build_content_blocks(note.content)
        if blocks:
            payload["children"] = blocks

        response = self._client.pages.create(**payload)
        return page_id_from_response(response)


def page_id_from_response(response: object) -> str:
    if not isinstance(response, dict):
        raise TypeError(f"Unexpected Notion create response type: {type(response)!r}")
    page_id = response.get("id")
    if not isinstance(page_id, str):
        raise TypeError(f"Unexpected Notion page id type: {type(page_id)!r}")
    return page_id


def build_properties(
    note: AtomicNote,
    *,
    title_property: str = "Name",
    tags_property: str = "Tags",
) -> dict[str, Any]:
    return {
        title_property: {
            "title": [
                {
                    "type": "text",
                    "text": {"content": note.title[:_MAX_RICH_TEXT]},
                }
            ],
        },
        tags_property: {
            "multi_select": [{"name": tag} for tag in note.tags],
        },
    }


def build_content_blocks(content: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    paragraphs = content.split("\n\n") if content.strip() else []
    for paragraph in paragraphs:
        text = paragraph.strip() or " "
        for start in range(0, len(text), _MAX_RICH_TEXT):
            chunk = text[start : start + _MAX_RICH_TEXT]
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": chunk}},
                        ],
                    },
                }
            )
    return blocks
