from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3


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
class TaskRecord:
    task_id: str
    job_id: str
    state: str
    generation: int
    attempt: int
    worker_id: str | None
    lease_expires_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TaskDescriptorRecord:
    task_id: str
    job_id: str
    priority: int
    descriptor_version: int
    descriptor: dict[str, Any]
    reconstructable: bool
    created_at: str


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
    """Durable single-writer-oriented SQLite job/task state and event journal."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path).expanduser().resolve()

    @property
    def database_path(self) -> Path:
        return self._path

    def initialize(self) -> None:
        if not self._path.parent.is_dir():
            raise ValueError("JobStore parent directory must already exist")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._create_base_schema(connection)
                version = self._read_or_seed_schema_version(connection)
                if version > SCHEMA_VERSION or version < 1:
                    raise RuntimeError("incompatible JobStore schema version")
                if version == 1:
                    self._migrate_v1_to_v2(connection)
                    version = 2
                if version == 2:
                    self._migrate_v2_to_v3(connection)
                    version = 3
                if version != SCHEMA_VERSION:
                    raise RuntimeError("incompatible JobStore schema version")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _create_base_schema(connection: sqlite3.Connection) -> None:
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

    @staticmethod
    def _read_or_seed_schema_version(connection: sqlite3.Connection) -> int:
        row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is not None:
            return int(row[0])
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES('schema_version', '1')"
        )
        return 1

    @staticmethod
    def _migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                state TEXT NOT NULL,
                generation INTEGER NOT NULL,
                attempt INTEGER NOT NULL,
                worker_id TEXT,
                lease_expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_job_state ON tasks(job_id, state);
            """
        )
        connection.execute(
            "UPDATE metadata SET value = '2' WHERE key = 'schema_version'"
        )

    @staticmethod
    def _migrate_v2_to_v3(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS task_descriptors (
                task_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                priority INTEGER NOT NULL,
                descriptor_version INTEGER NOT NULL,
                descriptor_json TEXT NOT NULL,
                reconstructable INTEGER NOT NULL CHECK(reconstructable IN (0, 1)),
                created_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(task_id),
                FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            );
            CREATE INDEX IF NOT EXISTS idx_task_descriptors_job
                ON task_descriptors(job_id, priority, task_id);
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO task_descriptors(
                task_id, job_id, priority, descriptor_version,
                descriptor_json, reconstructable, created_at
            )
            SELECT task_id, job_id, 20, 0, '{}', 0, created_at FROM tasks
            """
        )
        connection.execute(
            "UPDATE metadata SET value = '3' WHERE key = 'schema_version'"
        )

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
                self._append_event(
                    connection,
                    job_id=job_id,
                    event_code="JOB.CREATED",
                    from_state=None,
                    to_state="CREATED",
                    generation=0,
                    occurred_at=now,
                    detail={},
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

    def list_jobs(self, *, states: tuple[str, ...] | None = None) -> tuple[JobRecord, ...]:
        query = (
            "SELECT job_id, state, generation, source_hash, config_hash, created_at, updated_at "
            "FROM jobs"
        )
        parameters: tuple[Any, ...] = ()
        if states:
            placeholders = ",".join("?" for _ in states)
            query += f" WHERE state IN ({placeholders})"
            parameters = states
        query += " ORDER BY created_at, job_id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(JobRecord(*row) for row in rows)

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
                self._append_event(
                    connection,
                    job_id=job_id,
                    event_code=event_code,
                    from_state=expected_state,
                    to_state=new_state,
                    generation=generation,
                    occurred_at=now,
                    detail=detail or {},
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_job(job_id)

    def create_task(
        self,
        task_id: str,
        *,
        job_id: str,
        priority: int = 20,
        descriptor: dict[str, Any] | None = None,
        descriptor_version: int = 1,
    ) -> TaskRecord:
        if not isinstance(priority, int):
            raise TypeError("priority must be an integer")
        if descriptor_version <= 0:
            raise ValueError("descriptor_version must be positive")
        now = self._timestamp()
        descriptor_payload = descriptor or {}
        reconstructable = descriptor is not None
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO tasks(
                        task_id, job_id, state, generation, attempt, worker_id,
                        lease_expires_at, created_at, updated_at
                    ) VALUES (?, ?, 'PENDING', 0, 0, NULL, NULL, ?, ?)
                    """,
                    (task_id, job_id, now, now),
                )
                connection.execute(
                    """
                    INSERT INTO task_descriptors(
                        task_id, job_id, priority, descriptor_version,
                        descriptor_json, reconstructable, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        job_id,
                        priority,
                        descriptor_version,
                        json.dumps(descriptor_payload, ensure_ascii=False, sort_keys=True),
                        int(reconstructable),
                        now,
                    ),
                )
                self._append_event(
                    connection,
                    job_id=job_id,
                    event_code="TASK.CREATED",
                    from_state=None,
                    to_state="PENDING",
                    generation=0,
                    occurred_at=now,
                    detail={
                        "task_id": task_id,
                        "priority": priority,
                        "descriptor_version": descriptor_version,
                        "reconstructable": reconstructable,
                    },
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> TaskRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT task_id, job_id, state, generation, attempt, worker_id,
                       lease_expires_at, created_at, updated_at
                FROM tasks WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return TaskRecord(*row)

    def get_task_descriptor(self, task_id: str) -> TaskDescriptorRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT task_id, job_id, priority, descriptor_version,
                       descriptor_json, reconstructable, created_at
                FROM task_descriptors WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return TaskDescriptorRecord(
            task_id=row[0],
            job_id=row[1],
            priority=row[2],
            descriptor_version=row[3],
            descriptor=json.loads(row[4]),
            reconstructable=bool(row[5]),
            created_at=row[6],
        )

    def list_reconstructable_tasks(
        self,
        job_id: str,
        *,
        states: tuple[str, ...] = ("PENDING", "INTERRUPTED"),
    ) -> tuple[tuple[TaskRecord, TaskDescriptorRecord], ...]:
        if not states:
            return ()
        placeholders = ",".join("?" for _ in states)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    t.task_id, t.job_id, t.state, t.generation, t.attempt,
                    t.worker_id, t.lease_expires_at, t.created_at, t.updated_at,
                    d.priority, d.descriptor_version, d.descriptor_json,
                    d.reconstructable, d.created_at
                FROM tasks t
                JOIN task_descriptors d ON d.task_id = t.task_id
                WHERE t.job_id = ? AND t.state IN ({placeholders})
                  AND d.reconstructable = 1
                ORDER BY d.priority, t.task_id
                """,
                (job_id, *states),
            ).fetchall()
        results: list[tuple[TaskRecord, TaskDescriptorRecord]] = []
        for row in rows:
            task = TaskRecord(*row[:9])
            descriptor = TaskDescriptorRecord(
                task_id=row[0],
                job_id=row[1],
                priority=row[9],
                descriptor_version=row[10],
                descriptor=json.loads(row[11]),
                reconstructable=bool(row[12]),
                created_at=row[13],
            )
            results.append((task, descriptor))
        return tuple(results)

    def assign_task(
        self,
        task_id: str,
        *,
        expected_generation: int,
        worker_id: str,
        attempt: int,
        lease_expires_at: str,
    ) -> TaskRecord:
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        now = self._timestamp()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                current = connection.execute(
                    "SELECT job_id, state, attempt FROM tasks WHERE task_id = ?",
                    (task_id,),
                ).fetchone()
                if current is None:
                    raise KeyError(task_id)
                job_id, state, current_attempt = current
                if state not in {"PENDING", "INTERRUPTED"} or attempt <= current_attempt:
                    raise RuntimeError("stale or invalid task assignment")
                cursor = connection.execute(
                    """
                    UPDATE tasks
                    SET state = 'RUNNING', generation = generation + 1, attempt = ?,
                        worker_id = ?, lease_expires_at = ?, updated_at = ?
                    WHERE task_id = ? AND generation = ?
                    """,
                    (attempt, worker_id, lease_expires_at, now, task_id, expected_generation),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("stale or invalid task assignment")
                generation = expected_generation + 1
                self._append_event(
                    connection,
                    job_id=job_id,
                    event_code="TASK.ASSIGNED",
                    from_state=state,
                    to_state="RUNNING",
                    generation=generation,
                    occurred_at=now,
                    detail={
                        "task_id": task_id,
                        "worker_id": worker_id,
                        "attempt": attempt,
                        "lease_expires_at": lease_expires_at,
                    },
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_task(task_id)

    def renew_task_lease(
        self,
        task_id: str,
        *,
        expected_generation: int,
        worker_id: str,
        attempt: int,
        lease_expires_at: str,
    ) -> TaskRecord:
        now = self._timestamp()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks
                    SET generation = generation + 1, lease_expires_at = ?, updated_at = ?
                    WHERE task_id = ? AND state = 'RUNNING' AND generation = ?
                      AND worker_id = ? AND attempt = ?
                    """,
                    (
                        lease_expires_at,
                        now,
                        task_id,
                        expected_generation,
                        worker_id,
                        attempt,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("stale or invalid task lease renewal")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_task(task_id)

    def finish_task(
        self,
        task_id: str,
        *,
        expected_generation: int,
        worker_id: str,
        attempt: int,
        new_state: str,
        event_code: str,
    ) -> TaskRecord:
        if new_state not in {"SUCCEEDED", "FAILED", "REVIEW", "INTERRUPTED"}:
            raise ValueError("invalid terminal/interrupted task state")
        now = self._timestamp()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                current = connection.execute(
                    "SELECT job_id FROM tasks WHERE task_id = ?",
                    (task_id,),
                ).fetchone()
                if current is None:
                    raise KeyError(task_id)
                job_id = current[0]
                cursor = connection.execute(
                    """
                    UPDATE tasks
                    SET state = ?, generation = generation + 1,
                        lease_expires_at = NULL, updated_at = ?
                    WHERE task_id = ? AND state = 'RUNNING' AND generation = ?
                      AND worker_id = ? AND attempt = ?
                    """,
                    (new_state, now, task_id, expected_generation, worker_id, attempt),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("stale or invalid task completion")
                generation = expected_generation + 1
                self._append_event(
                    connection,
                    job_id=job_id,
                    event_code=event_code,
                    from_state="RUNNING",
                    to_state=new_state,
                    generation=generation,
                    occurred_at=now,
                    detail={
                        "task_id": task_id,
                        "worker_id": worker_id,
                        "attempt": attempt,
                    },
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get_task(task_id)

    def list_tasks(self, job_id: str, *, state: str | None = None) -> tuple[TaskRecord, ...]:
        query = (
            "SELECT task_id, job_id, state, generation, attempt, worker_id, "
            "lease_expires_at, created_at, updated_at FROM tasks WHERE job_id = ?"
        )
        parameters: tuple[Any, ...] = (job_id,)
        if state is not None:
            query += " AND state = ?"
            parameters = (job_id, state)
        query += " ORDER BY task_id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(TaskRecord(*row) for row in rows)

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

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        *,
        job_id: str,
        event_code: str,
        from_state: str | None,
        to_state: str | None,
        generation: int,
        occurred_at: str,
        detail: dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO events(
                job_id, event_code, from_state, to_state, generation, occurred_at, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                event_code,
                from_state,
                to_state,
                generation,
                occurred_at,
                json.dumps(detail, ensure_ascii=False, sort_keys=True),
            ),
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat()
