"""Tests for the JSON file repository."""

from __future__ import annotations

from pathlib import Path

import pytest

from todo.models import TodoItem
from todo.repositories import JsonTodoRepository


def test_list_empty_when_file_missing(repo: JsonTodoRepository) -> None:
    assert repo.list_all() == []


def test_add_persists_and_returns(repo: JsonTodoRepository, data_file: Path) -> None:
    item = repo.add(TodoItem(id=1, title="first"))
    assert item.id == 1
    assert data_file.exists()
    assert [t.title for t in repo.list_all()] == ["first"]


def test_add_rejects_duplicate_id(repo: JsonTodoRepository) -> None:
    repo.add(TodoItem(id=1, title="a"))
    with pytest.raises(ValueError):
        repo.add(TodoItem(id=1, title="b"))


def test_update_existing_item(repo: JsonTodoRepository) -> None:
    repo.add(TodoItem(id=1, title="x"))
    updated = TodoItem(id=1, title="x", done=True)
    repo.update(updated)
    assert repo.get(1) == updated


def test_update_missing_raises_keyerror(repo: JsonTodoRepository) -> None:
    with pytest.raises(KeyError):
        repo.update(TodoItem(id=99, title="ghost"))


def test_delete_returns_bool(repo: JsonTodoRepository) -> None:
    repo.add(TodoItem(id=1, title="x"))
    assert repo.delete(1) is True
    assert repo.delete(1) is False
    assert repo.list_all() == []


def test_list_returns_sorted_by_id(repo: JsonTodoRepository) -> None:
    for tid in [3, 1, 2]:
        repo.add(TodoItem(id=tid, title=f"t{tid}"))
    assert [t.id for t in repo.list_all()] == [1, 2, 3]


def test_replace_all(repo: JsonTodoRepository) -> None:
    repo.add(TodoItem(id=1, title="old"))
    repo.replace_all([TodoItem(id=10, title="fresh")])
    items = repo.list_all()
    assert len(items) == 1 and items[0].title == "fresh"


def test_corrupted_file_falls_back_to_empty(data_file: Path) -> None:
    data_file.write_text("not-json", encoding="utf-8")
    assert JsonTodoRepository(data_file).list_all() == []
