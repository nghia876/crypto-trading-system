"""Bounded broad news adapters and durable poll_once over the existing evidence store.

No analyst, asset, price trigger, scheduler, article crawler, or second database.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree

import requests

from tradingagents.information.binance_spot import (
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    MarketDataCollectionError,
)
from tradingagents.information.observations import Observation, Transformation, _require_aware
from tradingagents.information.sources import BROAD_NEWS_CONFIG, NewsDiscoveryConfig


def canonical_article_url(value: str) -> str:
    """Preserve all query parameters (including identity/signatures); strip fragment only."""
    url = urlsplit(value.strip())
    if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
        raise ValueError("invalid article URL")
    if len(value) > 4096:
        raise ValueError("article URL too long")
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, ""))


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _date(value, *, gdelt=False):
    if not value:
        return None
    try:
        if gdelt:
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            result = parsedate_to_datetime(value)
        _require_aware("source timestamp", result)
        return result.astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        return None


def parse_news_snapshot(
    text: str, config: NewsDiscoveryConfig, *, retrieved_at: datetime
) -> MarketDataBatch:
    """Atomic bounded snapshot; malformed dates are explicit UNKNOWN, not local-time guesses."""
    _require_aware("retrieved_at", retrieved_at)
    retrieved_at = retrieved_at.astimezone(UTC)
    snapshot_hash = _digest(text)
    if (
        len(text.encode()) > config.max_bytes
        or "<!DOCTYPE" in text.upper()
        or "<!ENTITY" in text.upper()
    ):
        raise MarketDataCollectionError("unsafe or oversized news snapshot")
    try:
        if config.format == "gdelt":
            obj = json.loads(text)
            items = obj.get("articles")
            if not isinstance(items, list):
                raise ValueError("expected GDELT articles list")
            entries = [
                (
                    x.get("title", ""),
                    x.get("url", ""),
                    None,
                    None,
                    x.get("seendate"),
                    x.get("domain"),
                )
                for x in items
            ]
        else:
            root = ElementTree.fromstring(text)
            atom = "{http://www.w3.org/2005/Atom}"
            if root.tag == "rss" and root.find("channel") is not None:
                entries = [
                    (
                        x.findtext("title", ""),
                        x.findtext("link", ""),
                        x.findtext("pubDate"),
                        None,
                        None,
                        None,
                    )
                    for x in root.findall("./channel/item")
                ]
            elif root.tag == atom + "feed":
                entries = []
                for x in root.findall(atom + "entry"):
                    links = [
                        a.get("href", "")
                        for a in x.findall(atom + "link")
                        if a.get("rel", "alternate") == "alternate"
                    ]
                    entries.append(
                        (
                            x.findtext(atom + "title", ""),
                            links[0] if links else "",
                            x.findtext(atom + "published"),
                            x.findtext(atom + "updated"),
                            None,
                            None,
                        )
                    )
            else:
                raise ValueError("expected RSS or Atom feed")
        if len(entries) > config.max_items:
            raise ValueError("news item limit exceeded")
        rows = {}
        for title, original, pub_raw, updated_raw, seen_raw, publisher in entries:
            title = " ".join(title.split())
            if not title or len(title) > 2000:
                raise ValueError("missing or oversized headline")
            canonical = canonical_article_url(original)
            published, updated = _date(pub_raw), _date(updated_raw)
            article_id = "article:" + _digest(canonical)
            content_hash = _digest(json.dumps([title, pub_raw, updated_raw], ensure_ascii=False))
            version_id = article_id + ":" + content_hash
            payload = {
                "event_id": article_id,
                "article_id": article_id,
                "version_id": version_id,
                "claim": title,
                "domain": config.domain,
                "content_hash": content_hash,
                "content_scope": "headline and supplied publication/update fields; no article body",
                "original_url": original,
                "canonical_url": canonical,
                "published_raw": pub_raw,
                "updated_raw": updated_raw,
                "updated_at": updated.isoformat() if updated else None,
                "discovery_seen_raw": seen_raw,
                "discovery_seen_at": _date(seen_raw, gdelt=True).isoformat()
                if _date(seen_raw, gdelt=True)
                else None,
                "publication_status": "source_reported"
                if published
                else "unknown_missing_or_invalid",
                "updated_status": "source_reported" if updated else "unknown_missing_or_invalid",
                "date_anomalies": [
                    name
                    for name, value in (
                        ("future_publication", published),
                        ("future_update", updated),
                    )
                    if value and value > retrieved_at
                ]
                + (
                    ["update_before_publication"]
                    if updated and published and updated < published
                    else []
                ),
                "publisher_host": publisher or urlsplit(canonical).hostname,
                "origin": "unknown",
                "syndication": "unknown",
                "independent_confirmation": "unknown",
                "fact_status": "source_reported_claim",
                "verified_facts": [],
                "lifecycle": "unconfirmed",
                "credibility": "unmeasured",
                "event_time_status": "unknown; envelope uses publication or local retrieval proxy",
                "confirmed_at": None,
                "reaction_at": None,
                "contradiction_search": "not_performed",
                "config_version": config.version,
                "config_fingerprint": config.fingerprint,
                "query": config.query,
                "snapshot_hash": snapshot_hash,
            }
            # Source, domain and acquisition copy remain distinct evidence; URL overlap never adds votes.
            row = Observation(
                observation_id="news:"
                + _digest(config.fingerprint + version_id + retrieved_at.isoformat()),
                source_id=config.source.source_id,
                subject=article_id,
                metric="narrative.event",
                payload=payload,
                event_time=published or retrieved_at,
                publication_time=published,
                effective_time=updated,
                first_seen_time=retrieved_at,
                retrieved_at=retrieved_at,
                raw_reference=original,
                schema_version="narrative-news-v1",
                unit="event_record",
                transformations=(
                    Transformation("broad_news", "1", (("config", config.fingerprint),)),
                ),
            )
            rows[row.observation_id] = row
        return MarketDataBatch(
            tuple(sorted(rows.values(), key=lambda x: x.observation_id)),
            (),
            retrieved_at,
            source_definitions=(config.source_definition,),
        )
    except (ElementTree.ParseError, ValueError, TypeError, AttributeError, KeyError) as exc:
        raise MarketDataCollectionError(f"Invalid news snapshot: {exc}") from exc


def fetch_news_snapshot(config, session):
    params = None
    if config.format == "gdelt":
        params = {
            "query": config.query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": config.max_items,
            "timespan": "1d",
            "sort": "datedesc",
        }
    with session.get(
        config.source.endpoint,
        params=params,
        timeout=(3.05, 10),
        stream=True,
        allow_redirects=False,
    ) as response:
        response.raise_for_status()
        if 300 <= response.status_code < 400:
            raise MarketDataCollectionError(
                "redirect refused; configure the public endpoint explicitly"
            )
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > config.max_bytes:
                raise MarketDataCollectionError("news byte limit exceeded")
            chunks.append(chunk)
    return b"".join(chunks).decode("utf-8-sig")


def poll_once(store, configs=BROAD_NEWS_CONFIG, *, poll_id: str, session=None, clock=None):
    """Persist each outcome atomically; a durable poll ID retries without refetching.

    Callers use a new ID for each new poll; same ID/config resumes partial runs.
    Availability uses local completion time, never request start or GDELT seendate.
    No retry on 429/errors. A later deliberate poll is caller policy.
    """
    if not poll_id.strip() or len(poll_id) > 256 or len(configs) > 16:
        raise ValueError("bounded poll ID and at most 16 sources required")
    session = session or requests.Session()
    clock = clock or (lambda: datetime.now(UTC))
    outcomes = []
    for config in configs:
        coverage_id = "news-poll:" + _digest(poll_id + config.fingerprint)
        existing = store.coverage_by_id(coverage_id)
        if existing is not None:
            outcomes.append(existing)
            continue
        text, failure, http_status = None, None, None
        try:
            text = fetch_news_snapshot(config, session)
        except (requests.RequestException, MarketDataCollectionError, UnicodeError) as exc:
            failure = type(exc).__name__  # avoid credentials or unbounded remote error text
            http_status = getattr(getattr(exc, "response", None), "status_code", None)
        completed = clock()
        _require_aware("poll completion", completed)
        completed = completed.astimezone(UTC)
        batch = MarketDataBatch((), (), completed, source_definitions=(config.source_definition,))
        if failure is None:
            try:
                batch = parse_news_snapshot(text, config, retrieved_at=completed)
            except MarketDataCollectionError as exc:
                failure = type(exc).__name__
        batch = replace(
            batch,
            observations=tuple(
                replace(
                    row,
                    first_seen_time=min(
                        row.first_seen_time,
                        store.first_seen_for_subject(row.subject) or row.first_seen_time,
                    ),
                )
                for row in batch.observations
            ),
        )
        eligible = tuple(
            x.observation_id
            for x in batch.observations
            if x.is_available_at(completed)
            and (x.effective_time is None or x.effective_time <= completed)
        )
        detail = json.dumps(
            {
                "outcome": "failure" if failure else ("success" if batch.observations else "empty"),
                "error": failure,
                "http_status": http_status,
                "config": config.fingerprint,
                "version": config.version,
                "query": config.query,
                "snapshot_hash": _digest(text) if text is not None else None,
                "items": len(batch.observations),
                "completeness": "unknown",
                "first_seen_semantics": "earliest locally stored observation of canonical article; retrieved_at is this copy",
            },
            sort_keys=True,
        )
        coverage = CoverageRecord(
            coverage_id,
            config.source.source_id,
            config.domain,
            "narrative.event",
            completed,
            CoverageStatus.UNAVAILABLE
            if failure
            else (CoverageStatus.PRESENT if eligible else CoverageStatus.UNKNOWN),
            detail,
            eligible,
        )
        store.append(
            MarketDataBatch(
                batch.observations, (), completed, (coverage,), batch.source_definitions
            )
        )
        outcomes.append(coverage)
    return tuple(outcomes)
