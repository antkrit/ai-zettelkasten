import json

from deepseek import DeepSeekAPI

from zettelkasten.models import MAX_ATOMIC_NOTES, AtomicNote, SourceText

_SYSTEM_PROMPT = f"""\
You are an assistant that converts source material into atomic Zettelkasten notes.

Return a JSON object only. Do not use markdown fences or any text outside the JSON object.

Schema:
{{
  "notes": [
    {{
      "title": "concise title expressing one idea",
      "content": "self-contained explanation of that idea",
      "tags": ["lowercase", "concise", "topic", "tags"]
    }}
  ]
}}

Rules:
- Extract zero or more atomic ideas from the source (at most {MAX_ATOMIC_NOTES}).
- Each note must capture exactly one reusable idea, not a general summary of the whole source.
- Each note must be understandable on its own without the original source.
- Preserve important nuance and qualifications from the source.
- Do not invent facts, examples, interpretations, or conclusions that are not supported by the source.
- Prefer precise language over vague generalizations.
- Use markdown only inside the "content" field when useful.
- Use 1–8 concise, lowercase tags per note that describe the concepts in that note.
- Do not include generic tags such as "note", "study", or "information".
- If the source has no extractable idea, return {{"notes": []}}.
"""


class DeepSeekProvider:
    """AIProvider backed by the DeepSeek chat completions API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "deepseek-chat",
    ) -> None:
        if not api_key:
            raise ValueError("DeepSeek api_key is required")
        self._client = DeepSeekAPI(api_key)
        self._model = model

    def generate_atomic_notes(self, source: SourceText) -> list[AtomicNote]:
        raw = self._complete(source.content)
        return self._parse(raw)

    def _complete(self, content: str) -> str:
        result = self._client.chat_completion(
            prompt=content,
            prompt_sys=_SYSTEM_PROMPT,
            model=self._model,
            stream=False,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        if not isinstance(result, str):
            raise TypeError(
                f"Expected str from DeepSeek chat_completion, got {type(result)!r}"
            )
        return result

    def _parse(self, raw: str) -> list[AtomicNote]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"DeepSeek returned invalid JSON: {raw[:500]!r}") from exc

        if not isinstance(data, dict) or "notes" not in data:
            raise ValueError(
                f"DeepSeek JSON must be an object with a 'notes' array: {raw[:500]!r}"
            )

        notes_raw = data["notes"]
        if not isinstance(notes_raw, list):
            raise ValueError(f"'notes' must be a list, got {type(notes_raw)!r}")

        return [AtomicNote.model_validate(item) for item in notes_raw]
