"""Bounded original-publisher macro snapshots; never historical knowledge.

BLS statistical levels are eligible. Treasury expansion and BEA remain explicit
gaps. Existing calendar observations describe schedules, not numeric vintages.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import requests

from tradingagents.information.binance_spot import MarketDataCollectionError
from tradingagents.information.liquidity import _aware, _batch
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.scheduled_events import (
    bls_release_calendar_source,
    parse_bls_release_calendar,
)
from tradingagents.information.sources import Source, SourceRegistry

BLS_NOTICE = "BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov."


@dataclass(frozen=True)
class MacroSpec:
    key: str
    metric: str
    definition: str
    units: str
    frequency: str
    stale_days: int


BLS_SPECS = (
    MacroSpec(
        "CUSR0000SA0",
        "macro.bls.cpi_sa_index",
        "CPI-U all items, US city average, seasonally adjusted",
        "index (1982-84=100)",
        "monthly",
        75,
    ),
    MacroSpec(
        "CUSR0000SA0L1E",
        "macro.bls.core_cpi_sa_index",
        "CPI-U less food and energy, US city average, seasonally adjusted",
        "index (1982-84=100)",
        "monthly",
        75,
    ),
    MacroSpec(
        "CES0000000001",
        "macro.bls.nonfarm_payrolls_sa",
        "Total nonfarm payroll employment level, seasonally adjusted; not monthly change",
        "thousand employees",
        "monthly",
        75,
    ),
    MacroSpec(
        "LNS14000000",
        "macro.bls.unemployment_sa_pct",
        "Civilian unemployment rate age 16+, seasonally adjusted",
        "percent",
        "monthly",
        75,
    ),
)
YIELD_SPECS = tuple(
    MacroSpec(
        f"BC_{tenor}YEAR",
        f"macro.treasury.par_{tenor}y_pct",
        f"Treasury nominal {tenor}-year interpolated par yield; not a bill discount rate or traded quote",
        "percent",
        "business day",
        4,
    )
    for tenor in (2, 10)
)


def _source(key, provider, endpoint, specs, policy, eligibility):
    return Source(
        source_id=f"macro.original.{key}",
        source_type="original_publisher",
        provider=provider,
        endpoint=endpoint,
        collection_method="Bounded keyless request; caller driven; no automatic retry",
        metric_scope=tuple(s.metric for s in specs),
        timezone="America/New_York",
        publication_semantics="Reference period is not publication; snapshot publication unknown",
        revision_behavior="Canonical store appends changed period values at local acquisition",
        polling_frequency="At most hourly per collector instance; coordinate globally before unattended use",
        rate_limit="Respect publisher quotas and Retry-After; no automatic retries",
        limitations=("No historical vintage reconstruction; snapshot is not complete coverage",),
        legal_constraints=(
            policy,
            "Preserve attribution and acquisition date; no logo or endorsement",
        ),
        metadata=(("eligibility", eligibility),),
    )


BLS = _source(
    "bls",
    "U.S. Bureau of Labor Statistics",
    "https://api.bls.gov/publicAPI/v1/timeseries/data/",
    BLS_SPECS,
    "https://www.bls.gov/developers/termsOfService.htm ; https://www.bls.gov/bls/linksite.htm ; public-domain statistics; secondary use without end-use controls; attribution/date/disclaimer required",
    "eligible",
)
TREASURY = _source(
    "treasury_par",
    "U.S. Department of the Treasury",
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml",
    YIELD_SPECS,
    "Official structured feed documented; detailed home.treasury.gov service automation/storage/AI rights review unresolved; not Fiscal Data clearance",
    "pending",
)
BEA = _source(
    "bea_nipa",
    "U.S. Bureau of Economic Analysis",
    "https://apps.bea.gov/api/data/",
    (),
    "https://www.bea.gov/help/faq/147 ; https://apps.bea.gov/API/_pdf/bea_api_tos.pdf ; API registration required; metadata/table/line/vintage and incorporated website policies not validated",
    "pending",
)
BEA = replace(
    BEA,
    metric_scope=("macro.bea.pce_price_index", "macro.bea.core_pce_price_index", "macro.bea.gdp"),
    authentication_required=True,
)
SOURCES = (BLS, TREASURY, BEA)


def _row(source, spec, period, value, at, *, extra=None):
    from decimal import Decimal, InvalidOperation

    # Both feeds publish ordinary decimal text. Bound it before Decimal/format:
    # a tiny exponent string can otherwise allocate an arbitrarily large value.
    if (
        not isinstance(value, str)
        or len(value) > 64
        or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value)
    ):
        raise MarketDataCollectionError("Expected bounded plain decimal text")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise MarketDataCollectionError("Invalid macro number") from exc
    if not number.is_finite() or number < 0:
        raise MarketDataCollectionError("Macro level must be finite and nonnegative")
    marker = datetime.combine(period, datetime.min.time(), ZoneInfo("America/New_York"))
    if period > at.astimezone(ZoneInfo("America/New_York")).date():
        raise MarketDataCollectionError("Future macro reference period")
    payload = dict(
        value=format(number, "f"),
        units=spec.units,
        frequency=spec.frequency,
        definition=spec.definition,
        reference_date=period.isoformat(),
        **(extra or {}),
    )
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return Observation(
        observation_id=f"om:{spec.key}:{period}:{digest}:{at.isoformat()}",
        source_id=source.source_id,
        subject="US",
        metric=spec.metric,
        payload=payload,
        event_time=marker,
        effective_time=marker,
        first_seen_time=at,
        retrieved_at=at,
        raw_reference=source.endpoint,
        schema_version="original-macro-v1",
        unit=spec.units,
        transformations=(Transformation("original_macro_snapshot", "1"),),
        quality_notes=(
            "Reference period marker is not release time; publication unknown; first availability is local acquisition",
        ),
    )


def parse_bls_json(body: str, *, retrieved_at: datetime, series_ids=None):
    """Keep monthly levels/footnotes; reject wrong series and ambiguous duplicates.

    M13 annual averages are deliberately excluded. No growth rate, actual release
    time, historical revision order, or calendar-to-value linkage is inferred.
    """
    at = _aware(retrieved_at)
    if len(body) > 2_000_000:
        raise MarketDataCollectionError("BLS response exceeds 2 MB")
    expected = tuple(series_ids) if series_ids is not None else tuple(s.key for s in BLS_SPECS)
    specs = {s.key: s for s in BLS_SPECS}
    if not expected or len(set(expected)) != len(expected) or set(expected) - specs.keys():
        raise ValueError("Unsupported/duplicate BLS series selection")
    try:
        doc = json.loads(body)
        if doc["status"] != "REQUEST_SUCCEEDED":
            raise MarketDataCollectionError("BLS reports failed request")
        results = doc["Results"]
        if isinstance(results, list):
            if len(results) != 1:
                raise MarketDataCollectionError("Unexpected BLS Results shape")
            results = results[0]
        rows, seen, seen_series = [], set(), set()
        series = results["series"]
        if not isinstance(series, list) or len(series) > len(expected):
            raise MarketDataCollectionError("Invalid BLS series list")
        for group in series:
            key = group["seriesID"]
            if key not in expected or key in seen_series:
                raise MarketDataCollectionError("Unexpected/duplicate BLS series")
            seen_series.add(key)
            data = group["data"]
            if not isinstance(data, list) or len(data) > 130:
                raise MarketDataCollectionError("BLS row bound exceeded")
            for item in data:
                period = item["period"]
                if period == "M13":
                    continue
                if not re.fullmatch(r"M(0[1-9]|1[0-2])", period):
                    raise MarketDataCollectionError("Unsupported BLS period")
                raw_year = item["year"]
                if not isinstance(raw_year, str) or not re.fullmatch(r"[0-9]{4}", raw_year):
                    raise MarketDataCollectionError("Expected four-digit BLS year text")
                year, month = int(raw_year), int(period[1:])
                ref = date(year, month, 1)
                if item.get("periodName", calendar.month_name[month]) != calendar.month_name[month]:
                    raise MarketDataCollectionError("BLS period label mismatch")
                if (key, ref) in seen:
                    raise MarketDataCollectionError("Duplicate BLS period")
                seen.add((key, ref))
                notes = item.get("footnotes", [])
                if not isinstance(notes, list) or any(
                    not isinstance(n, dict) or any(not isinstance(v, str) for v in n.values())
                    for n in notes
                ):
                    raise MarketDataCollectionError("Invalid BLS footnotes")
                raw = item["value"]
                if raw in ("-", ".", "", "NA", "N/A", None):
                    continue
                rows.append(
                    _row(
                        BLS,
                        specs[key],
                        ref,
                        raw,
                        at,
                        extra={
                            "series_id": key,
                            "observation_period": f"{year:04d}-{month:02d}",
                            "period_end": date(
                                year, month, calendar.monthrange(year, month)[1]
                            ).isoformat(),
                            "seasonal_adjustment": "SA",
                            "footnotes": notes,
                            "vintage": "current snapshot, local prospective revisions only",
                        },
                    )
                )
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise MarketDataCollectionError("Malformed BLS snapshot") from exc
    return _batch(BLS, rows, at)


def parse_treasury_par_xml(body: str, *, retrieved_at: datetime):
    """Validate a bounded official Atom/OData sample; output stays analyst gated."""
    at = _aware(retrieved_at)
    if "<!DOCTYPE" in body.upper() or "<!ENTITY" in body.upper() or len(body) > 2_000_000:
        raise MarketDataCollectionError("Unsafe/oversize Treasury XML")
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
        "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
    }
    try:
        root = ET.fromstring(body)
        if root.tag != f"{{{ns['a']}}}feed":
            raise MarketDataCollectionError("Expected Treasury Atom feed")
        rows, seen = [], set()
        entries = root.findall("a:entry", ns)
        if len(entries) > 366:
            raise MarketDataCollectionError("Treasury row bound exceeded")
        for entry in entries:
            props = entry.find("a:content/m:properties", ns)
            if props is None:
                raise MarketDataCollectionError("Missing Treasury properties")
            raw_date = props.findtext("d:NEW_DATE", namespaces=ns)
            ref = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S").date()
            if ref in seen:
                raise MarketDataCollectionError("Duplicate Treasury date")
            seen.add(ref)
            for spec in YIELD_SPECS:
                cells = props.findall(f"d:{spec.key}", ns)
                if len(cells) != 1:
                    raise MarketDataCollectionError("Missing/duplicate Treasury tenor")
                cell = cells[0]
                if cell.get(f"{{{ns['m']}}}null") == "true":
                    continue
                if cell.get(f"{{{ns['m']}}}type") != "Edm.Double":
                    raise MarketDataCollectionError("Unexpected Treasury number type")
                rows.append(
                    _row(
                        TREASURY,
                        spec,
                        ref,
                        cell.text,
                        at,
                        extra={
                            "tenor_years": int(spec.key.split("_")[1][:-4]),
                            "eligibility": "pending",
                        },
                    )
                )
    except (ET.ParseError, TypeError, ValueError) as exc:
        raise MarketDataCollectionError("Malformed Treasury par feed") from exc
    return _batch(TREASURY, rows, at)


def _failure_detail(exc):
    """Classify failures without exposing response bodies, URLs or credentials."""
    if isinstance(exc, requests.Timeout):
        return "Network timeout"
    if isinstance(exc, requests.RequestException):
        return f"Network failure ({type(exc).__name__})"
    status = re.match(r"HTTP [0-9]{3}(?:;|$)", str(exc))
    if status:
        return status[0].rstrip(";")
    return f"Schema/encoding failure ({type(exc).__name__})"


class OriginalMacroCollector:
    """One request per call with bounded streaming, no redirects and cooldown.

    Instance cooldown prevents tight retries, including HTTP Retry-After. It is
    deliberately not a scheduler: cross-process quotas require caller coordination.
    """

    def __init__(self, *, session=None, clock=None, registry=None):
        self.session = session or requests.Session()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.registry = registry if registry is not None else SourceRegistry()
        self.next_request_at = None
        self.calendar_next_request_at = None
        for source in SOURCES:
            if source.source_id not in self.registry:
                self.registry.register(source)
            elif self.registry.get(source.source_id) != source:
                raise ValueError("Conflicting macro source definition")

    def collect(self, key="bls", *, series_ids=None):
        at = _aware(self.clock())
        source = {
            "bls": BLS,
            "bls_calendar": bls_release_calendar_source(at.year),
            "treasury_par": TREASURY,
            "bea": BEA,
        }[key]
        if key == "bls_calendar":
            return self._calendar(source, at)
        if source is not BLS:
            return _batch(
                source,
                (),
                at,
                failure=(
                    "Gated: free registration, incorporated terms and exact NIPA/vintage mapping unvalidated; no request"
                    if source is BEA
                    else "Gated: source-specific rights review incomplete; no request"
                ),
            )
        ids = tuple(series_ids) if series_ids is not None else tuple(s.key for s in BLS_SPECS)
        if not ids or len(set(ids)) != len(ids) or set(ids) - {s.key for s in BLS_SPECS}:
            raise ValueError("Unsupported/duplicate BLS series selection")
        if self.next_request_at is not None and at < self.next_request_at:
            return _batch(
                source,
                (),
                at,
                failure=f"Cooldown until {self.next_request_at.isoformat()}; no request",
            )
        self.next_request_at = at + timedelta(hours=1)
        try:
            # GET single series and POST selected series are both documented v1 signatures.
            with self.session.post(
                source.endpoint,
                json={"seriesid": list(ids)},
                timeout=(3.05, 15),
                stream=True,
                allow_redirects=False,
            ) as response:
                retry = response.headers.get("Retry-After")
                if retry:
                    try:
                        until = (
                            at + timedelta(seconds=max(0, int(retry)))
                            if retry.isdigit()
                            else _aware(parsedate_to_datetime(retry))
                        )
                        self.next_request_at = max(self.next_request_at, until)
                    except (ValueError, TypeError, OverflowError):
                        pass  # The default one-hour cooldown still applies.
                if response.status_code != 200:
                    raise MarketDataCollectionError(f"HTTP {response.status_code}; no value")
                parts, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 2_000_000:
                        raise MarketDataCollectionError("Macro response exceeds 2 MB")
                    parts.append(chunk)
                body = b"".join(parts).decode("utf-8-sig")
            return parse_bls_json(body, retrieved_at=_aware(self.clock()), series_ids=ids)
        except (requests.RequestException, MarketDataCollectionError, UnicodeError) as exc:
            return _batch(
                source,
                (),
                _aware(self.clock()),
                failure=f"{_failure_detail(exc)}; no value inferred; respect cooldown",
            )

    def _calendar(self, source, at):
        """Reuse the existing annual schedule parser and scheduled-event contract."""
        if self.calendar_next_request_at is not None and at < self.calendar_next_request_at:
            return _batch(source, (), at, failure="Calendar cooldown; no request")
        self.calendar_next_request_at = at + timedelta(hours=1)
        try:
            with self.session.get(
                source.endpoint, timeout=(3.05, 15), stream=True, allow_redirects=False
            ) as response:
                retry = response.headers.get("Retry-After")
                if retry:
                    try:
                        until = (
                            at + timedelta(seconds=max(0, int(retry)))
                            if retry.isdigit()
                            else _aware(parsedate_to_datetime(retry))
                        )
                        self.calendar_next_request_at = max(self.calendar_next_request_at, until)
                    except (ValueError, TypeError, OverflowError):
                        pass
                if response.status_code != 200:
                    raise MarketDataCollectionError(
                        f"HTTP {response.status_code}; calendar unavailable"
                    )
                parts, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 2_000_000:
                        raise MarketDataCollectionError("Calendar exceeds 2 MB")
                    parts.append(chunk)
                body = b"".join(parts).decode("utf-8-sig")
            # A schedule is never relabeled as actual release time for numeric rows.
            return parse_bls_release_calendar(body, retrieved_at=_aware(self.clock()), year=at.year)
        except (requests.RequestException, MarketDataCollectionError, UnicodeError) as exc:
            return _batch(
                source,
                (),
                _aware(self.clock()),
                failure=f"{_failure_detail(exc)}; release dates unknown",
            )


def selected_original_macro(view):
    result = []
    for spec in BLS_SPECS + YIELD_SPECS:
        source = BLS if spec in BLS_SPECS else TREASURY
        rows = [
            o
            for o in view.observations
            if o.source_id == source.source_id
            and o.metric == spec.metric
            and o.subject == "US"
            and o.schema_version == "original-macro-v1"
            and o.unit == spec.units
            and o.event_time <= view.decision_time
            and o.is_available_at(view.decision_time)
        ]
        if dict(source.metadata)["eligibility"] != "eligible":
            rows = []
        result.append(
            (
                spec,
                max(
                    rows,
                    key=lambda o: (o.event_time, o.available_at, o.observation_id),
                    default=None,
                ),
            )
        )
    return tuple(result)


def render_original_macro(view):
    lines = []
    for spec, row in selected_original_macro(view):
        if row is None:
            lines.append(
                f"- {spec.definition}: unknown; {spec.units}; {'eligibility pending' if spec in YIELD_SPECS else 'no eligible observation'}"
            )
        else:
            stale = view.decision_time - row.event_time > timedelta(days=spec.stale_days)
            lines.append(
                f"- {spec.key}: {row.payload['value']} {spec.units}; {spec.definition}; {spec.frequency}; period: {row.payload['observation_period']}; {'stale' if stale else 'fresh'}; publication: unknown; acquired: {row.retrieved_at.isoformat()}; evidence: {row.observation_id}"
            )
    if any(row for _, row in selected_original_macro(view)):
        lines.append(
            f"- Source: U.S. Bureau of Labor Statistics; normalized levels, not growth estimates. {BLS_NOTICE}"
        )
    lines.append(
        "- BEA PCE/core PCE price indexes and GDP: unknown; gated pending free access, terms and exact table/vintage validation. Calendar schedules do not establish actual publication or numeric vintages."
    )
    return lines
