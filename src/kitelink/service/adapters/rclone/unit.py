"""Generate systemd --user unit for rclone mount with localhost RC."""

from __future__ import annotations

from pathlib import Path

from kitelink.util.preferences import xdg_cache_dir, xdg_config_dir

MOUNT_UNIT_NAME = "kitelink-mount.service"
# 5572 is rclone's common default and often taken by other mounts.
RC_ADDR = "127.0.0.1:5573"


def user_systemd_dir() -> Path:
    path = Path.home() / ".config" / "systemd" / "user"
    path.mkdir(parents=True, exist_ok=True)
    return path


def mount_unit_path() -> Path:
    return user_systemd_dir() / MOUNT_UNIT_NAME


def render_mount_unit(
    *,
    remote: str = "kitelink:",
    mountpoint: Path,
    cache_max_size: str = "10G",
    rclone_bin: str = "/usr/bin/rclone",
    config_path: Path | None = None,
) -> str:
    config_path = config_path or (xdg_config_dir() / "rclone" / "rclone.conf")
    cache_dir = xdg_cache_dir() / "vfs"
    # RC is intentionally loopback-only
    return f"""[Unit]
Description=Kitelink Google Drive mount (rclone)
After=default.target network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={rclone_bin} mount {remote} "{mountpoint}" \\
    --config "{config_path}" \\
    --cache-dir "{cache_dir}" \\
    --vfs-cache-mode full \\
    --vfs-cache-max-size {cache_max_size} \\
    --vfs-cache-max-age 24h \\
    --dir-cache-time 24h \\
    --poll-interval 1m \\
    --buffer-size 32M \\
    --rc \\
    --rc-addr {RC_ADDR}
ExecStop=/usr/bin/fusermount3 -uz "{mountpoint}"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""


def write_mount_unit(**kwargs) -> Path:  # type: ignore[no-untyped-def]
    path = mount_unit_path()
    path.write_text(render_mount_unit(**kwargs), encoding="utf-8")
    return path
