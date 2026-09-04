"""rclone RC client — localhost only."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from kitelink.util.logging import get_logger

log = get_logger("kitelink.rclone.rc")

DEFAULT_RC_URL = "http://127.0.0.1:5573"


def assert_localhost_url(url: str) -> None:
    """Reject non-loopback RC endpoints (constitution / security)."""
    lowered = url.lower().strip()
    if not (
        lowered.startswith("http://127.0.0.1:")
        or lowered.startswith("http://localhost:")
        or lowered.startswith("http://[::1]:")
    ):
        raise ValueError(f"RC URL must be loopback-only, got: {url}")


class RcloneRC:
    def __init__(self, base_url: str = DEFAULT_RC_URL) -> None:
        assert_localhost_url(base_url)
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, payload: dict[str, Any] | None = None, timeout: float = 3.0) -> dict[str, Any]:
        url = f"{self.base_url}/{method.lstrip('/')}"
        assert_localhost_url(self.base_url)
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                parsed = json.loads(body)
                return parsed if isinstance(parsed, dict) else {}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            log.debug("RC %s failed: %s", method, exc)
            raise

    def core_stats(self) -> dict[str, Any]:
        return self.call("core/stats")
