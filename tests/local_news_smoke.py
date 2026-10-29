"""Opt-in loopback HTTP smoke; synthetic evidence in a disposable test store only.

Run from checkout: python -m tests.local_news_smoke
This tests real HTTP streaming without external DNS, HTTPS or provider validation.
"""

from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

import requests

from tradingagents.information.polling import coordinate, job_lock
from tradingagents.information.sources import BROAD_NEWS_CONFIG
from tradingagents.information.store import SQLiteInformationStore

BODY = b"<rss><channel><item><title>SYNTHETIC ceasefire talks</title><link>https://example.org/synthetic</link></item></channel></rss>"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args):
        pass


class LoopbackFixtureSession(requests.Session):
    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint
        self.trust_env = False  # local fixture only; never external/proxy requests
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return super().get(self.endpoint, **kwargs)


def main():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with TemporaryDirectory(prefix="synthetic-news-smoke-") as folder:
            store = SQLiteInformationStore(Path(folder) / "fixture.db")
            now = datetime.now(UTC)
            with LoopbackFixtureSession(f"http://127.0.0.1:{server.server_port}/") as session:
                with job_lock(store):
                    outcomes, _ = coordinate(
                        store, BROAD_NEWS_CONFIG[:1], now=now, session=session, clock=lambda: now
                    )
                assert len(outcomes) == 1 and len(store.view_at(now).observations) == 1, outcomes[
                    0
                ].detail
                reopened = SQLiteInformationStore(store.path)
                coordinate(
                    reopened,
                    BROAD_NEWS_CONFIG[:1],
                    now=now + timedelta(seconds=1),
                    session=session,
                    clock=lambda: now + timedelta(seconds=1),
                )
                assert session.calls == 1
                assert not reopened.view_at(now - timedelta(microseconds=1)).observations
            print(
                "PASS: synthetic loopback HTTP -> poll -> SQLite -> reopen/repeat -> cutoff replay"
            )
            print("External live-source gate NOT tested; fixture database deleted.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
