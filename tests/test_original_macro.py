"""Original macro schemas, bounded collection and canonical prospective replay."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
import requests

from tradingagents.information import SQLiteInformationStore
from tradingagents.information.binance_spot import MarketDataCollectionError
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.original_macro import (
    BLS,
    BLS_SPECS,
    OriginalMacroCollector,
    parse_bls_json,
    parse_treasury_par_xml,
    selected_original_macro,
)

NOW = datetime(2026, 1, 9, 12, tzinfo=UTC)


def bls(value="325.5"):
    return json.dumps(
        {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": s.key,
                        "data": [
                            {
                                "year": "2025",
                                "period": "M12",
                                "periodName": "December",
                                "value": value,
                                "footnotes": [{"code": "P", "text": "Preliminary."}],
                            }
                        ],
                    }
                    for s in BLS_SPECS
                ]
            },
        }
    )


def treasury(value="4.10"):
    return f"""<feed xmlns="http://www.w3.org/2005/Atom" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"><entry><content><m:properties><d:NEW_DATE m:type="Edm.DateTime">2026-01-08T00:00:00</d:NEW_DATE><d:BC_2YEAR m:type="Edm.Double">{value}</d:BC_2YEAR><d:BC_10YEAR m:type="Edm.Double">4.20</d:BC_10YEAR></m:properties></content></entry></feed>"""


def test_meanings_months_units_and_legacy_result_shape():
    doc = json.loads(bls())
    doc["Results"] = [doc["Results"]]
    batch = parse_bls_json(json.dumps(doc), retrieved_at=NOW)
    assert len(batch.observations) == 4
    for row, spec in zip(batch.observations, BLS_SPECS, strict=True):
        assert row.unit == spec.units and row.metric == spec.metric
        assert row.event_time == datetime(2025, 12, 1, 5, tzinfo=UTC)
        assert row.payload["period_end"] == "2025-12-31"
        assert row.publication_time is None and row.available_at == NOW
        assert row.payload["seasonal_adjustment"] == "SA"
        assert row.payload["footnotes"][0]["code"] == "P"
    assert "not monthly change" in batch.observations[2].payload["definition"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("value", "NaN"),
        ("value", "Infinity"),
        ("value", "-1"),
        ("value", "bad"),
        ("period", "Q01"),
        ("period", "M00"),
        ("year", "2027"),
        ("periodName", "November"),
        ("footnotes", ["bad"]),
        ("footnotes", [{"text": 3}]),
    ],
)
def test_bad_bls_rows_fail_atomically(field, value):
    doc = json.loads(bls())
    doc["Results"]["series"][0]["data"][0][field] = value
    with pytest.raises(MarketDataCollectionError):
        parse_bls_json(json.dumps(doc), retrieved_at=NOW)


@pytest.mark.parametrize("change", ["series", "period", "status", "shape", "json"])
def test_bad_bls_envelopes(change):
    doc = json.loads(bls())
    if change == "series":
        doc["Results"]["series"][0]["seriesID"] = "CUUR0000SA0"
    elif change == "period":
        group = doc["Results"]["series"][0]
        group["data"] *= 2
    elif change == "status":
        doc["status"] = "REQUEST_NOT_PROCESSED"
    elif change == "shape":
        doc["Results"] = []
    with pytest.raises(MarketDataCollectionError):
        parse_bls_json("invalid" if change == "json" else json.dumps(doc), retrieved_at=NOW)


def test_annual_missing_and_absent_series_are_unknown():
    doc = json.loads(bls())
    groups = doc["Results"]["series"]
    groups[0]["data"][0]["period"] = "M13"
    groups[1]["data"][0]["value"] = "-"
    groups.pop()
    batch = parse_bls_json(json.dumps(doc), retrieved_at=NOW)
    assert len(batch.observations) == 1
    assert [c.status.value for c in batch.coverage] == ["unknown", "unknown", "present", "unknown"]


@pytest.mark.parametrize(
    "parser,first,changed",
    [
        (parse_bls_json, bls(), bls("326.7")),
        (parse_treasury_par_xml, treasury(), treasury("4.50")),
    ],
)
def test_restart_corrections_idempotence_no_backdated_vintages(tmp_path, parser, first, changed):
    path = tmp_path / "same.db"
    store = SQLiteInformationStore(path)
    initial = parser(first, retrieved_at=NOW)
    store.append(initial)
    store.append(initial)
    unchanged = parser(first, retrieved_at=NOW + timedelta(minutes=1))
    store.append(unchanged)
    assert not store.view_at(NOW - timedelta(microseconds=1)).observations
    later = NOW + timedelta(hours=1)
    revision = parser(changed, retrieved_at=later)
    store.append(revision)
    store.append(revision)
    reopened = SQLiteInformationStore(path)
    before = reopened.view_at(later - timedelta(microseconds=1)).observations
    after = reopened.view_at(later).observations
    assert {o.observation_id for o in before} == {o.observation_id for o in initial.observations}
    assert len(after) == len(before)
    assert any(o.supersedes_observation_id for o in after)
    assert all(o.available_at == NOW for o in before)


def test_treasury_exact_tenor_units_null_and_gate(tmp_path):
    batch = parse_treasury_par_xml(treasury(), retrieved_at=NOW)
    assert [o.payload["tenor_years"] for o in batch.observations] == [2, 10]
    assert all(o.unit == "percent" for o in batch.observations)
    assert all(o.event_time == datetime(2026, 1, 8, 5, tzinfo=UTC) for o in batch.observations)
    null = treasury().replace('m:type="Edm.Double">4.10', 'm:null="true">')
    assert len(parse_treasury_par_xml(null, retrieved_at=NOW).observations) == 1
    store = SQLiteInformationStore(tmp_path / "gated.db")
    store.append(batch)
    assert not any(row for _, row in selected_original_macro(store.view_at(NOW)))


@pytest.mark.parametrize(
    "body",
    [
        "<!DOCTYPE feed>" + treasury(),
        treasury().replace("BC_2YEAR", "BC_3YEAR"),
        treasury("NaN"),
        treasury().replace("2026-01-08", "2027-01-08"),
        treasury().replace("Edm.Double", "Edm.String"),
        "<feed/>",
    ],
)
def test_treasury_schema_fail_closed(body):
    with pytest.raises(MarketDataCollectionError):
        parse_treasury_par_xml(body, retrieved_at=NOW)


def response(body=None, status=200, headers=None):
    obj = Mock(status_code=status, headers=headers or {})
    obj.__enter__ = Mock(return_value=obj)
    obj.__exit__ = Mock(return_value=False)
    obj.iter_content.return_value = [body if body is not None else bls().encode()]
    return obj


@pytest.mark.parametrize("kind", ["429", "redirect", "large", "timeout", "invalid", "success"])
def test_bounded_requests_backoff_and_failure_coverage(kind):
    session = Mock()
    status = 429 if kind == "429" else 302 if kind == "redirect" else 200
    data = b"x" * 2_000_001 if kind == "large" else b"bad" if kind == "invalid" else None
    session.post.return_value = response(data, status, {"Retry-After": "7200"})
    if kind == "timeout":
        session.post.side_effect = requests.Timeout()
    collector = OriginalMacroCollector(session=session, clock=lambda: NOW)
    batch = collector.collect()
    assert len(batch.observations) == (4 if kind == "success" else 0)
    assert all(
        c.status.value == ("present" if kind == "success" else "unavailable")
        for c in batch.coverage
    )
    assert session.post.call_args.kwargs["timeout"] == (3.05, 15)
    assert session.post.call_args.kwargs["allow_redirects"] is False
    collector.collect()
    assert session.post.call_count == 1
    if kind != "timeout":
        assert collector.next_request_at == NOW + timedelta(hours=2)


def test_gates_no_request_and_explicit_coverage():
    session = Mock()
    collector = OriginalMacroCollector(session=session, clock=lambda: NOW)
    for key, count in (("treasury_par", 2), ("bea", 3)):
        batch = collector.collect(key)
        assert not batch.observations and len(batch.coverage) == count
        assert all(c.status.value == "unavailable" for c in batch.coverage)
    session.post.assert_not_called()
    session.get.assert_not_called()


def test_context_budget_preserves_world_sections_and_macro_ids(tmp_path):
    store = SQLiteInformationStore(tmp_path / "context.db")
    batch = parse_bls_json(bls(), retrieved_at=NOW)
    store.append(batch)
    text = render_analysis_information(build_analysis_information(store, NOW))
    assert len(text) <= 28000
    assert all(o.observation_id in text for o in batch.observations)
    assert "Original-publisher inflation/labor/rates:" in text
    assert "Narrative events:" in text and "unknown" in text
    assert "BLS.gov cannot vouch" in text and "publication: unknown" in text
    assert BLS.source_id in {s.source_id for s in OriginalMacroCollector().registry.all()}


@pytest.mark.parametrize("kind", ["success", "oversize", "redirect", "timeout"])
def test_bounded_existing_calendar_contract(kind):
    from tests.test_scheduled_events import BLS_SCHEDULE_HTML

    session = Mock()
    body = b"x" * 2_000_001 if kind == "oversize" else BLS_SCHEDULE_HTML.encode()
    session.get.return_value = response(body, 302 if kind == "redirect" else 200)
    if kind == "timeout":
        session.get.side_effect = requests.Timeout()
    collector = OriginalMacroCollector(session=session, clock=lambda: NOW)
    batch = collector.collect("bls_calendar")
    assert len(batch.observations) == (2 if kind == "success" else 0)
    assert all(
        o.metric == "macro.scheduled_event" and o.publication_time is None
        for o in batch.observations
    )
    collector.collect("bls_calendar")
    assert session.get.call_count == 1


def test_dst_and_stale_selection(tmp_path):
    doc = json.loads(bls())
    for group in doc["Results"]["series"]:
        group["data"][0].update(year="2025", period="M07", periodName="July")
    batch = parse_bls_json(json.dumps(doc), retrieved_at=NOW)
    assert batch.observations[0].event_time == datetime(2025, 7, 1, 4, tzinfo=UTC)
    store = SQLiteInformationStore(tmp_path / "stale.db")
    store.append(batch)
    assert "stale; publication: unknown" in render_analysis_information(
        build_analysis_information(store, NOW)
    )


@pytest.mark.parametrize("retry", ["Fri, 09 Jan 2026 15:00:00 GMT", "invalid"])
def test_retry_after_http_date_and_invalid_header(retry):
    session = Mock()
    session.post.return_value = response(status=429, headers={"Retry-After": retry})
    collector = OriginalMacroCollector(session=session, clock=lambda: NOW)
    collector.collect()
    assert collector.next_request_at == NOW + timedelta(hours=3 if retry.startswith("Fri") else 1)


@pytest.mark.parametrize(
    "field,value",
    [
        ("year", 2025.9),
        ("year", True),
        ("year", "2025.9"),
        ("value", "1e10000"),
        ("value", "9" * 65),
        ("value", 325.5),
    ],
)
def test_numeric_schema_bounds_reject_coercion_and_expansion(field, value):
    doc = json.loads(bls())
    doc["Results"]["series"][0]["data"][0][field] = value
    with pytest.raises(MarketDataCollectionError):
        parse_bls_json(json.dumps(doc), retrieved_at=NOW)


@pytest.mark.parametrize("key", ["bls", "bls_calendar"])
def test_connection_lost_mid_stream_never_returns_partial_values(tmp_path, key):
    session = Mock()
    reply = response()

    def interrupted_stream(*args):
        yield bls().encode()[:100]
        raise requests.ConnectionError("secret-like remote detail")

    reply.iter_content.side_effect = interrupted_stream
    session.post.return_value = reply
    session.get.return_value = reply
    collector = OriginalMacroCollector(session=session, clock=lambda: NOW)
    batch = collector.collect(key)
    assert not batch.observations
    assert all(c.status.value == "unavailable" for c in batch.coverage)
    assert all("Network failure (ConnectionError)" in c.detail for c in batch.coverage)
    assert all("secret-like" not in c.detail for c in batch.coverage)
    store = SQLiteInformationStore(tmp_path / "interrupted.db")
    store.append(batch)
    reopened = SQLiteInformationStore(store.path)
    assert not reopened.view_at(NOW).observations
    assert reopened.view_at(NOW).coverage


@pytest.mark.parametrize("status", [403, 429, 503])
def test_http_failure_diagnostics_are_distinct_from_network_and_schema(status):
    session = Mock()
    session.post.return_value = response(status=status)
    batch = OriginalMacroCollector(session=session, clock=lambda: NOW).collect()
    assert all(f"HTTP {status}" in c.detail for c in batch.coverage)
