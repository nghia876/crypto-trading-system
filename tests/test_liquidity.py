"""Deterministic publisher schemas, acquisition failures and canonical replay."""

import json
from datetime import UTC, date, datetime, timedelta

import pytest
import requests

from tradingagents.information import SQLiteInformationStore
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.liquidity import (
    LiquidityCollector,
    MarketDataCollectionError,
    parse_h41_html,
    parse_on_rrp_json,
    parse_tga_json,
    selected_liquidity,
)

NOW = datetime(2026, 1, 9, 12, tzinfo=UTC)
RELEASE = date(2026, 1, 8)


def h41(assets="6745635"):
    cells = {
        "t2h1c2": "Averages of daily figures",
        "t2h1c3": "Wednesday<br>Jan 07, 2026",
        "t2h2c1": "Week ended<br>Jan 07, 2026",
        "t7h1c3": "Wednesday<br>Jan 07, 2026",
        "t7r25c1": "Total assets",
        "t7r25c2": "(0)",
        "t7r25c3": assets,
        "t2r16c1": "Reserve balances with Federal Reserve Banks",
        "t2r16c2": "2893770",
        "t2r16c5": "2895236",
        "t2r8c1": "U.S. Treasury, General Account",
        "t2r8c2": "999727",
        "t2r8c5": "1015632",
    }
    return (
        "Release Date: January 8, 2026 <p>Millions of dollars</p><table>"
        + "".join(f'<tr><td id="{k}"><span>{v}</span></td></tr>' for k, v in cells.items())
        + "</table>"
    )


def rrp(amount=353000000, **changes):
    op = {
        "operationId": "RP 010826 26",
        "auctionStatus": "Results",
        "operationType": "Reverse Repo",
        "operationDate": "2026-01-08",
        "term": "Overnight",
        "lastUpdated": "2026-01-08 13:15:42",
        "totalAmtAccepted": amount,
        "details": [{"securityType": "Treasury", "amtAccepted": amount}],
        **changes,
    }
    return json.dumps({"repo": {"operations": [op]}})


def tga(value="1052530"):
    return json.dumps(
        {
            "data": [
                {
                    "record_date": "2026-01-08",
                    "account_type": "Treasury General Account (TGA) Closing Balance",
                    "open_today_bal": value,
                    "close_today_bal": "null",
                }
            ],
            "meta": {"dataFormats": {"open_today_bal": "$1,000,000"}},
        }
    )


PARSERS = (
    lambda body, at: parse_h41_html(body, release_date=RELEASE, retrieved_at=at),
    lambda body, at: parse_on_rrp_json(body, retrieved_at=at),
    lambda body, at: parse_tga_json(body, retrieved_at=at),
)


@pytest.mark.parametrize(
    "parser,initial,correction",
    zip(PARSERS, (h41(), rrp(), tga()), (h41("7000000"), rrp(100), tga("100")), strict=True),
)
def test_revisions_restart_and_repeated_batches(tmp_path, parser, initial, correction):
    path = tmp_path / "canonical.db"
    store = SQLiteInformationStore(path)
    batch = parser(initial, NOW)
    store.append(batch)
    store.append(batch)
    assert not store.view_at(NOW - timedelta(microseconds=1)).observations
    before = store.view_at(NOW).observations
    assert len(before) == len(batch.observations)
    later = NOW + timedelta(hours=1)
    store.append(parser(initial, later))  # unchanged poll preserves earliest knowledge
    assert store.view_at(later).observations == before
    revised = parser(correction, later + timedelta(hours=1))
    store.append(revised)
    store.append(revised)  # exact retry of an automatically linked correction
    reopened = SQLiteInformationStore(path)
    assert reopened.view_at(NOW).observations == before
    after = reopened.view_at(later + timedelta(hours=1)).observations
    assert len(after) == len(before)
    assert after != before
    assert any(o.supersedes_observation_id for o in after)


def test_h41_exact_columns_and_unknown_publication():
    batch = PARSERS[0](h41(), NOW)
    assert [o.payload["value"] for o in batch.observations] == [
        "6745635",
        "2893770",
        "2895236",
        "999727",
        "1015632",
    ]
    assert all(
        o.unit == "million USD" and o.publication_time is None and o.available_at == NOW
        for o in batch.observations
    )
    assert batch.observations[0].event_time.utcoffset() == timedelta(hours=-5)
    missing = PARSERS[0](h41("N/A"), NOW)
    assert missing.coverage[0].status == "unknown"


@pytest.mark.parametrize(
    "body",
    [
        h41().replace("Total assets", "Reserve bank credit"),
        h41().replace("Millions", "Billions"),
        h41().replace("Wednesday<br>Jan 07", "Wednesday<br>Jan 14"),
        h41("NaN"),
        h41().replace("January 8", "January 9"),
    ],
)
def test_h41_rejects_schema_or_date_drift(body):
    with pytest.raises(MarketDataCollectionError):
        PARSERS[0](body, NOW)


def test_on_rrp_units_selection_duplicates_and_dst():
    batch = PARSERS[1](rrp(), NOW)
    assert batch.observations[0].payload["value"] == "353000000"
    assert batch.observations[0].unit == "USD"
    assert batch.observations[0].publication_time is None
    assert batch.observations[0].payload["publisher_last_updated"] == "2026-01-08T13:15:42-05:00"
    assert not PARSERS[1](rrp(term="Term"), NOW).observations
    assert not PARSERS[1](
        rrp(details=[{"securityType": "Agency", "amtAccepted": 353000000}]), NOW
    ).observations
    doc = json.loads(rrp())
    doc["repo"]["operations"] *= 2
    assert len(PARSERS[1](json.dumps(doc), NOW).observations) == 1
    summer = rrp(operationDate="2026-07-09", lastUpdated="2026-07-09 13:15:42")
    row = PARSERS[1](summer, datetime(2026, 7, 10, tzinfo=UTC)).observations[0]
    assert row.payload["publisher_last_updated"] == "2026-07-09T13:15:42-04:00"


@pytest.mark.parametrize(
    "body",
    [
        "{}",
        "bad json",
        rrp(-1),
        rrp(float("inf")),
        rrp(details=[{"securityType": "Treasury", "amtAccepted": 1}]),
    ],
)
def test_rrp_malformed_fails_atomically(body):
    with pytest.raises(MarketDataCollectionError):
        PARSERS[1](body, NOW)


def test_tga_closing_label_units_and_pending_eligibility(tmp_path):
    batch = PARSERS[2](tga(), NOW)
    assert batch.observations[0].payload["value"] == "1052530"
    assert batch.observations[0].unit == "million USD"
    assert not PARSERS[2](tga().replace("Closing Balance", "Opening Balance"), NOW).observations
    assert not PARSERS[2](tga("null"), NOW).observations
    for body in (tga().replace("$1,000,000", "$1"), tga().replace("2026-01-08", "2020-01-08")):
        with pytest.raises(MarketDataCollectionError):
            PARSERS[2](body, NOW)
    store = SQLiteInformationStore(tmp_path / "tga.db")
    store.append(batch)
    assert selected_liquidity(store.view_at(NOW))[-1][1] is None


class Session:
    calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        assert kwargs["timeout"] == (3.05, 15)
        raise requests.Timeout()


def test_failure_batches_and_eligibility_no_request(tmp_path):
    session = Session()
    collector = LiquidityCollector(session=session, clock=lambda: NOW)
    store = SQLiteInformationStore(tmp_path / "failure.db")
    for key in ("h41", "on_rrp", "tga"):
        batch = collector.collect(key, release_date=RELEASE)
        assert not batch.observations
        assert all(c.status == "unavailable" for c in batch.coverage)
        store.append(batch)
    assert session.calls == 2
    rendered = render_analysis_information(build_analysis_information(store, NOW))
    assert "unknown" in rendered and "Eligibility pending" in rendered


def test_staleness_and_prompt_budget(tmp_path):
    store = SQLiteInformationStore(tmp_path / "render.db")
    store.append(PARSERS[0](h41(), NOW))
    store.append(PARSERS[1](rrp(), NOW))
    context = render_analysis_information(
        build_analysis_information(store, NOW + timedelta(days=20))
    )
    assert "stale" in context and "6745635 million USD" in context
    assert "BTC spot close: unknown" in context and "Narrative events:" in context
    assert len(context) <= 28000


class Response:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()

    def iter_content(self, size):
        yield self.body


@pytest.mark.parametrize(
    "body,status,expected",
    [
        (rrp().encode(), 200, "present"),
        (b"{}", 200, "unavailable"),
        (b"", 429, "unavailable"),
        (b"x" * 2_000_001, 200, "unavailable"),
        (b"", 302, "unavailable"),
    ],
    ids=["valid", "malformed", "rate-limited", "oversize", "redirect"],
)
def test_collector_bounds_and_parser_failures(body, status, expected):
    class Client:
        calls = 0

        def get(self, url, **kwargs):
            self.calls += 1
            assert not kwargs["allow_redirects"]
            return Response(body, status)

    client = Client()
    batch = LiquidityCollector(session=client, clock=lambda: NOW).collect("on_rrp")
    assert batch.coverage[0].status == expected
    assert client.calls == 1


def test_future_update_and_backfill_dates_fail():
    with pytest.raises(MarketDataCollectionError):
        PARSERS[1](rrp(lastUpdated="2026-01-10 13:15:42"), NOW)
    with pytest.raises(ValueError):
        PARSERS[0](h41(), NOW.replace(tzinfo=None))
