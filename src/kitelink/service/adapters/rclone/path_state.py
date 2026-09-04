"""Approximate path availability from VFS cache + transferring set."""

from __future__ import annotations

import os
from pathlib import Path

from kitelink.service.state import Confidence, PathState
from kitelink.util.preferences import xdg_cache_dir


def _vfs_cache_root() -> Path:
    return xdg_cache_dir() / "vfs"


def path_state(
    path: str,
    *,
    transferring_names: set[str] | None = None,
    mountpoint: str | None = None,
) -> tuple[PathState, Confidence]:
    """Best-effort Phase 1 heuristic — prefer cloud_or_unknown when unsure."""
    transferring_names = transferring_names or set()
    p = Path(path)

    # Match transferring by suffix/name
    name = p.name
    for tname in transferring_names:
        if tname.endswith(path) or tname.endswith(name) or name in tname:
            return PathState.SYNCING, Confidence.MEDIUM

    # If path is not under mountpoint, unknown
    if mountpoint and not str(p).startswith(str(Path(mountpoint).expanduser())):
        return PathState.CLOUD_OR_UNKNOWN, Confidence.LOW

    # Heuristic: if open() would be instant from page cache / vfs — check vfs dir
    # rclone VFS cache layout varies; look for any cache file containing the name.
    cache_root = _vfs_cache_root()
    if cache_root.is_dir():
        try:
            for root, _dirs, files in os.walk(cache_root):
                for fname in files:
                    if name and name in fname:
                        return PathState.LOCALLY_AVAILABLE, Confidence.LOW
                # Limit walk depth cost
                if root.count(os.sep) - str(cache_root).count(os.sep) > 4:
                    break
        except OSError:
            pass

    # If the file exists on the FUSE mount with size > 0, still may be cloud-backed.
    # Conservative: cloud_or_unknown unless we found cache evidence.
    try:
        if p.exists() and p.is_file() and p.stat().st_size == 0:
            return PathState.CLOUD_OR_UNKNOWN, Confidence.LOW
    except OSError:
        return PathState.ERROR, Confidence.LOW

    return PathState.CLOUD_OR_UNKNOWN, Confidence.LOW
