"""Read-only C1 candidate identity and sampled propagation, policy c1-v1.

Article IDs are stable provisional roots, not assertions of real incidents.
Only explicit, cutoff-eligible reviewed memberships associate different URLs.
Lexical proposals never merge roots or supply independent confirmation.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import timedelta


def history(view):
    return tuple(
        sorted(
            {
                r.observation_id: r
                for r in (*view.evidence_history, *view.observations)
                if r.metric == "narrative.event" and r.is_available_at(view.decision_time)
            }.values(),
            key=lambda r: (r.available_at, r.observation_id),
        )
    )


def article_key(row):
    return row.payload.get("canonical_url") or row.subject


def _id(value):
    return "candidate:" + hashlib.sha256(value.encode()).hexdigest()[:24]


def identity_conflicts(view, left, right):
    """Comparable explicit fields veto links; missing fields never prove identity."""
    from tradingagents.information.event_context import context_conflicts, reviewed_context
    from tradingagents.information.political_intelligence import (
        political_identity_conflicts,
        political_prompt,
    )

    context = reviewed_context(view)
    conflicts = context_conflicts(
        context.get(left.observation_id), context.get(right.observation_id)
    )
    conflicts += political_identity_conflicts(
        political_prompt(view, left), political_prompt(view, right)
    )
    # Retain explicit headline years/dates as uncertainty constraints, never infer
    # an occurrence date from a publication or retrieval timestamp.
    for pattern, label in (
        (r"\b(?:19|20)\d{2}\b", "headline_year"),
        (r"\b\d{4}-\d{2}-\d{2}\b", "headline_date"),
    ):
        a, b = (set(re.findall(pattern, r.payload.get("claim", ""))) for r in (left, right))
        if a and b and a.isdisjoint(b):
            conflicts.append(label)
    return sorted(set(conflicts))


def candidate_relations(view):
    """Bounded review proposals only; frozen historical matcher stays unchanged."""
    from tradingagents.information.political_intelligence import political_link_candidates

    report = political_link_candidates(view)
    rows = {r.observation_id: r for r in history(view)}
    kept, vetoes = [], [*report['context_vetoes'], *report["political_vetoes"]]
    for proposal in report["candidates"]:
        left, right = (rows[i] for i in proposal["evidence_ids"])
        conflicts = identity_conflicts(view, left, right)
        if conflicts:
            vetoes.append({"evidence_ids": proposal["evidence_ids"], "conflicts": conflicts})
        else:
            kept.append(
                {
                    "evidence_ids": proposal["evidence_ids"],
                    "status": "PROPOSAL_REQUIRES_REVIEW",
                    "independence": "UNKNOWN",
                }
            )
    return {
        "policy": "c1-v1",
        "cutoff": view.decision_time.isoformat(),
        "proposals": kept,
        "vetoes": vetoes,
        "scanned": report["scanned_records"],
        "omitted_records": report["omitted_records"],
        "omitted_proposals": report["omitted_candidates"],
    }


def sampled_window(view, start, end, *, rows=None, source_ids=None):
    """Half-open (start,end] clock window; local novelty, never global activity.

    New URLs, changed content versions and unchanged acquisitions are disjoint.
    Source-URL first mentions measure channel breadth, never independence.
    """
    from tradingagents.information.observations import _require_aware

    _require_aware("start", start)
    _require_aware("end", end)
    if not start < end <= view.decision_time:
        raise ValueError("positive window ending no later than cutoff required")
    all_rows = history(view)
    rows = None if rows is None else tuple(rows)
    allowed = None if rows is None else {article_key(r) for r in rows}
    source_ids = None if source_ids is None else set(source_ids)
    first, versions, mentions = {}, {}, {}
    retrieved = new = revised = repeats = 0
    publishers, sources, urls = set(), set(), set()
    missing_version = 0
    for row in all_rows:
        key = article_key(row)
        version = row.payload.get("version_id") or row.payload.get("content_hash")
        inside = (
            start < row.available_at <= end
            and (allowed is None or key in allowed)
            and (source_ids is None or row.source_id in source_ids)
        )
        if row.available_at > end:
            continue
        if inside:
            retrieved += 1
            urls.add(key)
            sources.add(row.source_id)
            publisher = row.payload.get("publisher_group")
            if publisher and str(publisher).casefold() != "unknown":
                publishers.add(publisher)
            if key not in first:
                new += 1
            elif version is None:
                missing_version += 1
            elif (key, version) not in versions:
                revised += 1
            else:
                repeats += 1
        first.setdefault(key, row.available_at)
        if version is not None:
            versions.setdefault((key, version), row.available_at)
        mentions.setdefault((key, row.source_id), row.available_at)
    health = []
    for record in view.coverage:
        if record.metric == "narrative.collection_health" and start < record.observed_at <= end:
            detail = json.loads(record.detail)
            if (allowed is None or record.source_id in {r.source_id for r in rows}) and (
                source_ids is None or record.source_id in source_ids
            ):
                health.append(
                    {
                        "source": record.source_id,
                        "observed_at": record.observed_at.isoformat(),
                        "missed_interval_seconds": detail.get("missed_interval_seconds"),
                        "completeness": detail.get("completeness", "UNKNOWN"),
                    }
                )
    return {
        "start_exclusive": start.isoformat(),
        "end_inclusive": end.isoformat(),
        "retrievals": retrieved,
        "new_urls": new,
        "revisions": revised,
        "unchanged_retrievals": repeats,
        "unknown_version_retrievals": missing_version,
        "observed_urls": len(urls),
        "publisher_breadth": len(publishers),
        "source_breadth": len(sources),
        "sources": sorted(sources),
        "new_source_url_mentions": sum(
            start < at <= end
            and (allowed is None or key in allowed)
            and (source_ids is None or source in source_ids)
            for (key, source), at in mentions.items()
        ),
        "health": health,
        "recorded_gap_rows": sum(start < g.observed_at <= end for g in view.gaps),
        "coverage": "SAMPLED; unobserved/offline intervals UNKNOWN; zero gap rows do not prove uptime",
        "independence": "UNKNOWN; source breadth is not corroboration",
        "origin": "UNKNOWN unless separately evidenced",
        "syndication": "UNKNOWN unless separately evidenced",
        "reach": "UNKNOWN",
        "worldwide_virality": "NOT_MEASURED",
        "acceleration": "NOT_MEASURED",
    }


def collection_sessions(view):
    """Real recorded coordinator intervals, grouped by exact run timestamps.

    Coverage available only on completion; no invented polls in offline periods.
    Other unjournaled observations remain measurable through explicit clock windows.
    """
    groups = {}
    for record in view.coverage:
        if (
            record.metric != "narrative.collection_health"
            or record.observed_at > view.decision_time
        ):
            continue
        detail = json.loads(record.detail)
        start, end = detail.get("run_started_at"), detail.get("run_completed_at")
        if start and end:
            groups.setdefault((start, end), set()).add(record.source_id)
    from datetime import datetime

    result = []
    for (start, end), sources in sorted(groups.items()):
        a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
        if a < b <= view.decision_time:
            result.append(
                dict(
                    sampled_window(view, a, b, source_ids=sources), session_sources=sorted(sources)
                )
            )
    return result


def candidate_packet(view, row):
    """One compact provisional root, retaining exact evidence and reviewed links.

    Membership is evidence-version-specific; revisions retain article identity
    but cannot silently inherit a semantic review of changed content.
    """
    from tradingagents.information.claim_lifecycle import claim_lifecycle
    from tradingagents.information.event_intelligence import incident_prompt
    from tradingagents.information.political_intelligence import political_prompt

    eligible = {r.observation_id: r for r in history(view)}
    if eligible.get(row.observation_id) != row:
        raise ValueError("packet requires exact cutoff-eligible stored evidence")
    versions = [r for r in eligible.values() if article_key(r) == article_key(row)]
    first = min((r.available_at for r in versions), default=row.available_at)
    window = sampled_window(
        view, view.decision_time - timedelta(days=1), view.decision_time, rows=(row,)
    )
    lifecycle = claim_lifecycle(view, row.subject)
    political = political_prompt(view, row)
    return {
        "id": _id(article_key(row)),
        "status": "CANDIDATE_UNRESOLVED",
        "article_id": row.subject,
        "version_id": row.payload.get("version_id"),
        "evidence_id": row.observation_id,
        "source": row.source_id,
        "publisher": row.payload.get("publisher_group"),
        "url": row.payload.get("canonical_url") or row.raw_reference,
        "available_at": row.available_at.isoformat(),
        "first_known": first.isoformat(),
        "published_at": row.publication_time.isoformat() if row.publication_time else None,
        "attributed_claim": row.payload.get("claim"),
        "evidence_level": row.payload.get("evidence_level", "HEADLINE_METADATA_ONLY"),
        "topic_status": "TENTATIVE_HEADLINE_INFERENCE; underlying incident unverified",
        "statement_kind": political.get("statement_kind")
        if political
        else "UNVERIFIED_ATTRIBUTED_ASSERTION",
        "reviewed_incidents": incident_prompt(view, row),
        "lifecycle_status": lifecycle["status"],
        "origin": lifecycle.get("origin", "UNKNOWN"),
        "independence": lifecycle["independence"],
        "attention_24h": {k: window[k] for k in ("new_urls", "revisions", "unchanged_retrievals")},
        "rights": row.payload.get("licence_attribution")
        or row.payload.get("evidence_rights_reference")
        or "existing metadata scope; no body grant",
    }


def compact_annotation(view, row):
    """Small packet header; surrounding renderer retains claims/source/rights/links."""
    packet = candidate_packet(view, row)
    counts = packet["attention_24h"]
    result = {
        "id": packet["id"],
        "state": "CANDIDATE",
        "first_known": packet["first_known"],
        "observed_24h": [counts[k] for k in ("new_urls", "revisions", "unchanged_retrievals")],
    }
    if packet["reviewed_incidents"]:
        from tradingagents.information.event_intelligence import incident_state

        eligible = {r.observation_id: r for r in history(view)}
        associations = []
        for incident in packet["reviewed_incidents"]:
            state = incident_state(view, incident["id"])
            members = [eligible[e] for e in state["evidence_ids"] if e in eligible]
            conflicts = sorted(
                {
                    c
                    for i, a in enumerate(members)
                    for b in members[i + 1 :]
                    for c in identity_conflicts(view, a, b)
                }
            )
            associations.append(
                {
                    "id": incident["id"],
                    "state": "CONFLICT_REQUIRES_REVIEW"
                    if conflicts
                    else "REVIEWED_CANDIDATE_ASSOCIATION",
                    "conflicts": conflicts,
                    "articles": len({article_key(r) for r in members}),
                    "truth": "UNKNOWN",
                }
            )
        result["associations"] = associations
    return result


def incident_packets(view):
    """Reviewed associations retain separate article roots, claims and provenance.

    Explicit conflicting identities quarantine the association. The packet never
    turns reviewer membership or publisher counts into factual confirmation.
    No connected-component/transitive lexical clustering is performed.
    """
    from tradingagents.information.event_intelligence import incident_state

    rows = {r.observation_id: r for r in history(view)}
    ids = sorted(
        {
            r.payload["incident_id"]
            for r in (*view.observations, *view.evidence_history)
            if r.metric == "narrative.incident_membership" and r.is_available_at(view.decision_time)
        }
    )
    packets = []
    for key in ids:
        state = incident_state(view, key)
        members = [rows[e] for e in state["evidence_ids"] if e in rows]
        conflicts = sorted(
            {
                c
                for i, a in enumerate(members)
                for b in members[i + 1 :]
                for c in identity_conflicts(view, a, b)
            }
        )
        packets.append(
            {
                "incident_id": key,
                "status": "CONFLICT_REQUIRES_REVIEW"
                if conflicts
                else "REVIEWED_CANDIDATE_ASSOCIATION",
                "conflicts": conflicts,
                "article_roots": sorted({_id(article_key(r)) for r in members}),
                "claims": [candidate_packet(view, r) for r in members],
                "attention": sampled_window(
                    view, view.decision_time - timedelta(days=1), view.decision_time, rows=members
                ),
                "truth": "UNKNOWN; membership does not confirm competing claims",
                "independence": "consult evidenced claim assertions; never publisher count",
            }
        )
    return packets
