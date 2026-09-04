"""rclone mount lifecycle via systemd --user."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from kitelink.service.adapters.rclone import auth_bridge, unit
from kitelink.util.logging import get_logger

log = get_logger("kitelink.rclone.mount")

MOUNT_UNIT = "kitelink-mount.service"


def _systemctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", "--user", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def rclone_binary() -> str:
    return shutil.which("rclone") or "/usr/bin/rclone"


def ensure_mountpoint(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def start_mount(mountpoint: Path, cache_max_size: str = "10G") -> tuple[bool, str]:
    ensure_mountpoint(mountpoint)
    rclone = rclone_binary()
    if not Path(rclone).exists() and shutil.which("rclone") is None:
        return False, "rclone is not installed. Install rclone ≥ 1.60."

    unit.write_mount_unit(
        remote=f"{auth_bridge.REMOTE_NAME}:",
        mountpoint=mountpoint,
        cache_max_size=cache_max_size,
        rclone_bin=rclone,
        config_path=auth_bridge.rclone_config_path(),
    )
    _systemctl("daemon-reload")
    enable = _systemctl("enable", "--now", MOUNT_UNIT)
    if enable.returncode != 0:
        msg = (enable.stderr or enable.stdout or "Failed to start mount service").strip()
        log.error("Mount start failed: %s", msg)
        return False, msg
    return True, "Mount started."


def stop_mount(mountpoint: Path | None = None) -> tuple[bool, str]:
    _systemctl("disable", "--now", MOUNT_UNIT)
    if mountpoint:
        subprocess.run(
            ["fusermount3", "-uz", str(mountpoint)],
            check=False,
            capture_output=True,
            text=True,
        )
    return True, "Mount stopped."


def restart_mount(mountpoint: Path, cache_max_size: str = "10G") -> tuple[bool, str]:
    stop_mount(mountpoint)
    return start_mount(mountpoint, cache_max_size=cache_max_size)


def is_active() -> bool:
    result = _systemctl("is-active", MOUNT_UNIT)
    return result.stdout.strip() == "active"
