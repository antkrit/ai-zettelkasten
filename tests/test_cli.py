from pathlib import Path

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
    assert '"title"' in out
    assert '"content"' in out
