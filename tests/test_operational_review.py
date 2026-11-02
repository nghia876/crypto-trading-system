"""Review forms bind versions without generating judgments or modifying SQLite."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tradingagents.information.operational_review import prepare_packet
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import replay_specimens


def test_real_proposals_neutral_forms_bind_versions_and_no_reviews(tmp_path):
    folder = Path(__file__).parent / "fixtures/phase37"
    data = json.loads((folder / "real_specimens.json").read_text(encoding="utf-8"))
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    replay_specimens(store, data["specimens"])
    # Normalized replay differs in payload from original live versions. Bind its
    # actual IDs for this test only, never rewrite original production proposals.
    view = store.view_at(datetime.fromisoformat(data["cutoff"]))
    rows = list(view.observations)
    proposals = [{"evidence_ids": [rows[0].observation_id, rows[1].observation_id]}]
    before = Path(store.path).read_bytes()
    packet = prepare_packet(store, proposals, cutoff=view.decision_time, checks={})
    assert packet["human_reviews"] == 0
    assert packet["pairs"][0]["label"] == "unknown"
    assert packet["pairs"][0]["reviewer"] is None
    assert set(packet["pairs"][0]["choices"]) == {"same_event", "different_event", "unknown"}
    assert all(a["occurrence_start"] is None and a["location_key"] is None for a in packet["articles"])
    assert "suggested_pair_identity" not in json.dumps(packet)
    assert Path(store.path).read_bytes() == before
    assert prepare_packet(store, proposals, cutoff=view.decision_time, checks={}) == packet
    with pytest.raises(ValueError, match="unavailable"):
        prepare_packet(store, proposals, cutoff=min(r.available_at for r in rows)-timedelta(days=1), checks={})
