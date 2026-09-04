"""Rclone adapter facade used by KitelinkCore."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kitelink.service.adapters.rclone import auth_bridge, mount, path_state as path_state_mod
from kitelink.service.adapters.rclone.rc import DEFAULT_RC_URL, RcloneRC
from kitelink.service.adapters.rclone.rc_stats import RcStatsPoller
from kitelink.service.state import Confidence, PathState, TransferActivity


class RcloneAdapter:
    def __init__(self) -> None:
        self.rc = RcloneRC(DEFAULT_RC_URL)
        self.poller = RcStatsPoller(self.rc)
        self._transferring_names: set[str] = set()

    def apply_tokens(self, tokens: dict[str, Any]) -> None:
        auth_bridge.write_remote_from_tokens(tokens)

    def clear_remote_secrets(self) -> None:
        auth_bridge.clear_remote()

    def start_mount(self, mountpoint: Path, cache_max_size: str = "10G") -> tuple[bool, str]:
        return mount.start_mount(mountpoint, cache_max_size=cache_max_size)

    def stop_mount(self, mountpoint: Path | None = None) -> tuple[bool, str]:
        return mount.stop_mount(mountpoint)

    def restart_mount(self, mountpoint: Path, cache_max_size: str = "10G") -> tuple[bool, str]:
        return mount.restart_mount(mountpoint, cache_max_size=cache_max_size)

    def is_mount_active(self) -> bool:
        return mount.is_active()

    def fetch_transferring(self) -> list[TransferActivity]:
        items = self.poller.fetch_transferring()
        self._transferring_names = {t.id for t in items}
        return items

    def path_state(self, path: str, mountpoint: str | None = None) -> tuple[PathState, Confidence]:
        return path_state_mod.path_state(
            path,
            transferring_names=self._transferring_names,
            mountpoint=mountpoint,
        )
