"""The whole graph, end to end, with scripted models and no network.

Every tool-using analyst calls each of its tools once through the vendor router,
the debates and managers run, and the decision is parsed and logged. This pins
the wiring: a restructure that drops a node, a tool or an edge fails here.
"""

from __future__ import annotations

import copy
import time
from datetime import UTC, datetime, timedelta, timezone

import pandas as pd
import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda
from pydantic import Field

from tradingagents.agents import context, schemas
from tradingagents.agents.analysts import sentiment_analyst
from tradingagents.dataflows import router
from tradingagents.dataflows.vendors.yahoo import market as yahoo_market, snapshot
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.graph.trading_graph import _information_decision_time
from tradingagents.information import (
    BLS_RELEASE_CALENDAR_SOURCE,
    FRED_SERIES,
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    Observation,
    ScheduledMacroEvent,
    Source,
    SourceStatus,
    SQLiteInformationStore,
    parse_fred_graph_csv,
)

TRADE_DATE = "2026-01-09"

# Enough for every free-text reader: the PM's labelled rating and the trader's
# closing proposal line.
TEXT = "Report.\n\n**Rating**: Overweight\n\nFINAL TRANSACTION PROPOSAL: **BUY**"

STRUCTURED = {
    schemas.ResearchPlan: schemas.ResearchPlan(
        recommendation=schemas.PortfolioRating.OVERWEIGHT, rationale="r", strategic_actions="a"),
    schemas.TraderProposal: schemas.TraderProposal(action=schemas.TraderAction.BUY, reasoning="r"),
    # The thesis quotes another party's rating; the decision is still the PM's own.
    schemas.PortfolioDecision: schemas.PortfolioDecision(
        rating=schemas.PortfolioRating.OVERWEIGHT, executive_summary="s",
        investment_thesis="Street consensus rating: Buy (28 of 35 analysts)."),
    schemas.SentimentReport: schemas.SentimentReport(
        overall_band=schemas.SentimentBand.NEUTRAL, overall_score=5.0, confidence="low", narrative="n"),
}

ARGS = {"symbol": "NVDA", "ticker": "NVDA", "curr_date": TRADE_DATE, "start_date": "2026-01-02",
        "end_date": TRADE_DATE, "indicator": "rsi", "topic": "Fed rate cut", "freq": "quarterly"}


class ScriptedModel(BaseChatModel):
    """Calls every bound tool once, then answers with TEXT."""

    structured: bool = False
    tools: tuple = ()
    calls: list = Field(default_factory=list)   # shared across bound copies
    threads: set = Field(default_factory=set)   # threads that served a tool-bound call
    fail_at: int | None = None                  # raise on this call, once

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self.model_copy(update={"tools": tuple(tools)})

    def with_structured_output(self, schema, **kwargs):
        if not self.structured:
            raise NotImplementedError
        return RunnableLambda(lambda _: self._count() or STRUCTURED[schema])

    def _count(self) -> None:
        self.calls.append(1)
        if len(self.calls) == self.fail_at:
            raise RuntimeError("provider unavailable")

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self._count()
        if self.tools:
            import threading
            import time
            self.threads.add(threading.current_thread().name)
            time.sleep(0.05)   # long enough for concurrent analysts to overlap
        if self.tools and not isinstance(messages[-1], ToolMessage):
            calls = [{"name": t.name, "id": f"call_{i}",
                      "args": {k: v for k, v in ARGS.items()
                               if k in t.tool_call_schema.model_json_schema()["properties"]}}
                     for i, t in enumerate(self.tools)]
            message = AIMessage(content="", tool_calls=calls)
        else:
            message = AIMessage(content=TEXT)
        return ChatResult(generations=[ChatGeneration(message=message)])


class PromptCapturingModel(ScriptedModel):
    prompts: list = Field(default_factory=list)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.prompts.append("\n".join(str(message.content) for message in messages))
        return super()._generate(messages, stop, run_manager, **kwargs)


class _Client:
    def __init__(self, model):
        self.model = model

    def get_llm(self):
        return self.model


@pytest.fixture
def offline(monkeypatch, tmp_path):
    """Every vendor answers offline; returns the set of router methods called."""
    called: set[str] = set()
    for method, vendors in router.VENDOR_METHODS.items():
        for vendor in vendors:
            monkeypatch.setitem(vendors, vendor,
                                lambda *a, _m=method, **k: called.add(_m) or f"{_m} data")
    prices = pd.DataFrame({
        "Date": pd.bdate_range(end=TRADE_DATE, periods=60),
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.5, "Volume": 1_000_000,
    })
    monkeypatch.setattr(snapshot, "load_ohlcv",
                        lambda *a, **k: called.add("ohlcv") or prices.copy())
    monkeypatch.setattr(sentiment_analyst, "fetch_stocktwits_messages", lambda *a, **k: "no posts")
    monkeypatch.setattr(sentiment_analyst, "fetch_reddit_posts", lambda *a, **k: "no posts")
    monkeypatch.setattr(yahoo_market.yf, "Ticker", lambda s: type("T", (), {"info": {"longName": "NVIDIA"}})())
    context._identity.cache_clear()
    return called


def _graph(tmp_path, monkeypatch, model, debug=False, **config):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg.update(results_dir=str(tmp_path / "results"), data_cache_dir=str(tmp_path / "cache"),
               memory_log_path=str(tmp_path / "log.md"), **config)
    monkeypatch.setattr(trading_graph, "create_tier_client", lambda config, tier, **k: _Client(model))
    return trading_graph.TradingAgentsGraph(config=cfg, debug=debug)


@pytest.mark.unit
def test_information_cutoff_uses_now_today_and_end_of_day_for_history():
    now = datetime(2026, 1, 9, 12, tzinfo=UTC)

    assert _information_decision_time("2026-01-09", now) == now
    assert _information_decision_time("2026-01-09", now.astimezone(
        timezone(timedelta(hours=7))
    )) == now
    with pytest.raises(ValueError, match="timezone-aware"):
        _information_decision_time("2026-01-09", now.replace(tzinfo=None))
    assert _information_decision_time("2026-01-08", now) == datetime(
        2026, 1, 8, 23, 59, 59, 999999, tzinfo=UTC
    )


@pytest.mark.unit
@pytest.mark.parametrize("historical", [False, True])
def test_crypto_run_context_reaches_the_real_market_analyst_prompt(
    tmp_path, monkeypatch, offline, historical
):
    store_path = tmp_path / "analysis.sqlite3"
    store = SQLiteInformationStore(store_path)
    now = datetime(2026, 1, 10, 12, tzinfo=UTC) if historical else datetime(2026, 1, 9, 12, tzinfo=UTC)
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)
    monkeypatch.setattr(trading_graph, "datetime", FrozenDatetime)
    cutoff = _information_decision_time(TRADE_DATE, now)
    funding = Observation(
        observation_id="stale-funding-evidence",
        source_id="derivatives.binance.usdm.funding",
        subject="BTCUSDT",
        metric="derivatives.funding_rate.usdm",
        payload={"funding_rate": "0.001"},
        event_time=datetime(2026, 1, 8, tzinfo=UTC),
        first_seen_time=cutoff,
        retrieved_at=cutoff,
        schema_version="usdm-funding-v1",
        unit="fraction",
    )
    source = Source(
        "derivatives.binance.usdm.funding", "exchange_rest", "Binance USD-M",
        "https://example.test/funding", "caller-driven", version="3",
        limitations=("historical vintages unavailable",), status=SourceStatus.DEGRADED,
    )
    coverage = CoverageRecord(
        "funding-stale", source.source_id, "BTCUSDT", funding.metric, cutoff,
        CoverageStatus.STALE, "collector has not refreshed the metric", (funding.observation_id,),
    )
    store.append(MarketDataBatch((funding,), (), cutoff, (coverage,), (source,)))

    spec = FRED_SERIES[0]
    macro = parse_fred_graph_csv(
        f"observation_date,{spec.series_id}\n2026-01-08,100.0\n",
        spec=spec, retrieved_at=cutoff,
    )
    event = ScheduledMacroEvent(
        event_id="test-cpi", title="CPI release", event_type="cpi_release",
        scheduled_at=cutoff + timedelta(days=1), source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://example.test/calendar",
    ).to_observation(retrieved_at=cutoff)
    future = Observation(
        observation_id="future-funding-must-not-leak", source_id=funding.source_id,
        subject=funding.subject, metric=funding.metric, payload={"funding_rate": "0.999"},
        event_time=cutoff, first_seen_time=cutoff + timedelta(microseconds=1),
        retrieved_at=cutoff + timedelta(microseconds=1),
    )
    store.append(macro)
    store.append(MarketDataBatch((event, future), (), cutoff + timedelta(seconds=1)))

    from tradingagents.information.narrative_events import parse_fed_monetary_feed
    rss = ("<rss><channel><item><title>Official policy headline</title>"
           "<link>https://www.federalreserve.gov/newsevents/pressreleases/monetary20260109a.htm</link>"
           "<pubDate>Fri, 09 Jan 2026 10:00:00 GMT</pubDate></item></channel></rss>")
    announcement = parse_fed_monetary_feed(rss, retrieved_at=cutoff)
    correction = parse_fed_monetary_feed(
        rss.replace("Official policy headline", "FUTURE POLICY CORRECTION"),
        retrieved_at=cutoff + timedelta(microseconds=1),
    )
    store.append(announcement)
    store.append(correction)

    model = PromptCapturingModel()
    graph = _graph(
        tmp_path, monkeypatch, model, information_store_path=str(store_path)
    )
    state, signal = graph.propagate("BTCUSDT", TRADE_DATE, asset_type="crypto")

    assert signal == state["final_rating"] == "Overweight"
    assert any(
        state["analysis_information"] in getattr(message, "content", "")
        for message in state["messages"]
    )
    market_prompts = [prompt for prompt in model.prompts if "get_verified_market_snapshot" in prompt]
    assert market_prompts
    market_prompt = "\n".join(market_prompts)
    assert announcement.observations[0].observation_id in market_prompt
    assert "Official policy headline" in market_prompt
    assert "FUTURE POLICY CORRECTION" not in market_prompt
    assert correction.observations[0].observation_id not in market_prompt
    assert "No causal price inference" in market_prompt
    assert len(state["analysis_information"]) <= 28000
    assert macro.observations[0].observation_id in market_prompt
    assert event.observation_id in market_prompt
    assert "future-funding-must-not-leak" not in market_prompt
    assert "0.999" not in market_prompt
    assert f"Decision cutoff: {cutoff.isoformat()}" in market_prompt
    assert "Replayable point-in-time market context" in market_prompt
    assert "Funding rate: 0.001; freshness: stale" in market_prompt
    assert "derivatives.binance.usdm.funding / BTCUSDT / derivatives.funding_rate.usdm: stale" in market_prompt
    assert "stale; observed at" in market_prompt
    assert "derivatives.binance.usdm.funding v3" in market_prompt
    assert "stale-funding-evidence" in market_prompt
    assert "schema: usdm-funding-v1; unit: fraction" in market_prompt


@pytest.mark.unit
@pytest.mark.parametrize("structured", [False, True], ids=["free-text", "structured"])
def test_a_full_run_reaches_a_logged_decision(tmp_path, monkeypatch, offline, structured):
    graph = _graph(tmp_path, monkeypatch, ScriptedModel(structured=structured))

    state, signal = graph.propagate("NVDA", TRADE_DATE)

    assert signal == state["final_rating"] == "Overweight"
    for key in ("market_report", "sentiment_report", "news_report", "fundamentals_report",
                "investment_plan", "trader_investment_plan", "final_trade_decision"):
        assert state[key].strip(), key
    tool_methods = {"get_stock_data", "get_indicators", "get_news", "get_global_news",
                    "get_macro_indicators", "get_prediction_markets", "get_fundamentals",
                    "get_balance_sheet", "get_cashflow", "get_income_statement",
                    "get_insider_transactions", "ohlcv"}
    assert offline == tool_methods
    assert [e["rating"] for e in graph.memory_log.load_entries()] == ["Overweight"]


@pytest.mark.unit
def test_an_interrupted_run_resumes_from_its_checkpoint(tmp_path, monkeypatch, offline):
    model = ScriptedModel(fail_at=12)            # past the analysts, before the decision
    graph = _graph(tmp_path, monkeypatch, model, checkpoint_enabled=True)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        graph.propagate("NVDA", TRADE_DATE)
    calls_before = len(model.calls)

    _, signal = graph.propagate("NVDA", TRADE_DATE)

    assert signal == "Overweight"
    resumed_calls = len(model.calls) - calls_before
    full_run = ScriptedModel()
    _graph(tmp_path / "fresh", monkeypatch, full_run).propagate("NVDA", TRADE_DATE)
    # The resumed run makes only the calls the interrupted one had not completed.
    assert resumed_calls == len(full_run.calls) - (model.fail_at - 1)


@pytest.mark.unit
def test_a_graph_reused_across_runs_keeps_no_run_state(tmp_path, monkeypatch, offline):
    """A backtest reuses one graph over its whole grid; holding every run's full
    state would grow without bound."""
    graph = _graph(tmp_path, monkeypatch, ScriptedModel())
    for trade_date in ("2026-01-08", TRADE_DATE):
        graph.propagate("NVDA", trade_date)

    held = [v for v in vars(graph).values() if isinstance(v, dict) and TRADE_DATE in v]
    assert held == []
    assert len(list(tmp_path.glob("results/NVDA/TradingAgentsStrategy_logs/*.json"))) == 2


@pytest.mark.unit
def test_the_analysts_run_at_the_same_time(tmp_path, monkeypatch, offline):
    model = ScriptedModel()
    graph = _graph(tmp_path, monkeypatch, model)

    assert not [n for n in graph.graph.get_graph().nodes if n.startswith("Msg Clear")]
    graph.propagate("NVDA", TRADE_DATE)

    assert len(model.threads) > 1


@pytest.mark.unit
def test_a_debug_run_prints_the_analysts_work_and_reaches_the_same_decision(tmp_path, monkeypatch, offline, capsys):
    """Debug mode streams the analysts' own graphs, so their tool calls still print."""
    graph = _graph(tmp_path, monkeypatch, ScriptedModel(), debug=True)

    state, signal = graph.propagate("NVDA", TRADE_DATE)

    assert signal == "Overweight"
    assert state["market_report"].strip() and state["fundamentals_report"].strip()
    printed = capsys.readouterr().out
    assert "get_stock_data" in printed and "get_balance_sheet" in printed


@pytest.mark.unit
def test_each_report_streams_as_soon_as_its_analyst_files_it(tmp_path, monkeypatch, offline):
    """The main state takes the analysts' reports only when the slowest one is
    done; the CLI shows each report, and stops each clock, as it lands."""
    graph = _graph(tmp_path, monkeypatch, ScriptedModel())
    reports = ("market_report", "sentiment_report", "news_report", "fundamentals_report")

    first = next(state for _, state in graph.stream_run(graph.create_run_state("NVDA", TRADE_DATE),
                                                        **graph.propagator.get_graph_args())
                 if state and any(state.get(k) for k in reports))

    assert sum(bool(first.get(k)) for k in reports) == 1


@pytest.mark.unit
def test_a_streamed_run_reads_its_own_graph_config(tmp_path, monkeypatch, offline):
    """The CLI streams the run; a process-wide config set elsewhere must not reach
    its tools, and the graph's config must not reach the caller between steps."""
    from tradingagents.dataflows.config import get_config, set_config

    graph = _graph(tmp_path, monkeypatch, ScriptedModel(), output_language="French")
    set_config({"output_language": "German"})
    seen = []
    monkeypatch.setitem(router.VENDOR_METHODS["get_stock_data"], "yfinance",
                        lambda *a, **k: seen.append(get_config()["output_language"]) or "prices")

    between = [get_config()["output_language"]
               for _ in graph.stream_run(graph.create_run_state("NVDA", TRADE_DATE), **graph.propagator.get_graph_args())]

    assert seen and set(seen) == {"French"}
    assert set(between) == {"German"}


class LoopingModel(ScriptedModel):
    """Calls a tool on every turn it is offered one (#1420)."""

    tool_turns: list = Field(default_factory=list)    # shared across bound copies
    last_turns: list = Field(default_factory=list)    # histories of the turns offered no tools

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        if not self.tools:
            self.last_turns.append(messages)
            return super()._generate(messages, stop, run_manager, **kwargs)
        self.tool_turns.append(1)
        tool = self.tools[0]
        call = {"name": tool.name, "id": f"call_{len(self.tool_turns)}",
                "args": {k: v for k, v in ARGS.items()
                         if k in tool.tool_call_schema.model_json_schema()["properties"]}}
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[call]))])


@pytest.mark.unit
def test_an_analyst_that_keeps_calling_tools_writes_its_report_at_the_limit(tmp_path, monkeypatch, offline):
    """A model that does not stop calling tools must not end the run (#1420)."""
    model = LoopingModel(structured=True)
    graph = _graph(tmp_path, monkeypatch, model, max_tool_rounds=3)

    final_state, rating = graph.propagate("NVDA", TRADE_DATE)

    assert len(model.tool_turns) == 3 * 3   # three tool-using analysts, three rounds each
    for key in ("market_report", "news_report", "fundamentals_report"):
        assert final_state[key] == TEXT
    assert rating == "Overweight"


@pytest.mark.unit
def test_the_last_turn_is_offered_no_tools_and_reads_its_tool_results_as_text(tmp_path, monkeypatch, offline):
    """Offered tools, a model may call one whatever it is told; a history holding
    tool calls may be refused by a provider when no tools are bound."""
    model = LoopingModel(structured=True)
    graph = _graph(tmp_path, monkeypatch, model, max_tool_rounds=2)

    graph.propagate("NVDA", TRADE_DATE)

    wrap_ups = [h for h in model.last_turns if isinstance(h[-1], HumanMessage) and "tool round" in h[-1].content]
    assert len(wrap_ups) == 3
    for history in wrap_ups:
        assert not any(isinstance(m, ToolMessage) or getattr(m, "tool_calls", None) for m in history)
        assert any("returned]" in str(m.content) for m in history)
        assert "tool rounds are spent" in history[0].content   # the system prompt lists no tools


@pytest.mark.unit
def test_a_tool_limit_the_recursion_limit_cannot_hold_is_refused(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="max_tool_rounds"):
        _graph(tmp_path, monkeypatch, ScriptedModel(), max_tool_rounds=60, max_recur_limit=100)


class TimedModel(ScriptedModel):
    """ScriptedModel that records each call's graph step, prompt and timing."""

    seen: list = Field(default_factory=list)    # shared across bound copies

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        step = (run_manager.metadata or {}).get("langgraph_node") if run_manager else None
        started = time.monotonic()
        if step in {"Market Analyst", "agent"} or step == "Memory Log":
            time.sleep(0.2)                     # long enough to see what overlaps
        result = super()._generate(messages, stop, run_manager, **kwargs)
        prompt = "\n".join(str(m.content) for m in messages)
        self.seen.append((step, prompt, started, time.monotonic()))
        return result


@pytest.mark.unit
def test_past_decisions_settle_alongside_the_analysts(tmp_path, monkeypatch, offline):
    from tradingagents.memory import settlement

    model = TimedModel()
    graph = _graph(tmp_path, monkeypatch, model)
    graph.memory_log.store_decision("NVDA", "2026-01-02", "Rating: Buy\n\nBuy NVDA.")
    closes = pd.Series([100.0 + i for i in range(10)], index=pd.bdate_range("2026-01-02", periods=10))
    monkeypatch.setattr(settlement, "get_closes", lambda *a, **k: closes)

    graph.propagate("NVDA", TRADE_DATE)

    reflections = [c for c in model.seen if c[0] == "Memory Log"]
    assert len(reflections) == 1                # settled once, inside the run
    analyst_turns = [c for c in model.seen if c[0] == "agent"]
    assert reflections[0][2] < max(c[3] for c in analyst_turns), "settled before the analysts, not alongside"
    settled = next(e for e in graph.memory_log.load_entries() if e["date"] == "2026-01-02")
    assert not settled["pending"]
    lessons = graph.memory_log.get_past_context("NVDA", as_of=TRADE_DATE)
    assert lessons
    pm_prompt = next(c[1] for c in model.seen if c[0] == "Portfolio Manager")
    assert lessons in pm_prompt


@pytest.mark.unit
def test_a_settlement_failure_is_noted_and_the_run_goes_on(tmp_path, monkeypatch, offline):
    """The analysts have spent their tokens by the time the join waits on settlement."""
    from tradingagents.reporting import write_report_tree

    graph = _graph(tmp_path, monkeypatch, ScriptedModel(structured=True))

    def locked():
        raise OSError("memory log is locked")

    monkeypatch.setattr(graph, "settle_all_pending", locked)
    final_state, rating = graph.propagate("NVDA", TRADE_DATE)

    assert rating == "Overweight"
    assert "could not be settled" in final_state["memory_note"]
    report = write_report_tree(final_state, "NVDA", tmp_path / "report").read_text()
    assert "Memory log: Past decisions could not be settled" in report


@pytest.mark.unit
def test_the_run_settles_other_tickers_due_decisions_too(tmp_path, monkeypatch, offline):
    """A ticker a scheduler stopped analysing still gets its decisions settled (#1445)."""
    from tradingagents.memory import settlement

    graph = _graph(tmp_path, monkeypatch, ScriptedModel(structured=True))
    graph.memory_log.store_decision("MSFT", "2026-01-02", "Rating: Buy\n\nBuy MSFT.")
    closes = pd.Series([100.0 + i for i in range(10)], index=pd.bdate_range("2026-01-02", periods=10))
    monkeypatch.setattr(settlement, "get_closes", lambda *a, **k: closes)

    graph.propagate("NVDA", TRADE_DATE)

    msft = next(e for e in graph.memory_log.load_entries() if e["ticker"] == "MSFT")
    assert not msft["pending"]


@pytest.mark.unit
def test_the_memory_step_reads_lessons_as_of_the_trade_date_and_settles_once(tmp_path, monkeypatch, offline):
    """A past-dated run reads only lessons known by its date (#1251); a resumed run
    that re-runs the step settles nothing twice."""
    from tradingagents.memory import settlement

    graph = _graph(tmp_path, monkeypatch, ScriptedModel(structured=True))
    graph.memory_log.store_decision("NVDA", "2026-01-02", "Rating: Buy\n\nBuy NVDA.")
    closes = pd.Series([100.0 + i for i in range(10)], index=pd.bdate_range("2026-01-02", periods=10))
    monkeypatch.setattr(settlement, "get_closes", lambda *a, **k: closes)
    asked = []
    real = graph.memory_log.get_past_context
    monkeypatch.setattr(graph.memory_log, "get_past_context",
                        lambda ticker, as_of=None, **k: asked.append(as_of) or real(ticker, as_of=as_of, **k))
    state = {"company_of_interest": "NVDA", "trade_date": "2026-01-20"}

    graph._memory_step(state)
    log_after_first = (tmp_path / "log.md").read_text()
    graph._memory_step(state)

    assert asked == ["2026-01-20", "2026-01-20"]
    assert (tmp_path / "log.md").read_text() == log_after_first


@pytest.mark.unit
@pytest.mark.parametrize("setting", [None, ""])
def test_crypto_information_store_is_optional(tmp_path, monkeypatch, offline, setting):
    def unexpected(*args, **kwargs):
        raise AssertionError("optional store must not be opened")
    monkeypatch.setattr(trading_graph, "SQLiteInformationStore", unexpected)
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=setting)
    state, signal = graph.propagate("BTCUSDT", TRADE_DATE, asset_type="crypto")
    assert signal == "Overweight"
    assert not state.get("analysis_information")
    assert all("Replayable point-in-time market context" not in p for p in model.prompts)


@pytest.mark.unit
@pytest.mark.parametrize("asset_type", ["crypto", "stock"])
def test_explicit_intraday_cutoff_through_actual_graph(tmp_path, monkeypatch, offline, asset_type):
    from tradingagents.information.news import parse_news_snapshot
    from tradingagents.information.sources import BROAD_NEWS_CONFIG

    cutoff = datetime(2026, 1, 9, 12, 30, 5, 123456, tzinfo=UTC)
    store = SQLiteInformationStore(tmp_path / "intraday.db")
    rss = '<rss><channel><item><title>Diplomatic negotiations underway</title><link>https://example.org/war</link><pubDate>Fri, 09 Jan 2026 10:00:00 GMT</pubDate></item></channel></rss>'
    first = parse_news_snapshot(rss, BROAD_NEWS_CONFIG[0], retrieved_at=cutoff)
    future = parse_news_snapshot(rss.replace("Diplomatic negotiations underway", "FUTURE WAR CORRECTION"), BROAD_NEWS_CONFIG[0], retrieved_at=cutoff + timedelta(microseconds=1))
    store.append(first)
    store.append(future)
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    state, signal = graph.propagate("BTCUSDT" if asset_type == "crypto" else "NVDA", TRADE_DATE,
                                    asset_type=asset_type, decision_time=cutoff)
    prompts = "\n".join(model.prompts)
    assert signal == "Overweight"
    assert f"Decision cutoff: {cutoff.isoformat()}" in prompts
    assert "Legacy news/social/market tools" in prompts
    assert "FUTURE WAR CORRECTION" not in prompts
    if asset_type == "crypto":
        assert "Diplomatic negotiations underway" in prompts
        assert first.observations[0].observation_id in prompts
        assert future.observations[0].observation_id not in prompts
        assert len(state["analysis_information"]) <= 28000
    else:
        assert not state["analysis_information"]


@pytest.mark.unit
def test_intraday_validation_and_checkpoint_guard(tmp_path, monkeypatch, offline):
    graph = _graph(tmp_path, monkeypatch, ScriptedModel())
    for cutoff in (datetime(2026, 1, 9, 12), datetime(2026, 1, 8, 12, tzinfo=UTC)):
        with pytest.raises(ValueError, match="aware|match"):
            graph.propagate("BTCUSDT", TRADE_DATE, asset_type="crypto", decision_time=cutoff)
    graph.config["checkpoint_enabled"] = True
    with pytest.raises(ValueError, match="checkpoint"):
        graph.propagate("BTCUSDT", TRADE_DATE, asset_type="crypto", decision_time=datetime(2026, 1, 9, 12, tzinfo=UTC))

@pytest.mark.unit
def test_claim_lifecycle_through_actual_graph(tmp_path, monkeypatch, offline):
    from tests.test_claim_lifecycle import article, persist
    from tradingagents.information.claim_lifecycle import record_claim_assertion

    cutoff = datetime(2026, 1, 9, 12, tzinfo=UTC)
    store = SQLiteInformationStore(tmp_path / "lifecycle.db")
    persist(store, article("a", "Semiconductor export controls announced"),
            article("b", "Export controls disputed"))
    support = record_claim_assertion(store, claim_id="a", kind="support", evidence_ids=("a",),
                                    recorded_at=cutoff, rationale="Primary announcement")
    opposition = record_claim_assertion(store, claim_id="a", kind="contradiction", evidence_ids=("b",),
                                       recorded_at=cutoff, rationale="Conflicting report")
    future = record_claim_assertion(store, claim_id="a", kind="correction", evidence_ids=("a",),
                                   target_ids=(opposition.observation_id,),
                                   recorded_at=cutoff+timedelta(microseconds=1), rationale="LATER CORRECTION")
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    state, _ = graph.propagate("BTCUSDT", TRADE_DATE, asset_type="crypto", decision_time=cutoff)
    prompt = "\n".join(model.prompts)
    assert '"supporting": ["a"]' in prompt and '"opposing": ["b"]' in prompt
    assert '"factual_truth": "unknown"' in prompt
    assert support.observation_id in prompt and opposition.observation_id in prompt
    assert future.observation_id not in prompt and "LATER CORRECTION" not in prompt
    assert len(state["analysis_information"]) <= 28000

@pytest.mark.unit
def test_acquired_claim_relationships_reach_graph(tmp_path, monkeypatch, offline):
    from tradingagents.information.claim_lifecycle import record_claim_assertion
    from tradingagents.information.news import parse_news_snapshot
    from tradingagents.information.sources import BROAD_NEWS_CONFIG

    cutoff = datetime(2026, 1, 9, 12, tzinfo=UTC)
    store = SQLiteInformationStore(tmp_path / "acquired-lifecycle.db")
    rows = []
    for index, title in enumerate(("Ceasefire agreed", "Ceasefire denied")):
        xml = f'<rss><channel><item><title>{title}</title><link>https://example.org/{index}</link></item></channel></rss>'
        batch = parse_news_snapshot(xml, BROAD_NEWS_CONFIG[index], retrieved_at=cutoff)
        store.append(batch)
        rows.append(batch.observations[0])
    for kind, row in zip(("support", "opposition"), rows, strict=True):
        record_claim_assertion(store, claim_id=rows[0].subject, kind=kind,
                               evidence_ids=(row.observation_id,), recorded_at=cutoff,
                               rationale="Curated source relationship")
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    state, _ = graph.propagate("BTCUSDT", TRADE_DATE, asset_type="crypto", decision_time=cutoff)
    prompt = "\n".join(model.prompts)
    assert '"claim_lifecycle"' in prompt and '"status": "contested"' in prompt
    assert all(row.observation_id in prompt for row in rows)
    assert "Ceasefire agreed" in prompt and "Ceasefire denied" in prompt
    assert len(state["analysis_information"]) <= 28000

@pytest.mark.unit
def test_recurring_poll_reaches_graph_at_cutoff(tmp_path, monkeypatch, offline):
    from tests.test_broad_news import TECH, WAR, atom, rss, session_for
    from tradingagents.information.polling import coordinate

    cutoff = datetime(2026, 1, 9, 12, tzinfo=UTC)
    store = SQLiteInformationStore(tmp_path / 'recurring-graph.db')
    coordinate(store, (WAR,), now=cutoff, clock=lambda: cutoff,
               session=session_for(rss('Ceasefire talks resume')))
    later = cutoff + timedelta(seconds=60)
    coordinate(store, (TECH,), now=later, clock=lambda: later,
               session=session_for(atom('Quantum laboratory breakthrough')))
    future = cutoff + timedelta(minutes=16)
    coordinate(store, (WAR,), now=future, clock=lambda: future,
               session=session_for(rss('FUTURE WAR CORRECTION')))
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    state, _ = graph.propagate('BTCUSDT', TRADE_DATE, asset_type='crypto', decision_time=later)
    prompt = '\n'.join(model.prompts)
    assert 'Ceasefire talks resume' in prompt and 'Quantum laboratory breakthrough' in prompt
    assert 'FUTURE WAR CORRECTION' not in prompt
    assert len(state['analysis_information']) <= 28000
