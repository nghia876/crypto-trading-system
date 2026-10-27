"""Public FRED graph-series observations with conservative PIT availability."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import requests

from tradingagents.information.binance_spot import (
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    MarketDataCollectionError,
)
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.sources import Source, SourceRegistry
from tradingagents.information.store import InformationView

_FRED_GRAPH_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


@dataclass(frozen=True, slots=True)
class FredSeriesSpec:
    """A selected public macro series and its explicit interpretation."""

    series_id: str
    label: str
    metric: str
    units: str
    frequency: str
    source: Source
    proxy_for: str | None = None


def _fred_spec(
    series_id: str,
    label: str,
    metric: str,
    units: str,
    frequency: str,
    *,
    source_name: str = "Federal Reserve Bank of St. Louis FRED; original source listed per series",
    proxy_for: str | None = None,
) -> FredSeriesSpec:
    source = Source(
        source_id=f"macro.fred.{series_id.lower()}",
        source_type="public_macro_csv",
        provider=source_name,
        endpoint=f"{_FRED_GRAPH_CSV}?id={series_id}",
        collection_method="Caller-driven download of the public FRED graph CSV",
        asset_scope=("BTC",),
        metric_scope=(metric,),
        timezone="UTC",
        historical_depth="Historical observations; no historical availability or vintage time in graph CSV",
        publication_semantics=(
            "Observation date is reference time only; local first-seen/retrieval time bounds replay availability"
        ),
        revision_behavior="Changed values are appended as later known revisions by the information store",
        authentication_required=False,
        reliability="UNKNOWN — not yet measured by this project",
        limitations=(
            "Graph CSV does not expose release timestamps or vintages",
            "Historical backfills are available to replay only from local ingestion time",
            *((f"Proxy for {proxy_for}; not the exact requested instrument",) if proxy_for else ()),
        ),
    )
    return FredSeriesSpec(series_id, label, metric, units, frequency, source, proxy_for)


FRED_SERIES: tuple[FredSeriesSpec, ...] = (
    _fred_spec(
        "DTWEXBGS",
        "Nominal broad U.S. dollar index",
        "macro.usd.broad_nominal_index",
        "index (Jan 2006=100)",
        "daily",
        source_name="Federal Reserve Board via FRED",
        proxy_for="a broad dollar-strength measure; not the ICE U.S. Dollar Index (DXY)",
    ),
    _fred_spec(
        "DCOILWTICO",
        "WTI crude oil spot price",
        "macro.oil.wti_usd_per_barrel",
        "USD/barrel",
        "daily",
        source_name="U.S. Energy Information Administration via FRED",
    ),
    _fred_spec(
        "DGS2",
        "2-year Treasury constant maturity rate",
        "macro.treasury_2y_yield_pct",
        "percent",
        "daily",
        source_name="U.S. Treasury via Federal Reserve Board and FRED",
    ),
    _fred_spec(
        "NFCI",
        "Chicago Fed National Financial Conditions Index",
        "macro.risk.financial_conditions_index",
        "index",
        "weekly",
        source_name="Federal Reserve Bank of Chicago via FRED",
        proxy_for="U.S. financial conditions; not a direct market risk-on/risk-off price proxy",
    ),
    _fred_spec(
        "SP500",
        "S&P 500 daily close",
        "macro.risk.sp500_close",
        "index points",
        "daily",
        source_name="S&P Dow Jones Indices LLC via FRED; source terms apply",
        proxy_for="broad U.S. equity risk appetite",
    ),
    _fred_spec(
        "VIXCLS",
        "CBOE Volatility Index daily close",
        "macro.risk.vix_close",
        "index points",
        "daily",
        source_name="Chicago Board Options Exchange via FRED; source terms apply",
        proxy_for="U.S. equity implied volatility / risk aversion",
    ),
)
_SPECS_BY_ID = {spec.series_id: spec for spec in FRED_SERIES}
_SPECS_BY_METRIC = {spec.metric: spec for spec in FRED_SERIES}


def parse_fred_graph_csv(
    text: str,
    *,
    spec: FredSeriesSpec,
    retrieved_at: datetime,
    start: date | None = None,
    end: date | None = None,
) -> MarketDataBatch:
    """Parse one FRED graph CSV without treating reference dates as availability."""
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    retrieved_at = retrieved_at.astimezone(UTC)
    if start is not None and end is not None and end < start:
        raise ValueError("end must be on or after start")
    try:
        reader = csv.reader(io.StringIO(text))
        header = next(reader)
        if len(header) < 2 or header[0].strip().lower() not in {"observation_date", "date"}:
            raise MarketDataCollectionError("FRED CSV has an unexpected header")
        if header[1].strip().upper() != spec.series_id:
            raise MarketDataCollectionError("FRED CSV series does not match the requested series")
        observations = []
        for row in reader:
            if len(row) < 2:
                raise MarketDataCollectionError("FRED CSV contains a malformed row")
            date_text, raw_value = row[0].strip(), row[1].strip()
            if not date_text or not raw_value or raw_value in {".", "NA", "N/A"}:
                continue
            try:
                reference_date = date.fromisoformat(date_text)
                value = Decimal(raw_value)
            except (ValueError, InvalidOperation) as exc:
                raise MarketDataCollectionError(
                    "FRED CSV contains an invalid date or value"
                ) from exc
            if not value.is_finite():
                raise MarketDataCollectionError("FRED CSV value must be finite")
            if reference_date > retrieved_at.date():
                raise MarketDataCollectionError("FRED CSV contains a future observation date")
            if start is not None and reference_date < start:
                continue
            if end is not None and reference_date > end:
                continue
            event_time = datetime.combine(reference_date, datetime.min.time(), UTC)
            payload: dict[str, object] = {
                "series_id": spec.series_id,
                "label": spec.label,
                "value": format(value, "f"),
                "units": spec.units,
                "frequency": spec.frequency,
            }
            if spec.proxy_for:
                payload["proxy_for"] = spec.proxy_for
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
            observations.append(
                Observation(
                    observation_id=(
                        f"fred:{spec.series_id}:{reference_date.isoformat()}:{digest}:"
                        f"{retrieved_at.isoformat()}"
                    ),
                    source_id=spec.source.source_id,
                    subject="US",
                    metric=spec.metric,
                    payload=payload,
                    schema_version="fred-series-v1",
                    unit=spec.units,
                    event_time=event_time,
                    effective_time=event_time,
                    first_seen_time=retrieved_at,
                    retrieved_at=retrieved_at,
                    raw_reference=f"{spec.source.endpoint}&cosd={reference_date.isoformat()}&coed={reference_date.isoformat()}",
                    transformations=(Transformation("parse_fred_graph_csv", "1"),),
                    quality="unknown",
                    quality_notes=(
                        "FRED graph CSV provides an observation date, not a release timestamp or vintage",
                    ),
                )
            )
    except StopIteration as exc:
        raise MarketDataCollectionError("FRED CSV is empty") from exc
    except csv.Error as exc:
        raise MarketDataCollectionError("FRED CSV could not be parsed") from exc
    coverage = CoverageRecord(
        f"{spec.source.source_id}:{retrieved_at.isoformat()}", spec.source.source_id,
        "US", spec.metric, retrieved_at,
        CoverageStatus.PRESENT if observations else CoverageStatus.UNKNOWN,
        f"{len(observations)} usable observation(s) in response",
        tuple(item.observation_id for item in observations),
    )
    return MarketDataBatch(tuple(observations), (), retrieved_at, (coverage,), (spec.source,))


class FredPublicSeriesCollector:
    """Caller-driven, keyless retrieval of selected public FRED graph CSV series."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
        registry: SourceRegistry | None = None,
    ) -> None:
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(UTC))
        self.registry = registry or SourceRegistry(tuple(spec.source for spec in FRED_SERIES))
        for spec in FRED_SERIES:
            if spec.source.source_id not in self.registry:
                self.registry.register(spec.source)
            elif self.registry.get(spec.source.source_id) != spec.source:
                raise ValueError(
                    f"registry contains conflicting metadata for {spec.source.source_id}"
                )

    def collect(
        self,
        series_id: str,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> MarketDataBatch:
        """Fetch a selected series, optionally restricting reference dates."""
        try:
            spec = _SPECS_BY_ID[series_id.upper()]
        except KeyError as exc:
            raise ValueError(f"unsupported FRED series: {series_id}") from exc
        if start is not None and end is not None and end < start:
            raise ValueError("end must be on or after start")
        params: dict[str, str] = {"id": spec.series_id}
        if start is not None:
            params["cosd"] = start.isoformat()
        if end is not None:
            params["coed"] = end.isoformat()
        try:
            response = self._session.get(_FRED_GRAPH_CSV, params=params, timeout=(3.05, 15.0))
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MarketDataCollectionError(f"FRED graph CSV request failed: {exc}") from exc
        retrieved_at = self._clock()
        return parse_fred_graph_csv(
            response.text,
            spec=spec,
            retrieved_at=retrieved_at,
            start=start,
            end=end,
        )


@dataclass(frozen=True, slots=True)
class MacroSeriesValue:
    series_id: str
    metric: str
    value: Decimal | None
    event_time: datetime | None
    available_at: datetime | None
    age: timedelta | None
    freshness: str
    evidence_observation_id: str | None
    proxy_for: str | None


@dataclass(frozen=True, slots=True)
class MacroState:
    decision_time: datetime
    series: tuple[MacroSeriesValue, ...]


def build_macro_state(
    view: InformationView,
    *,
    stale_after: timedelta = timedelta(days=7),
) -> MacroState:
    """Build deterministic macro state from eligible observations in a PIT view."""
    if view.decision_time.tzinfo is None or view.decision_time.utcoffset() is None:
        raise ValueError("decision_time must be timezone-aware")
    if stale_after < timedelta(0):
        raise ValueError("stale_after must be non-negative")
    latest_by_metric: dict[str, Observation] = {}
    for observation in view.observations:
        if (
            observation.metric not in _SPECS_BY_METRIC
            or observation.source_id != _SPECS_BY_METRIC[observation.metric].source.source_id
            or observation.subject != "US"
            or observation.event_time > view.decision_time
            or not observation.is_available_at(view.decision_time)
        ):
            continue
        current = latest_by_metric.get(observation.metric)
        key = (observation.event_time, observation.available_at, observation.observation_id)
        if current is None or key > (
            current.event_time,
            current.available_at,
            current.observation_id,
        ):
            latest_by_metric[observation.metric] = observation
    values = []
    for spec in FRED_SERIES:
        observation = latest_by_metric.get(spec.metric)
        if observation is None:
            values.append(
                MacroSeriesValue(
                    spec.series_id,
                    spec.metric,
                    None,
                    None,
                    None,
                    None,
                    "unknown",
                    None,
                    spec.proxy_for,
                )
            )
            continue
        try:
            value = Decimal(str(observation.payload["value"]))
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise ValueError(
                f"observation {observation.observation_id} has an invalid macro value"
            ) from exc
        if not value.is_finite():
            raise ValueError(
                f"observation {observation.observation_id} has a non-finite macro value"
            )
        age = view.decision_time - observation.event_time
        values.append(
            MacroSeriesValue(
                spec.series_id,
                spec.metric,
                value,
                observation.event_time,
                observation.available_at,
                age,
                "stale" if age > stale_after else "fresh",
                observation.observation_id,
                spec.proxy_for,
            )
        )
    return MacroState(view.decision_time, tuple(values))
