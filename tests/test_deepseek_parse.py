import json

import pytest

from zettelkasten.adapters.ai.deepseek import DeepSeekProvider
from zettelkasten.models import AtomicNote


def test_deepseek_parse_valid_payload() -> None:
    provider = DeepSeekProvider.__new__(DeepSeekProvider)
    raw = json.dumps(
        {
            "notes": [
                {
                    "title": "Active recall",
                    "content": "Retrieving memories strengthens them.",
                    "tags": ["learning", "memory"],
                }
            ]
        }
    )
    notes = DeepSeekProvider._parse(provider, raw)
    assert notes == [
        AtomicNote(
            title="Active recall",
            content="Retrieving memories strengthens them.",
            tags=["learning", "memory"],
        )
    ]


def test_deepseek_parse_rejects_invalid_json() -> None:
    provider = DeepSeekProvider.__new__(DeepSeekProvider)
    with pytest.raises(ValueError, match="invalid JSON"):
        DeepSeekProvider._parse(provider, "not-json")


def test_deepseek_parse_requires_notes_key() -> None:
    provider = DeepSeekProvider.__new__(DeepSeekProvider)
    with pytest.raises(ValueError, match="notes"):
        DeepSeekProvider._parse(provider, json.dumps({"title": "x"}))


def test_deepseek_requires_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        DeepSeekProvider("")
