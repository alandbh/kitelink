"""Phase 2 boundary: sync backends live under adapters/.

Phase 1 uses `rclone/`. Phase 2 should add a native FUSE/Drive API adapter that
implements the same operations used by `KitelinkCore`:

- ensure_authenticated_remote / clear_remote_secrets
- start_mount / stop_mount / restart_mount
- is_mount_active
- fetch_transferring
- path_state(path)

UI and D-Bus (`org.kitelink.Service1`) must not import rclone modules directly.
Keep rclone types and RC URLs inside this package.
"""
