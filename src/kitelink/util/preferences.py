"""XDG-based preferences persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from kitelink.service.state import UserPreferences

APP_NAME = "kitelink"


def xdg_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def xdg_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def xdg_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def preferences_path() -> Path:
    return xdg_config_dir() / "preferences.json"


def load_preferences() -> UserPreferences:
    path = preferences_path()
    if not path.exists():
        return UserPreferences()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return UserPreferences()
        return UserPreferences.from_dict(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return UserPreferences()


def save_preferences(prefs: UserPreferences) -> None:
    path = preferences_path()
    path.write_text(json.dumps(prefs.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_mountpoint() -> Path:
    return Path.home() / "Kitelink"
