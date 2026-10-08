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

# PDF (pymupdf4llm markdown, ~6-page chunks, parallel DeepSeek calls)
uv run zettelkasten path/to/paper.pdf
uv run zettelkasten --fake path/to/paper.pdf
# Notes (and Notion pages) stream as each source/chunk returns.
# --format json is NDJSON (one object per line) for all inputs.
# Single-source runs skip the thread pool; multi-chunk PDFs use up to 3 workers.

# Persist to Notion (requires NOTION_API_KEY + NOTION_DATABASE_ID)
uv run zettelkasten --notion path/to/source.txt
uv run zettelkasten --fake --notion path/to/source.txt
uv run zettelkasten --notion path/to/paper.pdf
```

Re-running `--notion` may create duplicate pages until idempotency exists.

### Experimental: embeddings → Qdrant

Requires `OPENAI_API_KEY`. Creates the collection on the first indexed note, sized from `OPENAI_EMBEDDING_MODEL`; never clears existing points. Re-indexing the same note overwrites it instead of duplicating.

- `QDRANT_PATH` (default `.qdrant`) is relative to the current directory; running from elsewhere uses a different, empty store.
- `--fake --qdrant` still calls OpenAI for embeddings and writes the fake notes into the same collection.
- Switching to a model with a different vector size requires a new `QDRANT_COLLECTION` or `rm -rf .qdrant`.
- Only one process can open the local store at a time (don't run `search` while indexing).

```bash
uv run zettelkasten --fake --qdrant path/to/source.txt
uv run zettelkasten --qdrant path/to/paper.pdf

# Semantic search over indexed notes
uv run zettelkasten search "differential privacy"
uv run zettelkasten search "SQL rewriting" -k 3
uv run zettelkasten search "joins" --format json

# Inspect stored payloads
uv run python -c "
from qdrant_client import QdrantClient
c = QdrantClient(path='.qdrant')
print(c.get_collection('atomic_notes'))
pts, _ = c.scroll('atomic_notes', limit=10, with_payload=True, with_vectors=False)
for p in pts:
    print(p.id, p.payload['metadata'])
"

# Clear manually between experiments
rm -rf .qdrant
```


## Tests

```bash
uv run pytest
```
