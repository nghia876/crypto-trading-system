"""Limited information-layer verification when optional native test imports fail.

This does not certify the full suite or actual analyst graph. Normal conftest is
unchanged. This standalone runner adds an explicit socket guard and selects only
pure information-layer tests (no vendor HTTP clients or LLM calls).
"""

import os
import socket


def refuse(*args, **kwargs):
    raise OSError("limited offline verification: network prohibited")


def main():
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    socket.socket.connect = refuse
    socket.socket.connect_ex = refuse
    socket.getaddrinfo = refuse
    import pytest

    names = (
        "recurring_news",
        "broad_news",
        "claim_lifecycle",
        "narrative_events",
        "information_contract",
        "information_store",
        "information_context_budget",
        "binance_spot_collector",
        "binance_usdm_collector",
        "binance_usdm_streams",
        "macro_series",
        "treasury_rates",
        "scheduled_events",
    )
    return pytest.main(
        [
            "--noconftest",
            "-q",
            "--basetemp=../.phase2-release-temp/pytest-m1-limited",
            *(f"tests/test_{name}.py" for name in names),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
