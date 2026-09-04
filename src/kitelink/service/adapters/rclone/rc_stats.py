"""RC stats → TransferActivity list."""

from __future__ import annotations

from kitelink.service.adapters.rclone.rc import RcloneRC
from kitelink.service.state import TransferActivity
from kitelink.service.transfer_filter import transfer_from_rclone
from kitelink.util.logging import get_logger

log = get_logger("kitelink.rclone.rc_stats")


class RcStatsPoller:
    def __init__(self, rc: RcloneRC | None = None) -> None:
        self.rc = rc or RcloneRC()

    def fetch_transferring(self) -> list[TransferActivity]:
        try:
            stats = self.rc.core_stats()
        except Exception:  # noqa: BLE001
            return []
        transferring = stats.get("transferring") or []
        if not isinstance(transferring, list):
            return []
        return [transfer_from_rclone(item) for item in transferring if isinstance(item, dict)]
