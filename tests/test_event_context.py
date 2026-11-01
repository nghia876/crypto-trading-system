"""Reviewed context acceptance and frozen synthetic holdout, never live data."""

import hashlib
import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_claim_lifecycle import T, article, persist
from tradingagents.information.event_context import record_event_context
from tradingagents.information.event_intelligence import (
    record_event_candidates,
    suggest_event_links,
)
from tradingagents.information.store import SQLiteInformationStore

FIXTURE = Path(__file__).parent / "fixtures/event_context_holdout.json"


def review(store, evidence_id, now=T, **context):
    return record_event_context(
        store,
        evidence_id=evidence_id,
        recorded_at=now,
        reviewer="synthetic-test-author",
        provenance="Synthetic contract case; no human review",
        rationale="Stipulated occurrence context, not a pair label",
        **context,
    )


def run_holdout(root):
    data = json.loads(FIXTURE.read_text())
    counts = {p: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for p in ("baseline_v1", "context_v2")}
    outcomes = []
    for family in data["families"]:
        for trial in data["trials"]:
            key = family["family"] + ":" + trial["id"]
            store = SQLiteInformationStore(root / (key.replace(":", "-") + ".db"))
            persist(store, article("a", family["claim"]), article("b", family["claim"]))
            for side in ("a", "b"):
                context = dict(trial[side])
                for field in ("start", "end"):
                    if field in context:
                        context["occurrence_" + field] = T + timedelta(hours=context.pop(field))
                if context:
                    review(store, side, **context)
            view = store.view_at(T)
            result = {"id": key, "label": trial["label"]}
            for policy, enabled in (("baseline_v1", False), ("context_v2", True)):
                actual = suggest_event_links(view, use_reviewed_context=enabled)
                assert actual == suggest_event_links(
                    SQLiteInformationStore(store.path).view_at(T), use_reviewed_context=enabled
                )
                positive = trial["label"] == "same_event"
                outcome = (
                    ("tp" if positive else "fp")
                    if actual["candidates"]
                    else ("fn" if positive else "tn")
                )
                counts[policy][outcome] += 1
                result[policy] = outcome
            outcomes.append(result)
    for values in counts.values():
        values["precision"] = values["tp"] / (values["tp"] + values["fp"])
        values["recall"] = values["tp"] / (values["tp"] + values["fn"])
    return {
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "provenance": data["provenance"],
        "metrics": counts,
        "cases": outcomes,
    }


def test_frozen_synthetic_holdout(tmp_path):
    report = run_holdout(tmp_path)
    assert (
        report["fixture_sha256"]
        == "4120ddff27be3ab44203d9d2e2d234ce34212c1653cb01242e41148bbb4caf1a"
    )
    assert report["metrics"]["baseline_v1"] == {
        "tp": 8,
        "fp": 16,
        "tn": 0,
        "fn": 0,
        "precision": 1 / 3,
        "recall": 1.0,
    }
    assert report["metrics"]["context_v2"] == {
        "tp": 8,
        "fp": 4,
        "tn": 12,
        "fn": 0,
        "precision": 2 / 3,
        "recall": 1.0,
    }


def test_late_context_correction_withdrawal_and_reopen(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(
        store,
        article("a", "Drought reduces Salta reservoir irrigation"),
        article("b", "Drought reduces Salta reservoir irrigation"),
    )
    original = record_event_candidates(store, now=T)
    late = T + timedelta(hours=1)
    review(store, "a", late, episode_key="salta:1")
    b = review(store, "b", late, episode_key="salta:2")
    assert not suggest_event_links(store.view_at(late))["candidates"]
    fixed = review(
        store, "b", late + timedelta(seconds=1), episode_key="salta:1", supersedes=b.observation_id
    )
    assert suggest_event_links(store.view_at(late + timedelta(seconds=1)))["candidates"]
    review(store, "b", late + timedelta(seconds=2), supersedes=fixed.observation_id)
    for cutoff in (T, late, late + timedelta(seconds=1), late + timedelta(seconds=2)):
        assert suggest_event_links(store.view_at(cutoff)) == suggest_event_links(
            SQLiteInformationStore(store.path).view_at(cutoff)
        )
    assert record_event_candidates(store, now=T) == original
    # Article revisions require their own review, no inheritance of older metadata.
    persist(
        store,
        replace(
            article("b", "Drought reduces Salta reservoir irrigation", time=late),
            observation_id="b-v2",
        ),
    )
    assert suggest_event_links(store.view_at(late))["candidates"]


@pytest.mark.parametrize(
    "context",
    [
        {"episode_key": ""},
        {"location_key": "x" * 161},
        {"occurrence_start": T},
        {"occurrence_start": T, "occurrence_end": T - timedelta(seconds=1)},
        {"occurrence_start": T.replace(tzinfo=None), "occurrence_end": T},
        {"occurrence_start": "today", "occurrence_end": T},
    ],
)
def test_invalid_context_rejected(tmp_path, context):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, article("a"))
    with pytest.raises(ValueError):
        review(store, "a", **context)


def test_unavailable_and_implicit_overwrite_refused(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    with pytest.raises(ValueError):
        review(store, "absent")
    persist(store, article("a"))
    review(store, "a", episode_key="one")
    with pytest.raises(ValueError):
        review(store, "a", episode_key="two")


def test_one_sided_context_cannot_veto_and_agreement_cannot_promote(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(
        store,
        article("a", "Drought reduces Salta reservoir irrigation"),
        article("b", "Drought reduces Salta reservoir irrigation"),
        article("c", "Flood damages distant shoreline housing"),
    )
    review(store, "a", episode_key="one")
    review(store, "c", episode_key="one")
    result = suggest_event_links(store.view_at(T))
    assert [c["evidence_ids"] for c in result["candidates"]] == [["a", "b"]]
    assert result["context_veto_count"] == 0


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        print(json.dumps(run_holdout(Path(directory)), indent=2, sort_keys=True))
