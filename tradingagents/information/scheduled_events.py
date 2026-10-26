"""Point-in-time contracts for scheduled U.S. macro events."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import requests

from tradingagents.information.binance_spot import MarketDataBatch, MarketDataCollectionError
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.sources import Source
from tradingagents.information.store import InformationView

BLS_RELEASE_CALENDAR_SOURCE = Source(
    source_id="macro.us.bls.release_calendar",
    source_type="government_calendar",
    provider="U.S. Bureau of Labor Statistics",
    endpoint="https://www.bls.gov/schedule/news_release/bls.ics",
    collection_method="Public calendar feed; caller-driven retrieval",
    asset_scope=("BTC",),
    metric_scope=("scheduled_macro_event",),
    timezone="America/New_York",
    historical_depth="Upcoming release calendar; historical announcement vintages not established",
    publication_semantics=(
        "Calendar provides scheduled release times; per-event public announcement time is not "
        "established, so local first-seen/retrieval time is the availability bound"
    ),
    revision_behavior=(
        "Schedule versions are append-only; replay selects the latest known version for each source event ID"
    ),
    authentication_required=False,
    reliability="UNKNOWN — timing and access have not been measured by this project",
    limitations=(
        "BLS releases only",
        "Calendar can be updated after initial publication",
        "A local retrieval does not prove when a date first became public",
    ),
)

FOMC_CALENDAR_SOURCE = Source(
    source_id="macro.us.federal_reserve.fomc_calendar",
    source_type="government_calendar",
    provider="Board of Governors of the Federal Reserve System",
    endpoint="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
    collection_method="Public meeting calendar; caller-driven retrieval",
    asset_scope=("BTC",),
    metric_scope=("scheduled_macro_event",),
    timezone="America/New_York",
    historical_depth="Meeting calendar lists current and prior years; event announcement vintages not established",
    publication_semantics=(
        "Calendar lists meeting dates and a page-level last-update date; local retrieval remains the "
        "conservative availability bound"
    ),
    revision_behavior=(
        "Schedule versions are append-only; replay selects the latest known version for each source event ID"
    ),
    authentication_required=False,
    reliability="UNKNOWN — timing and access have not been measured by this project",
    limitations=(
        "FOMC meetings only",
        "Some meeting dates may be tentative until confirmed",
        "Calendar page is not a complete U.S. economic release calendar",
    ),
)


@dataclass(frozen=True, slots=True)
class ScheduledMacroEvent:
    """A normalized calendar entry before it is wrapped as an observation."""

    event_id: str
    title: str
    event_type: str
    scheduled_at: datetime
    source: Source
    raw_reference: str
    status: str = "scheduled"
    scheduled_end_at: datetime | None = None
    time_precision: str = "instant"
    tentative: bool = False

    def __post_init__(self) -> None:
        for name in ("event_id", "title", "event_type", "raw_reference"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.scheduled_at.tzinfo is None or self.scheduled_at.utcoffset() is None:
            raise ValueError("scheduled_at must be timezone-aware")
        if self.scheduled_end_at is not None:
            if self.scheduled_end_at.tzinfo is None or self.scheduled_end_at.utcoffset() is None:
                raise ValueError("scheduled_end_at must be timezone-aware")
            if self.scheduled_end_at <= self.scheduled_at:
                raise ValueError("scheduled_end_at must be later than scheduled_at")
        if self.time_precision not in {"instant", "date"}:
            raise ValueError("time_precision must be 'instant' or 'date'")
        if self.time_precision == "date" and self.scheduled_end_at is None:
            raise ValueError("date-precision events require scheduled_end_at")
        if self.status not in {"scheduled", "cancelled"}:
            raise ValueError("status must be 'scheduled' or 'cancelled'")

    def to_observation(
        self,
        *,
        retrieved_at: datetime,
        first_seen_time: datetime | None = None,
        publication_time: datetime | None = None,
    ) -> Observation:
        """Create a future-event observation without backdating its availability."""
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        first_seen = first_seen_time or retrieved_at
        if first_seen.tzinfo is None or first_seen.utcoffset() is None:
            raise ValueError("first_seen_time must be timezone-aware")
        if publication_time is not None and (
            publication_time.tzinfo is None or publication_time.utcoffset() is None
        ):
            raise ValueError("publication_time must be timezone-aware")

        payload = {
            "event_id": self.event_id,
            "title": self.title,
            "event_type": self.event_type,
            "scheduled_at": self.scheduled_at.isoformat(),
            "time_precision": self.time_precision,
            "tentative": self.tentative,
            "status": self.status,
            "asset_scope": ["BTC"],
        }
        if self.scheduled_end_at is not None:
            payload["scheduled_end_at"] = self.scheduled_end_at.isoformat()
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        return Observation(
            observation_id=f"scheduled:{self.source.source_id}:{self.event_id}:{digest}:{retrieved_at.isoformat()}",
            source_id=self.source.source_id,
            # A calendar event ID, rather than the asset or timestamp, is the
            # identity key. This preserves distinct events at the same time.
            subject=self.event_id,
            metric="macro.scheduled_event",
            payload=payload,
            event_time=self.scheduled_at,
            first_seen_time=first_seen,
            retrieved_at=retrieved_at,
            publication_time=publication_time,
            effective_time=self.scheduled_at,
            raw_reference=self.raw_reference,
            transformations=(Transformation("normalize_scheduled_macro_event", "1"),),
            quality="unknown",
        )


def upcoming_macro_events(view: InformationView) -> tuple[Observation, ...]:
    """Return future macro events known by this view's decision-time cutoff."""
    decision_time = view.decision_time
    if decision_time.tzinfo is None or decision_time.utcoffset() is None:
        raise ValueError("decision_time must be timezone-aware")
    latest_by_event: dict[tuple[str, str], Observation] = {}
    for observation in view.observations:
        if (
            observation.metric != "macro.scheduled_event"
            or not observation.is_available_at(decision_time)
            or "BTC" not in observation.payload.get("asset_scope", ())
        ):
            continue
        event_id = observation.payload.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError(f"observation {observation.observation_id} has invalid event_id")
        key = (observation.source_id, event_id)
        current = latest_by_event.get(key)
        if current is None or (
            observation.available_at,
            observation.observation_id,
        ) > (current.available_at, current.observation_id):
            latest_by_event[key] = observation

    upcoming = []
    for observation in latest_by_event.values():
        if observation.payload.get("status") != "scheduled":
            continue
        scheduled_at_value = observation.payload.get("scheduled_at")
        if not isinstance(scheduled_at_value, str):
            raise ValueError(f"observation {observation.observation_id} has invalid scheduled_at")
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_value)
        except ValueError as exc:
            raise ValueError(
                f"observation {observation.observation_id} has invalid scheduled_at"
            ) from exc
        if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
            raise ValueError(
                f"observation {observation.observation_id} scheduled_at must be timezone-aware"
            )
        precision = observation.payload.get("time_precision", "instant")
        if precision not in {"instant", "date"}:
            raise ValueError(f"observation {observation.observation_id} has invalid time_precision")
        end_value = observation.payload.get("scheduled_end_at")
        if end_value is None:
            if precision == "date":
                raise ValueError(
                    f"observation {observation.observation_id} date event is missing scheduled_end_at"
                )
            upcoming_cutoff = scheduled_at
        elif isinstance(end_value, str):
            try:
                upcoming_cutoff = datetime.fromisoformat(end_value)
            except ValueError as exc:
                raise ValueError(
                    f"observation {observation.observation_id} has invalid scheduled_end_at"
                ) from exc
            if upcoming_cutoff.tzinfo is None or upcoming_cutoff.utcoffset() is None:
                raise ValueError(
                    f"observation {observation.observation_id} scheduled_end_at must be timezone-aware"
                )
            if upcoming_cutoff <= scheduled_at:
                raise ValueError(
                    f"observation {observation.observation_id} scheduled_end_at must be later"
                )
        else:
            raise ValueError(
                f"observation {observation.observation_id} has invalid scheduled_end_at"
            )
        if upcoming_cutoff > decision_time:
            upcoming.append(observation)
    return tuple(
        sorted(
            upcoming,
            key=lambda item: (
                datetime.fromisoformat(str(item.payload["scheduled_at"])),
                item.source_id,
                str(item.payload["event_id"]),
            ),
        )
    )


class _FomcCalendarParser(HTMLParser):
    """Extract FOMC meeting date rows without depending on a DOM library."""

    _MONTHS = {
        name: number
        for number, name in enumerate(
            (
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ),
            start=1,
        )
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.year: int | None = None
        self.tentative = False
        self.heading_depth = 0
        self.heading_text: list[str] = []
        self.heading_anchor_id: str | None = None
        self.paragraph_depth = 0
        self.paragraph_text: list[str] = []
        self.row_depth = 0
        self.row_text: list[str] = []
        self.meetings: list[tuple[int, str, int, int, bool, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "h4" and self.heading_depth == 0:
            self.heading_depth = 1
            self.heading_text = []
            self.heading_anchor_id = None
        elif self.heading_depth and tag == "h4":
            self.heading_depth += 1
        if self.heading_depth and tag == "a" and attributes.get("id"):
            self.heading_anchor_id = attributes["id"]
        if tag == "p" and self.paragraph_depth == 0:
            self.paragraph_depth = 1
            self.paragraph_text = []
        if tag == "div" and "row" in classes and "fomc-meeting" in classes and self.row_depth == 0:
            self.row_depth = 1
            self.row_text = []
        elif self.row_depth and tag == "div":
            self.row_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.row_depth and tag == "div":
            self.row_depth -= 1
            if self.row_depth == 0:
                self._finish_row()
        if self.heading_depth and tag == "h4":
            self.heading_depth -= 1
            if self.heading_depth == 0:
                text = " ".join(" ".join(self.heading_text).split())
                match = re.search(r"\b(20\d{2})\s+FOMC Meetings\b", text, re.IGNORECASE)
                if match:
                    self.year = int(match.group(1))
                    self.tentative = "tentative" in text.lower()
        if self.paragraph_depth and tag == "p":
            text = " ".join(" ".join(self.paragraph_text).split())
            match = re.search(
                r"two-day meeting is scheduled for\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
                r"(\d{1,2})\s*[-–]\s*(\d{1,2}),\s*(20\d{2})",
                text,
                re.IGNORECASE,
            )
            if match:
                self.meetings.append(
                    (
                        int(match.group(4)),
                        match.group(1).title(),
                        int(match.group(2)),
                        int(match.group(3)),
                        True,
                        None,
                    )
                )
            self.paragraph_depth = 0

    def handle_data(self, data: str) -> None:
        if self.heading_depth:
            self.heading_text.append(data)
        if self.paragraph_depth:
            self.paragraph_text.append(data)
        if self.row_depth:
            self.row_text.append(data)

    def _finish_row(self) -> None:
        text = " ".join(" ".join(self.row_text).split())
        match = re.match(
            r"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+"
            r"(?P<first>\d{1,2})(?:\s*[-–]\s*(?P<last>\d{1,2}))?\s*\*?\b",
            text,
            re.IGNORECASE,
        )
        if self.year is None or match is None:
            return
        month = self._MONTHS[match.group("month").title()]
        first_day = int(match.group("first"))
        last_day = int(match.group("last") or match.group("first"))
        if last_day < first_day:
            return
        try:
            date(self.year, month, last_day)
        except ValueError:
            return
        self.meetings.append(
            (
                self.year,
                match.group("month").title(),
                first_day,
                last_day,
                self.tentative,
                self.heading_anchor_id,
            )
        )


def parse_fomc_calendar(html: str, *, retrieved_at: datetime) -> MarketDataBatch:
    """Normalize official FOMC date windows; local retrieval is availability.

    The Federal Reserve calendar gives meeting dates, not intraday start times.
    Each meeting is therefore represented as a date-precision window in
    America/New_York, ending at midnight after its final listed day.
    """
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    retrieved_at = retrieved_at.astimezone(UTC)
    parser = _FomcCalendarParser()
    parser.feed(html)
    if not parser.meetings:
        raise MarketDataCollectionError("FOMC calendar contained no recognizable meeting rows")
    timezone = ZoneInfo("America/New_York")
    observations = []
    meetings = sorted(parser.meetings, key=lambda item: (item[0], parser._MONTHS[item[1]], item[2]))
    meeting_numbers: dict[int, int] = {}
    previous_meeting_end: datetime | None = None
    for year, month_name, first_day, last_day, tentative, anchor_id in meetings:
        meeting_numbers[year] = meeting_numbers.get(year, 0) + 1
        month = parser._MONTHS[month_name]
        first_date = date(year, month, first_day)
        end_date = date(year, month, last_day) + timedelta(days=1)
        scheduled_at = datetime.combine(first_date, time.min, timezone)
        scheduled_end_at = datetime.combine(end_date, time.min, timezone)
        meeting_is_tentative = tentative or (
            previous_meeting_end is not None and previous_meeting_end > retrieved_at
        )
        previous_meeting_end = scheduled_end_at
        if scheduled_end_at <= retrieved_at:
            continue
        date_label = f"{month_name} {first_day}" + (f"–{last_day}" if last_day != first_day else "")
        event = ScheduledMacroEvent(
            # A year-local sequence ID remains stable when the source changes
            # a meeting's dates, allowing the latest available schedule to
            # replace the prior schedule in replay.
            event_id=f"fomc:{year}:meeting-{meeting_numbers[year]:02d}",
            title=f"FOMC meeting ({date_label})",
            event_type="fomc_meeting",
            scheduled_at=scheduled_at,
            scheduled_end_at=scheduled_end_at,
            time_precision="date",
            tentative=meeting_is_tentative,
            source=FOMC_CALENDAR_SOURCE,
            raw_reference=FOMC_CALENDAR_SOURCE.endpoint + (f"#{anchor_id}" if anchor_id else ""),
        )
        observations.append(event.to_observation(retrieved_at=retrieved_at))
    observations.sort(key=lambda item: (item.event_time, item.observation_id))
    return MarketDataBatch(tuple(observations), (), retrieved_at)


class FOMCCalendarCollector:
    """Caller-driven unauthenticated collector for the official FOMC calendar."""

    def __init__(self, *, session: requests.Session | None = None, clock=None) -> None:
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(UTC))

    def collect(self) -> MarketDataBatch:
        try:
            response = self._session.get(FOMC_CALENDAR_SOURCE.endpoint, timeout=(3.05, 10.0))
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MarketDataCollectionError(f"FOMC calendar request failed: {exc}") from exc
        retrieved_at = self._clock()
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return parse_fomc_calendar(response.text, retrieved_at=retrieved_at)
