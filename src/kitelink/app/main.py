"""Kitelink GTK application entrypoint."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time

from kitelink.app.brand import apply_brand_css
from kitelink.app.client import ServiceClient
from kitelink.app.help_copy import APP_NAME
from kitelink.app.onboarding import build_onboarding
from kitelink.app.tray import TrayController
from kitelink.util.logging import get_logger

log = get_logger("kitelink.app")


def ensure_user_service() -> None:
    """Best-effort: start kitelink-service via systemd --user or spawn."""
    # Already running (e.g. terminal session) — do not spawn a duplicate.
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
    # Fallback: spawn service if entrypoint is on PATH
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

    def on_activate(application) -> None:  # type: ignore[no-untyped-def]
        apply_brand_css()
        if client is None:
            # Show onboarding that explains service failure
            win = build_onboarding(application, _BrokenClient())
            win.present()
            return
        try:
            auth_state, _email, _err = client.get_auth_status()
        except Exception:
            auth_state = "signed_out"

        tray = TrayController(application, client)
        if auth_state == "signed_in":
            tray.present()
            return

        def after_sign_in() -> None:
            tray.present()

        win = build_onboarding(application, client, on_signed_in=after_sign_in)
        win.present()

    app.connect("activate", on_activate)
    return app.run(sys.argv)


class _BrokenClient:
    def start_sign_in(self) -> tuple[bool, str]:
        return False, "Kitelink service is not running. Try: systemctl --user start kitelink.service"


if __name__ == "__main__":
    raise SystemExit(main())
