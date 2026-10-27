"""Append-only SQLite storage and point-in-time reconstruction for observations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from tradingagents.information.binance_spot import (
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    MarketDataGap,
)
from tradingagents.information.observations import (
    Observation,
    ObservationAvailability,
    ObservationQuality,
    Transformation,
)
from tradingagents.information.sources import Source, SourceStatus


class ObservationStoreConflict(RuntimeError):
    """An observation ID was reused for different immutable observation content."""


@dataclass(frozen=True, slots=True)
class InformationView:
    """Observations and known data gaps available by one decision cutoff."""

    decision_time: datetime
    observations: tuple[Observation, ...]
    gaps: tuple[MarketDataGap, ...]
    coverage: tuple[CoverageRecord, ...] = ()
    source_definitions: tuple[tuple[Source, datetime], ...] = ()


def _aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _json_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if hasattr(value, "items"):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"observation payload is not JSON-compatible: {type(value).__name__}")


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _observation_values(observation: Observation) -> tuple[object, ...]:
    return (
        observation.observation_id,
        observation.source_id,
        observation.subject,
        observation.metric,
        observation.event_time.isoformat(),
        observation.first_seen_time.isoformat(),
        observation.retrieved_at.isoformat(),
        _timestamp(observation.publication_time),
        _timestamp(observation.effective_time),
        observation.raw_reference,
        json.dumps(_json_value(observation.payload), sort_keys=True, separators=(",", ":")),
        json.dumps(
            [
                {"name": item.name, "version": item.version, "parameters": list(item.parameters)}
                for item in observation.transformations
            ],
            sort_keys=True,
            separators=(",", ":"),
        ),
        observation.quality.value,
        observation.availability.value,
        json.dumps(list(observation.quality_notes), separators=(",", ":")),
        observation.supersedes_observation_id,
        observation.schema_version,
        observation.unit,
    )


class SQLiteInformationStore:
    """Durable append-only store for observations and collector gap records.

    Each operation opens its own SQLite connection, so a store can be reopened
    across process restarts. Revisions are never updated in place. ``view_at``
    returns only versions whose conservative availability bound is at or before
    the cutoff and hides a prior version only when an eligible revision
    explicitly supersedes it.
    """

    _OBSERVATION_COLUMNS = (
        "observation_id, source_id, subject, metric, event_time, first_seen_time, "
        "retrieved_at, publication_time, effective_time, raw_reference, payload_json, "
        "transformations_json, quality, availability, quality_notes_json, "
        "supersedes_observation_id, schema_version, unit"
    )

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path == ":memory:":
            raise ValueError("durable information storage requires a filesystem database path")
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    first_seen_time TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    publication_time TEXT,
                    effective_time TEXT,
                    raw_reference TEXT,
                    payload_json TEXT NOT NULL,
                    transformations_json TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    availability TEXT NOT NULL,
                    quality_notes_json TEXT NOT NULL,
                    supersedes_observation_id TEXT,
                    schema_version TEXT NOT NULL DEFAULT '1',
                    unit TEXT NOT NULL DEFAULT 'unknown'
                );
                CREATE INDEX IF NOT EXISTS observations_event_idx
                    ON observations(subject, metric, event_time);
                CREATE TABLE IF NOT EXISTS source_definitions (
                    source_id TEXT NOT NULL, version TEXT NOT NULL, observed_at TEXT NOT NULL,
                    definition_json TEXT NOT NULL, PRIMARY KEY(source_id, version, observed_at)
                );
                CREATE TABLE IF NOT EXISTS coverage (
                    coverage_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS data_gaps (
                    subject TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    freshness TEXT NOT NULL,
                    PRIMARY KEY(subject, metric, event_time, observed_at, reason, freshness)
                );
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(observations)")}
            if "schema_version" not in columns:
                connection.execute(
                    "ALTER TABLE observations ADD COLUMN schema_version TEXT NOT NULL DEFAULT '1'"
                )
            if "unit" not in columns:
                connection.execute(
                    "ALTER TABLE observations ADD COLUMN unit TEXT NOT NULL DEFAULT 'unknown'"
                )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def append(self, batch: MarketDataBatch) -> None:
        """Persist a collector batch idempotently without overwriting history."""
        for observation in batch.observations:
            _aware("event_time", observation.event_time)
            _aware("first_seen_time", observation.first_seen_time)
            _aware("retrieved_at", observation.retrieved_at)
        for record in batch.coverage:
            _aware("coverage.observed_at", record.observed_at)
        for source in batch.source_definitions:
            if not isinstance(source, Source):
                raise TypeError("source_definitions must contain Source records")
            _aware("source definition observed_at", batch.retrieved_at)
        for gap in batch.gaps:
            _aware("gap.event_time", gap.event_time)
            _aware("gap.observed_at", gap.observed_at)

        insert_observation = (
            f"INSERT OR IGNORE INTO observations ({self._OBSERVATION_COLUMNS}) "
            f"VALUES ({','.join('?' for _ in range(18))})"
        )
        with self._connection() as connection:
            for observation in batch.observations:
                values = _observation_values(observation)
                existing_id = connection.execute(
                    f"SELECT {self._OBSERVATION_COLUMNS} FROM observations WHERE observation_id = ?",
                    (observation.observation_id,),
                ).fetchone()
                if existing_id is not None:
                    if (observation.metric == "narrative.event"
                            and observation.supersedes_observation_id is None):
                        # Match the append-time automatic revision link when a
                        # caller retries the identical immutable narrative batch.
                        stored = self._decode_observation(existing_id)
                        values = _observation_values(replace(
                            observation, supersedes_observation_id=stored.supersedes_observation_id
                        ))
                    if existing_id != values:
                        raise ObservationStoreConflict(
                            f"observation_id reused with different content: {observation.observation_id}"
                        )
                    continue

                candidates = connection.execute(
                    f"SELECT {self._OBSERVATION_COLUMNS} FROM observations "
                    "WHERE source_id = ? AND subject = ? AND metric = ?",
                    (observation.source_id, observation.subject, observation.metric),
                ).fetchall()
                prior_versions = []
                for row in candidates:
                    candidate = self._decode_observation(row)
                    if (
                        candidate.event_time == observation.event_time
                        and candidate.availability is ObservationAvailability.AVAILABLE
                    ):
                        prior_versions.append(candidate)
                prior_versions = [
                    prior
                    for prior in prior_versions
                    if prior.available_at <= observation.available_at
                ]
                prior = max(prior_versions, key=lambda item: item.available_at, default=None)
                if prior is not None and observation.supersedes_observation_id is None:
                    if (dict(prior.payload) == dict(observation.payload)
                            and observation.metric != "narrative.event"):
                        # A restarted collector may assign a new ID to an unchanged
                        # candle. Keep the first-seen version and do not move its
                        # point-in-time availability forward.
                        continue
                    # Narrative polls retain every copy so coverage evidence IDs
                    # always resolve, including unchanged feed repetitions.
                    observation = replace(
                        observation,
                        supersedes_observation_id=prior.observation_id,
                    )
                    values = _observation_values(observation)
                if observation.supersedes_observation_id is not None:
                    target = connection.execute(
                        f"SELECT {self._OBSERVATION_COLUMNS} FROM observations WHERE observation_id = ?",
                        (observation.supersedes_observation_id,),
                    ).fetchone()
                    if target is not None:
                        prior = self._decode_observation(target)
                        if (
                            prior.source_id,
                            prior.subject,
                            prior.metric,
                            prior.event_time,
                        ) != (
                            observation.source_id,
                            observation.subject,
                            observation.metric,
                            observation.event_time,
                        ):
                            raise ObservationStoreConflict(
                                "a revision must supersede the same source, subject, metric, and event time"
                            )
                cursor = connection.execute(insert_observation, values)
                if cursor.rowcount == 0:
                    existing = connection.execute(
                        f"SELECT {self._OBSERVATION_COLUMNS} FROM observations WHERE observation_id = ?",
                        (observation.observation_id,),
                    ).fetchone()
                    if existing != values:
                        raise ObservationStoreConflict(
                            f"observation_id reused with different content: {observation.observation_id}"
                        )
            connection.executemany(
                """INSERT OR IGNORE INTO source_definitions
                   (source_id, version, observed_at, definition_json) VALUES (?, ?, ?, ?)""",
                [(source.source_id, source.version, batch.retrieved_at.isoformat(),
                  json.dumps({**asdict(source), "status": source.status.value}, sort_keys=True, default=list))
                 for source in batch.source_definitions],
            )
            connection.executemany(
                """INSERT OR IGNORE INTO coverage
                   (coverage_id, source_id, subject, metric, observed_at, status, detail, evidence_ids_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        r.coverage_id,
                        r.source_id,
                        r.subject,
                        r.metric,
                        r.observed_at.isoformat(),
                        r.status.value,
                        r.detail,
                        json.dumps(r.evidence_ids),
                    )
                    for r in batch.coverage
                ],
            )
            connection.executemany(
                """INSERT OR IGNORE INTO data_gaps
                   (subject, metric, event_time, observed_at, reason, freshness)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        gap.subject,
                        gap.metric,
                        gap.event_time.isoformat(),
                        gap.observed_at.isoformat(),
                        gap.reason,
                        gap.freshness,
                    )
                    for gap in batch.gaps
                ],
            )

    def first_seen_for_subject(self, subject: str) -> datetime | None:
        """Earliest local observation across discovery sources, never publication time."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT first_seen_time FROM observations WHERE subject = ? AND metric = 'narrative.event'",
                (subject,),
            ).fetchall()
        return min((datetime.fromisoformat(row[0]) for row in rows), default=None)

    def coverage_by_id(self, coverage_id: str) -> CoverageRecord | None:
        """Read a durable poll outcome for restart-safe idempotency."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT coverage_id, source_id, subject, metric, observed_at, status, detail, evidence_ids_json FROM coverage WHERE coverage_id = ?",
                (coverage_id,),
            ).fetchone()
        if row is None:
            return None
        return CoverageRecord(*row[:4], datetime.fromisoformat(row[4]), CoverageStatus(row[5]), row[6], tuple(json.loads(row[7])))

    def view_at(self, decision_time: datetime) -> InformationView:
        """Reconstruct the observations and gaps known at an aware cutoff."""
        _aware("decision_time", decision_time)
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT {self._OBSERVATION_COLUMNS} FROM observations"
            ).fetchall()
            source_rows = connection.execute(
                "SELECT source_id, version, observed_at, definition_json FROM source_definitions"
            ).fetchall()
            coverage_rows = connection.execute(
                "SELECT coverage_id, source_id, subject, metric, observed_at, status, detail, evidence_ids_json FROM coverage"
            ).fetchall()
            gap_rows = connection.execute(
                """SELECT subject, metric, event_time, observed_at, reason, freshness
                   FROM data_gaps"""
            ).fetchall()

        eligible = [
            observation
            for row in rows
            if (observation := self._decode_observation(row)).is_available_at(decision_time)
        ]
        eligible_by_id = {observation.observation_id: observation for observation in eligible}
        superseded = set()
        for observation in eligible:
            if observation.supersedes_observation_id is None:
                continue
            prior = eligible_by_id.get(observation.supersedes_observation_id)
            if prior is not None and (
                prior.source_id,
                prior.subject,
                prior.metric,
                prior.event_time,
            ) == (
                observation.source_id,
                observation.subject,
                observation.metric,
                observation.event_time,
            ):
                superseded.add(prior.observation_id)
        visible = tuple(
            sorted(
                (item for item in eligible if item.observation_id not in superseded),
                key=lambda item: (item.event_time, item.metric, item.observation_id),
            )
        )
        resolved_gap_keys = {(item.subject, item.metric, item.event_time) for item in visible}
        gaps = tuple(
            sorted(
                (
                    MarketDataGap(
                        subject=row[0],
                        metric=row[1],
                        event_time=datetime.fromisoformat(row[2]),
                        observed_at=datetime.fromisoformat(row[3]),
                        reason=row[4],
                        freshness=row[5],
                    )
                    for row in gap_rows
                    if datetime.fromisoformat(row[3]) <= decision_time
                    and (row[0], row[1], datetime.fromisoformat(row[2])) not in resolved_gap_keys
                ),
                key=lambda item: (item.event_time, item.metric, item.observed_at),
            )
        )
        latest_sources = {}
        for source_id, version, observed_at, payload in source_rows:
            observed = datetime.fromisoformat(observed_at)
            if observed <= decision_time:
                key = (source_id, version)
                if key not in latest_sources or latest_sources[key][1] < observed:
                    definition = json.loads(payload)
                    for name in ("asset_scope", "metric_scope", "limitations", "legal_constraints", "metadata"):
                        definition[name] = tuple(tuple(v) if isinstance(v, list) else v for v in definition.get(name, ()))
                    definition["status"] = SourceStatus(definition["status"])
                    latest_sources[key] = (Source(**definition), observed)
        source_definitions = tuple(sorted(latest_sources.values(), key=lambda item: (item[0].source_id, item[1])))
        coverage = tuple(
            sorted(
                (
                    CoverageRecord(
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        datetime.fromisoformat(row[4]),
                        CoverageStatus(row[5]),
                        row[6],
                        tuple(json.loads(row[7])),
                    )
                    for row in coverage_rows
                    if datetime.fromisoformat(row[4]) <= decision_time
                ),
                key=lambda item: (
                    item.source_id,
                    item.subject,
                    item.metric,
                    item.observed_at,
                    item.coverage_id,
                ),
            )
        )
        return InformationView(decision_time, visible, gaps, coverage, source_definitions)

    @staticmethod
    def _decode_observation(row: tuple[Any, ...]) -> Observation:
        (
            observation_id,
            source_id,
            subject,
            metric,
            event_time,
            first_seen_time,
            retrieved_at,
            publication_time,
            effective_time,
            raw_reference,
            payload_json,
            transformations_json,
            quality,
            availability,
            quality_notes_json,
            supersedes_observation_id,
            schema_version,
            unit,
        ) = row
        transformations = tuple(
            Transformation(
                name=item["name"],
                version=item["version"],
                parameters=tuple(tuple(pair) for pair in item["parameters"]),
            )
            for item in json.loads(transformations_json)
        )
        return Observation(
            observation_id=observation_id,
            source_id=source_id,
            subject=subject,
            metric=metric,
            payload=json.loads(payload_json),
            event_time=datetime.fromisoformat(event_time),
            first_seen_time=datetime.fromisoformat(first_seen_time),
            retrieved_at=datetime.fromisoformat(retrieved_at),
            publication_time=(
                datetime.fromisoformat(publication_time) if publication_time else None
            ),
            effective_time=(datetime.fromisoformat(effective_time) if effective_time else None),
            raw_reference=raw_reference,
            transformations=transformations,
            quality=ObservationQuality(quality),
            availability=ObservationAvailability(availability),
            quality_notes=tuple(json.loads(quality_notes_json)),
            supersedes_observation_id=supersedes_observation_id,
            schema_version=schema_version,
            unit=unit,
        )
