"""Approximate path availability from VFS cache + transferring set."""

from __future__ import annotations

from pathlib import Path

from kitelink.service.adapters.rclone.auth_bridge import REMOTE_NAME
from kitelink.service.state import Confidence, PathState
from kitelink.util.preferences import xdg_cache_dir


def _vfs_data_root() -> Path:
    # rclone --cache-dir X with vfs-cache-mode full stores copies at X/vfs/<remote>/
    return xdg_cache_dir() / "vfs" / "vfs" / REMOTE_NAME


def cache_copy_for(path: str, mountpoint: str) -> Path | None:
    """Return the on-disk VFS cache copy for a mount path, if the mapping is valid."""
    try:
        target = Path(path).expanduser()
        root = Path(mountpoint).expanduser()
        rel = target.relative_to(root)
    except ValueError:
        return None
    if rel.as_posix() == ".":
        return None
    return _vfs_data_root() / rel


def path_state(
    path: str,
    *,
    transferring_names: set[str] | None = None,
    mountpoint: str | None = None,
) -> tuple[PathState, Confidence]:
    """Best-effort Phase 1 heuristic — prefer cloud_or_unknown when unsure."""
    transferring_names = transferring_names or set()
    p = Path(path)
    name = p.name

    for tname in transferring_names:
        if tname.endswith(path) or tname.endswith(name) or (name and name in tname):
            return PathState.SYNCING, Confidence.MEDIUM

    if mountpoint and not str(p.expanduser()).startswith(str(Path(mountpoint).expanduser())):
        return PathState.CLOUD_OR_UNKNOWN, Confidence.LOW

    if mountpoint:
        cached = cache_copy_for(str(p), mountpoint)
        try:
            if cached is not None and cached.is_file() and cached.stat().st_size > 0:
                return PathState.LOCALLY_AVAILABLE, Confidence.MEDIUM
        except OSError:
            return PathState.ERROR, Confidence.LOW

    try:
        if p.exists() and p.is_file() and p.stat().st_size == 0:
            return PathState.CLOUD_OR_UNKNOWN, Confidence.LOW
    except OSError:
        return PathState.ERROR, Confidence.LOW

    return PathState.CLOUD_OR_UNKNOWN, Confidence.LOW
