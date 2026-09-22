# ai-zettelkasten

Extract atomic Zettelkasten notes from text via AI; optionally write them to Notion.

## Setup

```bash
uv sync --group dev
cp .env.example .env   # set DEEPSEEK_* / NOTION_* secrets
```

Notion KB database needs at least: **Name** (title), **Tags** (multi_select).

## Usage

```bash
# Fake AI (offline)
echo "Spaced repetition strengthens memory." | uv run zettelkasten --fake

# DeepSeek
uv run zettelkasten path/to/source.txt
uv run zettelkasten --format json path/to/source.txt

# Persist to Notion (requires NOTION_API_KEY + NOTION_DATABASE_ID)
uv run zettelkasten --notion path/to/source.txt
uv run zettelkasten --fake --notion path/to/source.txt
```

Re-running `--notion` may create duplicate pages until idempotency exists.

## Tests

```bash
uv run pytest
```
