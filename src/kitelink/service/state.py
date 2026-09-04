"""Shared runtime state models for the Kitelink service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class AuthState(StrEnum):
    SIGNED_OUT = "signed_out"
    SIGNING_IN = "signing_in"
    SIGNED_IN = "signed_in"
    ERROR = "error"


class ConnectionState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    ERROR = "error"


class PathState(StrEnum):
    CLOUD_OR_UNKNOWN = "cloud_or_unknown"
    SYNCING = "syncing"
    LOCALLY_AVAILABLE = "locally_available"
    ERROR = "error"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"


class TransferKind(StrEnum):
    DOWNLOAD = "download"
    UPLOAD = "upload"
    UNKNOWN = "unknown"


@dataclass
class AccountSession:
    account_email: str | None = None
    auth_state: AuthState = AuthState.SIGNED_OUT
    last_error: str | None = None


@dataclass
class MountConnection:
    mountpoint: str = ""
    connection_state: ConnectionState = ConnectionState.STOPPED
    backend_id: str = "rclone"
    rc_endpoint: str = "http://127.0.0.1:5573"
    last_error: str | None = None


@dataclass
class FileAvailability:
    path: str
    state: PathState = PathState.CLOUD_OR_UNKNOWN
    confidence: Confidence = Confidence.LOW
    updated_at: float = 0.0


@dataclass
class TransferActivity:
    id: str
    display_name: str
    bytes_done: int = 0
    bytes_total: int | None = None
    speed_bps: float | None = None
    started_at: float = 0.0
    passes_filters: bool = False
    kind: TransferKind = TransferKind.UNKNOWN


@dataclass
class AggregatedTransferView:
    active_count: int = 0
    primary: TransferActivity | None = None
    headline: str = ""


@dataclass
class UserPreferences:
    vfs_cache_max_size: str = "10G"
    progress_min_bytes: int = 20 * 1024 * 1024
    progress_min_seconds: float = 3.0
    start_on_login: bool = True
    locale: str = "system"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserPreferences:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class ServiceHealth:
    overall: ConnectionState = ConnectionState.STOPPED
    mount_active: bool = False
    monitor_active: bool = False
    recent_events: list[str] = field(default_factory=list)
