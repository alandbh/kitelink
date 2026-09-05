"""Onboarding window: S01–S07 as a Gtk.Stack (hybrid first-run flow)."""

from __future__ import annotations

from collections.abc import Callable

from kitelink.app import help_copy as copy
from kitelink.app.widgets import load_logo, pill_button, prepare_window


def build_onboarding(
    app,
    client,
    on_signed_in: Callable[[], None] | None = None,
    *,
    service_unavailable: bool = False,
    on_retry_service: Callable[[], None] | None = None,
) -> object:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, GLib, Gtk  # type: ignore

    window = Adw.ApplicationWindow(application=app, title=copy.APP_NAME)
    window.set_default_size(480, 560)
    prepare_window(window)

    stack = Gtk.Stack()
    stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
    stack.set_hexpand(True)
    stack.set_vexpand(True)

    def page_box() -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_bottom(32)
        box.set_margin_start(32)
        box.set_margin_end(32)
        box.set_valign(Gtk.Align.CENTER)
        return box

    def heading(text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=text)
        lbl.add_css_class("title-1")
        lbl.set_wrap(True)
        lbl.set_justify(Gtk.Justification.CENTER)
        return lbl

    def body(text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=text)
        lbl.set_wrap(True)
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.add_css_class("dim-label")
        return lbl

    # --- S01 ---
    s01 = page_box()
    s01.append(heading(copy.S01_TITLE))
    s01.append(body(copy.S01_BODY))
    s01_retry = pill_button(copy.S01_RETRY, suggested=True)
    s01_close = pill_button(copy.S01_CLOSE)
    s01.append(s01_retry)
    s01.append(s01_close)
    stack.add_named(s01, "s01")

    def on_s01_retry(_b) -> None:
        window.close()
        if on_retry_service is not None:
            on_retry_service()

    s01_retry.connect("clicked", on_s01_retry)
    s01_close.connect("clicked", lambda *_: window.close())

    # --- S02 ---
    s02 = page_box()
    s02.append(load_logo(72))
    s02.append(heading(copy.APP_NAME))
    s02.append(body(copy.TAGLINE))
    for bullet in (copy.S02_BULLET_FOLDER, copy.S02_BULLET_EMBLEMS, copy.S02_BULLET_PROGRESS):
        row = Gtk.Label(label=f"• {bullet}")
        row.set_wrap(True)
        row.set_xalign(0)
        s02.append(row)
    s02_go = pill_button(copy.S02_CONTINUE, suggested=True)
    s02.append(s02_go)
    stack.add_named(s02, "s02")
    s02_go.connect("clicked", lambda *_: stack.set_visible_child_name("s03"))

    # --- S03 / S04 / S06 ---
    s03 = page_box()
    s03_title = heading(copy.S03_TITLE)
    s03_body = body(copy.S03_BODY)
    s03_status = Gtk.Label(label="")
    s03_status.set_wrap(True)
    s03_cta = pill_button(copy.S03_CTA, suggested=True)
    s03_cancel = pill_button(copy.S04_CANCEL)
    s03_cancel.set_visible(False)
    s03.append(s03_title)
    s03.append(s03_body)
    s03.append(s03_status)
    s03.append(s03_cta)
    s03.append(s03_cancel)
    stack.add_named(s03, "s03")

    watching = {"active": False}

    def show_sign_in_idle() -> None:
        s03_title.set_text(copy.S03_TITLE)
        s03_body.set_text(copy.S03_BODY)
        s03_status.set_text("")
        s03_cta.set_sensitive(True)
        s03_cta.set_visible(True)
        s03_cancel.set_visible(False)

    def show_waiting() -> None:
        s03_title.set_text(copy.S04_TITLE)
        s03_body.set_text(copy.S04_BODY)
        s03_cta.set_sensitive(False)
        s03_cta.set_visible(False)
        s03_cancel.set_visible(True)

    def show_error(msg: str) -> None:
        s03_title.set_text(copy.S06_TITLE)
        s03_body.set_text(msg or copy.S06_GENERIC)
        s03_status.set_text("")
        s03_cta.set_label(copy.S06_RETRY)
        s03_cta.set_sensitive(True)
        s03_cta.set_visible(True)
        s03_cancel.set_visible(False)

    def goto_connecting() -> None:
        stack.set_visible_child_name("s05")
        GLib.timeout_add(500, poll_mount)

    def goto_ready(email: str) -> None:
        who = email or "Google"
        s07_who.set_text(who)
        stack.set_visible_child_name("s07")

    def poll_auth() -> bool:
        if not watching["active"]:
            return False
        try:
            auth_state, email, err = client.get_auth_status()
        except Exception as exc:  # noqa: BLE001
            s03_status.set_text(str(exc))
            return True
        if auth_state == "signed_in":
            watching["active"] = False
            goto_connecting()
            return False
        if auth_state == "error":
            watching["active"] = False
            show_error(err or copy.S06_GENERIC)
            return False
        if auth_state == "signing_in":
            show_waiting()
        return True

    def start_watching() -> None:
        if watching["active"]:
            return
        watching["active"] = True
        GLib.timeout_add(500, poll_auth)

    def on_sign_in(_b) -> None:
        s03_cta.set_sensitive(False)
        try:
            ok, msg = client.start_sign_in()
            if ok:
                s03_status.set_text(msg)
                show_waiting()
                start_watching()
            else:
                show_error(msg)
        except Exception as exc:  # noqa: BLE001
            show_error(str(exc))

    def on_cancel(_b) -> None:
        watching["active"] = False
        show_sign_in_idle()
        s03_cta.set_label(copy.S03_CTA)

    s03_cta.connect("clicked", on_sign_in)
    s03_cancel.connect("clicked", on_cancel)

    # --- S05 ---
    s05 = page_box()
    s05.append(heading(copy.S05_TITLE))
    s05.append(body(copy.S05_BODY))
    spinner = Gtk.Spinner()
    spinner.start()
    s05.append(spinner)
    stack.add_named(s05, "s05")
    mount_tries = {"n": 0}

    def poll_mount() -> bool:
        mount_tries["n"] += 1
        try:
            conn, _mp, err = client.get_connection_status()
            auth, email, _ae = client.get_auth_status()
        except Exception:
            return True
        if auth != "signed_in":
            show_error(copy.S06_GENERIC)
            stack.set_visible_child_name("s03")
            return False
        if conn == "connected":
            goto_ready(email or "")
            return False
        if conn == "error":
            show_error(err or copy.S13_TITLE)
            stack.set_visible_child_name("s03")
            return False
        if mount_tries["n"] > 40:
            goto_ready(email or "")
            return False
        return True

    # --- S07 ---
    s07 = page_box()
    s07.append(heading(copy.S07_TITLE))
    s07_who = Gtk.Label(label="")
    s07_who.add_css_class("title-3")
    s07.append(s07_who)
    s07.append(body("Pasta pessoal / Kitelink"))
    s07.append(body(copy.S07_LEGEND))
    s07_open = pill_button(copy.S07_OPEN, suggested=True)
    s07_panel = pill_button(copy.S07_PANEL)
    s07.append(s07_open)
    s07.append(s07_panel)
    stack.add_named(s07, "s07")

    def finish_to_panel() -> None:
        window.close()
        if on_signed_in is not None:
            on_signed_in()

    def on_open_folder(_b) -> None:
        try:
            client.open_mountpoint()
        except Exception:
            pass
        finish_to_panel()

    s07_open.connect("clicked", on_open_folder)
    s07_panel.connect("clicked", lambda *_: finish_to_panel())

    window.set_content(stack)

    if service_unavailable:
        stack.set_visible_child_name("s01")
        return window

    def initial_check() -> bool:
        try:
            auth_state, email, _err = client.get_auth_status()
        except Exception:
            return False
        if auth_state == "signed_in":
            goto_connecting()
        elif auth_state == "signing_in":
            stack.set_visible_child_name("s03")
            show_waiting()
            start_watching()
        else:
            stack.set_visible_child_name("s02")
        return False

    GLib.idle_add(initial_check)
    return window
