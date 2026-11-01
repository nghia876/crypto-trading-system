"""Caller-reviewed occurrence context, appended to the canonical PIT store.

Context is evidence about one immutable article version, never a pair label or
incident membership. Canonical keys require reviewer normalization; disjoint
keys must mean disjoint places/episodes, not aliases or nested administrative areas.
"""

import hashlib
import json
from datetime import datetime

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.observations import Observation, _require_aware


def record_event_context(
    store,
    *,
    evidence_id,
    recorded_at,
    reviewer,
    provenance,
    rationale,
    episode_key=None,
    location_key=None,
    occurrence_start=None,
    occurrence_end=None,
    supersedes=None,
):
    """Append a review, correction or all-null withdrawal; never backdate acquisition.

    Caller supplies actual review/acquisition time, as for other curated APIs.
    Bounds describe the occurrence interval, not publication/reporting duration.
    Episode keys are globally namespaced; locations have one agreed granularity.
    """
    _require_aware("recorded_at", recorded_at)
    for value in (reviewer, provenance, rationale):
        if not isinstance(value, str) or not value.strip() or len(value) > 1000:
            raise ValueError("bounded reviewer, provenance and rationale required")
    for value in (episode_key, location_key):
        if value is not None and (
            not isinstance(value, str) or not value.strip() or len(value) > 160
        ):
            raise ValueError("context keys must be nonempty bounded canonical strings")
    for name, value in (("start", occurrence_start), ("end", occurrence_end)):
        if value is not None and not isinstance(value, datetime):
            raise ValueError("occurrence bounds must be aware datetimes")
        _require_aware(name, value)
    if (occurrence_start is None) != (occurrence_end is None) or (
        occurrence_start is not None and occurrence_start > occurrence_end
    ):
        raise ValueError("ordered paired occurrence bounds required")
    view = store.view_at(recorded_at)
    history = {r.observation_id: r for r in (*view.evidence_history, *view.observations)}
    evidence = history.get(evidence_id)
    if evidence is None or evidence.metric != "narrative.event":
        raise ValueError("available immutable narrative evidence required")
    previous = [
        r
        for r in view.observations
        if (r.metric == "narrative.event_context" and r.payload["evidence_id"] == evidence_id)
    ]
    if (previous and (len(previous) != 1 or supersedes != previous[0].observation_id)) or (
        not previous and supersedes is not None
    ):
        raise ValueError("correction must supersede the active review explicitly")
    payload = {
        "evidence_id": evidence_id,
        "reviewer": reviewer,
        "provenance": provenance,
        "rationale": rationale,
        "episode_key": episode_key,
        "location_key": location_key,
        "occurrence_start": occurrence_start.isoformat() if occurrence_start else None,
        "occurrence_end": occurrence_end.isoformat() if occurrence_end else None,
        "authority": "caller_reviewed_context",
    }
    digest = hashlib.sha256(
        (json.dumps(payload, sort_keys=True) + recorded_at.isoformat()).encode()
    ).hexdigest()
    row = Observation(
        observation_id="context:" + digest,
        source_id="derived.event_intelligence",
        subject="context:" + evidence_id,
        metric="narrative.event_context",
        payload=payload,
        event_time=evidence.event_time,
        first_seen_time=recorded_at,
        retrieved_at=recorded_at,
        supersedes_observation_id=supersedes,
        schema_version="event-context-v1",
        unit="context",
    )
    store.append(MarketDataBatch((row,), (), recorded_at))
    return row


def reviewed_context(view):
    """Active eligible reviews only; competing external rows are unknown.

    As for other curated records, write via the validated API, not raw SQL.
    """
    grouped = {}
    for row in view.observations:
        if row.metric == "narrative.event_context" and row.schema_version == "event-context-v1":
            grouped.setdefault(row.payload.get("evidence_id"), []).append(row)
    return {key: rows[0] for key, rows in grouped.items() if len(rows) == 1}


def context_conflicts(left, right):
    """Veto only comparable explicit conflicts. Agreement never promotes a link."""
    if left is None or right is None:
        return []
    a, b = left.payload, right.payload
    conflicts = [
        key
        for key in ("episode_key", "location_key")
        if a.get(key) and b.get(key) and a[key] != b[key]
    ]
    if all(p.get(k) for p in (a, b) for k in ("occurrence_start", "occurrence_end")) and (
        datetime.fromisoformat(a["occurrence_end"]) < datetime.fromisoformat(b["occurrence_start"])
        or datetime.fromisoformat(b["occurrence_end"])
        < datetime.fromisoformat(a["occurrence_start"])
    ):
        conflicts.append("occurrence_window")
    return conflicts
