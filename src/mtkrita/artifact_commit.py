from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .job_store import JobStore, TaskRecord
from .path_manager import PathKind, PathRef
from .resource_broker import CommittedArtifact, ResourceBroker

ARTIFACT_COMMIT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ArtifactCommitRecord:
    commit_id: str
    job_id: str
    task_id: str
    worker_id: str
    attempt: int
    task_generation: int
    source_path: str
    target_kind: str
    target_path: str
    expected_sha256: str
    byte_size: int
    state: str
    created_at: str
    updated_at: str


class ArtifactCommitJournal:
    """Durable commit-intent journal stored in the JobStore SQLite database."""

    def __init__(self, jobs: JobStore) -> None:
        self._jobs = jobs
        self._path = jobs.database_path

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS artifact_commits (
                        commit_id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        task_id TEXT NOT NULL,
                        worker_id TEXT NOT NULL,
                        attempt INTEGER NOT NULL,
                        task_generation INTEGER NOT NULL,
                        source_path TEXT NOT NULL,
                        target_kind TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        expected_sha256 TEXT NOT NULL,
                        byte_size INTEGER NOT NULL,
                        state TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY(job_id) REFERENCES jobs(job_id),
                        FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_artifact_commits_state
                        ON artifact_commits(state);
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_artifact_commits_target
                        ON artifact_commits(job_id, target_path)
                        WHERE state != 'SUPERSEDED';
                    """
                )
                row = connection.execute(
                    "SELECT value FROM metadata WHERE key = 'artifact_commit_schema_version'"
                ).fetchone()
                if row is None:
                    connection.execute(
                        "INSERT INTO metadata(key, value) VALUES(?, ?)",
                        ("artifact_commit_schema_version", str(ARTIFACT_COMMIT_SCHEMA_VERSION)),
                    )
                elif int(row[0]) != ARTIFACT_COMMIT_SCHEMA_VERSION:
                    raise RuntimeError("incompatible artifact commit schema version")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def create_intent(
        self,
        *,
        commit_id: str,
        task: TaskRecord,
        source: PathRef,
        target: PathRef,
        expected_sha256: str,
        byte_size: int,
    ) -> ArtifactCommitRecord:
        if task.state != "RUNNING" or task.worker_id is None or task.attempt <= 0:
            raise RuntimeError("task is not an authoritative RUNNING attempt")
        if source.job_id != task.job_id or target.job_id != task.job_id:
            raise ValueError("artifact commit job identity mismatch")
        if source.worker_id != task.worker_id:
            raise ValueError("artifact source worker does not own task attempt")
        if source.kind != PathKind.WORKER_SCRATCH:
            raise ValueError("artifact source must be worker scratch")
        if target.kind not in {PathKind.OUTPUT, PathKind.EVIDENCE}:
            raise ValueError("artifact target must be output or evidence")
        if byte_size < 0:
            raise ValueError("byte_size must be non-negative")

        now = self._timestamp()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                current = connection.execute(
                    """
                    SELECT state, generation, worker_id, attempt
                    FROM tasks WHERE task_id = ? AND job_id = ?
                    """,
                    (task.task_id, task.job_id),
                ).fetchone()
                expected = ("RUNNING", task.generation, task.worker_id, task.attempt)
                if current != expected:
                    raise RuntimeError("stale task attempt cannot create artifact commit intent")
                connection.execute(
                    """
                    INSERT INTO artifact_commits(
                        commit_id, job_id, task_id, worker_id, attempt, task_generation,
                        source_path, target_kind, target_path, expected_sha256, byte_size,
                        state, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INTENT', ?, ?)
                    """,
                    (
                        commit_id,
                        task.job_id,
                        task.task_id,
                        task.worker_id,
                        task.attempt,
                        task.generation,
                        str(source.path),
                        target.kind.value,
                        str(target.path),
                        expected_sha256,
                        byte_size,
                        now,
                        now,
                    ),
                )
                self._append_event(
                    connection,
                    task=task,
                    event_code="ARTIFACT.COMMIT_INTENT",
                    detail={
                        "commit_id": commit_id,
                        "target_path": str(target.path),
                        "sha256": expected_sha256,
                    },
                    occurred_at=now,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get(commit_id)

    def get(self, commit_id: str) -> ArtifactCommitRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT commit_id, job_id, task_id, worker_id, attempt, task_generation,
                       source_path, target_kind, target_path, expected_sha256, byte_size,
                       state, created_at, updated_at
                FROM artifact_commits WHERE commit_id = ?
                """,
                (commit_id,),
            ).fetchone()
        if row is None:
            raise KeyError(commit_id)
        return ArtifactCommitRecord(*row)

    def list_pending(self) -> tuple[ArtifactCommitRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT commit_id, job_id, task_id, worker_id, attempt, task_generation,
                       source_path, target_kind, target_path, expected_sha256, byte_size,
                       state, created_at, updated_at
                FROM artifact_commits
                WHERE state IN ('INTENT', 'PROMOTED')
                ORDER BY created_at, commit_id
                """
            ).fetchall()
        return tuple(ArtifactCommitRecord(*row) for row in rows)

    def mark_promoted(self, commit_id: str) -> ArtifactCommitRecord:
        return self._set_state(commit_id, expected_states={"INTENT"}, new_state="PROMOTED")

    def mark_integrity_failed(self, commit_id: str, *, reason: str) -> ArtifactCommitRecord:
        record = self.get(commit_id)
        updated = self._set_state(
            commit_id,
            expected_states={"INTENT", "PROMOTED"},
            new_state="FAILED_INTEGRITY",
        )
        self._record_artifact_event(record, "ARTIFACT.INTEGRITY_FAILED", {"reason": reason})
        return updated

    def mark_superseded(self, commit_id: str, *, reason: str) -> ArtifactCommitRecord:
        record = self.get(commit_id)
        updated = self._set_state(
            commit_id,
            expected_states={"INTENT", "PROMOTED"},
            new_state="SUPERSEDED",
        )
        self._record_artifact_event(record, "ARTIFACT.COMMIT_SUPERSEDED", {"reason": reason})
        return updated

    def finalize_success(self, commit_id: str) -> ArtifactCommitRecord:
        record = self.get(commit_id)
        now = self._timestamp()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                current_commit = connection.execute(
                    "SELECT state FROM artifact_commits WHERE commit_id = ?",
                    (commit_id,),
                ).fetchone()
                if current_commit is None or current_commit[0] not in {"INTENT", "PROMOTED"}:
                    raise RuntimeError("artifact commit is not finalizable")
                cursor = connection.execute(
                    """
                    UPDATE tasks
                    SET state = 'SUCCEEDED', generation = generation + 1,
                        lease_expires_at = NULL, updated_at = ?
                    WHERE task_id = ? AND job_id = ? AND state = 'RUNNING'
                      AND generation = ? AND worker_id = ? AND attempt = ?
                    """,
                    (
                        now,
                        record.task_id,
                        record.job_id,
                        record.task_generation,
                        record.worker_id,
                        record.attempt,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("stale task attempt cannot finalize artifact commit")
                connection.execute(
                    """
                    UPDATE artifact_commits
                    SET state = 'COMMITTED', updated_at = ?
                    WHERE commit_id = ? AND state IN ('INTENT', 'PROMOTED')
                    """,
                    (now, commit_id),
                )
                task = TaskRecord(
                    task_id=record.task_id,
                    job_id=record.job_id,
                    state="SUCCEEDED",
                    generation=record.task_generation + 1,
                    attempt=record.attempt,
                    worker_id=record.worker_id,
                    lease_expires_at=None,
                    created_at="",
                    updated_at=now,
                )
                self._append_event(
                    connection,
                    task=task,
                    event_code="TASK.SUCCEEDED_WITH_ARTIFACT",
                    detail={
                        "commit_id": commit_id,
                        "target_path": record.target_path,
                        "sha256": record.expected_sha256,
                    },
                    occurred_at=now,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.get(commit_id)

    def target_ref(self, record: ArtifactCommitRecord) -> PathRef:
        return PathRef(
            kind=PathKind(record.target_kind),
            path=Path(record.target_path),
            job_id=record.job_id,
        )

    def _set_state(
        self,
        commit_id: str,
        *,
        expected_states: set[str],
        new_state: str,
    ) -> ArtifactCommitRecord:
        now = self._timestamp()
        placeholders = ",".join("?" for _ in expected_states)
        ordered = tuple(sorted(expected_states))
        with self._connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE artifact_commits SET state = ?, updated_at = ?
                WHERE commit_id = ? AND state IN ({placeholders})
                """,
                (new_state, now, commit_id, *ordered),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("artifact commit state transition rejected")
        return self.get(commit_id)

    def _record_artifact_event(
        self,
        record: ArtifactCommitRecord,
        event_code: str,
        detail: dict[str, object],
    ) -> None:
        task = self._jobs.get_task(record.task_id)
        now = self._timestamp()
        with self._connect() as connection:
            self._append_event(
                connection,
                task=task,
                event_code=event_code,
                detail={"commit_id": record.commit_id, **detail},
                occurred_at=now,
            )

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        *,
        task: TaskRecord,
        event_code: str,
        detail: dict[str, object],
        occurred_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO events(
                job_id, event_code, from_state, to_state, generation, occurred_at, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.job_id,
                event_code,
                task.state,
                task.state,
                task.generation,
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


@dataclass(frozen=True)
class ArtifactCommitCoordinator:
    journal: ArtifactCommitJournal
    broker: ResourceBroker

    def commit_task_artifact(
        self,
        *,
        commit_id: str,
        task: TaskRecord,
        source: PathRef,
        target: PathRef,
        expected_sha256: str | None = None,
    ) -> CommittedArtifact:
        candidate = self.broker.validate_worker_file(
            source,
            expected_sha256=expected_sha256,
        )
        self.journal.create_intent(
            commit_id=commit_id,
            task=task,
            source=source,
            target=target,
            expected_sha256=candidate.sha256,
            byte_size=candidate.byte_size,
        )
        committed = self.broker.commit_worker_file(
            source,
            target,
            expected_sha256=candidate.sha256,
        )
        self.journal.mark_promoted(commit_id)
        self.journal.finalize_success(commit_id)
        return committed


@dataclass(frozen=True)
class ArtifactCommitReconciler:
    journal: ArtifactCommitJournal
    broker: ResourceBroker
    jobs: JobStore

    def reconcile(self) -> tuple[str, ...]:
        finalized: list[str] = []
        for record in self.journal.list_pending():
            task = self.jobs.get_task(record.task_id)
            authoritative = (
                task.job_id == record.job_id
                and task.state == "RUNNING"
                and task.generation == record.task_generation
                and task.worker_id == record.worker_id
                and task.attempt == record.attempt
            )
            if not authoritative:
                self.journal.mark_superseded(
                    record.commit_id,
                    reason="task attempt is no longer authoritative",
                )
                continue

            target = self.journal.target_ref(record)
            if not target.path.exists():
                if record.state == "PROMOTED":
                    self.journal.mark_integrity_failed(
                        record.commit_id,
                        reason="promoted artifact is missing",
                    )
                continue

            try:
                self.broker.verify_authoritative_file(
                    target,
                    expected_sha256=record.expected_sha256,
                    expected_byte_size=record.byte_size,
                )
            except (FileNotFoundError, ValueError) as exc:
                self.journal.mark_integrity_failed(record.commit_id, reason=str(exc))
                continue

            if record.state == "INTENT":
                self.journal.mark_promoted(record.commit_id)
            self.journal.finalize_success(record.commit_id)
            finalized.append(record.commit_id)
        return tuple(finalized)
