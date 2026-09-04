"""Onboarding / sign-in window."""

from __future__ import annotations

from collections.abc import Callable

from kitelink.app.brand import apply_brand_css
from kitelink.app.help_copy import APP_NAME, HELP_PROGRESS, TAGLINE


def build_onboarding(
    app,
    client,
    on_signed_in: Callable[[], None] | None = None,
) -> object:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, GLib, Gtk  # type: ignore

    apply_brand_css()
    window = Adw.ApplicationWindow(application=app, title=APP_NAME)
    window.set_default_size(480, 360)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    box.set_margin_top(32)
    box.set_margin_bottom(32)
    box.set_margin_start(32)
    box.set_margin_end(32)

    title = Gtk.Label(label=APP_NAME)
    title.add_css_class("title-1")
    subtitle = Gtk.Label(label=TAGLINE)
    subtitle.set_wrap(True)
    help_lbl = Gtk.Label(label=HELP_PROGRESS)
    help_lbl.set_wrap(True)
    status = Gtk.Label(label="Sign in with Google to connect your Drive.")
    status.set_wrap(True)

    btn = Gtk.Button(label="Sign in with Google")
    btn.add_css_class("suggested-action")
    btn.add_css_class("pill")

    watching = {"active": False}

    def finish_signed_in(email: str) -> None:
        watching["active"] = False
        who = email or "Google account"
        status.set_text(f"Signed in as {who}")
        btn.set_sensitive(False)
        window.close()
        if on_signed_in is not None:
            on_signed_in()

    def poll_auth() -> bool:
        if not watching["active"]:
            return False
        try:
            auth_state, email, err = client.get_auth_status()
        except Exception as exc:  # noqa: BLE001
            status.set_text(f"Waiting for service…\n{exc}")
            return True
        if auth_state == "signed_in":
            finish_signed_in(email or "")
            return False
        if auth_state == "error":
            status.set_text(err or "Sign-in failed.")
            btn.set_sensitive(True)
            watching["active"] = False
            return False
        if auth_state == "signing_in":
            status.set_text("Waiting for Google sign-in to finish…")
        return True

    def start_watching() -> None:
        if watching["active"]:
            return
        watching["active"] = True
        GLib.timeout_add(500, poll_auth)

    def on_click(_btn) -> None:  # type: ignore[no-untyped-def]
        btn.set_sensitive(False)
        try:
            ok, msg = client.start_sign_in()
            status.set_text(msg if ok else f"Could not start sign-in: {msg}")
            if ok:
                start_watching()
            else:
                btn.set_sensitive(True)
        except Exception as exc:  # noqa: BLE001
            status.set_text(f"Service unavailable: {exc}")
            btn.set_sensitive(True)

    btn.connect("clicked", on_click)

    # If sign-in already completed (e.g. previous attempt), transition immediately.
    def initial_check() -> bool:
        try:
            auth_state, email, _err = client.get_auth_status()
        except Exception:
            return False
        if auth_state == "signed_in":
            finish_signed_in(email or "")
        elif auth_state == "signing_in":
            status.set_text("Waiting for Google sign-in to finish…")
            start_watching()
        return False

    GLib.idle_add(initial_check)

    box.append(title)
    box.append(subtitle)
    box.append(help_lbl)
    box.append(status)
    box.append(btn)
    window.set_content(box)
    return window
