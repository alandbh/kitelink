"""D-Bus org.kitelink.Service1 implementation via Gio."""

from __future__ import annotations

from typing import Any

from kitelink import BUS_NAME, INTERFACE_NAME, OBJECT_PATH
from kitelink.auth.session import SessionManager
from kitelink.service.core import KitelinkCore
from kitelink.util.logging import get_logger

log = get_logger("kitelink.ipc")

# XML introspection matching specs/001-kitelink-mvp/contracts/dbus-org.kitelink.Service1.xml
INTROSPECTION_XML = f"""
<node>
  <interface name="{INTERFACE_NAME}">
    <method name="GetAuthStatus">
      <arg type="s" name="auth_state" direction="out"/>
      <arg type="s" name="account_email" direction="out"/>
      <arg type="s" name="last_error" direction="out"/>
    </method>
    <method name="StartSignIn">
      <arg type="b" name="accepted" direction="out"/>
      <arg type="s" name="message" direction="out"/>
    </method>
    <method name="SignOut">
      <arg type="b" name="ok" direction="out"/>
      <arg type="s" name="message" direction="out"/>
    </method>
    <method name="GetConnectionStatus">
      <arg type="s" name="connection_state" direction="out"/>
      <arg type="s" name="mountpoint" direction="out"/>
      <arg type="s" name="last_error" direction="out"/>
    </method>
    <method name="OpenMountpoint">
      <arg type="b" name="ok" direction="out"/>
    </method>
    <method name="RestartConnection">
      <arg type="b" name="ok" direction="out"/>
      <arg type="s" name="message" direction="out"/>
    </method>
    <method name="GetPathState">
      <arg type="s" name="path" direction="in"/>
      <arg type="s" name="state" direction="out"/>
      <arg type="s" name="confidence" direction="out"/>
    </method>
    <method name="GetAggregatedTransfers">
      <arg type="i" name="active_count" direction="out"/>
      <arg type="s" name="headline" direction="out"/>
      <arg type="s" name="primary_name" direction="out"/>
      <arg type="x" name="primary_bytes_done" direction="out"/>
      <arg type="x" name="primary_bytes_total" direction="out"/>
      <arg type="d" name="primary_speed_bps" direction="out"/>
    </method>
    <method name="GetPreferences">
      <arg type="s" name="json" direction="out"/>
    </method>
    <method name="SetPreferences">
      <arg type="s" name="json" direction="in"/>
      <arg type="b" name="ok" direction="out"/>
      <arg type="s" name="message" direction="out"/>
    </method>
    <method name="GetDiagnostics">
      <arg type="s" name="json" direction="out"/>
    </method>
    <signal name="StatusChanged">
      <arg type="s" name="connection_state"/>
      <arg type="s" name="auth_state"/>
    </signal>
    <signal name="TransfersChanged">
      <arg type="i" name="active_count"/>
      <arg type="s" name="headline"/>
    </signal>
    <signal name="PathStateMayHaveChanged">
      <arg type="s" name="path_prefix"/>
    </signal>
  </interface>
</node>
"""


class Service1:
    """Gio.DBusExportedObject wrapper."""

    def __init__(self, core: KitelinkCore) -> None:
        self.core = core
        self.session_mgr = SessionManager(core, core.oauth)
        self._connection: Any = None
        self._registration_id: int | None = None
        self._node_info: Any = None

    def register(self, connection: Any) -> None:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio  # type: ignore

        self._connection = connection
        self._node_info = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION_XML)
        iface = self._node_info.interfaces[0]
        self._registration_id = connection.register_object(
            OBJECT_PATH,
            iface,
            self._on_method_call,
            None,
            None,
        )
        self.core.on_status(self._emit_status)
        self.core.on_transfers(self._emit_transfers)
        self.core.on_path_hint(self._emit_path)
        log.info("Registered %s at %s", INTERFACE_NAME, OBJECT_PATH)

    def _emit_status(self, connection_state: str, auth_state: str) -> None:
        self._emit_signal("StatusChanged", "(ss)", (connection_state, auth_state))

    def _emit_transfers(self, active_count: int, headline: str) -> None:
        self._emit_signal("TransfersChanged", "(is)", (active_count, headline))

    def _emit_path(self, path_prefix: str) -> None:
        self._emit_signal("PathStateMayHaveChanged", "(s)", (path_prefix,))

    def _emit_signal(self, name: str, signature: str, args: tuple) -> None:
        if not self._connection:
            return
        try:
            from gi.repository import GLib  # type: ignore

            self._connection.emit_signal(
                None,
                OBJECT_PATH,
                INTERFACE_NAME,
                name,
                GLib.Variant(signature, args),
            )
        except Exception as exc:  # noqa: BLE001
            log.debug("signal %s failed: %s", name, exc)

    def _on_method_call(  # type: ignore[no-untyped-def]
        self,
        connection,
        sender,
        object_path,
        interface_name,
        method_name,
        parameters,
        invocation,
    ) -> None:
        from gi.repository import GLib  # type: ignore

        try:
            result = self._dispatch(method_name, parameters)
            invocation.return_value(result)
        except Exception as exc:  # noqa: BLE001
            log.error("D-Bus method %s failed: %s", method_name, exc, exc_info=True)
            invocation.return_dbus_error("org.kitelink.Error.Failed", str(exc))

    def _dispatch(self, method_name: str, parameters: Any) -> Any:
        from gi.repository import GLib  # type: ignore

        if method_name == "GetAuthStatus":
            return GLib.Variant(
                "(sss)",
                (
                    self.core.session.auth_state.value,
                    self.core.session.account_email or "",
                    self.core.session.last_error or "",
                ),
            )
        if method_name == "StartSignIn":
            ok, msg = self.core.start_sign_in()
            return GLib.Variant("(bs)", (ok, msg))
        if method_name == "SignOut":
            ok, msg = self.session_mgr.sign_out()
            return GLib.Variant("(bs)", (ok, msg))
        if method_name == "GetConnectionStatus":
            return GLib.Variant(
                "(sss)",
                (
                    self.core.connection.connection_state.value,
                    self.core.connection.mountpoint,
                    self.core.connection.last_error or "",
                ),
            )
        if method_name == "OpenMountpoint":
            return GLib.Variant("(b)", (self.core.open_mountpoint(),))
        if method_name == "RestartConnection":
            ok, msg = self.core.restart_connection()
            return GLib.Variant("(bs)", (ok, msg))
        if method_name == "GetPathState":
            path = parameters.unpack()[0]
            state, confidence = self.core.get_path_state(path)
            return GLib.Variant("(ss)", (state, confidence))
        if method_name == "GetAggregatedTransfers":
            view = self.core.transfers
            primary = view.primary
            return GLib.Variant(
                "(issxxd)",
                (
                    int(view.active_count),
                    view.headline or "",
                    primary.display_name if primary else "",
                    int(primary.bytes_done) if primary else 0,
                    int(primary.bytes_total or 0) if primary else 0,
                    float(primary.speed_bps or 0.0) if primary else 0.0,
                ),
            )
        if method_name == "GetPreferences":
            return GLib.Variant("(s)", (self.core.get_preferences_json(),))
        if method_name == "SetPreferences":
            raw = parameters.unpack()[0]
            ok, msg = self.core.set_preferences_json(raw)
            return GLib.Variant("(bs)", (ok, msg))
        if method_name == "GetDiagnostics":
            return GLib.Variant("(s)", (self.core.diagnostics_json(),))
        raise RuntimeError(f"Unknown method {method_name}")


def own_bus_name(core: KitelinkCore) -> int:
    """Own the session bus name and run a GLib main loop. Returns exit code."""
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib  # type: ignore

    service = Service1(core)
    loop = GLib.MainLoop()

    def on_bus_acquired(connection: Any, name: str) -> None:
        service.register(connection)
        core.bootstrap_if_signed_in()

    def on_name_acquired(connection: Any, name: str) -> None:
        log.info("Acquired bus name %s", name)

    def on_name_lost(connection: Any, name: str) -> None:
        log.error("Lost bus name %s", name)
        loop.quit()

    owner_id = Gio.bus_own_name(
        Gio.BusType.SESSION,
        BUS_NAME,
        Gio.BusNameOwnerFlags.NONE,
        on_bus_acquired,
        on_name_acquired,
        on_name_lost,
    )
    try:
        loop.run()
    finally:
        Gio.bus_unown_name(owner_id)
        core.stop_monitor()
    return 0
