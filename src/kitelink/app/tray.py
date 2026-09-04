"""Status tray / indicator window for Kitelink."""

from __future__ import annotations

from kitelink.app.help_copy import APP_NAME, HELP_SYNC_STATES
from kitelink.app.notifications import notify_transfer_progress
from kitelink.app.preferences import open_preferences


class TrayController:
    def __init__(self, app, client) -> None:  # type: ignore[no-untyped-def]
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw, GLib, Gtk  # type: ignore

        self.app = app
        self.client = client
        self.GLib = GLib
        self.Gtk = Gtk

        # Adw.ApplicationWindow (not Gtk) so content/layout match onboarding.
        self.window = Adw.ApplicationWindow(application=app, title=APP_NAME)
        self.window.set_default_size(360, 280)
        self.window.set_hide_on_close(True)

        self.status_label = Gtk.Label(label="Starting…")
        self.status_label.set_wrap(True)
        self.transfer_label = Gtk.Label(label="")
        self.transfer_label.set_wrap(True)
        self.help = Gtk.Label(label=HELP_SYNC_STATES)
        self.help.set_wrap(True)
        self.help.add_css_class("dim-label")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.append(self.status_label)
        box.append(self.transfer_label)
        box.append(self.help)

        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for label, handler in [
            ("Open Kitelink folder", self._open_folder),
            ("Preferences", self._prefs),
            ("Diagnostics", self._diagnostics),
            ("Sign out", self._sign_out),
            ("Quit", self._quit),
        ]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", handler)
            menu_box.append(btn)
        box.append(menu_box)
        self.window.set_content(box)

        # Defer polling until after the window is mapped so a slow/failed D-Bus
        # call cannot block first paint (ghost window).
        GLib.idle_add(self._start_polling)

    def _start_polling(self) -> bool:
        self._tick()
        self.GLib.timeout_add_seconds(2, self._tick)
        return False

    def present(self) -> None:
        self.window.present()

    def _tick(self) -> bool:
        try:
            auth_state, email, auth_err = self.client.get_auth_status()
            conn_state, mountpoint, conn_err = self.client.get_connection_status()
            transfers = self.client.get_aggregated_transfers()
            active, headline, *_rest = transfers
            who = email or "Google account"
            line = f"{who} — {conn_state}"
            if auth_state != "signed_in":
                line = f"Auth: {auth_state}"
            if mountpoint:
                line += f"\n{mountpoint}"
            if auth_err or conn_err:
                line += f"\n{auth_err or conn_err}"
            self.status_label.set_text(line)
            self.transfer_label.set_text(headline if active else "Idle")
            # Policy: never call notify-send per transfer
            notify_transfer_progress("", "")
        except Exception as exc:  # noqa: BLE001
            self.status_label.set_text(f"Waiting for Kitelink service…\n{exc}")
        return True

    def _open_folder(self, *_a) -> None:  # type: ignore[no-untyped-def]
        try:
            self.client.open_mountpoint()
        except Exception:
            pass

    def _prefs(self, *_a) -> None:  # type: ignore[no-untyped-def]
        try:
            open_preferences(self.window, self.client)
        except Exception as exc:  # noqa: BLE001
            self.transfer_label.set_text(str(exc))

    def _diagnostics(self, *_a) -> None:  # type: ignore[no-untyped-def]
        try:
            raw = self.client.get_diagnostics()
            self.transfer_label.set_text(raw[:500] + ("…" if len(raw) > 500 else ""))
        except Exception as exc:  # noqa: BLE001
            self.transfer_label.set_text(str(exc))

    def _sign_out(self, *_a) -> None:  # type: ignore[no-untyped-def]
        try:
            ok, msg = self.client.sign_out()
            self.transfer_label.set_text(msg if ok else f"Sign-out failed: {msg}")
        except Exception as exc:  # noqa: BLE001
            self.transfer_label.set_text(str(exc))

    def _quit(self, *_a) -> None:  # type: ignore[no-untyped-def]
        self.app.quit()
