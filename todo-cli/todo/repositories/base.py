"""Abstract repository contract for todo persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models import TodoItem


class TodoRepository(ABC):
    """Interface every concrete todo repository must implement.

    Implementations may persist to JSON, SQLite, an HTTP service, etc.
    """

    @abstractmethod
    def list_all(self) -> list[TodoItem]:
        """Return all todos ordered by ``id`` ascending."""

    @abstractmethod
    def get(self, todo_id: int) -> TodoItem | None:
        """Return the todo with ``todo_id`` or ``None`` when not found."""

    @abstractmethod
    def add(self, item: TodoItem) -> TodoItem:
        """Persist ``item`` and return the stored representation."""

    @abstractmethod
    def update(self, item: TodoItem) -> TodoItem:
        """Replace an existing todo. Raises ``KeyError`` if missing."""

    @abstractmethod
    def delete(self, todo_id: int) -> bool:
        """Delete a todo; return ``True`` if removed, ``False`` if absent."""

    @abstractmethod
    def replace_all(self, items: Iterable[TodoItem]) -> None:
        """Replace the entire collection (used by bulk operations / tests)."""
