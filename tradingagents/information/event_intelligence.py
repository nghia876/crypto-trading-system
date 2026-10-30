"""Curated incident identity and bounded evidence-gap research in the canonical store.

Headline equality is a review candidate only. Membership never establishes truth,
independence, occurrence time, or a causal market relationship.
"""

from __future__ import annotations

import hashlib
import json
import re

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.claim_lifecycle import claim_lifecycle
from tradingagents.information.observations import Observation
from tradingagents.information.sources import SPECIALIST_WORLD_CONFIG


def _history(view):
    return {
        r.observation_id: r
        for r in (*view.evidence_history, *view.observations)
        if r.is_available_at(view.decision_time)
    }


def record_incident_membership(
    store, *, incident_id, evidence_ids, recorded_at, rationale, retract_ids=()
):
    """Append reviewed membership or retract named memberships without rewriting history.

    Stable incident IDs must distinguish location/episode, supplied by a reviewer.
    Corrections to membership retire explicit earlier memberships, not articles.
    """
    if (
        not isinstance(incident_id, str)
        or not incident_id.strip()
        or len(incident_id) > 160
        or not isinstance(rationale, str)
        or not rationale.strip()
        or len(rationale) > 1000
        or not 1 <= len(evidence_ids) <= 32
        or len(retract_ids) > 32
    ):
        raise ValueError("bounded identity, rationale and evidence required")
    history = _history(store.view_at(recorded_at))
    if any(e not in history or history[e].metric != "narrative.event" for e in evidence_ids):
        raise ValueError("membership requires available narrative evidence")
    if any(
        t not in history
        or history[t].metric != "narrative.incident_membership"
        or history[t].payload.get("incident_id") != incident_id
        for t in retract_ids
    ):
        raise ValueError("retractions require earlier memberships of this incident")
    payload = {
        "incident_id": incident_id,
        "evidence_ids": sorted(set(evidence_ids)),
        "retract_ids": sorted(set(retract_ids)),
        "rationale": rationale,
        "authority": "caller_curated_incident_membership",
    }
    digest = hashlib.sha256(
        (json.dumps(payload, sort_keys=True) + recorded_at.isoformat()).encode()
    ).hexdigest()
    row = Observation(
        observation_id="incident:" + digest,
        source_id="derived.event_intelligence",
        subject="incident:" + digest,
        metric="narrative.incident_membership",
        payload=payload,
        event_time=recorded_at,
        first_seen_time=recorded_at,
        retrieved_at=recorded_at,
        schema_version="incident-membership-v1",
        unit="membership",
    )
    store.append(MarketDataBatch((row,), (), recorded_at))
    return row


def incident_state(view, incident_id):
    """Replay reviewed incident identity, competing claims and their correction lineage."""
    history = _history(view)
    links = sorted(
        (
            r
            for r in history.values()
            if r.metric == "narrative.incident_membership"
            and r.payload.get("incident_id") == incident_id
            and all(e in history for e in r.payload["evidence_ids"])
            and all(t in history for t in r.payload["retract_ids"])
        ),
        key=lambda r: (r.available_at, r.observation_id),
    )
    retired = {t for r in links for t in r.payload["retract_ids"]}
    evidence = sorted(
        {e for r in links if r.observation_id not in retired for e in r.payload["evidence_ids"]}
    )
    subjects = sorted({history[e].subject for e in evidence})
    claims = {s: claim_lifecycle(view, s) for s in subjects}
    versions = [history[e] for e in evidence]
    return {
        "incident_id": incident_id,
        "evidence_ids": evidence,
        "claims": claims,
        "first_known": min((r.first_seen_time for r in versions), default=None),
        "available_at": min((r.available_at for r in links), default=None),
        "membership_history": tuple(links),
        "retired": sorted(retired),
        "factual_truth": "unknown",
        "occurrence_time": None,
        "independence": "unknown; consult individual claim evidence, never count publishers",
    }


def incident_prompt(view, row):
    """Compact annotation within each existing whole-record narrative reservation."""
    history = _history(view)
    ids = sorted(
        {
            r.payload["incident_id"]
            for r in history.values()
            if r.metric == "narrative.incident_membership"
            and row.observation_id in r.payload["evidence_ids"]
        }
    )
    result = []
    for key in ids:
        state = incident_state(view, key)
        if row.observation_id in state["evidence_ids"]:
            result.append(
                {
                    "id": key,
                    "first_known": state["first_known"].isoformat(),
                    "membership_available": state["available_at"].isoformat(),
                    "reports": len(state["claims"]),
                    "truth": "unknown",
                    "contested": any(c["opposing"] for c in state["claims"].values()),
                }
            )
    return result[:4]


def research_plan(view, incident_id, *, max_sources=2):
    """Select existing rights-reviewed original feeds for missing/counterevidence.

    This polls whole eligible feeds, not arbitrary URLs or article bodies. No new
    rights clearance is inferred for BBC/GDELT. Unsupported domains stay missing.
    """
    if not 1 <= max_sources <= 4:
        raise ValueError("research source budget must be 1..4")
    state = incident_state(view, incident_id)
    history = _history(view)
    domains = {history[e].payload.get("domain") for e in state["evidence_ids"]}
    configs = [c for c in SPECIALIST_WORLD_CONFIG if c.domain in domains]
    return {
        "incident_id": incident_id,
        "cutoff": view.decision_time.isoformat(),
        "evidence_ids": state["evidence_ids"],
        "reason": "Seek missing independent evidence, competing claims and corrections; absence proves nothing",
        "source_ids": [c.source.source_id for c in configs[:max_sources]],
        "missing_domains": sorted(
            d for d in domains if d and not any(c.domain == d for c in configs)
        ),
        "contradiction_search": "not_performed",
        "truth": "unknown",
        "evidence_gaps": [
            "event_occurrence_time_unknown",
            "semantic_disconfirmation_review_missing",
        ]
        + (
            ["independent_origin_evidence_missing"]
            if any(c["independence"] == "unknown" for c in state["claims"].values())
            else []
        )
        + (["incident_membership_missing"] if not state["evidence_ids"] else []),
        "questions": (
            ["Resolve competing reported claims using original corrections; preserve both accounts"]
            if any(c["opposing"] for c in state["claims"].values())
            else ["Find disconfirming reports; missing opposition is not confirmation"]
        )
        + ["Find evidenced origin/independence; publisher count is not a vote"],
    }


def research_once(store, incident_id, *, now, max_sources=2, session=None, clock=None):
    """Execute a fresh bounded plan under the existing lock, quotas and failure journal."""
    from tradingagents.information.polling import coordinate, job_lock

    with job_lock(store):
        plan = research_plan(store.view_at(now), incident_id, max_sources=max_sources)
        if not plan["source_ids"]:
            return plan, ()
        outcomes, health = coordinate(
            store,
            now=now,
            max_sources=max(2, max_sources),
            source_ids=frozenset(plan["source_ids"]),
            session=session,
            clock=clock,
        )
        completed = max([now] + [r.observed_at for r in outcomes])
        history = _history(store.view_at(completed))
        seeds = [history[e] for e in plan["evidence_ids"]]

        def terms(row):
            return set(re.findall(r"[\w-]{4,}", str(row.payload.get("claim", "")).casefold()))

        seed_terms = set().union(*(terms(r) for r in seeds))
        acquired = sorted({e for r in outcomes for e in r.evidence_ids})
        candidates = [
            e
            for e in acquired
            if e in history
            and e not in plan["evidence_ids"]
            and len(terms(history[e]) & seed_terms) >= 2
        ][:16]
        payload = plan | {
            "candidate_evidence_ids": candidates,
            "candidate_status": "lexical review candidates only; no automatic incident merge or contradiction judgment",
            "poll_ids": [r.coverage_id for r in outcomes],
            "execution": "attempted" if outcomes else "deferred_by_existing_poll_controls",
            "contradiction_search": (
                "bounded_feed_candidate_scan; semantic review not performed"
                if acquired
                else "no_eligible_acquired_evidence; semantic review not performed"
            ),
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        audit = Observation(
            observation_id="research:" + digest,
            source_id="derived.event_intelligence",
            subject="research:" + digest,
            metric="narrative.research_attempt",
            payload=payload,
            event_time=completed,
            first_seen_time=completed,
            retrieved_at=completed,
            schema_version="event-research-v1",
            unit="research_attempt",
        )
        store.append(MarketDataBatch((audit,), (), completed))
        return payload, (outcomes, health)


def main(argv=None):
    """Operate on an existing canonical database; never create a second live store."""
    import argparse
    from datetime import UTC, datetime
    from pathlib import Path

    from tradingagents.information.store import SQLiteInformationStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("link", "plan", "research", "show"))
    parser.add_argument("--store", required=True)
    parser.add_argument("--incident", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--retract", action="append", default=[])
    parser.add_argument("--rationale", default="")
    parser.add_argument("--cutoff")
    args = parser.parse_args(argv)
    if not Path(args.store).is_file():
        parser.error("existing canonical store required")
    now = datetime.now(UTC)
    cutoff = datetime.fromisoformat(args.cutoff) if args.cutoff else now
    if args.command in {"link", "research"} and args.cutoff:
        parser.error("writes use current local acquisition time; cutoff is read-only")
    store = SQLiteInformationStore(args.store)
    if args.command == "link":
        row = record_incident_membership(
            store,
            incident_id=args.incident,
            evidence_ids=tuple(args.evidence),
            recorded_at=now,
            rationale=args.rationale,
            retract_ids=tuple(args.retract),
        )
        result = {"membership_id": row.observation_id}
    elif args.command == "research":
        result, _ = research_once(store, args.incident, now=now)
    elif args.command == "plan":
        result = research_plan(store.view_at(cutoff), args.incident)
    else:
        state = incident_state(store.view_at(cutoff), args.incident)
        result = {
            k: state[k]
            for k in (
                "incident_id",
                "evidence_ids",
                "first_known",
                "available_at",
                "retired",
                "factual_truth",
                "occurrence_time",
                "independence",
            )
        } | {
            "claims": {
                k: {
                    field: c[field]
                    for field in (
                        "status",
                        "supporting",
                        "opposing",
                        "independence",
                        "retired",
                    )
                }
                for k, c in state["claims"].items()
            }
        }
    print(json.dumps(result, default=str, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
