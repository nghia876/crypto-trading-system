"""Phase 3.3 acceptance: bounded suggestions, open gaps and immutable PIT audits."""

from dataclasses import replace
from datetime import timedelta

import pytest
import requests

from tests.test_broad_news import rss, session_for
from tests.test_claim_lifecycle import T, article, persist
from tradingagents.information.claim_lifecycle import claim_lifecycle, record_claim_assertion
from tradingagents.information.event_intelligence import (
    candidate_history,
    candidate_prompt,
    evidence_gaps,
    record_event_candidates,
    research_once,
    research_plan,
    suggest_event_links,
)
from tradingagents.information.store import SQLiteInformationStore


def drought(key, text="Drought threatens Colorado farmland irrigation", **kwargs):
    row = article(key, text, **kwargs)
    return replace(row, payload=dict(row.payload) | {"domain": "DROUGHT_WATER"})


def test_independently_sourced_drought_suggested_without_btc_or_support(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(
        store,
        drought("a", source="agency"),
        drought("b", "Colorado irrigation farmland drought warning", source="regional"),
    )
    snapshot = record_event_candidates(store, now=T)
    candidate = snapshot.payload["candidates"][0]
    assert tuple(candidate["evidence_ids"]) == ("a", "b")
    assert candidate["status"] == "candidate_requires_review"
    assert tuple(candidate["event_types"]) == ("drought",)
    assert tuple(candidate["shared_anchors"]) == ("colorado",)
    assert {s["id"] for s in candidate["sources"]} == {"agency", "regional"}
    assert candidate["sources"][0]["available_at"] == T.isoformat()
    assert claim_lifecycle(store.view_at(T), "a")["supporting"] == []
    assert "BTC" not in str(snapshot.payload)
    assert candidate_prompt(store.view_at(T), drought("a"))


@pytest.mark.parametrize(
    "titles",
    [
        ("Flood damages homes in Lahore Pakistan", "Flood damages homes in Karachi Pakistan"),
        ("Acapulco Mexico floods damage homes", "Monterrey Mexico floods damage homes"),
        (
            "Monsoon Flood Damages Homes In Lahore India",
            "Monsoon Flood Damages Homes In Karachi India",
        ),
    ],
)
def test_unrelated_floods_same_country_never_linked(tmp_path, titles):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, article("a", titles[0]), article("b", titles[1]))
    assert suggest_event_links(store.view_at(T))["candidates"] == []


def test_explicit_disjoint_locations_and_time_or_type_veto(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    a = drought("a")
    b = drought("b")
    persist(
        store,
        replace(a, payload=dict(a.payload) | {"locations": ["north"]}),
        replace(b, payload=dict(b.payload) | {"locations": ["south"]}),
    )
    assert not suggest_event_links(store.view_at(T))["candidates"]
    other = SQLiteInformationStore(tmp_path / "time.db")
    persist(other, drought("a"), drought("b", time=T + timedelta(days=4)))
    assert not suggest_event_links(other.view_at(T + timedelta(days=4)))["candidates"]
    third = SQLiteInformationStore(tmp_path / "type.db")
    persist(third, drought("a"), drought("b", text="Flood threatens Colorado farmland irrigation"))
    assert not suggest_event_links(third.view_at(T))["candidates"]


def test_syndication_and_reacquisition_add_no_independent_support(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(
        store,
        *(
            replace(
                drought(k),
                payload=dict(drought(k).payload)
                | {"publisher_group": "shared-wire", "syndication": "reported_copy"},
            )
            for k in ("a", "b", "c")
        ),
    )
    record_claim_assertion(
        store,
        claim_id="a",
        kind="syndication",
        evidence_ids=("a",),
        target_ids=("b",),
        recorded_at=T,
        rationale="Same wire origin",
    )
    record_event_candidates(store, now=T)
    assert "independent_origin_evidence_missing" in evidence_gaps(store.view_at(T), ["a", "b", "c"])
    assert claim_lifecycle(store.view_at(T), "a")["independence"] == "unknown"
    repeat = replace(drought("a"), observation_id="a-repeat", retrieved_at=T + timedelta(hours=1))
    persist(store, repeat)
    result = suggest_event_links(store.view_at(T + timedelta(hours=1)))
    assert result["scanned_records"] == 3
    assert all(len(c["evidence_ids"]) == 2 for c in result["candidates"])
    assert claim_lifecycle(store.view_at(T + timedelta(hours=1)), "a")["supporting"] == []


def test_late_contradiction_correction_and_reopen_identical_candidate_history(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, drought("a"), drought("b"))
    first = record_event_candidates(store, now=T)
    late = T + timedelta(hours=1)
    # Old publication/first-known cannot expose the newly acquired correction early.
    corrected = replace(
        drought("a", "Correction drought threatens Colorado farmland irrigation"),
        observation_id="a-correction",
        retrieved_at=late,
    )
    persist(store, corrected)
    record_claim_assertion(
        store,
        claim_id="a",
        kind="contradiction",
        evidence_ids=("a-correction",),
        recorded_at=late,
        rationale="Reviewed competing report",
    )
    second = record_event_candidates(store, now=late)
    early = store.view_at(T)
    assert candidate_history(early) == (first,)
    assert "correction" not in str(first.payload)
    assert "contradictory_reports_unresolved" not in evidence_gaps(early, ["a"])
    assert tuple(second.payload["candidates"][0]["review_cues"]) == ("correction",)
    assert "contradictory_reports_unresolved" in evidence_gaps(store.view_at(late), ["a"])
    reopened = SQLiteInformationStore(store.path)
    for cutoff in (T - timedelta(seconds=1), T, late):
        assert candidate_history(store.view_at(cutoff)) == candidate_history(
            reopened.view_at(cutoff)
        )
    assert candidate_history(reopened.view_at(late)) == (first, second)
    assert record_event_candidates(reopened, now=late) == second


def test_seed_needs_no_reviewed_membership_and_gaps_remain_open(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, drought("a"))
    plan = research_plan(store.view_at(T), "a")
    assert plan["source_ids"] == ["news.usgs.drought"]
    assert "original_source_evidence_missing" in plan["evidence_gaps"]
    assert "independent_origin_evidence_missing" in plan["evidence_gaps"]
    assert all(q["status"] == "open" and "Colorado" in q["question"] for q in plan["questions"])
    result, _ = research_once(
        store, "a", now=T, clock=lambda: T, session=session_for("<rss><channel/></rss>")
    )
    assert result["candidate_evidence_ids"] == []
    assert result["evidence_gaps"] == plan["evidence_gaps"]
    assert result["truth"] == "unknown"
    assert any(
        r.metric == "narrative.research_attempt"
        for r in SQLiteInformationStore(store.path).view_at(T).observations
    )


@pytest.mark.parametrize("error", ["timeout", "rate_limit"])
def test_failure_research_bounded_no_findings_and_reopen_cooldown(tmp_path, error):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, drought("a"))
    if error == "timeout":
        failure = requests.Timeout("private remote details")
    else:
        response = requests.Response()
        response.status_code = 429
        response.headers["Retry-After"] = "7200"
        failure = requests.HTTPError("private remote details", response=response)
    session = session_for(error=failure)
    result, _ = research_once(store, "a", now=T, session=session, clock=lambda: T, max_sources=1)
    assert session.get.call_count == 1
    assert session.get.call_args.kwargs["timeout"] == (3.05, 10)
    assert session.get.call_args.kwargs["allow_redirects"] is False
    assert result["candidate_evidence_ids"] == []
    assert "private remote details" not in str(store.view_at(T))
    assert result["questions"] and all(q["status"] == "open" for q in result["questions"])
    reopened = SQLiteInformationStore(store.path)
    research_once(reopened, "a", now=T + timedelta(seconds=20), session=session, clock=lambda: T)
    assert session.get.call_count == 1


def test_unsupported_domain_audited_without_network(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, article("health", "Outbreak in remote location"))
    session = session_for(error=AssertionError("must not fetch"))
    result, outcome = research_once(store, "health", now=T, session=session)
    assert not session.get.called and not outcome
    assert result["execution"] == "unsupported_no_eligible_source"
    assert result["evidence_gaps"] and result["candidate_evidence_ids"] == []
    assert any(r.metric == "narrative.research_attempt" for r in store.view_at(T).observations)


def test_record_and_candidate_caps_deterministic(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, *(drought(str(i)) for i in range(132)))
    plan = suggest_event_links(store.view_at(T), max_records=16, max_candidates=3)
    assert plan["scanned_records"] == 16 and plan["omitted_records"] == 116
    assert len(plan["candidates"]) == 3 and plan["omitted_candidates"] == 117
    assert plan == suggest_event_links(
        SQLiteInformationStore(store.path).view_at(T), max_records=16, max_candidates=3
    )
    with pytest.raises(ValueError):
        suggest_event_links(store.view_at(T), max_records=129)


def test_research_acquires_drought_and_records_suggestions(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, drought("a"))
    result, _ = research_once(
        store,
        "a",
        now=T,
        clock=lambda: T,
        session=session_for(
            rss(
                "Drought threatens Colorado farmland irrigation",
                url="https://water.usgs.gov/alerts/colorado",
            )
        ),
    )
    snapshots = candidate_history(store.view_at(T))
    assert result["candidate_snapshot_id"] == snapshots[-1].observation_id
    assert len(snapshots[-1].payload["candidates"]) == 1
    assert result["truth"] == "unknown" and result["evidence_gaps"]


def test_suggest_cli_structured_output_and_no_historical_writes(tmp_path, capsys):
    import json

    from tradingagents.information.event_intelligence import main

    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, drought("a"), drought("b"))
    main(["suggest", "--store", str(store.path)])
    output = json.loads(capsys.readouterr().out)
    assert output["candidates"][0]["evidence_ids"] == ["a", "b"]
    assert isinstance(output["candidates"][0]["sources"][0], dict)
    with pytest.raises(SystemExit):
        main(["suggest", "--store", str(store.path), "--cutoff", T.isoformat()])
    with pytest.raises(SystemExit):
        main(["suggest", "--store", str(tmp_path / "missing.db")])
