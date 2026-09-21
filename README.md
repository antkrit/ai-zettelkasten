# ai-zettelkasten

Local v0: extract atomic Zettelkasten notes from text via AI.

## Setup

```bash
uv sync --group dev
cp .env.example .env   # set empty secrets
```

## Usage

```bash
# Fake provider
echo "Spaced repetition strengthens memory." | uv run zettelkasten --fake

# DeepSeek (requires DEEPSEEK_API_KEY)
uv run zettelkasten path/to/source.txt
uv run zettelkasten --format json path/to/source.txt
```

## Tests

```bash
uv run pytest
```
