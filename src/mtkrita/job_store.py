from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    state: str
    generation: int
    source_hash: str | None
    config_hash: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class JobEvent:
    sequence: int
    job_id: str
    event_code: str
    from_state: str | None
    to_state: str | None
    generation: int
    occurred_at: str
    detail: dict[str, Any]


class JobStore:
    """Durable single-writer-oriented SQLite job state and event journal."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path).expanduser().resolve()

    @property
    def database_path(self) -> Path:
        return self._path

    def initialize(self) -> None:
        if not self._path.parent.is_dir():
            raise ValueError("JobStore parent directory must already exist")
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    source_hash TEXT,
                    config_hash TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    event_code TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT,
                    generation INTEGER NOT NULL,
                    occurred_at TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                );
                """
            )
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO metadata(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row[0]) != SCHEMA_VERSION:
                raise RuntimeError("incompatible JobStore schema version")

    def create_job(
        self,
        job_id: str,
        *,
        source_hash: str | None = None,
        config_hash: str | None = None,
    ) -> JobRecord:
        now = self._timestamp()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO jobs(
                        job_id, state, generation, source_hash, config_hash, created_at, updated_at
                    ) VALUES (?, 'CREATED', 0, ?, ?, ?, ?)
                    """,
                    (job_id, source_hash, config_hash, now, now),
                )
                connection.execute(
                    """
                    INSERT INTO events(
                        job_id, event_code, from_state, to_state, generation, occurred_at, detail_json
                    ) VALUES (?, 'JOB.CREATED', NULL, 'CREATED', 0, ?, '{}')
                    """,
                    (job_id, now),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> JobRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT job_id, state, generation, source_hash, config_hash, created_at, updated_at
                FROM jobs WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return JobRecord(*row)

    def transition(
        self,
        job_id: str,
        *,
        expected_state: str,
        expected_generation: int,
        new_state: str,
        event_code: str,
        detail: dict[str, Any] | None = None,
    ) -> JobRecord:
        now = self._timestamp()
        detail_json = json.dumps(detail or {}, ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE jobs
                    SET state = ?, generation = generation + 1, updated_at = ?
                    WHERE job_id = ? AND state = ? AND generation = ?
                    """,
                    (new_state, now, job_id, expected_state, expected_generation),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("stale or invalid job state transition")
                generation = expected_generation + 1
                connection.execute(
                    """
                    INSERT INTO events(
                        job_id, event_code, from_state, to_state,
                        generation, occurred_at, detail_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        event_code,
                        expected_state,
                        new_state,
                        generation,
                        now,
                        detail_json,
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_job(job_id)

    def list_events(self, job_id: str) -> tuple[JobEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sequence, job_id, event_code, from_state, to_state,
                       generation, occurred_at, detail_json
                FROM events WHERE job_id = ? ORDER BY sequence
                """,
                (job_id,),
            ).fetchall()
        return tuple(
            JobEvent(
                sequence=row[0],
                job_id=row[1],
                event_code=row[2],
                from_state=row[3],
                to_state=row[4],
                generation=row[5],
                occurred_at=row[6],
                detail=json.loads(row[7]),
            )
            for row in rows
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat()
