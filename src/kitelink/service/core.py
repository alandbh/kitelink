"""Central service orchestrator."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kitelink.auth.oauth import OAuthManager
from kitelink.auth.session import SessionManager
from kitelink.service.adapters.rclone import RcloneAdapter
from kitelink.service.state import (
    AccountSession,
    AggregatedTransferView,
    AuthState,
    ConnectionState,
    MountConnection,
    ServiceHealth,
    UserPreferences,
)
from kitelink.service.transfer_filter import TransferFilter
from kitelink.util.logging import get_logger, safe_event
from kitelink.util.preferences import default_mountpoint, load_preferences, save_preferences

log = get_logger("kitelink.core")


class KitelinkCore:
    def __init__(self) -> None:
        self.prefs = load_preferences()
        self.session = AccountSession()
        mountpoint = str(default_mountpoint())
        self.connection = MountConnection(mountpoint=mountpoint)
        self.health = ServiceHealth()
        self.rclone = RcloneAdapter()
        self.oauth = OAuthManager()
        self.session_mgr = SessionManager(self, self.oauth)
        self.filter = TransferFilter(
            min_bytes=self.prefs.progress_min_bytes,
            min_seconds=self.prefs.progress_min_seconds,
        )
        self.transfers = AggregatedTransferView()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._monitor: threading.Thread | None = None
        self._status_listeners: list[Callable[[str, str], None]] = []
        self._transfer_listeners: list[Callable[[int, str], None]] = []
        self._path_listeners: list[Callable[[str], None]] = []
        self._vfs_cached_files: int = -1
        self.session_mgr.refresh_from_store()

    def push_event(self, message: str) -> None:
        with self._lock:
            self.health.recent_events.append(message)
            self.health.recent_events = self.health.recent_events[-50:]

    def on_status(self, cb: Callable[[str, str], None]) -> None:
        self._status_listeners.append(cb)

    def on_transfers(self, cb: Callable[[int, str], None]) -> None:
        self._transfer_listeners.append(cb)

    def on_path_hint(self, cb: Callable[[str], None]) -> None:
        self._path_listeners.append(cb)

    def emit_status_changed(self) -> None:
        for cb in list(self._status_listeners):
            try:
                cb(self.connection.connection_state.value, self.session.auth_state.value)
            except Exception as exc:  # noqa: BLE001
                log.debug("status listener error: %s", exc)

    def emit_transfers_changed(self) -> None:
        for cb in list(self._transfer_listeners):
            try:
                cb(self.transfers.active_count, self.transfers.headline)
            except Exception as exc:  # noqa: BLE001
                log.debug("transfer listener error: %s", exc)

    def start_monitor(self) -> None:
        if self._monitor and self._monitor.is_alive():
            return
        self._stop.clear()
        self._monitor = threading.Thread(target=self._monitor_loop, name="kitelink-monitor", daemon=True)
        self._monitor.start()
        self.health.monitor_active = True

    def stop_monitor(self) -> None:
        self._stop.set()
        self.health.monitor_active = False

    def _monitor_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._poll_once()
            except Exception as exc:  # noqa: BLE001
                log.debug("monitor tick failed: %s", exc)
            self._stop.wait(1.0)

    def _poll_once(self) -> None:
        active = self.rclone.is_mount_active()
        with self._lock:
            self.health.mount_active = active
            if active and self.connection.connection_state in {
                ConnectionState.STARTING,
                ConnectionState.STOPPED,
                ConnectionState.ERROR,
            }:
                self.connection.connection_state = ConnectionState.CONNECTED
                self.connection.last_error = None
                self.emit_status_changed()
            elif not active and self.session.auth_state == AuthState.SIGNED_IN:
                if self.connection.connection_state in {
                    ConnectionState.CONNECTED,
                    ConnectionState.STARTING,
                }:
                    self.connection.connection_state = ConnectionState.DEGRADED
                    if not self.connection.last_error:
                        self.connection.last_error = (
                            "Mount inactive — check kitelink-mount.service "
                            "(often RC port conflict with another rclone)."
                        )
                    self.emit_status_changed()

            items = self.rclone.fetch_transferring() if active else []
            view = self.filter.update(items)
            changed = (
                view.active_count != self.transfers.active_count
                or view.headline != self.transfers.headline
            )
            self.transfers = view
            cache_changed = False
            if active:
                try:
                    cached = self.rclone.cached_file_count()
                except Exception:  # noqa: BLE001
                    cached = self._vfs_cached_files
                if cached != self._vfs_cached_files:
                    cache_changed = self._vfs_cached_files != -1 or cached > 0
                    self._vfs_cached_files = cached
        if changed:
            self.emit_transfers_changed()
            if view.active_count:
                self._path_notify(self.connection.mountpoint)
        if cache_changed:
            self._path_notify(self.connection.mountpoint)

    def _path_notify(self, prefix: str) -> None:
        for cb in list(self._path_listeners):
            try:
                cb(prefix)
            except Exception:  # noqa: BLE001
                pass

    def start_sign_in(self) -> tuple[bool, str]:
        self.session.auth_state = AuthState.SIGNING_IN
        self.session.last_error = None
        self.emit_status_changed()

        def ok(tokens: dict[str, Any]) -> None:
            try:
                self.rclone.apply_tokens(tokens)
                self.session.auth_state = AuthState.SIGNED_IN
                self.session.account_email = tokens.get("account_email")
                self.session.last_error = None
                self.push_event(safe_event("Signed in", email=self.session.account_email or ""))
                self.emit_status_changed()
                self.start_mount()
            except Exception as exc:  # noqa: BLE001
                self.session.auth_state = AuthState.ERROR
                self.session.last_error = str(exc)
                self.emit_status_changed()

        def err(message: str) -> None:
            self.session.auth_state = AuthState.ERROR
            self.session.last_error = message
            self.emit_status_changed()

        return self.oauth.start_sign_in_async(ok, err)

    def start_mount(self) -> tuple[bool, str]:
        self.connection.connection_state = ConnectionState.STARTING
        self.emit_status_changed()
        mp = Path(self.connection.mountpoint)
        ok, msg = self.rclone.start_mount(mp, cache_max_size=self.prefs.vfs_cache_max_size)
        if ok:
            self.connection.connection_state = ConnectionState.CONNECTED
            self.connection.last_error = None
            self.push_event(safe_event("Mount started"))
            self.start_monitor()
        else:
            self.connection.connection_state = ConnectionState.ERROR
            self.connection.last_error = msg
            self.push_event(safe_event("Mount failed", error=msg))
        self.emit_status_changed()
        return ok, msg

    def stop_mount(self) -> tuple[bool, str]:
        ok, msg = self.rclone.stop_mount(Path(self.connection.mountpoint))
        self.connection.connection_state = ConnectionState.STOPPED
        self.health.mount_active = False
        self.emit_status_changed()
        return ok, msg

    def restart_connection(self) -> tuple[bool, str]:
        ok, msg = self.rclone.restart_mount(
            Path(self.connection.mountpoint),
            cache_max_size=self.prefs.vfs_cache_max_size,
        )
        if ok:
            self.connection.connection_state = ConnectionState.CONNECTED
            self.connection.last_error = None
            self.start_monitor()
        else:
            self.connection.connection_state = ConnectionState.ERROR
            self.connection.last_error = msg
        self.emit_status_changed()
        return ok, msg

    def open_mountpoint(self) -> bool:
        mp = Path(self.connection.mountpoint)
        if not mp.exists():
            return False
        try:
            import subprocess

            subprocess.Popen(["xdg-open", str(mp)], start_new_session=True)
            return True
        except OSError:
            return False

    def get_path_state(self, path: str) -> tuple[str, str]:
        state, confidence = self.rclone.path_state(path, mountpoint=self.connection.mountpoint)
        return state.value, confidence.value

    def get_preferences_json(self) -> str:
        return json.dumps(self.prefs.to_dict())

    def set_preferences_json(self, raw: str) -> tuple[bool, str]:
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                return False, "Preferences must be a JSON object."
            self.prefs = UserPreferences.from_dict({**self.prefs.to_dict(), **data})
            save_preferences(self.prefs)
            self.filter.min_bytes = self.prefs.progress_min_bytes
            self.filter.min_seconds = self.prefs.progress_min_seconds
            # Apply cache size by rewriting unit; restart if connected
            if self.session.auth_state == AuthState.SIGNED_IN:
                self.restart_connection()
            return True, "Preferences saved."
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return False, f"Invalid preferences: {exc}"

    def diagnostics_json(self) -> str:
        from kitelink.service.diagnostics import build_diagnostics

        return json.dumps(build_diagnostics(self), indent=2)

    def bootstrap_if_signed_in(self) -> None:
        self.session_mgr.refresh_from_store()
        if self.session.auth_state != AuthState.SIGNED_IN:
            return
        try:
            tokens = self.oauth.refresh_tokens()
            self.rclone.apply_tokens(tokens)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not refresh stored tokens: %s", exc)
            tokens = self.oauth.load_tokens()
            if tokens:
                self.rclone.apply_tokens(tokens)
        if not self.rclone.is_mount_active():
            self.start_mount()
        else:
            self.connection.connection_state = ConnectionState.CONNECTED
            self.start_monitor()
            self.emit_status_changed()
