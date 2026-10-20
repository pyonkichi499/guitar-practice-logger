"""テイクの記録（SQLite）。"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS takes (
    id          INTEGER PRIMARY KEY,
    song_id     TEXT    NOT NULL,
    recorded_at TEXT    NOT NULL,
    bpm         INTEGER NOT NULL,
    file_path   TEXT    NOT NULL UNIQUE,
    intaken_at  TEXT    NOT NULL
);
"""


@dataclass(frozen=True)
class Take:
    song_id: str
    recorded_at: datetime
    bpm: int
    file_path: Path


class TakeStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def last_bpm(self, song_id: str) -> int | None:
        row = self._conn.execute(
            "SELECT bpm FROM takes WHERE song_id = ? ORDER BY recorded_at DESC LIMIT 1",
            (song_id,),
        ).fetchone()
        return row[0] if row else None

    def add(self, take: Take) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO takes (song_id, recorded_at, bpm, file_path, intaken_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    take.song_id,
                    take.recorded_at.isoformat(timespec="seconds"),
                    take.bpm,
                    str(take.file_path),
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )
