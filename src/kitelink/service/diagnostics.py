"""User-safe diagnostics payload (no secrets)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kitelink.service.adapters.rclone.mount import rclone_binary
from kitelink.util.preferences import preferences_path, xdg_cache_dir

if TYPE_CHECKING:
    from kitelink.service.core import KitelinkCore


def build_diagnostics(core: KitelinkCore) -> dict[str, Any]:
    return {
        "auth_state": core.session.auth_state.value,
        "account_email": core.session.account_email,
        "connection_state": core.connection.connection_state.value,
        "mountpoint": core.connection.mountpoint,
        "mount_active": core.health.mount_active,
        "monitor_active": core.health.monitor_active,
        "backend": core.connection.backend_id,
        "rc_endpoint": core.connection.rc_endpoint,
        "rclone_binary": rclone_binary(),
        "cache_dir": str(xdg_cache_dir()),
        "preferences_path": str(preferences_path()),
        "vfs_cache_max_size": core.prefs.vfs_cache_max_size,
        "progress_min_bytes": core.prefs.progress_min_bytes,
        "progress_min_seconds": core.prefs.progress_min_seconds,
        "transfer_headline": core.transfers.headline,
        "transfer_count": core.transfers.active_count,
        "last_auth_error": core.session.last_error,
        "last_connection_error": core.connection.last_error,
        "recent_events": list(core.health.recent_events),
    }
