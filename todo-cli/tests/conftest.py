"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow running tests without `pip install -e .`
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from todo.repositories import JsonTodoRepository  # noqa: E402
from todo.services import TodoService  # noqa: E402


@pytest.fixture()
def data_file(tmp_path: Path) -> Path:
    """Provide an isolated JSON data file per test."""
    return tmp_path / "todos.json"


@pytest.fixture()
def repo(data_file: Path) -> JsonTodoRepository:
    return JsonTodoRepository(data_file)


@pytest.fixture()
def service(repo: JsonTodoRepository) -> TodoService:
    return TodoService(repo)
