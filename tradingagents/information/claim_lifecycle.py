"""Evidence-backed claim assertions; reporting and corroboration never establish truth.

Callers curate semantic relationships. Headlines alone are only candidate matches.
All assertions are observations in the existing store, never mutable status rows.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.store import InformationView, SQLiteInformationStore

KINDS = frozenset(
    {
        "support",
        "confirmation",
        "opposition",
        "contradiction",
        "correction",
        "supersession",
        "resolution",
        "origin",
        "syndication",
        "independence",
        "official_report",
    }
)


def correlation_candidates(view: InformationView) -> tuple[tuple[str, ...], ...]:
    """Exact normalized claim matches are review candidates, never automatic merges."""
    groups = {}
    for row in view.observations:
        if row.metric == "narrative.event" and row.is_available_at(view.decision_time):
            text = " ".join(str(row.payload.get("claim", "")).casefold().split())
            if text:
                groups.setdefault(text, set()).add(row.subject)
    return tuple(sorted(tuple(sorted(ids)) for ids in groups.values() if len(ids) > 1))


def record_claim_assertion(
    store: SQLiteInformationStore,
    *,
    claim_id: str,
    kind: str,
    evidence_ids: tuple[str, ...],
    recorded_at: datetime,
    rationale: str,
    target_ids: tuple[str, ...] = (),
) -> Observation:
    """Append a curated relationship supported by locally eligible source evidence.

    target_ids identify earlier assertions being corrected/retracted/resolved, or
    the counterpart source observations for origin/syndication/independence.
    No source name, hostname or headline equality proves independence.
    """
    if kind not in KINDS or not rationale.strip() or len(rationale) > 2000:
        raise ValueError("known kind and bounded nonempty rationale required")
    view = store.view_at(recorded_at)
    history = {r.observation_id: r for r in view.evidence_history}
    roots = [r for r in history.values() if r.subject == claim_id and r.metric == "narrative.event"]
    if not roots or not evidence_ids or len(evidence_ids) > 32 or len(target_ids) > 32:
        raise ValueError("eligible claim and 1..32 source evidence records required")
    for evidence in evidence_ids:
        if evidence not in history or history[evidence].metric != "narrative.event":
            raise ValueError("source evidence must be eligible narrative observations")
    for target in target_ids:
        if target not in history:
            raise ValueError("target must be locally eligible")
        row = history[target]
        if row.metric == "narrative.claim_assertion" and row.payload.get("claim_id") != claim_id:
            raise ValueError("cannot retract another claim's assertion")
    if (
        kind
        in {"correction", "supersession", "resolution", "origin", "syndication", "independence"}
        and not target_ids
    ):
        raise ValueError("relationship requires explicit targets")
    if kind in {"origin", "syndication", "independence"}:
        if any(history[t].metric != "narrative.event" for t in target_ids):
            raise ValueError("provenance targets must be source observations")
        if set(evidence_ids) & set(target_ids):
            raise ValueError("provenance needs distinct source evidence")
    else:
        if any(history[t].metric != "narrative.claim_assertion" for t in target_ids):
            raise ValueError("lifecycle targets must be assertions")
    payload = {
        "claim_id": claim_id,
        "kind": kind,
        "evidence_ids": sorted(set(evidence_ids)),
        "target_ids": sorted(set(target_ids)),
        "rationale": rationale,
        "fact_status": "source_reported_claim",
        "authority": "caller_curated_evidence_assertion",
    }
    digest = hashlib.sha256(
        (json.dumps(payload, sort_keys=True) + recorded_at.isoformat()).encode()
    ).hexdigest()
    row = Observation(
        observation_id="claim:" + digest,
        source_id="derived.claim_lifecycle",
        subject="claim:" + digest,
        metric="narrative.claim_assertion",
        payload=payload,
        event_time=recorded_at,
        first_seen_time=recorded_at,
        retrieved_at=recorded_at,
        schema_version="narrative-claim-v1",
        unit="claim_assertion",
        transformations=(Transformation("curated_claim_relationship", "1"),),
    )
    store.append(MarketDataBatch((row,), (), recorded_at))
    return row


def claim_lifecycle(view: InformationView, claim_id: str) -> dict:
    """Replay only eligible assertions with resolvable eligible source evidence.

    Corrections retire named assertions, not entire claims. Resolution is reported
    as an evidenced assertion; later opposition reopens uncertainty. All history
    remains available, including retracted and simultaneous conflicting assertions.
    """
    history = {
        r.observation_id: r
        for r in (*view.evidence_history, *view.observations)
        if r.is_available_at(view.decision_time)
    }
    assertions = sorted(
        (
            r
            for r in history.values()
            if r.schema_version == "narrative-claim-v1"
            and r.payload.get("claim_id") == claim_id
            and all(e in history for e in r.payload["evidence_ids"])
            and all(t in history for t in r.payload["target_ids"])
        ),
        key=lambda r: (r.available_at, r.observation_id),
    )
    retired = {
        t
        for r in assertions
        if r.payload["kind"] in {"correction", "supersession", "resolution"}
        for t in r.payload["target_ids"]
    }
    active = [r for r in assertions if r.observation_id not in retired]
    support = [
        r for r in active if r.payload["kind"] in {"support", "confirmation", "official_report"}
    ]
    opposing = [r for r in active if r.payload["kind"] in {"opposition", "contradiction"}]
    # Dependency always defeats an independence assertion for the same pair.
    dependent = {
        frozenset((history[e].subject, history[t].subject))
        for r in active
        if r.payload["kind"] in {"origin", "syndication"}
        for e in r.payload["evidence_ids"]
        for t in r.payload["target_ids"]
    }
    # Close dependency chains across syndicated copies and repeat acquisitions.
    nodes = {e for pair in dependent for e in pair}
    components = {e: {e} for e in nodes}
    for pair in dependent:
        merged = set().union(*(components[e] for e in pair))
        for e in merged:
            components[e] = merged
    dependent = {frozenset((e, t)) for group in components.values() for e in group for t in group}
    supporting_ids = {e for r in support for e in r.payload["evidence_ids"]}
    independent = [
        r
        for r in active
        if r.payload["kind"] == "independence"
        and any(
            e in supporting_ids
            and t in supporting_ids
            and history[e].source_id != history[t].source_id
            and history[e].subject != history[t].subject
            and frozenset((history[e].subject, history[t].subject)) not in dependent
            for e in r.payload["evidence_ids"]
            for t in r.payload["target_ids"]
        )
    ]
    status = "contested" if opposing else "unconfirmed"
    if not opposing and independent:
        status = "independently_corroborated_reporting"
    if not opposing and active and active[-1].payload["kind"] == "resolution":
        status = "reported_resolved"

    def ids(rows):
        return sorted({e for r in rows for e in r.payload["evidence_ids"]})

    evidence_ids = {e for r in assertions for e in r.payload["evidence_ids"]}
    evidence_ids.update(
        t
        for r in assertions
        for t in r.payload["target_ids"]
        if history[t].metric == "narrative.event"
    )
    return {
        "claim_id": claim_id,
        "status": status,
        "factual_truth": "unknown",
        "supporting": ids(support),
        "opposing": ids(opposing),
        "independence": "evidenced" if independent else "unknown",
        "official_report": any(r.payload["kind"] == "official_report" for r in active)
        or any(
            r.subject == claim_id and r.payload.get("lifecycle") == "officially_reported"
            for r in history.values()
        ),
        "assertions": tuple(assertions),
        "retired": sorted(retired),
        "evidence": tuple(history[e] for e in sorted(evidence_ids)),
    }


def lifecycle_prompt(view: InformationView, claim_id: str) -> dict | None:
    state = claim_lifecycle(view, claim_id)
    if not state["assertions"]:
        return None
    return {
        k: state[k]
        for k in (
            "status",
            "factual_truth",
            "supporting",
            "opposing",
            "independence",
            "official_report",
        )
    } | {
        "history": [
            {
                "id": r.observation_id,
                "kind": r.payload["kind"],
                "targets": list(r.payload["target_ids"]),
                "evidence_ids": list(r.payload["evidence_ids"]),
                "rationale": r.payload["rationale"],
                "available": r.available_at.isoformat(),
            }
            for r in state["assertions"]
        ],
        "evidence": [
            {
                "id": r.observation_id,
                "source": r.source_id,
                "claim": r.payload.get("claim"),
                "url": r.raw_reference,
                "published": r.publication_time.isoformat() if r.publication_time else None,
                "first_seen": r.first_seen_time.isoformat(),
                "retrieved": r.retrieved_at.isoformat(),
                "available": r.available_at.isoformat(),
            }
            for r in state["evidence"]
        ],
        "uncertainty": "Curated reporting relationships; truth and complete contradiction search UNKNOWN",
    }
