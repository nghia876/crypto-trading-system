"""Single-view consumer seam for one replayable BTC market analysis input."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tradingagents.information.market_state import BTCMarketState, build_btc_market_state
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
    """Render deterministic state with its cutoff and evidence IDs for an analyst."""
    state = result.market_state
    spot = state.spot
    lines = [
        "Replayable point-in-time market context (use as structured evidence):",
        f"Decision cutoff: {result.view.decision_time.isoformat()}",
        f"BTC spot close: {spot.latest_close if spot.latest_close is not None else 'unknown'} USDT/BTC",
        f"Spot freshness: {spot.freshness}; bars: {spot.candle_count}",
        f"Spot evidence IDs: {', '.join(spot.evidence_observation_ids) or 'none'}",
        f"Funding rate: {state.funding.funding_rate if state.funding.funding_rate is not None else 'unknown'}; evidence: {state.funding.evidence_observation_id or 'none'}",
        f"Open interest: {state.open_interest.open_interest if state.open_interest.open_interest is not None else 'unknown'}; evidence: {state.open_interest.evidence_observation_id or 'none'}",
        f"Macro series: {len(state.macro.series)}; scheduled events: {len(state.upcoming_macro_events)}",
        "Missing sources or observations mean unknown; they are not negative evidence.",
    ]
    return "\n".join(lines)
