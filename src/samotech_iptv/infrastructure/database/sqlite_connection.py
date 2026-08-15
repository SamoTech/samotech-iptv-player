"""Deterministic ownership for short-lived SQLite operation connections."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@contextmanager
def sqlite_connection(
    database_path: str | Path, *, foreign_keys: bool = False
) -> Iterator[sqlite3.Connection]:
    """Commit or roll back one operation, then close its connection in all paths."""
    connection = sqlite3.connect(database_path)
    try:
        if foreign_keys:
            connection.execute("PRAGMA foreign_keys = ON")
        yield connection
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()
