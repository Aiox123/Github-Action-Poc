"""Tests for the TodoItem domain model."""

from __future__ import annotations

import pytest

from todo.models import TodoItem


def test_creation_strips_title() -> None:
    item = TodoItem(id=1, title="  buy milk  ")
    assert item.title == "buy milk"
    assert item.done is False
    assert item.completed_at is None
    assert item.created_at  # populated


def test_empty_title_rejected() -> None:
    with pytest.raises(ValueError):
        TodoItem(id=1, title="   ")


def test_mark_done_is_idempotent() -> None:
    item = TodoItem(id=1, title="x")
    item.mark_done()
    first_completed_at = item.completed_at
    item.mark_done()  # second call should not overwrite timestamp
    assert item.done is True
    assert item.completed_at == first_completed_at


def test_roundtrip_dict() -> None:
    original = TodoItem(id=42, title="ship feature")
    restored = TodoItem.from_dict(original.to_dict())
    assert restored == original
