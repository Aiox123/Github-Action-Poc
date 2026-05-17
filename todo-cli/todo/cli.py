"""Command-line interface for the todo app."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__, storage


def _cmd_list(_args: argparse.Namespace) -> int:
    todos = storage.load()
    if not todos:
        print("(no todos yet — try `todo add \"your task\"`)")
        return 0
    for t in todos:
        mark = "x" if t.get("done") else " "
        print(f"[{mark}] {t['id']:>3}  {t['title']}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    item = storage.add(args.title)
    print(f"Added #{item['id']}: {item['title']}")
    return 0


def _cmd_done(args: argparse.Namespace) -> int:
    if storage.complete(args.id):
        print(f"Completed #{args.id}")
        return 0
    print(f"No todo with id={args.id}", file=sys.stderr)
    return 1


def _cmd_rm(args: argparse.Namespace) -> int:
    if storage.remove(args.id):
        print(f"Removed #{args.id}")
        return 0
    print(f"No todo with id={args.id}", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="A tiny todo CLI.")
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
