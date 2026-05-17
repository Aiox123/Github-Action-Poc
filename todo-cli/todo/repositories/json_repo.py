"""JSON file backed implementation of :class:`TodoRepository`."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from ..models import TodoItem
from .base import TodoRepository


class JsonTodoRepository(TodoRepository):
    """Persist todos as a JSON array on disk.

    The file is read/written on every call to keep the class simple and
    side-effect free in terms of in-memory caching. For PoC purposes that
    trade-off is acceptable; a future SQLite implementation can replace
    this without touching the service layer.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    # ---- helpers ----------------------------------------------------
    def _read(self) -> list[TodoItem]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(raw, list):
            return []
        return [TodoItem.from_dict(item) for item in raw if isinstance(item, dict)]

    def _write(self, items: list[TodoItem]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in items]
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ---- TodoRepository API -----------------------------------------
    def list_all(self) -> list[TodoItem]:
        return sorted(self._read(), key=lambda i: i.id)

    def get(self, todo_id: int) -> TodoItem | None:
        for item in self._read():
            if item.id == todo_id:
                return item
        return None

    def add(self, item: TodoItem) -> TodoItem:
        items = self._read()
        if any(existing.id == item.id for existing in items):
            raise ValueError(f"todo with id={item.id} already exists")
        items.append(item)
        self._write(items)
        return item

    def update(self, item: TodoItem) -> TodoItem:
        items = self._read()
        for idx, existing in enumerate(items):
            if existing.id == item.id:
                items[idx] = item
                self._write(items)
                return item
        raise KeyError(item.id)

    def delete(self, todo_id: int) -> bool:
        items = self._read()
        new_items = [i for i in items if i.id != todo_id]
        if len(new_items) == len(items):
            return False
        self._write(new_items)
        return True

    def replace_all(self, items: Iterable[TodoItem]) -> None:
        self._write(list(items))
