import json
from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from zettelkasten.cli import main


def test_cli_fake_markdown(tmp_path: Path, capsys) -> None:
    path = tmp_path / "source.txt"
    path.write_text("Spaced repetition strengthens long-term memory.", encoding="utf-8")
    main(["--fake", str(path)])
    out = capsys.readouterr().out
    assert out.startswith("# ")
    assert "Spaced repetition" in out


def test_cli_fake_json(tmp_path: Path, capsys) -> None:
    path = tmp_path / "source.txt"
    path.write_text("Active recall beats rereading.", encoding="utf-8")
    main(["--fake", "--format", "json", str(path)])
    out = capsys.readouterr().out
    assert out.lstrip().startswith("{")
    assert '"title"' in out
    assert '"content"' in out


@pytest.fixture
def qdrant_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QDRANT_PATH", str(tmp_path / "qdrant"))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "zettelkasten.cli.OpenAIEmbeddings",
        lambda **_: DeterministicFakeEmbedding(size=8),
    )


def test_cli_search_requires_collection(qdrant_env) -> None:
    with pytest.raises(
        SystemExit,
        match="^Search failed: Qdrant collection 'atomic_notes' does not exist",
    ):
        main(["search", "anything"])


def test_cli_qdrant_requires_openai_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(SystemExit, match="require OPENAI_API_KEY"):
        main(["--fake", "--qdrant", "unused.txt"])


def test_cli_qdrant_index_then_search(qdrant_env, tmp_path: Path, capsys) -> None:
    path = tmp_path / "source.txt"
    path.write_text("Active recall beats rereading.", encoding="utf-8")
    main(["--fake", "--qdrant", str(path)])
    main(["--fake", "--qdrant", str(path)])
    capsys.readouterr()

    main(["search", "--format", "json", "recall"])
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    hit = json.loads(lines[0])
    assert hit["title"] == "Active recall beats rereading."
    assert isinstance(hit["score"], float)

    main(["search", "recall"])
    out = capsys.readouterr().out
    assert out.startswith("# Active recall beats rereading.")
    assert "Score: " in out
