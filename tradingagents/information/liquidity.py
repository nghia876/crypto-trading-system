"""Original-publisher liquidity evidence in the canonical information contracts.

No historical date is treated as local knowledge. Collector calls are bounded,
caller driven and never retry. Missing rows and failed requests are not zeros.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import requests

from tradingagents.information.binance_spot import (
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    MarketDataCollectionError,
)
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.sources import Source
from tradingagents.information.store import InformationView


@dataclass(frozen=True)
class LiquiditySpec:
    key: str
    metric: str
    definition: str
    units: str
    frequency: str
    stale_after: timedelta


SPECS = (
    LiquiditySpec(
        "assets",
        "macro.fed.total_assets_wednesday",
        "H.4.1 table 5 total assets, Wednesday level",
        "million USD",
        "weekly",
        timedelta(days=10),
    ),
    LiquiditySpec(
        "reserves_avg",
        "macro.fed.reserves_weekly_average",
        "H.4.1 table 1 reserve balances with Federal Reserve Banks, average of daily figures",
        "million USD",
        "weekly",
        timedelta(days=10),
    ),
    LiquiditySpec(
        "reserves_wed",
        "macro.fed.reserves_wednesday",
        "H.4.1 table 1 reserve balances with Federal Reserve Banks, Wednesday level",
        "million USD",
        "weekly",
        timedelta(days=10),
    ),
    LiquiditySpec(
        "tga_avg",
        "macro.fed.tga_weekly_average",
        "H.4.1 table 1 U.S. Treasury General Account, average of daily figures",
        "million USD",
        "weekly",
        timedelta(days=10),
    ),
    LiquiditySpec(
        "tga_wed",
        "macro.fed.tga_wednesday",
        "H.4.1 table 1 U.S. Treasury General Account, Wednesday level",
        "million USD",
        "weekly",
        timedelta(days=10),
    ),
    LiquiditySpec(
        "on_rrp",
        "macro.nyfed.on_rrp_accepted",
        "Overnight Treasury reverse repo total accepted per operation; not all H.4.1 reverse repos",
        "USD",
        "operation/business day",
        timedelta(days=4),
    ),
    LiquiditySpec(
        "tga_daily",
        "macro.treasury.tga_daily_closing",
        "DTS Treasury General Account closing balance; not a weekly average",
        "million USD",
        "business day",
        timedelta(days=4),
    ),
)
BY_KEY = {spec.key: spec for spec in SPECS}


def _source(key, provider, endpoint, keys, policy, eligible):
    return Source(
        source_id=f"macro.original.{key}",
        source_type="original_publisher",
        provider=provider,
        endpoint=endpoint,
        collection_method="Bounded public request; no retry",
        metric_scope=tuple(BY_KEY[k].metric for k in keys),
        timezone="America/New_York",
        publication_semantics="Exact publication unknown unless explicitly supplied; reference date never availability",
        revision_behavior="Append changed rows at acquisition; retain earlier versions in canonical SQLite store",
        polling_frequency="Caller driven; at most one request per source per hour recommended",
        rate_limit="No automatic retry; HTTP 429/Retry-After requires caller cooldown",
        limitations=(
            "Current snapshots do not establish historical vintages or complete coverage",
        ),
        legal_constraints=(
            policy,
            "No endorsement; preserve publisher notices; normalized numeric evidence is a transformation",
        ),
        metadata=(("eligibility", "eligible" if eligible else "pending"),),
    )


H41 = _source(
    "h41",
    "Federal Reserve Board",
    "https://www.federalreserve.gov/releases/h41/",
    tuple(s.key for s in SPECS[:5]),
    "https://www.federalreserve.gov/disclaimer.htm — Board data generally public domain, exceptions apply; cite Board",
    True,
)
RRP = _source(
    "on_rrp",
    "Federal Reserve Bank of New York",
    "https://markets.newyorkfed.org/api/rp/reverserepo/all/results/last/100.json",
    ("on_rrp",),
    "https://www.newyorkfed.org/privacy/termsofuse — automated access/storage/derivatives permitted subject to conditions; preserve notices and terms",
    True,
)
TGA = _source(
    "tga",
    "U.S. Treasury Fiscal Data",
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance",
    ("tga_daily",),
    "Detailed Fiscal Data automation/retention/AI-use terms review pending; public access is not permission",
    False,
)
SOURCES = (H41, RRP, TGA)


def _aware(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("acquisition time must be timezone-aware")
    return value.astimezone(UTC)


def _number(raw):
    try:
        value = Decimal(str(raw).replace(",", "").replace(" ", "").replace("\xa0", ""))
    except InvalidOperation as exc:
        raise MarketDataCollectionError("Invalid liquidity number") from exc
    if not value.is_finite() or value < 0:
        raise MarketDataCollectionError("Liquidity value must be finite and nonnegative")
    return format(value, "f")


def _observation(
    source,
    key,
    reference_date,
    raw,
    retrieved_at,
    url,
    *,
    extra=None,
    publication=None,
    subject="US",
):
    spec = BY_KEY[key]
    event_time = datetime.combine(reference_date, datetime.min.time(), ZoneInfo("America/New_York"))
    if reference_date > retrieved_at.astimezone(ZoneInfo("America/New_York")).date():
        raise MarketDataCollectionError("Future liquidity reference date")
    payload = {
        "value": _number(raw),
        "units": spec.units,
        "frequency": spec.frequency,
        "definition": spec.definition,
        "reference_date": reference_date.isoformat(),
        **(extra or {}),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return Observation(
        observation_id=f"liq:{key}:{subject}:{reference_date}:{digest}:{retrieved_at.isoformat()}",
        source_id=source.source_id,
        subject=subject,
        metric=spec.metric,
        payload=payload,
        event_time=event_time,
        effective_time=event_time,
        publication_time=publication,
        first_seen_time=retrieved_at,
        retrieved_at=retrieved_at,
        raw_reference=url,
        transformations=(Transformation("original_liquidity_normalization", "1"),),
        schema_version="original-liquidity-v1",
        unit=spec.units,
        quality_notes=(
            "Reference time is a New York date marker, not release time",
            "Publication time unknown unless explicitly recorded",
        ),
    )


def _batch(source, observations, retrieved_at, *, failure=None):
    retrieved_at = _aware(retrieved_at)
    observations = tuple(observations)
    records = []
    for metric in source.metric_scope:
        rows = [o for o in observations if o.metric == metric]
        status = (
            CoverageStatus.UNAVAILABLE
            if failure
            else CoverageStatus.PRESENT
            if rows
            else CoverageStatus.UNKNOWN
        )
        detail = (
            failure
            or f"{len(rows)} usable rows; snapshot only, intervening dates/holidays not certified complete"
        )
        # No invented IDs for unchanged rows that the store deduplicates.
        records.append(
            CoverageRecord(
                f"{source.source_id}:{metric}:{retrieved_at.isoformat()}",
                source.source_id,
                "US",
                metric,
                retrieved_at,
                status,
                detail,
            )
        )
    return MarketDataBatch(observations, (), retrieved_at, tuple(records), (source,))


class _Cells(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.active = None
        self.parts = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "p"}:
            self.text.append(" ")
            if self.active:
                self.parts.append(" ")
        if tag in {"td", "th"}:
            self.active = dict(attrs).get("id")
            self.parts = []

    def handle_data(self, data):
        self.text.append(data)
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.active:
            if self.active in self.cells:
                raise MarketDataCollectionError("Duplicate H.4.1 cell identifier")
            self.cells[self.active] = " ".join("".join(self.parts).split())
            self.active = None


def parse_h41_html(body: str, *, release_date: date, retrieved_at: datetime) -> MarketDataBatch:
    """Validate labeled publisher cells, never positional guesses across tables."""
    retrieved_at = _aware(retrieved_at)
    if release_date > retrieved_at.astimezone(ZoneInfo("America/New_York")).date():
        raise MarketDataCollectionError("Future H.4.1 release date")
    parser = _Cells()
    parser.feed(body)
    cells = parser.cells
    plain = " ".join(" ".join(parser.text).split())
    if "Millions of dollars" not in plain or release_date.strftime("%B") not in plain:
        raise MarketDataCollectionError("H.4.1 units/release date missing")
    release_match = re.search(r"Release Date:\s*([A-Za-z]+ \d{1,2}, \d{4})", plain)
    if not release_match or datetime.strptime(release_match[1], "%B %d, %Y").date() != release_date:
        raise MarketDataCollectionError("H.4.1 release date mismatch")
    if cells.get("t2h1c2") != "Averages of daily figures":
        raise MarketDataCollectionError("H.4.1 average column changed")
    try:
        reference = datetime.strptime(cells["t2h1c3"], "Wednesday %b %d, %Y").date()
        average = datetime.strptime(cells["t2h2c1"], "Week ended %b %d, %Y").date()
        assets_date = datetime.strptime(cells["t7h1c3"], "Wednesday %b %d, %Y").date()
    except (KeyError, ValueError) as exc:
        raise MarketDataCollectionError("H.4.1 reference headers changed") from exc
    if (
        reference != average
        or reference != assets_date
        or reference.weekday() != 2
        or reference > release_date
    ):
        raise MarketDataCollectionError("H.4.1 date columns disagree")
    url = f"{H41.endpoint}{release_date:%Y%m%d}/"
    rows = []
    for prefix, label, selections in (
        ("t7r25", "Total assets", (("c3", "assets"),)),
        (
            "t2r16",
            "Reserve balances with Federal Reserve Banks",
            (("c2", "reserves_avg"), ("c5", "reserves_wed")),
        ),
        ("t2r8", "U.S. Treasury, General Account", (("c2", "tga_avg"), ("c5", "tga_wed"))),
    ):
        if cells.get(prefix + "c1") != label:
            raise MarketDataCollectionError(f"H.4.1 row changed: {label}")
        for column, key in selections:
            raw = cells.get(prefix + column)
            if raw in {None, "", "N/A", "ND", "."}:
                continue
            rows.append(
                _observation(
                    H41,
                    key,
                    reference,
                    raw,
                    retrieved_at,
                    url,
                    extra={
                        "release_date": release_date.isoformat(),
                        "publisher_cell": prefix + column,
                    },
                )
            )
    return _batch(H41, rows, retrieved_at)


def parse_on_rrp_json(body: str, *, retrieved_at: datetime) -> MarketDataBatch:
    """Keep only Results / Overnight / Treasury, in the API's dollar units."""
    retrieved_at = _aware(retrieved_at)
    try:
        operations = json.loads(body)["repo"]["operations"]
        if not isinstance(operations, list):
            raise ValueError("operations must be a list")
        rows, seen = [], {}
        for op in operations:
            if (
                op["auctionStatus"] != "Results"
                or op["term"] != "Overnight"
                or op["operationType"] != "Reverse Repo"
            ):
                continue
            if not op["details"] or any(d["securityType"] != "Treasury" for d in op["details"]):
                continue
            amount = _number(op["totalAmtAccepted"])
            if Decimal(amount) != sum(Decimal(_number(d["amtAccepted"])) for d in op["details"]):
                raise ValueError("accepted amount does not reconcile")
            op_id = op["operationId"]
            if not isinstance(op_id, str) or not op_id or len(op_id) > 100:
                raise ValueError("invalid operation ID")
            if op_id in seen:
                if seen[op_id] != op:
                    raise ValueError("conflicting duplicate operation")
                continue
            seen[op_id] = op
            # releaseTime is the offer opening, NOT result publication.
            updated = datetime.strptime(op["lastUpdated"], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=ZoneInfo("America/New_York")
            )
            if updated > retrieved_at:
                raise ValueError("future publisher update time")
            rows.append(
                _observation(
                    RRP,
                    "on_rrp",
                    date.fromisoformat(op["operationDate"]),
                    amount,
                    retrieved_at,
                    RRP.endpoint,
                    subject=op_id,
                    extra={
                        "operation_id": op_id,
                        "publisher_last_updated": updated.isoformat(),
                        "attribution": f"© {updated.year} Federal Reserve Bank of New York. Content from the New York Fed subject to the Terms of Use at newyorkfed.org.",
                        "terms_url": "https://www.newyorkfed.org/privacy/termsofuse",
                        "transformation_notice": "Normalized numeric evidence; no endorsement; publisher update time is not proven publication time",
                    },
                    publication=None,
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise MarketDataCollectionError("Malformed ON RRP results") from exc
    return _batch(RRP, rows, retrieved_at)


def parse_tga_json(body: str, *, retrieved_at: datetime) -> MarketDataBatch:
    """Post-redesign closing-label row uses open_today_bal. Older schema is gated."""
    retrieved_at = _aware(retrieved_at)
    try:
        document = json.loads(body)
        if document["meta"]["dataFormats"]["open_today_bal"] != "$1,000,000":
            raise ValueError("unverified TGA units")
        rows, seen = [], {}
        for row in document["data"]:
            if row["account_type"] != "Treasury General Account (TGA) Closing Balance":
                continue
            reference = date.fromisoformat(row["record_date"])
            if reference < date(2022, 4, 1):
                raise ValueError("historical DTS schema not validated")
            raw = row["open_today_bal"]
            if raw in {None, "null", "", "N/A"}:
                continue
            value = _number(raw)
            if reference in seen:
                if seen[reference] != value:
                    raise ValueError("conflicting duplicate TGA date")
                continue
            seen[reference] = value
            rows.append(
                _observation(
                    TGA,
                    "tga_daily",
                    reference,
                    value,
                    retrieved_at,
                    TGA.endpoint,
                    extra={
                        "account_type": row["account_type"],
                        "publisher_field": "open_today_bal",
                        "eligibility": "pending; parser correctness does not authorize collection/AI use",
                    },
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise MarketDataCollectionError("Malformed/unsupported DTS closing balance") from exc
    return _batch(TGA, rows, retrieved_at)


class LiquidityCollector:
    """One bounded call, no retries/redirects; failures persist as coverage batches.

    TGA collection is deliberately gated pending terms review. Parsers remain
    available for deterministic schema validation, not as an eligibility bypass.
    """

    def __init__(self, *, session=None, clock=None):
        self.session = session or requests.Session()
        self.clock = clock or (lambda: datetime.now(UTC))

    def collect(self, key: str, *, release_date: date | None = None) -> MarketDataBatch:
        source = {"h41": H41, "on_rrp": RRP, "tga": TGA}[key]
        if source is TGA:
            return _batch(
                source,
                (),
                self.clock(),
                failure="Eligibility pending: no request; automation/retention/AI-use review required",
            )
        if source is H41 and release_date is None:
            raise ValueError("H.4.1 requires an explicit dated release")
        url = f"{source.endpoint}{release_date:%Y%m%d}/" if source is H41 else source.endpoint
        try:
            with self.session.get(
                url, timeout=(3.05, 15), stream=True, allow_redirects=False
            ) as response:
                response.raise_for_status()
                if response.status_code != 200:
                    raise MarketDataCollectionError(
                        f"Unexpected HTTP status {response.status_code}"
                    )
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 2_000_000:
                        raise MarketDataCollectionError("Liquidity response exceeds 2 MB")
                    chunks.append(chunk)
                body = b"".join(chunks).decode("utf-8-sig")
            acquired = _aware(self.clock())
            if source is H41:
                return parse_h41_html(body, release_date=release_date, retrieved_at=acquired)
            return parse_on_rrp_json(body, retrieved_at=acquired)
        except (requests.RequestException, MarketDataCollectionError, UnicodeError) as exc:
            return _batch(
                source,
                (),
                self.clock(),
                failure=f"{type(exc).__name__}: request/parser failed; no value inferred; caller must honor cooldown/Retry-After",
            )


def selected_liquidity(
    view: InformationView,
) -> tuple[tuple[LiquiditySpec, Observation | None], ...]:
    """One latest eligible reference per metric; revisions are resolved by view_at."""
    result = []
    for spec in SPECS:
        source = next(s for s in SOURCES if spec.metric in s.metric_scope)
        candidates = [
            o
            for o in view.observations
            if o.metric == spec.metric
            and o.source_id == source.source_id
            and o.schema_version == "original-liquidity-v1"
            and o.event_time <= view.decision_time
            and o.is_available_at(view.decision_time)
        ]
        # Pending sources must not become analyst evidence through direct parser use.
        if dict(source.metadata)["eligibility"] != "eligible":
            candidates = []
        result.append(
            (
                spec,
                max(
                    candidates,
                    key=lambda o: (o.event_time, o.available_at, o.observation_id),
                    default=None,
                ),
            )
        )
    return tuple(result)


def render_liquidity(view: InformationView) -> list[str]:
    lines = []
    for spec, row in selected_liquidity(view):
        if row is None:
            lines.append(
                f"- {spec.definition}: unknown; {spec.units}; no eligible evidence (daily Treasury TGA eligibility pending)"
                if spec.key == "tga_daily"
                else f"- {spec.definition}: unknown; {spec.units}; no eligible evidence"
            )
            continue
        stale = view.decision_time - row.event_time > spec.stale_after
        lines.append(
            f"- {spec.definition}: {row.payload['value']} {spec.units}; {spec.frequency}; {'stale' if stale else 'fresh'}; observed date: {row.payload['reference_date']}; publication: {row.publication_time.isoformat() if row.publication_time else 'unknown'}; available: {row.available_at.isoformat()}; evidence: {row.observation_id}"
        )
        if spec.key == "on_rrp":
            lines.append(
                f"- {row.payload['attribution']} Terms: {row.payload['terms_url']}. Normalized numeric evidence; no endorsement."
            )
    return lines
