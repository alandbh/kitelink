# Data Model: Kitelink Phase 1 MVP

**Date**: 2026-09-03  
**Feature**: `001-kitelink-mvp`

Phase 1 persists little application state. Most “entities” are runtime views derived from rclone + keyring + preferences.

## Entities

### AccountSession

| Field | Type | Notes |
|-------|------|-------|
| account_email | string \| null | Display identity after sign-in |
| auth_state | enum | `signed_out`, `signing_in`, `signed_in`, `error` |
| last_error | string \| null | User-safe message; never tokens |
| keyring_ref | opaque | libsecret item identity managed by auth module |

**Rules**: Sign-out clears keyring item and forces mount stop. Only one session per OS user in Phase 1.

### MountConnection

| Field | Type | Notes |
|-------|------|-------|
| mountpoint | path | Default `~/Kitelink` |
| connection_state | enum | `stopped`, `starting`, `connected`, `degraded`, `error` |
| backend_id | string | Phase 1: `rclone` |
| rc_endpoint | string | Always loopback URL |
| last_error | string \| null | User-safe |

**Transitions**: `stopped → starting → connected`; any state → `error`; `connected → degraded` on transient issues; sign-out/stop → `stopped`.

### FileAvailability

| Field | Type | Notes |
|-------|------|-------|
| path | string | Absolute path under mountpoint |
| state | enum | `cloud_or_unknown`, `syncing`, `locally_available`, `error` |
| confidence | enum | `low`, `medium` (Phase 1 never claims `high`) |
| updated_at | timestamp | Local monotonic/wall for cache invalidation |

**Rules**: Prefer `cloud_or_unknown` when cache heuristics are inconclusive. Nautilus asks by path; service answers from local heuristic cache.

### TransferActivity

| Field | Type | Notes |
|-------|------|-------|
| id | string | Stable id for UI (path or backend transfer name) |
| display_name | string | Basename |
| bytes_done | int | |
| bytes_total | int \| null | |
| speed_bps | float \| null | |
| started_at | timestamp | For duration filter |
| passes_filters | bool | Size + duration gates |
| kind | enum | `download`, `upload`, `unknown` |

### AggregatedTransferView

| Field | Type | Notes |
|-------|------|-------|
| active_count | int | Count of filtered transfers |
| primary | TransferActivity \| null | Largest or longest |
| headline | string | e.g. “3 files transferring” |

### UserPreferences

| Field | Type | Default (draft) |
|-------|------|-----------------|
| vfs_cache_max_size | string | `10G` |
| progress_min_bytes | int | `20971520` (20 MiB) |
| progress_min_seconds | float | `3.0` |
| start_on_login | bool | `true` |
| locale | string | system |

Stored under XDG config (`~/.config/kitelink/`).

### ServiceHealth

| Field | Type | Notes |
|-------|------|-------|
| overall | enum | mirrors connection + auth summary for tray |
| mount_active | bool | |
| monitor_active | bool | transfer watcher |
| recent_events | list | ring buffer of user-safe diagnostics |

## Relationships

```text
AccountSession 1 ── controls ──► MountConnection
MountConnection 1 ── produces ► FileAvailability (many)
MountConnection 1 ── produces ► TransferActivity (many)
TransferActivity * ── filtered into ► AggregatedTransferView
UserPreferences ── configures ► MountConnection + filters
```

## Persistence map

| Entity | Persistence |
|--------|-------------|
| AccountSession secrets | libsecret |
| UserPreferences | XDG config file |
| MountConnection | derived + systemd unit state |
| FileAvailability | in-memory cache (+ optional short TTL file cache) |
| TransferActivity | ephemeral from RC polls |
