"""Bounded political acquisition labels, queries and attributed review context.

Labels suggest searches only: never establish an election, winner, truth, event
identity or BTC transmission. Structured context is supplied by a reviewer, not
guessed from headlines. Existing article and publisher/copy identities survive.
"""

import hashlib
import json
import re

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.observations import Observation, _require_aware

POLITICAL_TOPICS = {
    "ELECTION_CALENDAR": r"election|electoral|midterm|referendum|ballot|élection|eleiç|bầu cử",
    "VOTE_COUNT_REPORTING": r"vote count|counting|recount|exit poll|kiểm phiếu",
    "REPORTED_ELECTION_RESULTS": r"election result|certif|official result|kết quả bầu cử",
    "REPORTED_POLLING": r"opinion poll|polling|survey|sondage|thăm dò",
    "GOVERNMENT_CONTROL": r"parliament|congress|senate|coalition|cabinet|executive|legislature",
    "FISCAL_TAX_CRYPTO_POLICY": r"fiscal|tax|budget|crypto.{0,30}regulat|legislat",
    "INTERNATIONAL_RELATIONS": r"diploma|sanction|tariff|trade|treaty",
    "POLITICAL_PUBLIC_CLAIMS": r"politic|election|rumou?r|denial|denies|correction|false claim",
}

# No live search is implied. These rotate within a separate two-query ceiling,
# retaining all existing headline-expansion slots and feed/host request limits.
POLITICAL_QUERY_SEEDS = (
    "global election calendar electoral commission voting dates",
    "election vote counting recount developing reported official results",
    "opinion polling reported measurement population fieldwork date methodology",
    "legislative executive control parliament coalition government formation",
    "fiscal tax budget crypto regulation legislative instrument jurisdiction",
    "international relations sanctions trade tariffs policy institution country",
    "political public claims rumors denials corrections election reporting",
    "eleições resultados apuração sondagens país data instituição",
    "élections dépouillement résultats sondages pays date institution",
    "bầu cử kiểm phiếu kết quả thăm dò quốc gia ngày cơ quan",
)


def political_topics(text):
    return [name for name, pattern in POLITICAL_TOPICS.items() if re.search(pattern, text, re.I)]


def political_queries(rows, *, previous=(), budget=2):
    """Pending manual seeds and one grounded expansion; no external execution.

    Token overlap is not incident matching. Keep the complete bounded headline
    (including years/race/location when supplied), never normalize races together.
    """
    if not 0 <= budget <= 2:
        raise ValueError("political query budget must be 0..2")
    candidates = []
    for row in rows:
        if political_topics(row.payload.get("claim", "")):
            candidates.append((row.payload["claim"][:210] + " election policy jurisdiction date",
                               [row.observation_id], "retrieved_political_headline"))
            break
    candidates.extend((q, [], "political_coverage_seed") for q in POLITICAL_QUERY_SEEDS)
    queries = []
    for query, evidence, origin in candidates:
        key = hashlib.sha256(("political:" + query).encode()).hexdigest()
        if key in previous or len(queries) >= budget:
            continue
        queries.append({"query": query, "query_id": key, "origin": origin,
                        "input_evidence_ids": evidence, "executor": "manual_external_search",
                        "status": "pending", "fanout": 0, "channels_covered": [],
                        "channels_missed": ["external search not yet performed"],
                        "relation_status": "No event identity or corroboration inferred"})
    return queries


def record_political_context(store, *, evidence_id, recorded_at, reviewer, provenance,
                             statement_kind="unknown", result_status="unknown",
                             jurisdiction=None, institution=None, race=None, election_date=None,
                             instrument=None, entities=(), location=None, poll_population=None,
                             poll_fieldwork_date=None, supersedes=None):
    """Immutable attributed review on exact evidence; unknowns remain unknown.

    Dates are source-reported strings, not publication-derived occurrence times.
    Polls without population/date remain incomplete measurements, never forecasts.
    These fields cannot authorize grouping or override original-source evidence.
    """
    _require_aware("recorded_at", recorded_at)
    if statement_kind not in {"unknown", "factual_claim", "opinion", "speculation", "rumor",
                              "denial", "correction", "reported_poll_measurement"}:
        raise ValueError("unsupported statement kind")
    if result_status not in {"unknown", "not_applicable", "developing_unverified_count",
                             "publisher_reported_result", "documented_official_result"}:
        raise ValueError("unsupported reported result status")
    fields = {"jurisdiction": jurisdiction, "institution": institution, "race": race,
              "election_date": election_date, "instrument": instrument, "location": location,
              "poll_population": poll_population, "poll_fieldwork_date": poll_fieldwork_date}
    for value in (reviewer, provenance):
        if not isinstance(value, str) or not value.strip() or len(value) > 1000:
            raise ValueError("bounded reviewer and source provenance required")
    if not isinstance(entities, (list, tuple)) or len(entities) > 8:
        raise ValueError("bounded entities required")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 160
           for v in (*entities, *(v for v in fields.values() if v is not None))):
        raise ValueError("bounded source-reported context required")
    view = store.view_at(recorded_at)
    history = {r.observation_id: r for r in (*view.evidence_history, *view.observations)}
    evidence = history.get(evidence_id)
    if evidence is None or evidence.metric != "narrative.event":
        raise ValueError("available narrative evidence required")
    active = [r for r in view.observations if r.metric == "narrative.political_context"
              and r.payload.get("evidence_id") == evidence_id]
    if ((active and (len(active) != 1 or supersedes != active[0].observation_id))
            or (not active and supersedes is not None)):
        raise ValueError("explicit active review supersession required")
    payload = dict(fields, evidence_id=evidence_id, reviewer=reviewer, provenance=provenance,
                   statement_kind=statement_kind, result_status=result_status,
                   entities=list(entities), authority="attributed_reviewer_not_verified_truth",
                   polling_completeness="supplied" if poll_population and poll_fieldwork_date
                   else "population/date incomplete or not applicable")
    digest = hashlib.sha256((json.dumps(payload, sort_keys=True)
                             + recorded_at.isoformat()).encode()).hexdigest()
    row = Observation("political:" + digest, "derived.political_context", "political:" + evidence_id,
                      "narrative.political_context", payload, evidence.event_time,
                      recorded_at, recorded_at, supersedes_observation_id=supersedes,
                      schema_version="political-context-v1")
    store.append(MarketDataBatch((row,), (), recorded_at))
    return row


def political_prompt(view, evidence):
    rows = [r for r in view.observations if r.metric == "narrative.political_context"
            and r.schema_version == "political-context-v1"
            and r.payload.get("evidence_id") == evidence.observation_id]
    if len(rows) != 1:
        return None
    row = rows[0]
    return {"review_id": row.observation_id, "available_at": row.available_at.isoformat(),
            **{k: v for k, v in row.payload.items() if v is not None and k != "evidence_id"}}


def political_identity_conflicts(left, right):
    """Only comparable explicit conflicts; agreement never establishes identity."""
    if left is None or right is None:
        return []
    return ["political_" + key for key in
            ("jurisdiction", "institution", "race", "election_date", "instrument")
            if left.get(key) and right.get(key) and left[key] != right[key]]


def political_link_candidates(view):
    """Acquisition-only overlay; keep the frozen historical matcher unchanged.

    Existing matcher produces suggestions, never automatic merges. This bounded
    political search lane vetoes explicit conflicts and preserves unknowns.
    No labels, winner forecasts or positive grouping instructions enter matching.
    """
    from tradingagents.information.event_intelligence import suggest_event_links

    report = suggest_event_links(view)
    rows = {r.observation_id: r for r in view.observations if r.metric == "narrative.event"}
    kept, vetoes = [], []
    for candidate in report["candidates"]:
        left, right = (rows[key] for key in candidate["evidence_ids"])
        conflicts = political_identity_conflicts(political_prompt(view, left), political_prompt(view, right))
        if conflicts:
            vetoes.append({"evidence_ids": candidate["evidence_ids"], "conflicts": conflicts})
        else:
            kept.append(candidate)
    return {**report, "candidates": kept, "political_vetoes": vetoes,
            "political_policy": "attributed-identity-v1; no automatic merge"}
