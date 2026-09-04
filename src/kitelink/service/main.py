"""Kitelink user service entrypoint."""

from __future__ import annotations

import sys

from kitelink.ipc.service1 import own_bus_name
from kitelink.service.core import KitelinkCore
from kitelink.util.logging import get_logger

log = get_logger("kitelink.service")


def main(argv: list[str] | None = None) -> int:
    _ = argv
    log.info("Starting Kitelink service")
    core = KitelinkCore()
    try:
        return own_bus_name(core)
    except Exception as exc:  # noqa: BLE001
        log.error("Service failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
