"""Domain models for the todo application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow_iso() -> str:
    """Return current UTC time as an ISO-8601 string with offset."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TodoItem:
    """A single todo entry.

    Attributes
    ----------
    id:
        Stable, monotonically increasing integer identifier.
    title:
        Non-empty human readable description.
    done:
        Completion flag.
    created_at:
        ISO-8601 timestamp (UTC) of creation.
    completed_at:
        ISO-8601 timestamp (UTC) of completion, or ``None`` if pending.
    """

    id: int
    title: str
    done: bool = False
    created_at: str = field(default_factory=_utcnow_iso)
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title must be a non-empty string")
        self.title = self.title.strip()

    # ---- (de)serialization helpers ----------------------------------
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TodoItem:
        return cls(
            id=int(payload["id"]),
            title=str(payload["title"]),
            done=bool(payload.get("done", False)),
            created_at=str(payload.get("created_at") or _utcnow_iso()),
            completed_at=payload.get("completed_at"),
        )

    # ---- domain behaviour -------------------------------------------
    def mark_done(self) -> None:
        """Idempotently mark this item as completed."""
        if not self.done:
            self.done = True
            self.completed_at = _utcnow_iso()
