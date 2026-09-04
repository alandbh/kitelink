"""Apply preference changes to mount unit / filter (delegates to core)."""

from __future__ import annotations

from kitelink.service.core import KitelinkCore


def apply_preferences_json(core: KitelinkCore, raw: str) -> tuple[bool, str]:
    return core.set_preferences_json(raw)
