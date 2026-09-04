"""Notification policy — never spam per-file banners for RC transfers.

Phase 1 default: tray aggregated status only.
`notify-send` is reserved for rare high-level events (optional, off by default).
"""

from __future__ import annotations

from kitelink.util.logging import get_logger

log = get_logger("kitelink.notifications")

# Hard policy flag — do not flip on without product review.
ALLOW_DESKTOP_NOTIFICATIONS = False


def notify_transfer_progress(_title: str, _body: str) -> None:
    """Intentionally a no-op for per-transfer progress (constitution II)."""
    return


def maybe_notify_high_level(title: str, body: str) -> None:
    if not ALLOW_DESKTOP_NOTIFICATIONS:
        log.debug("Suppressed notification: %s — %s", title, body)
        return
    try:
        import subprocess

        subprocess.run(
            ["notify-send", "--app-name=Kitelink", title, body],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        log.debug("notify-send failed: %s", exc)
