"""Application configuration.

Resolves the on-disk data file used by repositories. Allows overriding via
the ``TODO_DATA_FILE`` environment variable so tests and ops can isolate state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_FILE = Path(__file__).resolve().parent.parent / "todos.json"


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    data_file: Path

    @classmethod
    def from_env(cls) -> Settings:
        override = os.environ.get("TODO_DATA_FILE")
        data_file = Path(override).expanduser().resolve() if override else DEFAULT_DATA_FILE
        return cls(data_file=data_file)


def get_settings() -> Settings:
    """Factory used by CLI / API layers."""
    return Settings.from_env()
