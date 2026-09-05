"""Kitelink GTK application entrypoint."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time

from kitelink.app.brand import apply_brand_css
from kitelink.app.client import ServiceClient
from kitelink.app.onboarding import build_onboarding
from kitelink.app.tray import TrayController
from kitelink.util.logging import get_logger

log = get_logger("kitelink.app")


def ensure_user_service() -> None:
    """Best-effort: start kitelink-service via systemd --user or spawn."""
    try:
        ServiceClient()
        return
    except Exception:
        pass

    result = subprocess.run(
        ["systemctl", "--user", "start", "kitelink.service"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return
    if shutil.which("kitelink-service"):
        subprocess.Popen(
            ["kitelink-service"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.8)


def wait_for_service(timeout: float = 8.0) -> ServiceClient | None:
    deadline = time.time() + timeout
    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            return ServiceClient()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(0.4)
    log.warning("Service not ready: %s", last_exc)
    return None


def main(argv: list[str] | None = None) -> int:
    _ = argv
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw  # type: ignore

    ensure_user_service()
    client = wait_for_service()

    app = Adw.Application(application_id="org.kitelink.App")
    session: dict = {"tray": None, "client": client}

    def show_onboarding(*, unavailable: bool = False) -> None:
        cl = session["client"]

        def after_sign_in() -> None:
            show_tray()

        def retry_service() -> None:
            ensure_user_service()
            session["client"] = wait_for_service(timeout=6.0)
            app.activate()

        win = build_onboarding(
            app,
            cl or _BrokenClient(),
            on_signed_in=after_sign_in,
            service_unavailable=unavailable,
            on_retry_service=retry_service,
        )
        win.present()

    def show_tray() -> None:
        cl = session["client"]
        if cl is None:
            show_onboarding(unavailable=True)
            return
        if session["tray"] is None:
            session["tray"] = TrayController(app, cl, on_sign_out=after_sign_out)
        session["tray"].present()

    def after_sign_out() -> None:
        tray = session["tray"]
        if tray is not None:
            tray.hide()
            session["tray"] = None
        show_onboarding(unavailable=False)

    def on_activate(application) -> None:  # type: ignore[no-untyped-def]
        _ = application
        apply_brand_css()
        cl = session["client"]
        if cl is None:
            ensure_user_service()
            session["client"] = wait_for_service(timeout=4.0)
            cl = session["client"]
        if cl is None:
            show_onboarding(unavailable=True)
            return
        try:
            auth_state, _email, _err = cl.get_auth_status()
        except Exception:
            auth_state = "signed_out"
        if auth_state == "signed_in":
            show_tray()
            return
        show_onboarding(unavailable=False)

    app.connect("activate", on_activate)
    return app.run(sys.argv)


class _BrokenClient:
    def start_sign_in(self) -> tuple[bool, str]:
        return False, "O serviço do Kitelink não está em execução."

    def get_auth_status(self) -> tuple[str, str, str]:
        return "signed_out", "", "service_unavailable"

    def get_connection_status(self) -> tuple[str, str, str]:
        return "stopped", "", ""


if __name__ == "__main__":
    raise SystemExit(main())
