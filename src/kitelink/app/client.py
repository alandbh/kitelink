"""D-Bus client helpers for the GTK app."""

from __future__ import annotations

import json
from typing import Any

from kitelink import BUS_NAME, INTERFACE_NAME, OBJECT_PATH


class ServiceClient:
    def __init__(self) -> None:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio  # type: ignore

        self._Gio = Gio
        self._proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            BUS_NAME,
            OBJECT_PATH,
            INTERFACE_NAME,
            None,
        )

    def call(self, method: str, signature: str = "", *args: Any) -> Any:
        from gi.repository import GLib  # type: ignore

        params = None
        if signature:
            params = GLib.Variant(f"({signature})", args)
        result = self._proxy.call_sync(
            method,
            params,
            self._Gio.DBusCallFlags.NONE,
            15000,
            None,
        )
        return result.unpack() if result is not None else None

    def get_auth_status(self) -> tuple[str, str, str]:
        return self.call("GetAuthStatus")

    def start_sign_in(self) -> tuple[bool, str]:
        return self.call("StartSignIn")

    def sign_out(self) -> tuple[bool, str]:
        return self.call("SignOut")

    def get_connection_status(self) -> tuple[str, str, str]:
        return self.call("GetConnectionStatus")

    def open_mountpoint(self) -> bool:
        return bool(self.call("OpenMountpoint")[0])

    def restart_connection(self) -> tuple[bool, str]:
        return self.call("RestartConnection")

    def get_aggregated_transfers(self) -> tuple:
        return self.call("GetAggregatedTransfers")

    def get_preferences(self) -> dict:
        raw = self.call("GetPreferences")[0]
        return json.loads(raw)

    def set_preferences(self, data: dict) -> tuple[bool, str]:
        return self.call("SetPreferences", "s", json.dumps(data))

    def get_diagnostics(self) -> str:
        return self.call("GetDiagnostics")[0]
