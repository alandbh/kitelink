"""Transfer filter and aggregation — calm progress UX."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from kitelink.service.state import AggregatedTransferView, TransferActivity, TransferKind


@dataclass
class _Tracked:
    activity: TransferActivity
    first_seen: float
    last_seen: float


@dataclass
class TransferFilter:
    min_bytes: int = 20 * 1024 * 1024
    min_seconds: float = 3.0
    _active: dict[str, _Tracked] = field(default_factory=dict)

    def update(self, transfers: list[TransferActivity], now: float | None = None) -> AggregatedTransferView:
        now = time.monotonic() if now is None else now
        current_ids = {t.id for t in transfers}

        for t in transfers:
            existing = self._active.get(t.id)
            if existing is None:
                t.started_at = now
                self._active[t.id] = _Tracked(activity=t, first_seen=now, last_seen=now)
            else:
                t.started_at = existing.first_seen
                existing.activity = t
                existing.last_seen = now

        for tid in list(self._active):
            if tid not in current_ids:
                del self._active[tid]

        visible: list[TransferActivity] = []
        for tracked in self._active.values():
            act = tracked.activity
            duration = now - tracked.first_seen
            size = act.bytes_total or act.bytes_done
            passes = size >= self.min_bytes and duration >= self.min_seconds
            act.passes_filters = passes
            if passes:
                visible.append(act)

        if not visible:
            return AggregatedTransferView(active_count=0, primary=None, headline="")

        primary = max(
            visible,
            key=lambda a: (a.bytes_total or a.bytes_done, a.bytes_done),
        )
        count = len(visible)
        if count == 1:
            headline = f"Downloading {primary.display_name}"
        else:
            headline = f"{count} files transferring"
        return AggregatedTransferView(active_count=count, primary=primary, headline=headline)


def transfer_from_rclone(item: dict, now: float | None = None) -> TransferActivity:
    """Map an rclone RC transferring entry to TransferActivity (adapter helper)."""
    now = time.monotonic() if now is None else now
    name = str(item.get("name") or item.get("group") or "transfer")
    display = name.rsplit("/", 1)[-1]
    size = int(item.get("size") or 0)
    done = int(item.get("bytes") or 0)
    speed = float(item.get("speed") or 0)
    return TransferActivity(
        id=name,
        display_name=display,
        bytes_done=done,
        bytes_total=size if size > 0 else None,
        speed_bps=speed if speed > 0 else None,
        started_at=now,
        kind=TransferKind.DOWNLOAD,
    )
