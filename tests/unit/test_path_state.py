"""Unit tests for rclone VFS path-state heuristics."""

from __future__ import annotations

from pathlib import Path

from kitelink.service.adapters.rclone.path_state import cache_copy_for, path_state
from kitelink.service.state import PathState


def test_cache_copy_maps_under_mount(tmp_path: Path, monkeypatch) -> None:
    mount = tmp_path / "Kitelink"
    cache = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache))
    target = mount / "1-Trabalhos" / "file.docx"
    mapped = cache_copy_for(str(target), str(mount))
    assert mapped == cache / "kitelink" / "vfs" / "vfs" / "kitelink" / "1-Trabalhos" / "file.docx"


def test_locally_available_when_vfs_copy_exists(tmp_path: Path, monkeypatch) -> None:
    mount = tmp_path / "Kitelink"
    cache_home = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    target = mount / "docs" / "readme.txt"
    cached = cache_copy_for(str(target), str(mount))
    assert cached is not None
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"hello")
    state, _conf = path_state(str(target), mountpoint=str(mount))
    assert state == PathState.LOCALLY_AVAILABLE


def test_cloud_when_no_vfs_copy(tmp_path: Path, monkeypatch) -> None:
    mount = tmp_path / "Kitelink"
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    target = mount / "docs" / "missing.txt"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"placeholder")
    state, _conf = path_state(str(target), mountpoint=str(mount))
    assert state == PathState.CLOUD_OR_UNKNOWN


def test_syncing_when_name_in_transfer_set(tmp_path: Path) -> None:
    mount = tmp_path / "Kitelink"
    target = mount / "big.bin"
    state, _conf = path_state(
        str(target),
        transferring_names={"big.bin"},
        mountpoint=str(mount),
    )
    assert state == PathState.SYNCING
