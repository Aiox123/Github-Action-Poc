"""argparse based command-line interface for the todo application."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .config import get_settings
from .repositories import JsonTodoRepository
from .services import TodoNotFoundError, TodoService


def _build_service() -> TodoService:
    settings = get_settings()
    return TodoService(JsonTodoRepository(settings.data_file))


# ---- command handlers ---------------------------------------------------
def _cmd_list(_args: argparse.Namespace, service: TodoService) -> int:
    items = service.list()
    if not items:
        print('(no todos yet — try `todo add "your task"`)')
        return 0
    for t in items:
        mark = "x" if t.done else " "
        print(f"[{mark}] {t.id:>3}  {t.title}")
    return 0


def _cmd_add(args: argparse.Namespace, service: TodoService) -> int:
    item = service.add(args.title)
    print(f"Added #{item.id}: {item.title}")
    return 0


def _cmd_done(args: argparse.Namespace, service: TodoService) -> int:
    try:
        item = service.complete(args.id)
    except TodoNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Completed #{item.id}")
    return 0


def _cmd_rm(args: argparse.Namespace, service: TodoService) -> int:
    try:
        service.delete(args.id)
    except TodoNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Removed #{args.id}")
    return 0


# ---- parser -------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="A layered todo CLI.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all todos").set_defaults(func=_cmd_list)

    p_add = sub.add_parser("add", help="Add a new todo")
    p_add.add_argument("title", help="Title of the todo")
    p_add.set_defaults(func=_cmd_add)

    p_done = sub.add_parser("done", help="Mark a todo as done")
    p_done.add_argument("id", type=int, help="Todo id")
    p_done.set_defaults(func=_cmd_done)

    p_rm = sub.add_parser("rm", help="Remove a todo")
    p_rm.add_argument("id", type=int, help="Todo id")
    p_rm.set_defaults(func=_cmd_rm)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = _build_service()
    return args.func(args, service)


if __name__ == "__main__":
    raise SystemExit(main())
