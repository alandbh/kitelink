"""libsecret / Secret Service credential store."""

from __future__ import annotations

import json
from typing import Any

from kitelink.util.logging import get_logger

log = get_logger("kitelink.auth.keyring")

SERVICE_NAME = "org.kitelink.Credentials"
ACCOUNT_LABEL = "google-oauth"


class KeyringStore:
    """Store OAuth tokens in the system keyring (Secret Service)."""

    def __init__(self, service: str = SERVICE_NAME, account: str = ACCOUNT_LABEL) -> None:
        self.service = service
        self.account = account

    def _collection(self):  # type: ignore[no-untyped-def]
        import secretstorage

        bus = secretstorage.dbus_init()
        return secretstorage.get_default_collection(bus)

    def save(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload)
        try:
            collection = self._collection()
            if collection.is_locked():
                collection.unlock()
            # Replace existing
            for item in collection.get_all_items():
                attrs = item.get_attributes()
                if attrs.get("service") == self.service and attrs.get("account") == self.account:
                    item.delete()
            collection.create_item(
                f"Kitelink {self.account}",
                {"service": self.service, "account": self.account, "application": "kitelink"},
                data.encode("utf-8"),
                replace=True,
            )
        except Exception as exc:  # noqa: BLE001 — surface as soft failure
            log.error("Failed to save credentials to keyring: %s", exc)
            raise RuntimeError("Could not store credentials in the system keyring.") from exc

    def load(self) -> dict[str, Any] | None:
        try:
            collection = self._collection()
            if collection.is_locked():
                collection.unlock()
            for item in collection.get_all_items():
                attrs = item.get_attributes()
                if attrs.get("service") == self.service and attrs.get("account") == self.account:
                    raw = item.get_secret().decode("utf-8")
                    data = json.loads(raw)
                    return data if isinstance(data, dict) else None
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to load credentials: %s", exc)
            return None
        return None

    def clear(self) -> None:
        try:
            collection = self._collection()
            if collection.is_locked():
                collection.unlock()
            for item in list(collection.get_all_items()):
                attrs = item.get_attributes()
                if attrs.get("service") == self.service and attrs.get("account") == self.account:
                    item.delete()
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to clear credentials: %s", exc)
