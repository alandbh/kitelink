"""Unit tests for calm transfer filtering."""

from __future__ import annotations

from kitelink.service.state import TransferActivity, TransferKind
from kitelink.service.transfer_filter import TransferFilter


def _act(id_: str, size: int, done: int = 0) -> TransferActivity:
    return TransferActivity(
        id=id_,
        display_name=id_.rsplit("/", 1)[-1],
        bytes_done=done,
        bytes_total=size,
        kind=TransferKind.DOWNLOAD,
    )


def test_ignores_small_short_transfers() -> None:
    filt = TransferFilter(min_bytes=20 * 1024 * 1024, min_seconds=3.0)
    t0 = 100.0
    view = filt.update([_act("thumb.jpg", 200_000)], now=t0)
    assert view.active_count == 0
    view = filt.update([_act("thumb.jpg", 200_000)], now=t0 + 10)
    assert view.active_count == 0


def test_shows_large_transfer_after_duration() -> None:
    filt = TransferFilter(min_bytes=20 * 1024 * 1024, min_seconds=3.0)
    big = 70 * 1024 * 1024
    t0 = 50.0
    view = filt.update([_act("doc.pdf", big, done=1_000_000)], now=t0)
    assert view.active_count == 0
    view = filt.update([_act("doc.pdf", big, done=10_000_000)], now=t0 + 3.5)
    assert view.active_count == 1
    assert "doc.pdf" in view.headline


def test_aggregates_multiple_visible_transfers() -> None:
    filt = TransferFilter(min_bytes=1, min_seconds=0)
    t0 = 1.0
    view = filt.update(
        [_act("a.bin", 50_000_000, 10), _act("b.bin", 60_000_000, 20)],
        now=t0,
    )
    assert view.active_count == 2
    assert "2 files" in view.headline


def test_clears_when_transfer_disappears() -> None:
    filt = TransferFilter(min_bytes=1, min_seconds=0)
    t0 = 1.0
    filt.update([_act("a.bin", 50_000_000)], now=t0)
    view = filt.update([], now=t0 + 1)
    assert view.active_count == 0
    assert view.headline == ""
