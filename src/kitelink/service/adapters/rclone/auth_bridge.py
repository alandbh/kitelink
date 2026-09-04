"""Map OAuth tokens into a private rclone config (never log contents)."""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Any

from kitelink.util.logging import get_logger
from kitelink.util.preferences import xdg_config_dir

log = get_logger("kitelink.rclone.auth_bridge")

REMOTE_NAME = "kitelink"


def rclone_config_path() -> Path:
    path = xdg_config_dir() / "rclone"
    path.mkdir(parents=True, exist_ok=True)
    return path / "rclone.conf"


def write_remote_from_tokens(tokens: dict[str, Any]) -> Path:
    """Create/update the kitelink: Google Drive remote from OAuth tokens."""
    conf_path = rclone_config_path()
    parser = configparser.ConfigParser()
    if conf_path.exists():
        parser.read(conf_path)

    section = REMOTE_NAME
    if not parser.has_section(section):
        parser.add_section(section)

    client_id = tokens.get("client_id") or os.environ.get("KITELINK_GOOGLE_CLIENT_ID", "")
    client_secret = tokens.get("client_secret") or os.environ.get(
        "KITELINK_GOOGLE_CLIENT_SECRET", ""
    )
    refresh = tokens.get("refresh_token") or ""
    access = tokens.get("token") or ""

    # rclone Google Drive token JSON format
    token_json = (
        "{"
        f'"access_token":"{access}",'
        f'"token_type":"Bearer",'
        f'"refresh_token":"{refresh}",'
        '"expiry":"0001-01-01T00:00:00Z"'
        "}"
    )

    parser.set(section, "type", "drive")
    parser.set(section, "scope", "drive")
    if client_id:
        parser.set(section, "client_id", str(client_id))
    if client_secret:
        parser.set(section, "client_secret", str(client_secret))
    parser.set(section, "token", token_json)

    with conf_path.open("w", encoding="utf-8") as fh:
        parser.write(fh)
    try:
        os.chmod(conf_path, 0o600)
    except OSError:
        pass
    log.info("Updated rclone remote configuration for Kitelink")
    return conf_path


def clear_remote() -> None:
    conf_path = rclone_config_path()
    if not conf_path.exists():
        return
    parser = configparser.ConfigParser()
    parser.read(conf_path)
    if parser.has_section(REMOTE_NAME):
        parser.remove_section(REMOTE_NAME)
        with conf_path.open("w", encoding="utf-8") as fh:
            parser.write(fh)
        log.info("Cleared Kitelink rclone remote")
