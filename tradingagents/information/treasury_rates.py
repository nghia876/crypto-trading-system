"""Point-in-time collection of the public U.S. Treasury 10-year par yield."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import requests

from tradingagents.information.binance_spot import MarketDataBatch, MarketDataCollectionError
from tradingagents.information.observations import Observation, ObservationQuality, Transformation
from tradingagents.information.sources import Source, SourceRegistry

TREASURY_DGS10_SOURCE = Source(
    source_id="macro.us.treasury.daily_par_yield",
    source_type="government_csv",
    provider="U.S. Department of the Treasury",
    endpoint="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv",
    collection_method="Unauthenticated public CSV download for the current year",
    asset_scope=("US",),
    metric_scope=("treasury_10y_par_yield_pct",),
    timezone="America/New_York",
    historical_depth="Current-year CSV; older archives are separate static downloads",
    publication_semantics="Rows contain a measurement date; exact publication timestamp is not supplied",
    revision_behavior="Current CSV has no vintage history; changed rows are appended as superseding observations",
    polling_frequency="Caller controlled",
    authentication_required=False,
    reliability="UNKNOWN — not yet measured by this project",
    limitations=(
        "Daily interpolated par yield, not a real-time traded yield",
        "Historical backfills become available only at local first-seen/retrieval time",
        "The source does not provide publication timestamps or prior vintages",
    ),
)


def parse_treasury_yield_csv(
    body: str,
    *,
    retrieved_at: datetime,
    first_seen_time: datetime | None = None,
    year: int | None = None,
) -> MarketDataBatch:
    """Normalize the official CSV without treating measurement date as release time."""
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    first_seen = first_seen_time or retrieved_at
    if first_seen.tzinfo is None or first_seen.utcoffset() is None:
        raise ValueError("first_seen_time must be timezone-aware")
    observations = []
    try:
        reader = csv.DictReader(io.StringIO(body.lstrip("\ufeff")))
        if (
            not reader.fieldnames
            or "Date" not in reader.fieldnames
            or "10 Yr" not in reader.fieldnames
        ):
            raise MarketDataCollectionError("Treasury CSV is missing Date or 10 Yr columns")
        for row in reader:
            date_text, raw_yield = (row.get("Date") or "").strip(), (row.get("10 Yr") or "").strip()
            if not date_text or not raw_yield or raw_yield.upper() in {"N/A", "NA", "."}:
                continue
            try:
                measurement_date = datetime.strptime(date_text, "%m/%d/%Y").date()
                value = Decimal(raw_yield)
            except (ValueError, InvalidOperation) as exc:
                raise MarketDataCollectionError(
                    "Treasury CSV contains an invalid date or 10 Yr value"
                ) from exc
            if not value.is_finite() or value < 0:
                raise MarketDataCollectionError(
                    "Treasury 10 Yr yield must be finite and non-negative"
                )
            if year is not None and measurement_date.year != year:
                continue
            event_time = datetime.combine(measurement_date, datetime.min.time(), tzinfo=UTC)
            payload = {
                "yield_pct": format(value, "f"),
                "units": "percent",
                "measurement_date": date_text,
            }
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()[:20]
            observations.append(
                Observation(
                    observation_id=f"treasury:dgs10:{measurement_date.isoformat()}:{digest}",
                    source_id=TREASURY_DGS10_SOURCE.source_id,
                    subject="US",
                    metric="macro.treasury_10y_par_yield_pct",
                    payload=payload,
                    event_time=event_time,
                    effective_time=event_time,
                    first_seen_time=first_seen,
                    retrieved_at=retrieved_at,
                    raw_reference=TREASURY_DGS10_SOURCE.endpoint,
                    transformations=(Transformation("parse_treasury_daily_yield_csv", "1"),),
                    quality=ObservationQuality.VERIFIED,
                    quality_notes=(
                        "Official Treasury row; source publication time and revision vintage unavailable",
                    ),
                )
            )
    except csv.Error as exc:
        raise MarketDataCollectionError("Treasury CSV could not be parsed") from exc
    if not observations:
        raise MarketDataCollectionError("Treasury CSV contained no usable 10 Yr observations")
    return MarketDataBatch(tuple(observations), (), retrieved_at)


class TreasuryYieldCollector:
    """Fetch current-year daily Treasury yields; no key or external package required."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
        registry: SourceRegistry | None = None,
        timeout: float = 20.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._timeout = timeout
        if registry is not None and TREASURY_DGS10_SOURCE.source_id not in registry:
            registry.register(TREASURY_DGS10_SOURCE)

    def collect(self, *, year: int | None = None) -> MarketDataBatch:
        retrieved_at = self._clock()
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise ValueError("clock must return an aware datetime")
        target_year = year or retrieved_at.year
        url = f"{TREASURY_DGS10_SOURCE.endpoint}/{target_year}/all"
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MarketDataCollectionError("Treasury rates request failed") from exc
        return parse_treasury_yield_csv(response.text, retrieved_at=retrieved_at, year=target_year)
