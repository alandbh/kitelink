"""Session lifecycle: sign-out clears mount, keyring, and adapter secrets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kitelink.auth.oauth import OAuthManager
from kitelink.service.state import AuthState
from kitelink.util.logging import get_logger, safe_event

if TYPE_CHECKING:
    from kitelink.service.core import KitelinkCore

log = get_logger("kitelink.auth.session")


class SessionManager:
    def __init__(self, core: KitelinkCore, oauth: OAuthManager | None = None) -> None:
        self.core = core
        self.oauth = oauth or OAuthManager()

    def refresh_from_store(self) -> None:
        if self.oauth.is_signed_in():
            self.core.session.auth_state = AuthState.SIGNED_IN
            self.core.session.account_email = self.oauth.account_email()
            self.core.session.last_error = None
        else:
            self.core.session.auth_state = AuthState.SIGNED_OUT
            self.core.session.account_email = None

    def sign_out(self) -> tuple[bool, str]:
        try:
            self.core.stop_mount()
        except Exception as exc:  # noqa: BLE001
            log.warning("Mount stop during sign-out: %s", exc)

        try:
            self.core.rclone.clear_remote_secrets()
        except Exception as exc:  # noqa: BLE001
            log.warning("Adapter secret clear: %s", exc)

        self.oauth.clear()
        self.core.session.auth_state = AuthState.SIGNED_OUT
        self.core.session.account_email = None
        self.core.session.last_error = None
        self.core.push_event(safe_event("Signed out"))
        self.core.emit_status_changed()
        return True, "Signed out."
