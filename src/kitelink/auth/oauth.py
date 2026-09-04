"""OAuth 2 loopback sign-in for installed desktop apps."""

from __future__ import annotations

import os
import threading
from typing import Any, Callable

from kitelink.auth.keyring_store import KeyringStore
from kitelink.util.logging import get_logger

log = get_logger("kitelink.auth.oauth")

# Public clients must supply their own Google Cloud OAuth client.
# Never commit real secrets; use env or packaging-time injection.
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


class OAuthError(RuntimeError):
    pass


def _client_config() -> dict[str, Any]:
    client_id = os.environ.get("KITELINK_GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("KITELINK_GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise OAuthError(
            "Missing KITELINK_GOOGLE_CLIENT_ID / KITELINK_GOOGLE_CLIENT_SECRET. "
            "Create an OAuth Desktop client in Google Cloud Console and export these env vars."
        )
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://127.0.0.1"],
        }
    }


class OAuthManager:
    def __init__(self, store: KeyringStore | None = None) -> None:
        self.store = store or KeyringStore()
        self._lock = threading.Lock()
        self._signing_in = False

    def load_tokens(self) -> dict[str, Any] | None:
        return self.store.load()

    def is_signed_in(self) -> bool:
        data = self.load_tokens()
        if not data:
            return False
        return bool(data.get("refresh_token") or data.get("token"))

    def account_email(self) -> str | None:
        data = self.load_tokens() or {}
        email = data.get("account_email")
        return str(email) if email else None

    def start_sign_in_async(
        self,
        on_success: Callable[[dict[str, Any]], None],
        on_error: Callable[[str], None],
    ) -> tuple[bool, str]:
        with self._lock:
            if self._signing_in:
                return False, "Sign-in already in progress."
            self._signing_in = True

        def worker() -> None:
            try:
                tokens = self._run_loopback_flow()
                self.store.save(tokens)
                on_success(tokens)
            except Exception as exc:  # noqa: BLE001
                log.error("OAuth sign-in failed: %s", exc)
                on_error(str(exc))
            finally:
                with self._lock:
                    self._signing_in = False

        threading.Thread(target=worker, name="kitelink-oauth", daemon=True).start()
        return True, "Opening browser for Google sign-in…"

    def _run_loopback_flow(self) -> dict[str, Any]:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_config(_client_config(), scopes=DEFAULT_SCOPES)
        creds = flow.run_local_server(
            host="127.0.0.1",
            port=0,
            open_browser=True,
            authorization_prompt_message="",
            success_message="Kitelink sign-in complete. You can close this window.",
        )
        email = self._fetch_email(creds.token) if creds.token else None
        return {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or DEFAULT_SCOPES),
            "account_email": email,
        }

    def _fetch_email(self, access_token: str) -> str | None:
        try:
            import requests

            resp = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15,
            )
            if resp.ok:
                return resp.json().get("email")
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not fetch account email: %s", exc)
        return None

    def clear(self) -> None:
        self.store.clear()
