"""Tests for todo.storage using a temporary file."""

import json
from pathlib import Path

import sys

# Allow running tests without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from todo import storage  # noqa: E402


def test_add_and_load(tmp_path: Path) -> None:
    db = tmp_path / "t.json"
    item = storage.add("write tests", path=db)
    assert item["id"] == 1
    assert item["done"] is False

    loaded = storage.load(path=db)
    assert loaded == [{"id": 1, "title": "write tests", "done": False}]


def test_complete_and_remove(tmp_path: Path) -> None:
    db = tmp_path / "t.json"
    storage.add("a", path=db)
    storage.add("b", path=db)

    assert storage.complete(1, path=db) is True
    assert storage.complete(999, path=db) is False

    todos = storage.load(path=db)
    assert todos[0]["done"] is True
    assert todos[1]["done"] is False

    assert storage.remove(2, path=db) is True
    assert storage.remove(2, path=db) is False
    assert len(storage.load(path=db)) == 1


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    assert storage.load(path=tmp_path / "nope.json") == []


def test_save_creates_valid_json(tmp_path: Path) -> None:
    db = tmp_path / "t.json"
    storage.save([{"id": 1, "title": "x", "done": False}], path=db)
    assert json.loads(db.read_text(encoding="utf-8"))[0]["title"] == "x"
