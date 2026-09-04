# Research: Kitelink Phase 1 MVP

**Date**: 2026-09-03  
**Feature**: `001-kitelink-mvp`

## R1 — Sync backend for Phase 1

- **Decision**: Orchestrate `rclone mount` with VFS cache mode `full` and Remote Control on `127.0.0.1`.
- **Rationale**: Proven on Zorin for transparent Nautilus access; fastest path to validate UX without building FUSE yet (`readme-1.md`).
- **Alternatives considered**:
  - Own FUSE + Drive API immediately — higher fidelity, much longer time-to-MVP.
  - Full local mirror sync — simple badges, wrong product (disk-heavy, not on-demand).
  - gio/google-drive:// only — poor Windows-parity UX, weak offline/cache control.

## R2 — UI toolkit

- **Decision**: GTK 4 + libadwaita via PyGObject for tray, onboarding, and preferences.
- **Rationale**: Native GNOME/Zorin look; aligns with Nautilus ecosystem; Python matches extension language for Phase 1 speed.
- **Alternatives considered**: Electron (heavy, less native); Rust+relm4/gtk-rs (better long-term for daemon, slower MVP UI); Qt (weaker GNOME integration).

## R3 — File manager emblems

- **Decision**: `nautilus-python` InfoProvider calling Kitelink D-Bus for per-path state; symbolic emblems for cloud/sync/local/error.
- **Rationale**: Official extension path; keeps network I/O out of Nautilus by querying local service only.
- **Alternatives considered**: C extension (faster, heavier); no emblems until Phase 2 (fails a core JTBD).

## R4 — Progress UX (anti-spam)

- **Decision**: Tray-only aggregated progress with filters: default min size 20 MB, min duration 3 s; update single status surface; suppress completion for short/cancelled reads.
- **Rationale**: Failed `notify-send` monitor treated thumbnail reads as user downloads (`readme-1.md` §20).
- **Alternatives considered**: Per-file notifications (rejected); Nautilus-native progress bar (not available for FUSE reads).

## R5 — IPC contract

- **Decision**: Versioned D-Bus session interface `org.kitelink.Service1` for status, transfers, path state, preferences, auth lifecycle.
- **Rationale**: Constitution Principle III; GNOME-native; survives backend swap.
- **Alternatives considered**: Unix socket JSON-RPC (fine, less GNOME-idiomatic); gRPC (overkill).

## R6 — Auth & secrets

- **Decision**: OAuth 2 loopback for installed apps; store refresh token in libsecret; app owns Google Cloud OAuth client for public distribution; plan restricted `drive` scope verification.
- **Rationale**: Google desktop guidance; public product cannot use `drive.file` alone for whole-Drive mirror.
- **Alternatives considered**: Embed rclone interactive config only (poor branded UX); service accounts (wrong for consumer My Drive).

## R7 — Packaging

- **Decision**: Native `.deb` installing app, user systemd units, Nautilus extension path, and rclone dependency/version gate (distro package or vendored binary with license compliance).
- **Rationale**: FUSE + extension + systemd need host integration; Flatpak sandbox fights the design.
- **Alternatives considered**: Flatpak primary (rejected for MVP); AppImage (weaker systemd/extension story).

## R8 — Availability state heuristics (Phase 1)

- **Decision**: Approximate states from rclone VFS cache presence + RC transferring set + mount health; prefer `cloud_or_unknown` when unsure.
- **Rationale**: Honest Sync States principle; perfect badges need Phase 2 metadata DB.
- **Alternatives considered**: Always-gray emblems (too weak); pretend perfect sync (misleading).

## R9 — Phase 2 migration posture

- **Decision**: Keep rclone types inside `adapters/rclone/`; D-Bus payloads use Kitelink enums only; document Phase 2 daemon (Rust+FUSE+SQLite) as drop-in service implementing the same interface version or `Service2` with compatibility shim.
- **Rationale**: Avoid UI rewrite; match PRD phased strategy.
- **Alternatives considered**: Leak rclone paths/stats into UI (locks architecture).
