"""Compatibility entry point so ``python main.py <cmd>`` still works."""

from todo.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
