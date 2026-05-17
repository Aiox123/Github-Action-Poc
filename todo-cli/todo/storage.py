"""Todo storage backed by a local JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "todos.json"


def load(path: Path = DEFAULT_FILE) -> List[Dict[str, Any]]:
    """Load todos from the given JSON file. Returns [] if the file is missing."""
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save(todos: List[Dict[str, Any]], path: Path = DEFAULT_FILE) -> None:
    """Persist todos to the given JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add(title: str, path: Path = DEFAULT_FILE) -> Dict[str, Any]:
    """Append a new todo and return it."""
    todos = load(path)
    new_id = (max((t.get("id", 0) for t in todos), default=0)) + 1
    item = {"id": new_id, "title": title, "done": False}
    todos.append(item)
    save(todos, path)
    return item


def complete(todo_id: int, path: Path = DEFAULT_FILE) -> bool:
    """Mark a todo as done. Returns True if found, False otherwise."""
    todos = load(path)
    for t in todos:
        if t.get("id") == todo_id:
            t["done"] = True
            save(todos, path)
            return True
    return False


def remove(todo_id: int, path: Path = DEFAULT_FILE) -> bool:
    """Delete a todo by id. Returns True if removed."""
    todos = load(path)
    new_todos = [t for t in todos if t.get("id") != todo_id]
    if len(new_todos) == len(todos):
        return False
    save(new_todos, path)
    return True
