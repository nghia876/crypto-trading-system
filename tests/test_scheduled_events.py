"""Point-in-time scheduled macro event contract tests."""

from datetime import UTC, datetime, timedelta

import pytest

from tradingagents.information import (
    BLS_RELEASE_CALENDAR_SOURCE,
    FOMC_CALENDAR_SOURCE,
    FOMCCalendarCollector,
    InformationView,
    MarketDataBatch,
    MarketDataCollectionError,
    ScheduledMacroEvent,
    SQLiteInformationStore,
    build_btc_market_state,
    parse_fomc_calendar,
    upcoming_macro_events,
)

BASE = datetime(2026, 1, 1, tzinfo=UTC)

FOMC_HTML = """<!doctype html>
<h4><a id="current">2026 FOMC Meetings</a></h4>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month"><strong>January</strong></div>
  <div class="fomc-meeting__date">27-28</div>
</div>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month"><strong>March</strong></div>
  <div class="fomc-meeting__date">17-18*</div>
  <div>Statement: <a href="/statement">HTML</a></div>
</div>
<h4><a id="future">2027 FOMC Meetings (Tentative)</a></h4>
<div class="row fomc-meeting">
  <div class="fomc-meeting__month"><strong>January</strong></div>
  <div class="fomc-meeting__date">26-27</div>
</div>
<p>Note: A two-day meeting is scheduled for January 25-26, 2028. Each meeting date is tentative until confirmed at the meeting immediately preceding it.</p>
"""


def make_event(*, retrieved_at: datetime, scheduled_at: datetime):
    return ScheduledMacroEvent(
        event_id="bls:cpi:2026-02",
        title="Consumer Price Index release",
        event_type="cpi_release",
        scheduled_at=scheduled_at,
        source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://www.bls.gov/schedule/news_release/cpi.htm",
    ).to_observation(retrieved_at=retrieved_at)


def test_future_event_is_visible_only_after_local_first_seen_time():
    retrieved_at = BASE + timedelta(hours=1)
    scheduled_at = BASE + timedelta(days=30)
    event = make_event(retrieved_at=retrieved_at, scheduled_at=scheduled_at)

    before = upcoming_macro_events(
        InformationView(retrieved_at - timedelta(microseconds=1), (event,), ())
    )
    after = upcoming_macro_events(InformationView(retrieved_at, (event,), ()))

    assert before == ()
    assert after == (event,)
    assert event.event_time == scheduled_at
    assert event.available_at == retrieved_at
    assert build_btc_market_state(
        InformationView(retrieved_at, (event,), ())
    ).upcoming_macro_events == (event,)
    assert (
        build_btc_market_state(
            InformationView(retrieved_at - timedelta(microseconds=1), (event,), ())
        ).upcoming_macro_events
        == ()
    )


def test_scheduled_event_stops_being_upcoming_at_event_time():
    scheduled_at = BASE + timedelta(days=1)
    event = make_event(retrieved_at=BASE, scheduled_at=scheduled_at)

    visible = upcoming_macro_events(InformationView(scheduled_at, (event,), ()))

    assert visible == ()


def test_publication_time_cannot_make_an_event_available_before_observed():
    retrieved_at = BASE + timedelta(hours=1)
    publication_time = retrieved_at + timedelta(hours=1)
    scheduled_at = BASE + timedelta(days=1)
    event = ScheduledMacroEvent(
        event_id="fomc:2026-01",
        title="FOMC meeting",
        event_type="fomc_meeting",
        scheduled_at=scheduled_at,
        source=FOMC_CALENDAR_SOURCE,
        raw_reference="https://example.test/calendar",
    ).to_observation(retrieved_at=retrieved_at, publication_time=publication_time)

    assert upcoming_macro_events(InformationView(retrieved_at, (event,), ())) == ()
    assert upcoming_macro_events(InformationView(publication_time, (event,), ())) == (event,)


def test_fomc_calendar_parser_preserves_date_ranges_tentative_status_and_availability():
    retrieved_at = datetime(2026, 1, 3, tzinfo=UTC)

    batch = parse_fomc_calendar(FOMC_HTML, retrieved_at=retrieved_at)

    assert len(batch.observations) == 4
    first, current, future, next_year = batch.observations
    assert first.payload["event_id"] == "fomc:2026:meeting-01"
    assert first.payload["tentative"] is False
    assert current.payload["event_id"] == "fomc:2026:meeting-02"
    assert current.payload["time_precision"] == "date"
    assert current.payload["scheduled_at"].startswith("2026-03-17T00:00:00-04:00")
    assert current.payload["scheduled_end_at"].startswith("2026-03-19T00:00:00-04:00")
    assert current.payload["tentative"] is True
    assert future.payload["event_id"] == "fomc:2027:meeting-01"
    assert future.payload["tentative"] is True
    assert next_year.payload["event_id"] == "fomc:2028:meeting-01"
    assert next_year.payload["scheduled_at"].startswith("2028-01-25")
    assert next_year.payload["tentative"] is True
    assert all(item.available_at == retrieved_at for item in batch.observations)


def test_fomc_calendar_parser_rejects_unrecognized_html():
    with pytest.raises(MarketDataCollectionError, match="no recognizable meeting rows"):
        parse_fomc_calendar("<html><body>service unavailable</body></html>", retrieved_at=BASE)


def test_date_precision_event_remains_upcoming_through_its_final_day():
    retrieved_at = BASE
    event = ScheduledMacroEvent(
        event_id="fomc:2026-01-27",
        title="FOMC meeting",
        event_type="fomc_meeting",
        scheduled_at=datetime(2026, 1, 27, tzinfo=UTC),
        scheduled_end_at=datetime(2026, 1, 29, tzinfo=UTC),
        time_precision="date",
        source=FOMC_CALENDAR_SOURCE,
        raw_reference="https://example.test/fomc",
    ).to_observation(retrieved_at=retrieved_at)

    same_day = datetime(2026, 1, 28, 12, tzinfo=UTC)
    after_window = datetime(2026, 1, 29, tzinfo=UTC)
    assert upcoming_macro_events(InformationView(same_day, (event,), ())) == (event,)
    assert upcoming_macro_events(InformationView(after_window, (event,), ())) == ()


def test_fomc_collector_fetches_public_calendar_and_uses_utc_clock():
    class Response:
        text = FOMC_HTML

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        calls = []

        def get(self, url, *, timeout):
            self.calls.append((url, timeout))
            return Response()

    session = Session()
    retrieved_at = datetime(2026, 1, 3, tzinfo=UTC)
    batch = FOMCCalendarCollector(session=session, clock=lambda: retrieved_at).collect()

    assert session.calls == [(FOMC_CALENDAR_SOURCE.endpoint, (3.05, 10.0))]
    assert len(batch.observations) == 4
    assert all(item.available_at == retrieved_at for item in batch.observations)


def test_fomc_date_change_replays_latest_schedule_under_stable_meeting_id(tmp_path):
    first_seen = BASE
    moved_seen = BASE + timedelta(days=1)
    first = parse_fomc_calendar(FOMC_HTML, retrieved_at=first_seen)
    moved = parse_fomc_calendar(
        FOMC_HTML.replace(
            'March</strong></div>\n  <div class="fomc-meeting__date">17-18*',
            'March</strong></div>\n  <div class="fomc-meeting__date">18-19*',
        ),
        retrieved_at=moved_seen,
    )
    store = SQLiteInformationStore(tmp_path / "fomc-reschedule.sqlite3")
    store.append(first)
    store.append(moved)
    reopened = SQLiteInformationStore(store.path)

    before_change = upcoming_macro_events(reopened.view_at(first_seen))
    after_change = upcoming_macro_events(reopened.view_at(moved_seen))

    march_before = next(
        item for item in before_change if item.payload["event_id"] == "fomc:2026:meeting-02"
    )
    march_after = next(
        item for item in after_change if item.payload["event_id"] == "fomc:2026:meeting-02"
    )
    assert march_before.payload["scheduled_at"].startswith("2026-03-17")
    assert march_after.payload["scheduled_at"].startswith("2026-03-18")
    assert sum(item.payload["event_id"] == "fomc:2026:meeting-02" for item in after_change) == 1


def test_naive_event_or_retrieval_times_are_rejected():
    with pytest.raises(ValueError, match="scheduled_at"):
        ScheduledMacroEvent(
            "event", "title", "type", datetime(2026, 1, 2), BLS_RELEASE_CALENDAR_SOURCE, "url"
        )

    with pytest.raises(ValueError, match="retrieved_at"):
        ScheduledMacroEvent(
            "event", "title", "type", BASE + timedelta(days=1), BLS_RELEASE_CALENDAR_SOURCE, "url"
        ).to_observation(retrieved_at=datetime(2026, 1, 1))

    valid_event = ScheduledMacroEvent(
        "event", "title", "type", BASE + timedelta(days=1), BLS_RELEASE_CALENDAR_SOURCE, "url"
    )
    with pytest.raises(ValueError, match="first_seen_time"):
        valid_event.to_observation(retrieved_at=BASE, first_seen_time=datetime(2026, 1, 1))


def test_store_preserves_simultaneous_events_and_replays_reschedules_and_cancellations(tmp_path):
    database = tmp_path / "events.sqlite3"
    store = SQLiteInformationStore(database)
    first_seen = BASE + timedelta(hours=1)
    original_time = BASE + timedelta(days=10)
    moved_time = BASE + timedelta(days=12)
    first = make_event(retrieved_at=first_seen, scheduled_at=original_time)
    simultaneous = ScheduledMacroEvent(
        event_id="bls:employment:2026-01",
        title="Employment Situation",
        event_type="employment_release",
        scheduled_at=original_time,
        source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://www.bls.gov/schedule/news_release/empsit.htm",
    ).to_observation(retrieved_at=first_seen)
    store.append(MarketDataBatch((first, simultaneous), (), first_seen))

    before_update = store.view_at(first_seen)
    assert len(upcoming_macro_events(before_update)) == 2

    update_time = first_seen + timedelta(days=1)
    rescheduled = ScheduledMacroEvent(
        event_id="bls:cpi:2026-02",
        title="Consumer Price Index release",
        event_type="cpi_release",
        scheduled_at=moved_time,
        source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://www.bls.gov/schedule/news_release/cpi.htm",
    ).to_observation(retrieved_at=update_time)
    cancelled = ScheduledMacroEvent(
        event_id="bls:employment:2026-01",
        title="Employment Situation",
        event_type="employment_release",
        scheduled_at=original_time,
        source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://www.bls.gov/schedule/news_release/empsit.htm",
        status="cancelled",
    ).to_observation(retrieved_at=update_time)
    store.append(MarketDataBatch((rescheduled, cancelled), (), update_time))

    reopened = SQLiteInformationStore(database)
    assert upcoming_macro_events(reopened.view_at(first_seen)) == (first, simultaneous)
    after_update = upcoming_macro_events(reopened.view_at(update_time))
    assert after_update == (rescheduled,)
    assert after_update[0].payload["scheduled_at"] == moved_time.isoformat()
