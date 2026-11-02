"""Rights-bounded WORLD polling in the existing canonical information store.

One invocation is a finite job, suitable for an external 15-minute scheduler.
No article requests, paid service, automatic retries or semantic adjudication.
"""

import argparse
import hashlib
import json
import sqlite3
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from xml.sax.saxutils import escape

import requests

from tradingagents.information.discovery_sources import DISCOVERY_CONFIGS, RELATED_CONFIGS
from tradingagents.information.evidence_review import review_packet
from tradingagents.information.news import parse_news_snapshot
from tradingagents.information.news_evidence import replay_payload
from tradingagents.information.polling import coordinate, job_lock, source_gap_report
from tradingagents.information.sources import (
    OPERATIONAL_ADDITIONS,
    OPERATIONAL_REPAIR_CONFIG,
    SPECIALIST_WORLD_CONFIG,
    UK_WORLD_CONFIG,
)
from tradingagents.information.store import SQLiteInformationStore

ELIGIBLE_CONFIGS = (SPECIALIST_WORLD_CONFIG + OPERATIONAL_ADDITIONS + UK_WORLD_CONFIG
                    + OPERATIONAL_REPAIR_CONFIG)
REVIEWED_FINGERPRINTS = frozenset(c.fingerprint for c in ELIGIBLE_CONFIGS)
PILOT_REVIEWED_FINGERPRINTS = frozenset(c.fingerprint for c in DISCOVERY_CONFIGS + RELATED_CONFIGS)
USER_AGENT = "TradingAgentsWorldRadar/1.0"
RIGHTS_SCOPE = {
    "reviewed_at": "2026-11-02", "reviewer_kind": "agent_reviewed",
    "retained": "Agency headline, original URL, supplied dates and provenance only",
    "excluded": "Article bodies, summaries, images, logos and third-party-host links",
    "storage_basis": "Agency public-domain/reuse policies and UK OGL v3.0; attribution retained",
    "ai_basis": "Bounded factual processing of eligible agency metadata under reuse basis; no explicit AI-specific grant claimed",
    "uncertainties": "US public-domain basis does not resolve every foreign jurisdiction; agency host alone cannot prove authorship of all linked works",
    "blocked": "BBC/GDELT publisher reuse unresolved; CDC syndication redistribution restricted; CISA policy inaccessible; State current feed/rights unverified; EIA robots disallows RSS",
}


class RobotsDenied(requests.RequestException):
    """Reviewed endpoint denied by the publisher's access policy."""


class RobotsUnavailable(requests.RequestException):
    """Policy could not be verified; no feed request permitted."""


class RobotsDeferred(requests.RequestException):
    """Publisher crawl delay requires a later operator-controlled job."""


class PolicySession:
    """Exact reviewed configs; cached bounded robots checks before any feed request.

    Robots failures fail closed; they are not statements about copyright. Redirects
    are refused. The feed adapter records denial as an unavailable polling attempt.
    """

    def __init__(self, session, configs=ELIGIBLE_CONFIGS, *, wait_for_crawl_delay=False):
        if any(c.fingerprint not in REVIEWED_FINGERPRINTS | PILOT_REVIEWED_FINGERPRINTS
               for c in configs):
            raise ValueError("unreviewed WORLD configuration")
        self.session = session
        self.endpoints = {c.source.endpoint for c in configs}
        self.checks = {}
        self.wait_for_crawl_delay = wait_for_crawl_delay
        self.last_request = {}

    def get(self, url, **kwargs):
        if url not in self.endpoints:
            raise requests.RequestException("unreviewed endpoint")
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self.checks:
            checked = datetime.now(UTC).isoformat()
            started = time.monotonic()
            try:
                with self.session.get(origin + "/robots.txt", timeout=(3.05, 10),
                                      stream=True, allow_redirects=False,
                                      headers={"User-Agent": USER_AGENT}) as response:
                    status = response.status_code
                    raw = bytearray()
                    if status == 200:
                        for chunk in response.iter_content(8192):
                            raw.extend(chunk)
                            if len(raw) > 262144 or time.monotonic() - started > 20:
                                raise requests.RequestException("robots size limit")
                        parser = RobotFileParser()
                        parser.parse(raw.decode("utf-8-sig").splitlines())
                        allowed = parser.can_fetch(USER_AGENT, url)
                        delay = parser.crawl_delay(USER_AGENT) or 0
                        # No second host request in a job if publisher asks a longer delay.
                        allowed = allowed and delay <= 30
                    else:
                        allowed, delay = status in {404, 410}, None
                self.checks[origin] = {
                    "checked_at": checked, "status": status, "allowed": allowed,
                    "crawl_delay_seconds": delay,
                    "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
                    "parser": parser if status == 200 else None,
                }
                self.last_request[origin] = time.monotonic()
            except (requests.RequestException, UnicodeError):
                self.checks[origin] = {"checked_at": checked, "allowed": False,
                                       "error": "robots unavailable or invalid"}
        check = self.checks[origin]
        parser = check.get("parser")
        if check.get("error"):
            raise RobotsUnavailable("robots policy unverified")
        if not check["allowed"] or (parser and not parser.can_fetch(USER_AGENT, url)):
            raise RobotsDenied("robots policy blocked or unverified")
        # Default jobs defer; the finite pilot may explicitly honor a <=30s delay.
        if check.get("crawl_delay_seconds"):
            if not self.wait_for_crawl_delay:
                raise RobotsDeferred("robots crawl delay requires deferred acquisition")
            remaining = check["crawl_delay_seconds"] - (time.monotonic() - self.last_request[origin])
            if remaining > 0:
                time.sleep(remaining)
        self.last_request[origin] = time.monotonic()
        return self.session.get(url, headers={"User-Agent": USER_AGENT}, **kwargs)

    def report(self):
        return {key: {k: v for k, v in value.items() if k != "parser"}
                for key, value in self.checks.items()}


def coverage_metrics(view, configs=ELIGIBLE_CONFIGS):
    """PIT freshness and conservative publisher/copy partitions, never corroboration."""
    sources = []
    fresh_families, groups = set(), set()
    for config in configs:
        versions = [r for r in view.observations
                    if r.source_id == config.source.source_id and r.metric == "narrative.event"]
        latest = {}
        for row in sorted(versions, key=lambda r: (r.available_at, r.observation_id)):
            latest[row.subject] = row
        rows = list(latest.values())
        def timestamp(row):
            return row.publication_time or row.effective_time

        fresh = [r for r in rows if timestamp(r) is not None
                 and timedelta(0) <= view.decision_time - timestamp(r) <= timedelta(days=7)]
        if fresh:
            fresh_families.add(config.domain)
            groups.add(config.source.provider)
        sources.append({
            "source_id": config.source.source_id, "family": config.domain,
            "publisher_group": config.source.provider, "items": len(rows),
            "fresh_7d": len(fresh),
            "fresh_24h": sum(view.decision_time - timestamp(r) <= timedelta(days=1)
                             for r in fresh),
            "fresh_update_only": sum(r.publication_time is None for r in fresh),
            "newest_update": max((r.effective_time for r in rows if r.effective_time),
                                 default=None).isoformat()
            if any(r.effective_time for r in rows) else None,
            "newest_publication": max((r.publication_time for r in rows if r.publication_time),
                                      default=None).isoformat()
            if any(r.publication_time for r in rows) else None,
        })
    return {"freshness_window_days": 7,
            "freshness_basis": "Source publication, else source update; update is not incident occurrence or original publication",
            "sources": sources,
            "fresh_families": sorted(fresh_families), "fresh_publisher_groups": sorted(groups),
            "independent_original_origins": "UNVERIFIED; publisher diversity is not independent corroboration",
            "human_reviews": 0}


def run(store, *, session, now=None, clock=None, max_sources=6,
        observation_limit=12, retention_limits=None, window_start=None):
    policy = PolicySession(session)
    outcomes, health = coordinate(store, ELIGIBLE_CONFIGS, now=now, clock=clock,
                                  session=policy, interval=900, max_sources=max_sources,
                                  observation_limit=observation_limit,
                                  retention_limits=retention_limits, window_start=window_start)
    cutoff = max(r.observed_at for r in health)
    view = store.view_at(cutoff)
    from tradingagents.information.source_health import health_report

    selected = {key for outcome in outcomes for key in outcome.evidence_ids}
    rows = [r for r in view.observations if r.observation_id in selected]
    return {
        "cutoff": cutoff.isoformat(), "rights_scope": RIGHTS_SCOPE,
        "operational_health": health_report(store, ELIGIBLE_CONFIGS, cutoff=cutoff),
        "robots": policy.report(), "metrics": coverage_metrics(view),
        "polls": [{"source_id": r.source_id, "status": r.status.value,
                   "observed_at": r.observed_at.isoformat(), **json.loads(r.detail)}
                  for r in outcomes],
        "gaps": source_gap_report(view, ELIGIBLE_CONFIGS),
        "articles": [dict(r, status="UNREVIEWED") for r in review_packet(view)
                     if r["evidence_id"] in selected],
        "specimens": [{"source_id": r.source_id, "title": r.payload["claim"],
                       "intake_contract_version": 2,
                       "source_item_index": r.payload["source_item_index"],
                       "snapshot_item_count": r.payload["snapshot_item_count"],
                       "excluded_article_count": r.payload["excluded_article_count"],
                       "url": r.raw_reference, "published_raw": r.payload["published_raw"],
                       "updated_raw": r.payload["updated_raw"],
                       "retrieved_at": r.retrieved_at.isoformat(),
                       "available_at": r.available_at.isoformat(),
                       "first_seen_time": r.first_seen_time.isoformat(),
                       "snapshot_sha256": r.payload["snapshot_hash"],
                       "origin_cluster": "publisher:" + r.payload["publisher_group"],
                       "copy_cluster": r.subject,
                       "syndication": "UNKNOWN", "status": "UNREVIEWED"} for r in rows],
    }


def replay_specimens(store, specimens):
    """Offline tests only: normalized fields, never original-response XML or backfill."""
    for item in specimens:
        config = next(c for c in ELIGIBLE_CONFIGS if c.source.source_id == item["source_id"])
        # Atom represents both independently supplied timestamps without inventing publication.
        text = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>'
                + escape(item["title"]) + '</title><link href="'
                + escape(item["url"], {'"': '&quot;'}) + '"/>'
                + ("<published>" + escape(item["published_raw"]) + "</published>"
                   if item.get("published_raw") else "")
                + ("<updated>" + escape(item["updated_raw"]) + "</updated>"
                   if item.get("updated_raw") else "") + "</entry></feed>")
        batch = parse_news_snapshot(text, config,
                                    retrieved_at=datetime.fromisoformat(item["retrieved_at"]))
        store.append(replace(batch, observations=tuple(
            replace(row, first_seen_time=datetime.fromisoformat(item["first_seen_time"]),
                    payload=replay_payload(row.payload, item) | {"snapshot_hash": item["snapshot_sha256"]})
            for row in batch.observations)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--retention-limit", type=int, default=12)
    parser.add_argument("--window-start", type=datetime.fromisoformat)
    args = parser.parse_args(argv)
    if args.report.exists():
        parser.error("report already exists; retain immutable prior results")
    store = SQLiteInformationStore(args.store)
    with job_lock(store), requests.Session() as session:
        report = run(store, session=session, observation_limit=args.retention_limit,
                     window_start=args.window_start)
    with sqlite3.connect(store.path) as connection:
        report["sqlite_integrity"] = connection.execute("PRAGMA integrity_check").fetchone()[0]
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("cutoff", "metrics", "polls", "sqlite_integrity")}, indent=2))


if __name__ == "__main__":
    main()
