import pytest

from zettelkasten.adapters.notion.notion import (
    build_content_blocks,
    build_properties,
    page_id_from_response,
)
from zettelkasten.models import AtomicNote


def test_build_properties_maps_title_and_tags() -> None:
    note = AtomicNote(
        title="Active recall",
        content="Retrieving memories strengthens them.",
        tags=["learning", "memory"],
    )
    props = build_properties(note)
    assert props["Name"]["title"][0]["text"]["content"] == "Active recall"
    assert props["Tags"]["multi_select"] == [
        {"name": "learning"},
        {"name": "memory"},
    ]


def test_build_properties_respects_custom_property_names() -> None:
    note = AtomicNote(title="Title", content="Body", tags=["a"])
    props = build_properties(
        note,
        title_property="Title",
        tags_property="Topics",
    )
    assert "Title" in props
    assert "Topics" in props
    assert "Name" not in props


def test_build_properties_truncates_long_title() -> None:
    note = AtomicNote(title="x" * 2500, content="Body", tags=[])
    props = build_properties(note)
    assert len(props["Name"]["title"][0]["text"]["content"]) == 2000


def test_build_content_blocks_splits_paragraphs() -> None:
    blocks = build_content_blocks("First paragraph.\n\nSecond paragraph.")
    assert len(blocks) == 2
    assert blocks[0]["type"] == "paragraph"
    assert (
        blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "First paragraph."
    )
    assert (
        blocks[1]["paragraph"]["rich_text"][0]["text"]["content"] == "Second paragraph."
    )


def test_build_content_blocks_chunks_long_paragraph() -> None:
    blocks = build_content_blocks("a" * 4500)
    assert len(blocks) == 3
    assert len(blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]) == 2000
    assert len(blocks[1]["paragraph"]["rich_text"][0]["text"]["content"]) == 2000
    assert len(blocks[2]["paragraph"]["rich_text"][0]["text"]["content"]) == 500


def test_build_content_blocks_empty_content() -> None:
    assert build_content_blocks("") == []
    assert build_content_blocks("   ") == []


def test_page_id_from_response() -> None:
    assert page_id_from_response({"id": "abc-123"}) == "abc-123"


def test_page_id_from_response_rejects_bad_shapes() -> None:
    with pytest.raises(TypeError):
        page_id_from_response("not-a-dict")
    with pytest.raises(TypeError):
        page_id_from_response({"id": 123})
