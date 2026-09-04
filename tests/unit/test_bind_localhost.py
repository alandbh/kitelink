"""RC bind must remain loopback-only."""

from __future__ import annotations

import pytest

from kitelink.service.adapters.rclone.rc import assert_localhost_url
from kitelink.service.adapters.rclone.unit import RC_ADDR, render_mount_unit
from pathlib import Path


def test_assert_localhost_accepts_loopback() -> None:
    assert_localhost_url("http://127.0.0.1:5572")
    assert_localhost_url("http://localhost:5572")


def test_assert_localhost_rejects_lan() -> None:
    with pytest.raises(ValueError):
        assert_localhost_url("http://0.0.0.0:5572")
    with pytest.raises(ValueError):
        assert_localhost_url("http://192.168.1.10:5572")


def test_mount_unit_rc_is_loopback() -> None:
    text = render_mount_unit(mountpoint=Path("/home/user/Kitelink"))
    assert f"--rc-addr {RC_ADDR}" in text
    assert "0.0.0.0" not in text
    assert RC_ADDR.startswith("127.0.0.1")
