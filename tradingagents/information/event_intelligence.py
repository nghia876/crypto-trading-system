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
                    "open_gaps": evidence_gaps(view, state["evidence_ids"]),
                    "contested": any(c["opposing"] for c in state["claims"].values()),
                }
            )
    return result[:4]


# Versioned, intentionally conservative English headline heuristics. Discovery
# domains are query labels, so event type must also be present in source text.
_EVENT_WORDS = {
    "drought": "drought droughts water scarcity",
    "flood": "flood floods flooding",
    "wildfire": "wildfire wildfires blaze",
    "war": "war invasion ceasefire attack missile",
    "trade": "sanctions sanction tariff tariffs embargo trade",
    "agriculture": "harvest crop crops agriculture food famine",
    "energy": "energy electricity grid outage oil gas pipeline",
    "disaster": "earthquake tsunami hurricane cyclone disaster",
    "health": "outbreak pandemic epidemic virus vaccine health",
    "technology": "science ai chips semiconductor cyber ransomware breach",
    "regulation": "regulation regulator legislation ruling ban",
}
_GENERIC = {
    "the",
    "a",
    "an",
    "in",
    "on",
    "at",
    "of",
    "for",
    "and",
    "to",
    "from",
    "with",
    "by",
    "as",
    "is",
    "are",
    "has",
    "have",
    "after",
    "before",
    "new",
    "latest",
    "severe",
    "major",
    "reports",
    "report",
    "reported",
    "warning",
    "update",
    "correction",
    "corrected",
    "denied",
    "denies",
    "confirmed",
    "continues",
    "disrupts",
    "threatens",
    "hits",
    "country",
    "province",
    "region",
    "river",
    "basin",
    "emergency",
    "officials",
    "says",
    "say",
    "amid",
    "over",
    "under",
    "near",
    "across",
}
_GENERIC.update(
    [
        "china",
        "india",
        "pakistan",
        "usa",
        "us",
        "uk",
        "vietnam",
        "russia",
        "ukraine",
        "america",
        "europe",
        "africa",
        "asia",
        "brazil",
        "australia",
        "canada",
        "france",
        "germany",
        "italy",
        "spain",
        "japan",
        "indonesia",
        "thailand",
        "bangladesh",
    ]
)
_GENERIC.update(w for words in _EVENT_WORDS.values() for w in words.split())


def _features(row):
    text = str(row.payload.get("claim", ""))[:2000]
    words = set(re.findall(r"[^\W\d_]+", text.casefold()))
    distinctive = words - _GENERIC
    anchors = {w.casefold() for w in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)} & distinctive
    # Optional explicit metadata is evidence, never inferred geographic truth.
    locations = row.payload.get("locations", ())
    locations = (
        {x.strip().casefold() for x in locations[:16] if isinstance(x, str) and x.strip()}
        if isinstance(locations, (list, tuple))
        else set()
    )
    if not locations:
        # A conservative location proxy prevents country-level proximity merges.
        # Ambiguous/missing geography is not silently geocoded.
        locations = {
            " ".join(x.casefold().split())
            for x in re.findall(
                r"\b(?:[Ii]n|[Nn]ear|[Aa]t)\s+([A-Z][a-z]+(?:[ -][A-Z][a-z]+){0,2})", text
            )
        }
    entities = row.payload.get("entities", ())
    if isinstance(entities, (list, tuple)):
        anchors.update(
            x.strip().casefold() for x in entities[:16] if isinstance(x, str) and x.strip()
        )
    return {
        "types": {k for k, values in _EVENT_WORDS.items() if words & set(values.split())},
        "terms": distinctive,
        "anchors": anchors,
        "locations": locations,
        "review_cues": sorted(
            words & {"denied", "denies", "correction", "corrected", "retracted", "updated"}
        ),
    }


def suggest_event_links(view, *, max_records=128, max_candidates=32, use_reviewed_context=True):
    """Bounded deterministic suggestions; never membership, support or independence.

    Compare latest article versions only, within 72h publication/acquisition
    proxies. Require type, distinctive overlap, proper-name/entity anchor and
    similarity; explicitly disjoint locations veto a match. Unknown is skipped.
    """
    from tradingagents.information.event_context import context_conflicts, reviewed_context
    from tradingagents.information.narrative_events import narrative_events

    if not 2 <= max_records <= 128 or not 1 <= max_candidates <= 32:
        raise ValueError("candidate budgets: records 2..128, candidates 1..32")
    all_rows = narrative_events(view)
    rows = all_rows[:max_records]
    features = {r.observation_id: _features(r) for r in rows}
    contexts = reviewed_context(view) if use_reviewed_context else {}
    vetoes = []
    candidates = []
    for i, left in enumerate(rows):
        a = features[left.observation_id]
        for right in rows[i + 1 :]:
            b = features[right.observation_id]
            if left.subject == right.subject:
                continue
            delta = abs(
                (
                    (left.publication_time or left.available_at)
                    - (right.publication_time or right.available_at)
                ).total_seconds()
            )
            shared = a["terms"] & b["terms"]
            anchors = a["anchors"] & b["anchors"]
            types = a["types"] & b["types"]
            similarity = len(shared) / max(1, len(a["terms"] | b["terms"]))
            if (
                delta > 72 * 3600
                or not types
                or not anchors
                # Distinct named places/entities on both sides are ambiguous:
                # shared country or generic title-case words cannot override them.
                or (a["anchors"] - b["anchors"] and b["anchors"] - a["anchors"])
                or len(shared) < 2
                or similarity < 0.55
                or (a["locations"] and b["locations"] and not a["locations"] & b["locations"])
            ):
                continue
            conflict = context_conflicts(contexts.get(left.observation_id), contexts.get(right.observation_id))
            if conflict:
                vetoes.append({"evidence_ids": sorted((left.observation_id, right.observation_id)),
                               "conflicts": conflict})
                continue
            evidence = sorted((left, right), key=lambda r: r.observation_id)
            candidates.append(
                {
                    "evidence_ids": [r.observation_id for r in evidence],
                    "sources": [
                        {
                            "id": r.source_id,
                            "url": r.raw_reference,
                            "published_at": r.publication_time.isoformat()
                            if r.publication_time
                            else None,
                            "first_known": r.first_seen_time.isoformat(),
                            "retrieved_at": r.retrieved_at.isoformat(),
                            "available_at": r.available_at.isoformat(),
                        }
                        for r in evidence
                    ],
                    "status": "candidate_requires_review",
                    "independence": "unknown; repeated or syndicated reporting supplies no independent support",
                    "event_types": sorted(types),
                    "shared_anchors": sorted(anchors),
                    "shared_terms": sorted(shared),
                    "similarity": round(similarity, 4),
                    "time_proxy_delta_seconds": delta,
                    "review_cues": sorted(set(a["review_cues"] + b["review_cues"])),
                    "truth": "unknown",
                    "reviewed_context_ids": [contexts[r.observation_id].observation_id
                                             for r in evidence if r.observation_id in contexts],
                }
            )
    candidates.sort(key=lambda c: (-c["similarity"], c["evidence_ids"]))
    return {
        "policy": "event-link-reviewed-context-v2" if use_reviewed_context else "event-link-heuristic-v1",
        "context_veto_count": len(vetoes),
        "context_vetoes": sorted(vetoes, key=lambda c: c["evidence_ids"])[:max_candidates],
        "cutoff": view.decision_time.isoformat(),
        "scanned_records": len(rows),
        "omitted_records": max(0, len(all_rows) - len(rows)),
        "omitted_candidates": max(0, len(candidates) - max_candidates),
        "candidates": candidates[:max_candidates],
    }


def _append_audit(store, payload, now, kind):
    digest = hashlib.sha256(
        (json.dumps(payload, sort_keys=True) + now.isoformat()).encode()
    ).hexdigest()
    row = Observation(
        observation_id=kind + ":" + digest,
        source_id="derived.event_intelligence",
        subject=kind + ":" + digest,
        metric="narrative." + kind,
        payload=payload,
        event_time=now,
        first_seen_time=now,
        retrieved_at=now,
        schema_version=kind + "-v1",
        unit=kind,
    )
    store.append(MarketDataBatch((row,), (), now))
    return row


def record_event_candidates(store, *, now, max_records=128, max_candidates=32):
    """Append a suggestion snapshot; replay never recomputes prior suggestions."""
    return _append_audit(
        store,
        suggest_event_links(
            store.view_at(now), max_records=max_records, max_candidates=max_candidates
        ),
        now,
        "event_link_candidates",
    )


def candidate_history(view):
    history = _history(view)
    return tuple(
        sorted(
            (
                r
                for r in history.values()
                if r.metric == "narrative.event_link_candidates"
                and all(e in history for c in r.payload["candidates"] for e in c["evidence_ids"])
            ),
            key=lambda r: (r.available_at, r.observation_id),
        )
    )


def candidate_prompt(view, row):
    """Expose persisted suggestions separately from reviewed incident annotations."""
    snapshots = candidate_history(view)
    if not snapshots:
        return []
    return [
        {
            "evidence_ids": c["evidence_ids"],
            "status": c["status"],
            "available_at": snapshots[-1].available_at.isoformat(),
            "review_cues": c["review_cues"],
            "independence": "unknown",
        }
        for c in snapshots[-1].payload["candidates"]
        if row.observation_id in c["evidence_ids"]
    ][:2]


def _research_state(view, incident_id):
    state = incident_state(view, incident_id)
    seed = _history(view).get(incident_id)
    if not state["evidence_ids"] and seed is not None and seed.metric == "narrative.event":
        state["evidence_ids"] = [seed.observation_id]
        state["claims"] = {seed.subject: claim_lifecycle(view, seed.subject)}
    return state


def evidence_gaps(view, evidence_ids):
    """Open requirements, never findings inferred from publisher count or silence."""
    history = _history(view)
    rows = [history[e] for e in evidence_ids if e in history]
    claims = [claim_lifecycle(view, r.subject) for r in rows]
    gaps = [
        "event_occurrence_time_unknown",
        "disconfirmation_review_required",
        "updates_corrections_check_required",
    ]
    if not claims or not any(c["independence"] == "evidenced" for c in claims):
        gaps.append("independent_origin_evidence_missing")
    if not any(
        r.payload.get("source_type") == "original_specialist_news" or c["official_report"]
        for r, c in zip(rows, claims, strict=True)
    ):
        gaps.append("original_source_evidence_missing")
    if any(c["opposing"] for c in claims):
        gaps.append("contradictory_reports_unresolved")
    if not rows:
        gaps.append("incident_membership_missing")
    return gaps


def research_plan(view, incident_id, *, max_sources=2):
    """Select existing rights-reviewed original feeds for missing/counterevidence.

    This polls whole eligible feeds, not arbitrary URLs or article bodies. No new
    rights clearance is inferred for BBC/GDELT. Unsupported domains stay missing.
    """
    if not 1 <= max_sources <= 4:
        raise ValueError("research source budget must be 1..4")
    state = _research_state(view, incident_id)
    history = _history(view)
    domains = {history[e].payload.get("domain") for e in state["evidence_ids"]}
    configs = [c for c in SPECIALIST_WORLD_CONFIG if c.domain in domains]
    gaps = evidence_gaps(view, state["evidence_ids"])
    questions = {
        "independent_origin_evidence_missing": "Find independently evidenced origin, not syndicated copies",
        "original_source_evidence_missing": "Find an original agency report for the named episode/location",
        "disconfirmation_review_required": "Seek denial or contradictory accounts; preserve competing claims",
        "updates_corrections_check_required": "Check updates, corrections and retractions; absence proves nothing",
        "contradictory_reports_unresolved": "Resolve competing accounts with original evidence; retain unresolved contradictions",
    }
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
        "evidence_gaps": gaps,
        "questions": [
            {
                "gap": gap,
                "status": "open",
                "question": question
                + ": "
                + " | ".join(
                    str(history[e].payload.get("claim", ""))[:160]
                    for e in state["evidence_ids"][:2]
                ),
            }
            for gap, question in questions.items()
            if gap in gaps
        ],
        "research_mode": "bounded eligible whole-feed scan; questions are audit context, not arbitrary search queries",
    }


def research_once(store, incident_id, *, now, max_sources=2, session=None, clock=None):
    """Execute a fresh bounded plan under the existing lock, quotas and failure journal."""
    from tradingagents.information.polling import coordinate, job_lock

    with job_lock(store):
        plan = research_plan(store.view_at(now), incident_id, max_sources=max_sources)
        if not plan["source_ids"]:
            payload = plan | {
                "execution": "unsupported_no_eligible_source",
                "candidate_evidence_ids": [],
                "poll_ids": [],
            }
            _append_audit(store, payload, now, "research_attempt")
            return payload, ()
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
        suggestion = record_event_candidates(store, now=completed)
        payload = plan | {
            "candidate_snapshot_id": suggestion.observation_id,
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
        _append_audit(store, payload, completed, "research_attempt")
        return payload, (outcomes, health)


def main(argv=None):
    """Operate on an existing canonical database; never create a second live store."""
    import argparse
    from datetime import UTC, datetime
    from pathlib import Path

    from tradingagents.information.store import SQLiteInformationStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("link", "plan", "research", "show", "suggest"))
    parser.add_argument("--store", required=True)
    parser.add_argument("--incident")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--retract", action="append", default=[])
    parser.add_argument("--rationale", default="")
    parser.add_argument("--cutoff")
    args = parser.parse_args(argv)
    if not Path(args.store).is_file():
        parser.error("existing canonical store required")
    now = datetime.now(UTC)
    cutoff = datetime.fromisoformat(args.cutoff) if args.cutoff else now
    if args.command in {"link", "research", "suggest"} and args.cutoff:
        parser.error("writes use current local acquisition time; cutoff is read-only")
    if args.command != "suggest" and not args.incident:
        parser.error("incident key or seed evidence ID required")
    store = SQLiteInformationStore(args.store)
    if args.command == "suggest":
        result = dict(record_event_candidates(store, now=now).payload)
    elif args.command == "link":
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
    from collections.abc import Mapping

    print(
        json.dumps(
            result,
            default=lambda value: dict(value) if isinstance(value, Mapping) else str(value),
            sort_keys=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
