# Contracts: Kitelink Phase 1

This folder defines the **stable local IPC** between:

- GTK tray / preferences app
- Nautilus extension
- Kitelink user service (rclone adapter behind it)

Phase 2 MUST implement the same semantic contract (same interface name or a documented version bump with compatibility).

## Files

| File | Purpose |
|------|---------|
| [dbus-org.kitelink.Service1.xml](./dbus-org.kitelink.Service1.xml) | D-Bus introspection sketch for `org.kitelink.Service1` |
| This README | Usage notes and non-goals |

## Rules

1. No rclone-specific types in method signatures.
2. Path state answers MUST be fast and local (no Google round-trips on the D-Bus thread).
3. Transfer signals MUST already be filter-eligible or clients MUST use `GetAggregatedTransfers` only for UI banners.
4. Errors returned to clients MUST be user-safe strings (no tokens).
