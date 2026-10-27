"""Single-view consumer seam for one replayable BTC market analysis input."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from tradingagents.information.market_state import BTCMarketState, build_btc_market_state
from tradingagents.information.narrative_events import (
    render_narrative_events,
    selected_narrative_events,
)
from tradingagents.information.store import InformationView, SQLiteInformationStore


@dataclass(frozen=True, slots=True)
class AnalysisInformationInput:
    """One immutable view and all derived state for a single decision cutoff."""

    view: InformationView
    market_state: BTCMarketState

    def __post_init__(self) -> None:
        if self.market_state.decision_time != self.view.decision_time:
            raise ValueError("derived market state must use the view decision_time")


def build_analysis_information(
    store: SQLiteInformationStore, decision_time: datetime
) -> AnalysisInformationInput:
    """Read one replay view and derive market plus macro state from that same view."""
    view = store.view_at(decision_time)
    return AnalysisInformationInput(view=view, market_state=build_btc_market_state(view))


def render_analysis_information(result: AnalysisInformationInput) -> str:
    """Render cutoff, signal freshness, recorded coverage, and source lineage."""
    state = result.market_state
    spot = state.spot
    spot_evidence = spot.evidence_observation_ids[-21:]
    spot_evidence_label = (
        f"latest {len(spot_evidence)} of {len(spot.evidence_observation_ids)}"
        if len(spot.evidence_observation_ids) > len(spot_evidence)
        else str(len(spot_evidence))
    )
    lines = [
        "Replayable point-in-time market context (use as structured evidence):",
        f"Decision cutoff: {result.view.decision_time.isoformat()}",
        "Signals:",
        f"- BTC spot close: {_value(spot.latest_close)} USDT/BTC; freshness: {spot.freshness}; "
        f"bars: {spot.candle_count}; unresolved gaps: {spot.unresolved_gap_count}; "
        f"evidence IDs ({spot_evidence_label}): {_ids(spot_evidence)}",
        f"- Funding rate: {_value(state.funding.funding_rate)}; freshness: {state.funding.freshness}; "
        f"event time: {_time(state.funding.event_time)}; "
        f"evidence IDs: {_ids((state.funding.evidence_observation_id,))}",
        f"- Open interest: {_value(state.open_interest.open_interest)}; "
        f"freshness: {state.open_interest.freshness}; "
        f"event time: {_time(state.open_interest.event_time)}; "
        f"evidence IDs: {_ids((state.open_interest.evidence_observation_id,))}",
        f"- Perpetual mark/index: {_value(state.perpetual.mark_price)}/"
        f"{_value(state.perpetual.index_price)}; basis: {_value(state.perpetual.basis_pct)}%; "
        f"freshness: {state.perpetual.mark_freshness}; "
        f"evidence IDs: {_ids((state.perpetual.mark_evidence_observation_id,))}",
        f"- Contract status: {state.perpetual.contract_status or 'unknown'}; "
        f"freshness: {state.perpetual.status_freshness}; "
        f"evidence IDs: {_ids((state.perpetual.status_evidence_observation_id,))}",
        f"- Liquidation snapshots in prior 24 hours: {state.liquidation_snapshot_count_24h}; "
        f"latest event time: {_time(state.latest_liquidation_snapshot_event_time)}; "
        f"evidence IDs: {_ids((state.latest_liquidation_snapshot_evidence_observation_id,))}",
        f"- Treasury 10-year yield: {_value(state.treasury_yield.yield_pct)}%; "
        f"freshness: {state.treasury_yield.freshness}; "
        f"evidence IDs: {_ids((state.treasury_yield.evidence_observation_id,))}",
        "Macro series:",
    ]
    for item in sorted(state.macro.series, key=lambda item: (item.series_id, item.metric)):
        lines.append(
            f"- {item.series_id} ({item.metric}): {_value(item.value)}; "
            f"freshness: {item.freshness}; proxy for: {item.proxy_for or 'none'}; "
            f"evidence IDs: {_ids((item.evidence_observation_id,))}"
        )
    ordered_events = sorted(
        state.upcoming_macro_events,
        key=lambda item: (str(item.payload.get("scheduled_at", "")), item.observation_id),
    )
    lines.append("Upcoming scheduled macro events:")
    if state.upcoming_macro_events:
        for event in ordered_events:
            payload = event.payload
            lines.append(
                f"- {payload.get('title', 'untitled')} at {payload.get('scheduled_at', 'unknown')}; "
                f"status: {payload.get('status', 'unknown')}; source: {event.source_id}; "
                f"evidence IDs: {event.observation_id}"
            )
    else:
        lines.append("- unknown; no eligible scheduled-event observations")
    lines.append("Narrative events:")
    lines.extend(render_narrative_events(result.view))
    selected_ids = {item.observation_id for item in selected_narrative_events(result.view)}
    core_ids = {
        *(item.observation_id for item in selected_narrative_events(result.view)),
        *spot_evidence,
        state.funding.evidence_observation_id,
        state.open_interest.evidence_observation_id,
        state.perpetual.mark_evidence_observation_id,
        state.perpetual.status_evidence_observation_id,
        state.treasury_yield.evidence_observation_id,
        state.latest_liquidation_snapshot_evidence_observation_id,
        *(item.evidence_observation_id for item in state.macro.series),
        *(item.observation_id for item in ordered_events[:5]),
    } - {None}
    priority_ids = core_ids | {item.observation_id for item in ordered_events}
    priority_sources = {
        item.source_id for item in result.view.observations if item.observation_id in priority_ids
    }
    lines.append("Recorded coverage:")
    if result.view.coverage:
        for record in sorted(
            result.view.coverage,
            key=lambda item: (
                item.source_id not in priority_sources,
                item.status.value in {"present", "complete"},
                -item.observed_at.timestamp(),
                item.source_id,
                item.subject,
                item.metric,
                item.coverage_id,
            ),
        ):
            lines.append(
                f"- {record.source_id} / {record.subject} / {record.metric}: "
                f"{record.status.value}; observed at {record.observed_at.isoformat()}; "
                f"{record.detail or 'no detail'}; evidence IDs: {_ids(record.evidence_ids)}"
            )
    else:
        lines.append("- unknown; no coverage records available by the decision cutoff")
    lines.append("Point-in-time source definitions:")
    if result.view.source_definitions:
        for source, observed_at in sorted(
            result.view.source_definitions,
            key=lambda item: (
                item[0].source_id not in priority_sources,
                item[0].status.value == "available",
                -item[1].timestamp(),
                item[0].source_id,
                item[0].version,
            ),
        ):
            limitations = "; ".join(source.limitations) or "none recorded"
            lines.append(
                f"- {source.source_id} v{source.version} ({source.provider}, {source.status.value}); "
                f"known at {observed_at.isoformat()}; limitations: {limitations}"
            )
    else:
        lines.append("- unknown; no source definitions available by the decision cutoff")
    lines.append("Evidence metadata (schema and unit):")
    evidence_observations = sorted(
        (item for item in result.view.observations if item.observation_id in priority_ids),
        key=lambda item: (
            item.observation_id not in selected_ids,
            item.observation_id not in core_ids,
            item.source_id,
            item.metric,
            item.event_time,
            item.observation_id,
        ),
    )
    if evidence_observations:
        for item in evidence_observations:
            lines.append(
                f"- {item.observation_id}: {item.source_id} / {item.metric}; "
                f"schema: {item.schema_version}; unit: {item.unit}; "
                f"available at: {item.available_at.isoformat()}"
            )
    else:
        lines.append("- none; no eligible observations provide evidence")
    lines.append(
        "Missing sources or observations mean unknown, not negative evidence. "
        "Treat stale values as stale and use only the evidence IDs shown. "
        "Legacy news/social tool outputs are outside this store's point-in-time guarantees."
    )
    return _bounded_context(lines, result)


def _value(value: object) -> str:
    return "unknown" if value is None else str(value)


def _time(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "unknown"


def _ids(values) -> str:
    return ", ".join(value for value in values if value) or "none"


# Character budget (not model-specific tokens). Each section reserves its own
# capacity, so a long history cannot crowd out signals or macro/event lineage.
MAX_ANALYSIS_INFORMATION_CHARS = 28000
_SECTION_BUDGETS = {
    "Signals:": 6000,
    "Macro series:": 3500,
    "Upcoming scheduled macro events:": 3500,
    "Narrative events:": 4000,
    "Recorded coverage:": 3000,
    "Point-in-time source definitions:": 2500,
    "Evidence metadata (schema and unit):": 4000,
}


def _bounded_context(lines: list[str], result: AnalysisInformationInput) -> str:
    """Keep whole records/IDs; disclose every omitted row, including oversized rows."""
    sections: dict[str, list[str]] = {name: [] for name in _SECTION_BUDGETS}
    section = None
    for line in lines[2:-1]:
        if line in sections:
            section = line
        elif section is not None:
            sections[section].append(line)
    output = lines[:2] + [
        lines[-1],
        "Bounded context: omitted records are unknown here; omission does not establish absence, "
        "freshness, complete coverage, or source availability. Full lineage remains in the store.",
    ]
    # All statuses are summarized before capping detail; repeated historical
    # records are counts, not a claim about the latest state of each metric.
    for label, counts in (
        ("Coverage history conditions", Counter(r.status.value for r in result.view.coverage)),
        (
            "Source history conditions",
            Counter(s.status.value for s, _ in result.view.source_definitions),
        ),
    ):
        output.append(
            label
            + ": "
            + (", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "unknown (no records)")
        )
    state = result.market_state
    output.append(
        "Core freshness (independent of omitted detail): "
        f"spot={state.spot.freshness}; funding={state.funding.freshness}; "
        f"open_interest={state.open_interest.freshness}; mark={state.perpetual.mark_freshness}; "
        f"contract={state.perpetual.status_freshness}; treasury={state.treasury_yield.freshness}; "
        f"spot unresolved gaps={state.spot.unresolved_gap_count}"
    )
    for name, budget in _SECTION_BUDGETS.items():
        kept = []
        used = 0
        for row in sections[name]:
            # Reserve room for section heading and omission disclosure.
            if used + len(row) + 1 <= budget - 180:
                kept.append(row)
                used += len(row) + 1
        output.append(name)
        output.extend(kept)
        omitted = len(sections[name]) - len(kept)
        if omitted:
            output.append(
                f"- OMITTED {omitted} of {len(sections[name])} records due to section size budget; conditions/evidence may be missing."
            )
    rendered = "\n".join(output)
    assert len(rendered) <= MAX_ANALYSIS_INFORMATION_CHARS
    return rendered
