"""Dialogs S21–S24: emblem legend, diagnostics, sign-out, quit."""

from __future__ import annotations

import json

from kitelink.app import help_copy as copy
from kitelink.app.widgets import pill_button


def open_emblem_help(parent) -> None:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk  # type: ignore

    dialog = Adw.Window(title=copy.S21_TITLE, transient_for=parent, modal=True)
    dialog.set_default_size(420, 360)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    box.set_margin_top(20)
    box.set_margin_bottom(20)
    box.set_margin_start(20)
    box.set_margin_end(20)
    title = Gtk.Label(label=copy.S21_TITLE)
    title.add_css_class("title-2")
    box.append(title)
    for line in (copy.S21_CLOUD, copy.S21_SYNC, copy.S21_LOCAL, copy.S21_ERROR):
        lbl = Gtk.Label(label=line)
        lbl.set_wrap(True)
        lbl.set_xalign(0)
        box.append(lbl)
    honest = Gtk.Label(label=copy.S21_HONEST)
    honest.set_wrap(True)
    honest.add_css_class("dim-label")
    box.append(honest)
    dialog.set_content(box)
    dialog.present()


def open_diagnostics(parent, client) -> None:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gdk, Gtk  # type: ignore

    raw = client.get_diagnostics()
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        data = {"raw": raw}

    dialog = Adw.Window(title=copy.S22_TITLE, transient_for=parent, modal=True)
    dialog.set_default_size(440, 400)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_margin_top(20)
    box.set_margin_bottom(20)
    box.set_margin_start(20)
    box.set_margin_end(20)
    heading = Gtk.Label(label=copy.S22_TITLE)
    heading.add_css_class("title-2")
    box.append(heading)

    rows = [
        (copy.S22_ACCOUNT, str(data.get("account_email") or "—")),
        (copy.S22_CONNECTION, str(data.get("connection_state") or "—")),
        (copy.S22_MOUNT, "sim" if data.get("mount_active") else "não"),
        (copy.S22_BACKEND, str(data.get("backend") or "rclone")),
        (copy.S22_LAST_ERROR, str(data.get("last_connection_error") or data.get("last_auth_error") or "—")),
    ]
    for label, value in rows:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        k = Gtk.Label(label=label, xalign=0, hexpand=True)
        v = Gtk.Label(label=value, xalign=1)
        v.set_wrap(True)
        row.append(k)
        row.append(v)
        box.append(row)

    status = Gtk.Label(label="")
    copy_btn = pill_button(copy.S22_COPY, suggested=True)

    def on_copy(_b) -> None:
        text = json.dumps(data, indent=2, ensure_ascii=False)
        display = Gdk.Display.get_default()
        if display:
            display.get_clipboard().set(text)
        status.set_text(copy.S22_COPIED)

    copy_btn.connect("clicked", on_copy)
    box.append(copy_btn)
    box.append(status)
    dialog.set_content(box)
    dialog.present()


def confirm_sign_out(parent, on_confirm) -> None:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Adw", "1")
    from gi.repository import Adw  # type: ignore

    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading=copy.S23_TITLE,
        body=copy.S23_BODY,
    )
    dialog.add_response("cancel", copy.S23_CANCEL)
    dialog.add_response("signout", copy.S23_CONFIRM)
    dialog.set_response_appearance("signout", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")

    def on_response(_d, response: str) -> None:
        if response == "signout":
            on_confirm()

    dialog.connect("response", on_response)
    dialog.present()


def confirm_quit(parent, on_confirm) -> None:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Adw", "1")
    from gi.repository import Adw  # type: ignore

    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading=copy.S24_TITLE,
        body=copy.S24_BODY,
    )
    dialog.add_response("cancel", copy.S24_CANCEL)
    dialog.add_response("quit", copy.S24_CONFIRM)
    dialog.set_default_response("cancel")

    def on_response(_d, response: str) -> None:
        if response == "quit":
            on_confirm()

    dialog.connect("response", on_response)
    dialog.present()
