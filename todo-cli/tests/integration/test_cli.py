"""Integration tests covering the CLI end-to-end through subprocess-free invocation."""

from __future__ import annotations

from pathlib import Path

import pytest

from todo import cli


@pytest.fixture(autouse=True)
def _isolate_data_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TODO_DATA_FILE", str(tmp_path / "todos.json"))


def test_add_then_list(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["add", "buy milk"]) == 0
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "Added #1: buy milk" in out
    assert "buy milk" in out


def test_done_marks_completed(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["add", "x"])
    capsys.readouterr()  # flush
    assert cli.main(["done", "1"]) == 0
    cli.main(["list"])
    assert "[x]" in capsys.readouterr().out


def test_done_unknown_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["done", "999"])
    assert rc == 1
    assert "999" in capsys.readouterr().err


def test_rm_removes_item(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["add", "x"])
    capsys.readouterr()
    assert cli.main(["rm", "1"]) == 0
    cli.main(["list"])
    assert "(no todos" in capsys.readouterr().out
