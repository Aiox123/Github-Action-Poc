"""Tests for the TodoService business rules."""

from __future__ import annotations

import pytest

from todo.services import TodoNotFoundError, TodoService


def test_add_generates_monotonic_ids(service: TodoService) -> None:
    a = service.add("first")
    b = service.add("second")
    assert a.id == 1
    assert b.id == 2


def test_pending_and_completed_split(service: TodoService) -> None:
    a = service.add("a")
    service.add("b")
    service.complete(a.id)

    assert [t.title for t in service.pending()] == ["b"]
    assert [t.title for t in service.completed()] == ["a"]


def test_complete_marks_done_idempotently(service: TodoService) -> None:
    item = service.add("x")
    completed_once = service.complete(item.id)
    completed_twice = service.complete(item.id)
    assert completed_once.done is True
    assert completed_twice.completed_at == completed_once.completed_at


def test_complete_missing_raises(service: TodoService) -> None:
    with pytest.raises(TodoNotFoundError):
        service.complete(404)


def test_delete_missing_raises(service: TodoService) -> None:
    with pytest.raises(TodoNotFoundError):
        service.delete(404)


def test_get_returns_existing_item(service: TodoService) -> None:
    item = service.add("found")
    assert service.get(item.id).title == "found"
