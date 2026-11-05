"""Diagnostic boundaries: offline evidence cannot certify sustained operation."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_broad_news import T, rss, session_for
from tradingagents.information.evidence_review import digest
from tradingagents.information.news import poll_once
from tradingagents.information.operational_review import prepare_packet
from tradingagents.information.readiness import (
    audit_packet,
    classify_source,
    main,
    readiness_report,
)
from tradingagents.information.source_health import health_report
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import ELIGIBLE_CONFIGS


def packet_store(tmp_path):
    store = SQLiteInformationStore(tmp_path / "test.sqlite3")
    config = ELIGIBLE_CONFIGS[0]
    for index in range(2):
        poll_once(store, (config,), poll_id=str(index), clock=lambda: T,
                  session=session_for(rss(url=config.source.endpoint + f"?article={index}")))
    rows = store.view_at(T).observations
    packet = prepare_packet(store, [{"evidence_ids": [r.observation_id for r in rows]}],
                            cutoff=T, checks={})
    return store, packet


@pytest.mark.parametrize("transport,content,gap,expected", [
    ("responding", "fresh_24h", False, "fresh_24h"),
    ("responding", "stale_publication", False, "POSSIBLY_INACTIVE"),
    ("empty", "empty_or_unavailable", False, "POSSIBLY_INACTIVE"),
    ("failed", "stale_publication", False, "stale_publication"),
    ("responding", "fresh_24h", True, "fresh_24h"),
])
def test_independent_health_axes(transport, content, gap, expected):
    result = classify_source({"transport": transport, "content": content,
                              "collection_unobserved": gap})
    assert result["collection"] == ("UNKNOWN" if gap else "OBSERVED_RECENTLY")
    assert result["content"] == expected
    assert result["broken_publisher"] == "NOT PROVEN"
    if transport == "failed":
        assert result["transport"] == "FAILURE_OBSERVED"


def test_readonly_reopen_and_no_go_even_with_valid_packet(tmp_path, capsys):
    store, packet = packet_store(tmp_path)
    before = Path(store.path).read_bytes()
    result = readiness_report(store, packet, cutoff=T)
    assert result["decision"] == "NO-GO"
    assert result["review"]["original_versions_valid_at_cutoff"]
    assert result["review"]["pending_pairs"] == 1
    assert result["review"]["human_declared_pairs"] == 0
    assert result["sqlite_integrity"] == ["ok"]
    assert result["replay_probe"]["early_narrative_records"] == 0
    assert result["replay_probe"]["late_narrative_records"] == 2
    assert result["replay_probe"]["reopened_health_identical"]
    from tradingagents.information.sources import WORLD_DISCOVERY_DOMAINS
    assert {r["family"] for r in result["world_families"]} == set(WORLD_DISCOVERY_DOMAINS)
    assert result == readiness_report(SQLiteInformationStore(store.path, read_only=True), packet, cutoff=T)
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    assert main(["--store", store.path, "--packet", str(path), "--as-of", T.isoformat()]) == 0
    assert json.loads(capsys.readouterr().out) == result
    assert before == Path(store.path).read_bytes()


def test_packet_tamper_future_and_declared_human_not_authenticated(tmp_path):
    store, packet = packet_store(tmp_path)
    early = audit_packet(store, packet, T-timedelta(microseconds=1))
    assert not early["original_versions_valid_at_cutoff"]
    packet["pairs"][0]["review_kind"] = "human_declared"
    report = audit_packet(store, packet, T)
    assert not report["packet_hash_valid"]
    assert report["human_declared_pairs"] == 1
    assert not report["human_participation_authenticated"]
    packet["packet_sha256"] = digest({k: v for k, v in packet.items() if k != "packet_sha256"})
    assert audit_packet(store, packet, T)["packet_hash_valid"]
    packet["pairs"][0]["article_sha256"][0] = "invalid"
    assert not audit_packet(store, packet, T)["original_versions_valid_at_cutoff"]


def test_pit_and_source_independence_never_inferred(tmp_path):
    store, packet = packet_store(tmp_path)
    early = readiness_report(store, packet, cutoff=T-timedelta(microseconds=1))
    late = readiness_report(store, packet, cutoff=T+timedelta(days=2))
    assert early["journal"]["attempts_all_fingerprints"] == 0
    assert late["journal"]["attempts_all_fingerprints"] == 2
    assert late["metadata_totals"]["source_url_records"] == 2
    assert all(s["classification"]["collection"] == "UNKNOWN" for s in late["health"]["sources"])
    assert "UNVERIFIED" in late["coverage"]["independent_original_origins"]
    assert any(g["status"] == "BLOCKED" and "Rights" in g["requirement"] for g in late["checklist"])
    # Diagnostic classifications do not change the underlying health contract.
    assert health_report(store, ELIGIBLE_CONFIGS, cutoff=T)["sources"][0]["attempts"] == 2
