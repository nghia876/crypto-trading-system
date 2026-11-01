"""Evaluation regression, label isolation, unknowns and point-in-time integrity."""

import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_claim_lifecycle import T, article, persist
from tradingagents.information.event_evaluation import evaluate, main, run_fixture
from tradingagents.information.event_intelligence import suggest_event_links
from tradingagents.information.store import SQLiteInformationStore

FIXTURE = Path(__file__).parent / "fixtures/event_pairs_v1.json"


def label(**changes):
    return {
        "evidence_ids": ["a", "b"],
        "label": "same_event",
        "family": "drought",
        "stratum": "correction",
        "reporting_relationship": "cross_source",
        "confidence": "high",
        "review_status": "synthetic_authored",
        "provenance": "Synthetic test author; no human review",
        "rationale": "Same stipulated episode",
    } | changes


def test_frozen_benchmark_and_hard_negatives():
    result = run_fixture(FIXTURE)
    assert len(result["cases"]) == 80
    assert result["metrics"]["overall"] == {
        "tp": 30,
        "fp": 15,
        "tn": 25,
        "fn": 10,
        "precision": 30 / 45,
        "recall": 30 / 40,
    }
    assert len([k for k in result["metrics"] if k.startswith("family:")]) == 8
    assert result["metrics"]["reporting:same_publisher_syndication"]["fp"] == 2
    assert result["metrics"]["stratum:nearby_unrelated"]["tn"] == 25
    assert "no human review" in result["dataset"]


def test_labels_do_not_change_candidates_or_create_assertions(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    persist(
        store,
        article("a", "Drought threatens Colorado farmland irrigation"),
        article("b", "Colorado drought threatens farmland irrigation"),
    )
    before = store.view_at(T)
    candidates = suggest_event_links(before)
    assert evaluate(before, [label()])["metrics"]["overall"]["tp"] == 1
    assert evaluate(before, [label(label="different_event")])["metrics"]["overall"]["fp"] == 1
    assert candidates == suggest_event_links(store.view_at(T))
    assert before == SQLiteInformationStore(store.path).view_at(T)
    assert len(before.observations) == 2


def test_late_old_publication_unavailable_and_unknown_reopen(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    late = T + timedelta(hours=1)
    persist(
        store,
        article("a", "Drought threatens Colorado farmland irrigation"),
        replace(
            article("b", "Correction Colorado drought threatens farmland irrigation"),
            retrieved_at=late,
        ),
    )
    early = evaluate(store.view_at(T), [label()])
    assert early["pairs"][0]["outcome"] == "unavailable" and early["metrics"] == {}
    for cutoff in (T, late):
        assert evaluate(store.view_at(cutoff), [label()]) == evaluate(
            SQLiteInformationStore(store.path).view_at(cutoff), [label()]
        )
    assert (
        evaluate(store.view_at(late), [label(label="unknown")])["pairs"][0]["outcome"] == "unknown"
    )
    assert evaluate(store.view_at(late), [label(review_status="pending")])["metrics"] == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"label": "yes"},
        {"provenance": ""},
        {"review_status": "reviewed"},
        {"confidence": "certain"},
        {"evidence_ids": ["a", "a"]},
    ],
)
def test_invalid_labels_rejected(tmp_path, changes):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    with pytest.raises(ValueError):
        evaluate(store.view_at(T), [label(**changes)])


def test_duplicate_labels_and_missing_store_refused(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    with pytest.raises(ValueError):
        evaluate(store.view_at(T), [label(), label()])
    with pytest.raises(SystemExit):
        main(
            [
                "--store",
                str(tmp_path / "missing"),
                "--labels",
                str(FIXTURE),
                "--cutoff",
                T.isoformat(),
            ]
        )
    assert not (tmp_path / "missing").exists()


def test_fixture_cli_is_offline_and_has_fingerprint(capsys):
    main(["--fixture", str(FIXTURE)])
    result = json.loads(capsys.readouterr().out)
    assert len(result["sha256"]) == 64 and result["metrics"]["overall"]["fn"] == 10


def test_live_cli_opens_read_only_without_changing_store(tmp_path, capsys):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    persist(store, article("a"), article("b"))
    labels = tmp_path / "labels.json"
    labels.write_text(json.dumps([label()]), encoding="utf-8")
    before = Path(store.path).read_bytes()
    main(["--store", store.path, "--labels", str(labels), "--cutoff", T.isoformat()])
    assert json.loads(capsys.readouterr().out)["pairs"][0]["outcome"] == "fn"
    assert before == Path(store.path).read_bytes()
    reader = SQLiteInformationStore(store.path, read_only=True)
    import sqlite3

    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        persist(reader, article("c"))


def test_budget_omissions_not_hidden_from_metrics(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    persist(
        store,
        *(article(str(i), "Drought threatens Colorado farmland irrigation") for i in range(130)),
    )
    result = evaluate(store.view_at(T), [])
    assert result["omitted_records"] == 2
    assert result["omitted_candidates"] > 0
    assert result["unlabeled_predictions"] == 32
