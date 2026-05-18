"""Unit tests for TodoService.stats()."""

from todo.models import TodoItem
from todo.services import TodoService


class InMemoryRepo:
    """简单的内存仓库实现，仅用于测试。"""

    def __init__(self, items=None):
        self._items = list(items) if items else []

    def list_all(self):
        return list(self._items)

    # Below methods are implemented to satisfy the contract if needed
    def get(self, todo_id: int):
        for i in self._items:
            if i.id == todo_id:
                return i
        return None

    def add(self, item: TodoItem):
        self._items.append(item)
        return item

    def update(self, item: TodoItem):
        for idx, existing in enumerate(self._items):
            if existing.id == item.id:
                self._items[idx] = item
                return item
        raise KeyError(item.id)

    def delete(self, todo_id: int):
        new = [i for i in self._items if i.id != todo_id]
        removed = len(new) != len(self._items)
        self._items = new
        return removed

    def replace_all(self, items):
        self._items = list(items)


def test_stats_with_tasks():
    items = [
        TodoItem(id=1, title="a", done=True),
        TodoItem(id=2, title="b", done=False),
        TodoItem(id=3, title="c", done=True),
    ]
    repo = InMemoryRepo(items)
    svc = TodoService(repo)
    s = svc.stats()
    assert s["total"] == 3
    assert s["completed"] == 2
    assert s["pending"] == 1
    # 2/3 = 66.666... -> 66.7
    assert s["completion_rate"] == 66.7


def test_stats_no_tasks():
    repo = InMemoryRepo([])
    svc = TodoService(repo)
    s = svc.stats()
    assert s["total"] == 0
    assert s["completed"] == 0
    assert s["pending"] == 0
    assert s["completion_rate"] == 0.0


def test_stats_all_completed():
    items = [TodoItem(id=i, title=f"t{i}", done=True) for i in range(1, 6)]
    repo = InMemoryRepo(items)
    svc = TodoService(repo)
    s = svc.stats()
    assert s["total"] == 5
    assert s["completed"] == 5
    assert s["pending"] == 0
    assert s["completion_rate"] == 100.0
