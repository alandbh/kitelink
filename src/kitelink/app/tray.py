"""S10–S13 compact status panel (hybrid daily home)."""

from __future__ import annotations

from collections.abc import Callable

from kitelink.app import help_copy as copy
from kitelink.app.dialogs import confirm_quit, confirm_sign_out, open_diagnostics, open_emblem_help
from kitelink.app.notifications import notify_transfer_progress
from kitelink.app.preferences import open_preferences
from kitelink.app.widgets import load_logo, pill_button, prepare_window

_CONN_LABEL = {
    "connected": copy.S10_CONNECTED,
    "starting": copy.S05_TITLE,
    "degraded": copy.S12_TITLE,
    "error": copy.S13_TITLE,
    "stopped": copy.S12_TITLE,
}


class TrayController:
    def __init__(
        self,
        app,
        client,
        on_sign_out: Callable[[], None] | None = None,
    ) -> None:  # type: ignore[no-untyped-def]
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw, GLib, Gtk, Pango  # type: ignore

        self.app = app
        self.client = client
        self._on_sign_out = on_sign_out
        self.GLib = GLib
        self.Gtk = Gtk

        self.window = Adw.ApplicationWindow(application=app, title=copy.APP_NAME)
        self.window.set_default_size(360, 420)
        self.window.set_hide_on_close(True)
        prepare_window(self.window)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.append(load_logo(32))
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.header_state = Gtk.Label(label=copy.S10_CONNECTED, xalign=0)
        self.header_state.add_css_class("title-3")
        self.account_label = Gtk.Label(label="", xalign=0)
        self.account_label.add_css_class("dim-label")
        titles.append(self.header_state)
        titles.append(self.account_label)
        header.append(titles)
        root.append(header)

        folder_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.folder_label = Gtk.Label(label="~/Kitelink", xalign=0, hexpand=True)
        self.folder_label.set_ellipsize(Pango.EllipsizeMode.END)
        open_icon = Gtk.Button(label=copy.S10_OPEN_FOLDER)
        open_icon.add_css_class("flat")
        open_icon.connect("clicked", self._open_folder)
        folder_row.append(self.folder_label)
        folder_row.append(open_icon)
        root.append(folder_row)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        idle = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.idle_label = Gtk.Label(label=copy.S10_IDLE)
        self.idle_label.add_css_class("title-4")
        idle.append(self.idle_label)
        self.stack.add_named(idle, "idle")

        xfer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.xfer_headline = Gtk.Label(label="")
        self.xfer_headline.set_wrap(True)
        self.xfer_headline.set_xalign(0)
        self.xfer_bar = Gtk.ProgressBar()
        self.xfer_others = Gtk.Label(label="")
        self.xfer_others.add_css_class("dim-label")
        xfer.append(self.xfer_headline)
        xfer.append(self.xfer_bar)
        xfer.append(self.xfer_others)
        self.stack.add_named(xfer, "transfer")

        degraded = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        d_title = Gtk.Label(label=copy.S12_TITLE)
        d_title.add_css_class("title-4")
        d_body = Gtk.Label(label=copy.S12_BODY)
        d_body.set_wrap(True)
        self.degraded_detail = Gtk.Label(label="")
        self.degraded_detail.set_wrap(True)
        self.degraded_detail.add_css_class("dim-label")
        reconnect = pill_button(copy.S12_RECONNECT, suggested=True)
        reconnect.connect("clicked", self._reconnect)
        diag_d = pill_button(copy.S10_DIAGNOSTICS)
        diag_d.connect("clicked", self._diagnostics)
        degraded.append(d_title)
        degraded.append(d_body)
        degraded.append(self.degraded_detail)
        degraded.append(reconnect)
        degraded.append(diag_d)
        self.stack.add_named(degraded, "degraded")

        error = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        e_title = Gtk.Label(label=copy.S13_TITLE)
        e_title.add_css_class("title-4")
        self.error_detail = Gtk.Label(label="")
        self.error_detail.set_wrap(True)
        retry = pill_button(copy.S13_RETRY, suggested=True)
        retry.connect("clicked", self._reconnect)
        error.append(e_title)
        error.append(self.error_detail)
        error.append(retry)
        self.stack.add_named(error, "error")

        root.append(self.stack)

        primary = pill_button(copy.S10_OPEN_FOLDER, suggested=True)
        primary.connect("clicked", self._open_folder)
        prefs_btn = pill_button(copy.S10_PREFERENCES)
        prefs_btn.connect("clicked", self._prefs)
        help_btn = pill_button(copy.S10_HELP)
        help_btn.connect("clicked", self._help)
        root.append(primary)
        root.append(prefs_btn)
        root.append(help_btn)

        overflow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        more = Gtk.MenuButton(label="…")
        more.add_css_class("flat")
        pop = Gtk.Popover()
        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for label, handler in (
            (copy.S10_DIAGNOSTICS, self._diagnostics),
            (copy.S10_SIGN_OUT, self._sign_out),
            (copy.S10_QUIT, self._quit),
        ):
            b = Gtk.Button(label=label)
            b.add_css_class("flat")
            b.connect("clicked", handler)
            pop_box.append(b)
        pop.set_child(pop_box)
        more.set_popover(pop)
        overflow.append(more)
        root.append(overflow)

        self.window.set_content(root)
        GLib.idle_add(self._start_polling)

    def _start_polling(self) -> bool:
        self._tick()
        self.GLib.timeout_add_seconds(2, self._tick)
        return False

    def present(self) -> None:
        self.window.present()

    def hide(self) -> None:
        self.window.set_hide_on_close(False)
        self.window.close()

    def _tick(self) -> bool:
        try:
            auth_state, email, auth_err = self.client.get_auth_status()
            conn_state, mountpoint, conn_err = self.client.get_connection_status()
            transfers = self.client.get_aggregated_transfers()
            active, headline, _name, done, total, _spd = (
                transfers + (0, "", "", 0, 0, 0.0)
            )[:6]
            self.account_label.set_text(email or "")
            self.folder_label.set_text(mountpoint or "~/Kitelink")
            self.header_state.set_text(_CONN_LABEL.get(conn_state, copy.S10_CONNECTED))

            if conn_state == "error":
                self.error_detail.set_text(conn_err or auth_err or "")
                self.stack.set_visible_child_name("error")
            elif conn_state in {"degraded", "stopped"} or (
                auth_state == "signed_in" and conn_state != "connected" and conn_state != "starting"
            ):
                self.degraded_detail.set_text(conn_err or "")
                self.stack.set_visible_child_name("degraded")
            elif int(active or 0) > 0:
                self.xfer_headline.set_text(headline or copy.S05_TITLE)
                if total and int(total) > 0:
                    self.xfer_bar.set_fraction(min(1.0, float(done) / float(total)))
                else:
                    self.xfer_bar.pulse()
                extra = int(active) - 1
                self.xfer_others.set_text(copy.S11_OTHERS.format(n=extra) if extra > 0 else "")
                self.stack.set_visible_child_name("transfer")
            else:
                self.idle_label.set_text(copy.S10_IDLE)
                self.stack.set_visible_child_name("idle")
            notify_transfer_progress("", "")
        except Exception as exc:  # noqa: BLE001
            self.error_detail.set_text(str(exc))
            self.stack.set_visible_child_name("error")
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
            self.error_detail.set_text(str(exc))
            self.stack.set_visible_child_name("error")

    def _help(self, *_a) -> None:  # type: ignore[no-untyped-def]
        open_emblem_help(self.window)

    def _diagnostics(self, *_a) -> None:  # type: ignore[no-untyped-def]
        try:
            open_diagnostics(self.window, self.client)
        except Exception as exc:  # noqa: BLE001
            self.error_detail.set_text(str(exc))
            self.stack.set_visible_child_name("error")

    def _reconnect(self, *_a) -> None:  # type: ignore[no-untyped-def]
        try:
            self.client.restart_connection()
        except Exception as exc:  # noqa: BLE001
            self.error_detail.set_text(str(exc))
            self.stack.set_visible_child_name("error")

    def _sign_out(self, *_a) -> None:  # type: ignore[no-untyped-def]
        def do_sign_out() -> None:
            try:
                self.client.sign_out()
            except Exception:
                pass
            if self._on_sign_out is not None:
                self._on_sign_out()

        confirm_sign_out(self.window, do_sign_out)

    def _quit(self, *_a) -> None:  # type: ignore[no-untyped-def]
        confirm_quit(self.window, self.app.quit)
