# TODO-002 — Add due date & priority to todos

| Field | Value |
|---|---|
| **ID** | TODO-002 |
| **Status** | Open |
| **Priority** | High |
| **Assignee** | @aiox123 |
| **Reporter** | Product Team |
| **Created** | 2026-05-17 |
| **Target Release** | 0.3.0 |

---

## 1. Background

Users of the `todo-cli` tool need to plan their day. Today every task is just a
title with a "done" flag, so it is impossible to know *when* something is due
or *how important* it is. We want to add a due date and a priority to each
todo, plus query helpers that surface what matters today.

## 2. Acceptance Criteria

1. A new todo can be created with an optional **due date** (YYYY-MM-DD) and a
   **priority** (`low` / `med` / `high`, defaults to `med`).
2. `todo list` shows todos **sorted by priority** (high → low). Items keep
   their original order otherwise.
3. A new sub-command `todo today` lists todos **due today**.
4. The existing JSON storage continues to work — old todos without the new
   fields must still load successfully.
5. Unit tests cover the new behaviour and pass on Python 3.9.

## 3. Technical Notes

- Extend the `TodoItem` model in `todo/storage.py` with two new fields:
  `priority: str` and `due_date: str | None`.
- Update `storage.list()` so it returns items sorted by priority.
- Update `storage.add()` so it accepts `priority` and `due_date` keyword
  arguments.
- Implement `today()` in `storage.py` by filtering items whose `due_date`
  equals today's date.
- The CLI parser in `cli.py` should learn the new flags `--priority` and
  `--due`.
- Update `requirements-dev.txt` if any new dependency is needed (none expected).

## 4. Affected Files

- `todo-cli/todo/storage.py`
- `todo-cli/todo/cli.py`
- `todo-cli/tests/test_storage.py`

## 5. Out of Scope

- Recurring todos / reminders.
- Time-of-day (only date precision is required).
- Migration tool for existing data files.

## 6. Open Questions

> Left for the implementer to clarify during refinement.

- What happens when two items have the same priority? (Stable order? FIFO?)
- Should `today` consider the user's local timezone, or always UTC?
- Should the REST surface (if any) expose the new fields?
- Should we keep `low` / `med` / `high` as free-form strings or as an enum?

---
*This ticket intentionally references the previous (v0.1) layout of the
project. The Copilot CI review is expected to flag the inconsistencies
against the actual layered codebase (v0.2).*
