"""Opt-in bounded read-only diagnostics for the free news adapters.

Run: python -m tradingagents.information.network_diagnostics
Never disables certificate verification, changes proxies/DNS, retries, or persists data.
"""

from __future__ import annotations

import json
import os
import socket
import ssl
from datetime import UTC, datetime
from urllib.parse import urlsplit
from urllib.request import getproxies

import requests

from tradingagents.information.binance_spot import MarketDataCollectionError
from tradingagents.information.news import fetch_news_snapshot
from tradingagents.information.sources import BROAD_NEWS_CONFIG


def diagnose() -> dict:
    result = {
        "checked_at": datetime.now(UTC).isoformat(),
        "tls_library": ssl.OPENSSL_VERSION,
        "ca_bundle_exists": os.path.isfile(requests.certs.where()),
        "proxy_types_configured": sorted(getproxies()),
        "certificate_override_variables": [
            name
            for name in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE")
            if name in os.environ
        ],
        "dns": [],
        "requests": [],
    }
    for host in sorted(
        {urlsplit(c.source.endpoint).hostname for c in BROAD_NEWS_CONFIG}
        | {"www.federalreserve.gov"}
    ):
        try:
            socket.getaddrinfo(host, 443)
            result["dns"].append({"host": host, "resolved": True})
        except OSError as exc:
            result["dns"].append(
                {
                    "host": host,
                    "resolved": False,
                    "error_class": type(exc).__name__,
                    "errno": exc.errno,
                }
            )
    with requests.Session() as session:
        for config in BROAD_NEWS_CONFIG:
            report = {
                "source": config.source.source_id,
                "endpoint": config.source.endpoint,
                "config_fingerprint": config.fingerprint,
                "http_status": None,
                "retry_after": None,
            }
            try:
                text = fetch_news_snapshot(config, session)
                report.update(success=True, decoded_bytes=len(text.encode("utf-8")))
            except (requests.RequestException, MarketDataCollectionError, ValueError, UnicodeError) as exc:
                response = getattr(exc, "response", None)
                if response is not None:
                    report.update(
                        http_status=response.status_code,
                        retry_after=response.headers.get("Retry-After", "")[:100],
                    )
                chain = []
                current = exc
                while current is not None and len(chain) < 8:
                    chain.append(
                        {"class": type(current).__name__, "errno": getattr(current, "errno", None)}
                    )
                    current = current.__cause__ or current.__context__
                report.update(success=False, error_chain=chain)
            result["requests"].append(report)
    return result


if __name__ == "__main__":
    print(json.dumps(diagnose(), indent=2))
