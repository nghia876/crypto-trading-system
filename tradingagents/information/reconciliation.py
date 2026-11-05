"""Evaluation-only exact-row reconciliation. Never selects an operational store.

Caller owns private snapshots/manifest and approval. This deliberately bypasses
append(), whose ingestion deduplication and automatic links would rewrite history.
Only the current four-table schema is supported; no migrations are performed.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from tradingagents.information.store import SQLiteInformationStore

TABLES = ("observations", "source_definitions", "coverage", "data_gaps")


class ReconciliationConflict(ValueError):
    """Candidate must not be accepted; no winner is chosen."""


def read_rows(connection):
    """Read exact SQLite values, including JSON serialization and timestamp text."""
    return {table: connection.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in TABLES}


def row_digest(rows):
    return hashlib.sha256(json.dumps(sorted(rows, key=repr), ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def schema(connection):
    return connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).fetchall()


def validate(connection):
    """Check application references absent from SQL foreign-key declarations.

Repeated content versions are legal acquisition copies. Reusing a version for
different headline/date/evidence content, or a source version for a different
definition, is a conflict. No cross-store revision links are synthesized.
"""
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ReconciliationConflict("SQLite integrity failed")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise ReconciliationConflict("SQL foreign-key violation")
    rows = read_rows(connection)
    try:
        observations = {r[0]: SQLiteInformationStore._decode_observation(r)
                        for r in rows["observations"]}
    except (ValueError, TypeError, KeyError) as exc:
        raise ReconciliationConflict("invalid observation envelope") from exc
    definitions = {}
    source_ids = set()
    fingerprints = defaultdict(set)
    for source_id, version, _observed, definition in rows["source_definitions"]:
        value = json.loads(definition)
        if (value["source_id"], value["version"]) != (source_id, version):
            raise ReconciliationConflict("source definition identity mismatch")
        key = (source_id, version)
        if key in definitions and definitions[key] != value:
            raise ReconciliationConflict("conflicting source version")
        definitions[key] = value
        source_ids.add(source_id)
        metadata = dict(value.get("metadata", []))
        if fingerprint := metadata.get("config_fingerprint"):
            fingerprints[source_id].add(fingerprint)
    versions = {}
    children = defaultdict(list)
    for obs in observations.values():
        if obs.source_id not in source_ids:
            raise ReconciliationConflict("missing observation source")
        if prior_id := obs.supersedes_observation_id:
            prior = observations.get(prior_id)
            if prior is None or (prior.source_id, prior.subject, prior.metric, prior.event_time) != (
                obs.source_id, obs.subject, obs.metric, obs.event_time
            ) or prior.available_at > obs.available_at:
                raise ReconciliationConflict("invalid supersession lineage")
            children[prior_id].append(obs.observation_id)
        # Cycles and forks require review, rather than silently selecting a head.
        seen = {obs.observation_id}
        cursor = obs
        while cursor.supersedes_observation_id:
            target = cursor.supersedes_observation_id
            if target in seen or target not in observations:
                raise ReconciliationConflict("cyclic or dangling lineage")
            seen.add(target)
            cursor = observations[target]
        if obs.schema_version == "narrative-news-v1":
            payload = obs.payload
            if payload["config_fingerprint"] not in fingerprints[obs.source_id]:
                raise ReconciliationConflict("unregistered acquisition fingerprint")
            if payload["article_id"] != obs.subject or payload["version_id"] != (
                obs.subject + ":" + payload["content_hash"]
            ):
                raise ReconciliationConflict("article/version identity mismatch")
            content = tuple(payload.get(k) for k in (
                "claim", "published_raw", "updated_raw", "canonical_url", "evidence_text"
            ))
            key = payload["version_id"]
            if key in versions and versions[key] != content:
                raise ReconciliationConflict("conflicting content version")
            versions[key] = content
        # Derived observations also carry application-level references.
        for field in ("evidence_ids", "target_ids", "retract_ids"):
            for target in obs.payload.get(field, ()):
                if target not in observations:
                    raise ReconciliationConflict("dangling payload reference")
    if any(len(ids) > 1 for ids in children.values()):
        raise ReconciliationConflict("forked supersession lineage")
    for row in rows["coverage"]:
        if row[1] not in source_ids:
            raise ReconciliationConflict("missing coverage source")
        for evidence_id in json.loads(row[7]):
            if evidence_id not in observations:
                raise ReconciliationConflict("dangling coverage evidence")
    return {"counts": {t: len(r) for t, r in rows.items()},
            "row_sha256": {t: row_digest(r) for t, r in rows.items()},
            "supersession_links": sum(bool(o.supersedes_observation_id)
                                      for o in observations.values()),
            "source_ids": len(source_ids), "content_versions": len(versions)}


def merge_transaction(destination, incoming):
    """Strict primary-key equality checks plus post-insert semantic validation.

    All insertion and validation is one transaction. On any failure, return to
    the exact baseline rows. Identical shared keys are explicitly counted.
    """
    if destination.in_transaction:
        raise ValueError("destination must have no pending transaction")
    baseline = read_rows(destination)
    counts = {}
    try:
        destination.execute("BEGIN IMMEDIATE")
        for table in TABLES:
            info = destination.execute(f'PRAGMA table_info("{table}")').fetchall()
            keys = [i for i, c in sorted(enumerate(info), key=lambda pair: pair[1][5])
                    if c[5]]
            existing = {tuple(r[i] for i in keys): r for r in baseline[table]}
            inserted = identical = 0
            for row in sorted(incoming[table], key=repr):
                key = tuple(row[i] for i in keys)
                if key in existing:
                    if existing[key] != row:
                        raise ReconciliationConflict(f"unequal primary key in {table}")
                    identical += 1
                    continue
                destination.execute(f'INSERT INTO "{table}" VALUES ('
                                    + ",".join("?" for _ in row) + ")", row)
                existing[key] = row
                inserted += 1
            counts[table] = {"inserted": inserted, "identical_shared_keys": identical}
        result = validate(destination)
        destination.commit()
        return {"tables": counts, "validation": result}
    except BaseException:
        destination.rollback()
        if read_rows(destination) != baseline:
            raise RuntimeError("rollback failed exact-row verification") from None
        raise


def build_candidate(base_snapshot: Path, incoming_snapshot: Path, candidate: Path):
    """Create a NEW candidate only, outside this checkout, from RO snapshots.

    On rejection the private file is retained at its rolled-back baseline for
    diagnosis. Its existence never means accepted; only successful return does.
    """
    candidate = candidate.resolve()
    repository = Path(__file__).resolve().parents[2]
    if candidate.is_relative_to(repository) or candidate in (
        base_snapshot.resolve(), incoming_snapshot.resolve()
    ):
        raise ValueError("candidate must be private and distinct from inputs")
    with (
        sqlite3.connect(base_snapshot.resolve().as_uri() + "?mode=ro", uri=True) as base,
        sqlite3.connect(incoming_snapshot.resolve().as_uri() + "?mode=ro", uri=True) as incoming,
    ):
        if schema(base) != schema(incoming):
            raise ReconciliationConflict("schema mismatch; migration forbidden")
        names = {r[1] for r in schema(base) if r[0] == "table"}
        if names != set(TABLES):
            raise ReconciliationConflict("unsupported tables")
        validate(base)
        validate(incoming)
        with candidate.open("xb"):
            pass
        with sqlite3.connect(candidate) as destination:
            base.backup(destination)
            return merge_transaction(destination, read_rows(incoming))
