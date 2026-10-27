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
