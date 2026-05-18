"""Service layer encapsulating business rules for todos."""

from __future__ import annotations

from .models import TodoItem
from .repositories.base import TodoRepository


class TodoNotFoundError(LookupError):
    """Raised when an operation targets a missing todo id."""

    def __init__(self, todo_id: int) -> None:
        super().__init__(f"todo with id={todo_id} was not found")
        self.todo_id = todo_id


class TodoService:
    """Coordinates repository access and applies invariants.

    Responsibilities:
    * Generate monotonically increasing IDs.
    * Validate inputs at the boundary.
    * Provide query helpers (``list``, ``pending``, ``completed``).
    """

    def __init__(self, repo: TodoRepository) -> None:
        self._repo = repo

    # ---- queries ----------------------------------------------------
    def list(self) -> list[TodoItem]:
        return self._repo.list_all()

    def pending(self) -> list[TodoItem]:
        return [t for t in self._repo.list_all() if not t.done]

    def completed(self) -> list[TodoItem]:
        return [t for t in self._repo.list_all() if t.done]

    def get(self, todo_id: int) -> TodoItem:
        item = self._repo.get(todo_id)
        if item is None:
            raise TodoNotFoundError(todo_id)
        return item

    def stats(self) -> dict[str, object]:
        """生成统计信息。

        返回字典包含：
        - total: 总任务数
        - completed: 已完成数量
        - pending: 未完成数量
        - completion_rate: 完成率（百分比，保留 1 位小数）

        在无任务时，完成率返回 0.0。
        """
        items = self._repo.list_all()
        total = len(items)
        completed = sum(1 for t in items if t.done)
        pending = total - completed
        completion_rate = 0.0
        if total > 0:
            # 百分比并保留 1 位小数
            completion_rate = round((completed / total) * 100.0, 1)
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_rate": completion_rate,
        }

    # ---- commands ---------------------------------------------------
    def add(self, title: str) -> TodoItem:
        next_id = self._next_id()
        item = TodoItem(id=next_id, title=title)
        return self._repo.add(item)

    def complete(self, todo_id: int) -> TodoItem:
        item = self.get(todo_id)
        item.mark_done()
        return self._repo.update(item)

    def delete(self, todo_id: int) -> None:
        if not self._repo.delete(todo_id):
            raise TodoNotFoundError(todo_id)

    # ---- internals --------------------------------------------------
    def _next_id(self) -> int:
        items = self._repo.list_all()
        return (max((i.id for i in items), default=0)) + 1
