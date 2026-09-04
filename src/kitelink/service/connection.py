"""Connection helpers (thin wrappers for clarity / tests)."""

from __future__ import annotations

from kitelink.service.core import KitelinkCore


def get_connection_status(core: KitelinkCore) -> tuple[str, str, str]:
    return (
        core.connection.connection_state.value,
        core.connection.mountpoint,
        core.connection.last_error or "",
    )


def open_mountpoint(core: KitelinkCore) -> bool:
    return core.open_mountpoint()


def restart_connection(core: KitelinkCore) -> tuple[bool, str]:
    return core.restart_connection()
