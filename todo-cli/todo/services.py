"""Service layer encapsulating business rules for todos."""

from __future__ import annotations

import json
from pathlib import Path

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

    # ---- bulk / import-export --------------------------------------
    def export_to_file(self, path: Path) -> None:
        """Export all todos to a JSON file at `path`.

        The file is written with ensure_ascii=False and indent=2 so it's
        human-readable and preserves non-ascii characters.
        """
        items = self._repo.list_all()
        payload = [t.to_dict() for t in items]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_from_file(self, path: Path, merge: bool = True) -> None:
        """Import todos from a JSON file.

        Validation: the top-level must be a JSON array of objects. Each item
        must include at least `id` (int) and `title` (non-empty str). On any
        schema violation a ValueError with a clear Chinese message is raised.

        merge=True (default): preserve existing todos and append only new ids.
        merge=False (overwrite): replace repository contents with imported items.
        """
        if not path.exists():
            raise ValueError(f"导入文件不存在：{path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析 JSON：{exc}") from exc

        if not isinstance(raw, list):
            raise ValueError("导入文件格式错误：顶层应为 JSON 数组")

        items: list[TodoItem] = []
        for idx, entry in enumerate(raw, start=1):
            if not isinstance(entry, dict):
                raise ValueError(f"第{idx}项不是对象 (object)")
            # id
            if "id" not in entry:
                raise ValueError(f"第{idx}项缺失字段 'id'")
            try:
                _id = int(entry["id"])
            except Exception as exc:
                raise ValueError(f"第{idx}项字段 'id' 必须是整数") from exc
            # title
            if "title" not in entry:
                raise ValueError(f"第{idx}项缺失字段 'title'")
            if not isinstance(entry["title"], str) or not entry["title"].strip():
                raise ValueError(f"第{idx}项字段 'title' 必须是非空字符串")
            # optional fields: done (bool), created_at (str), completed_at (str|null)
            if "done" in entry and not isinstance(entry["done"], bool):
                raise ValueError(f"第{idx}项字段 'done' 必须是布尔值")
            if "created_at" in entry and entry["created_at"] is not None and not isinstance(entry["created_at"], str):
                raise ValueError(f"第{idx}项字段 'created_at' 必须是字符串或 null")
            if "completed_at" in entry and entry["completed_at"] is not None and not isinstance(entry["completed_at"], str):
                raise ValueError(f"第{idx}项字段 'completed_at' 必须是字符串或 null")

            # Use TodoItem.from_dict to normalize values (this may raise on invalid content)
            try:
                items.append(TodoItem.from_dict(entry))
            except Exception as exc:
                raise ValueError(f"第{idx}项数据无效：{exc}") from exc

        if merge:
            existing = {t.id: t for t in self._repo.list_all()}
            new_items = list(existing.values())
            # append items whose id is not present
            for it in items:
                if it.id not in existing:
                    new_items.append(it)
            # ensure stable ordering by id
            new_items = sorted(new_items, key=lambda x: x.id)
            self._repo.replace_all(new_items)
        else:
            # overwrite
            self._repo.replace_all(sorted(items, key=lambda x: x.id))

    # ---- internals --------------------------------------------------
    def _next_id(self) -> int:
        items = self._repo.list_all()
        return (max((i.id for i in items), default=0)) + 1
