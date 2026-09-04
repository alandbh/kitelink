# Implementation Plan: Kitelink Phase 1 MVP

**Branch**: `001-kitelink-mvp` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-kitelink-mvp/spec.md`

## Summary

Ship a public Linux desktop client that gives GNOME/Nautilus users a Drive Desktop–like folder with guided OAuth, automatic mount at `~/Kitelink`, approximate sync emblems, and calm aggregated tray progress. Phase 1 orchestrates **rclone mount + Remote Control** behind a versioned **D-Bus** service so GTK UI and Nautilus extension stay swappable for a Phase 2 native FUSE/Drive API engine.

## Technical Context

**Language/Version**: Python 3.12 (app, service, Nautilus extension)

**Primary Dependencies**: GTK 4, libadwaita, PyGObject, dbus-next (or dasbus), Secret Service via libsecret, rclone (≥ version gate documented in packaging), systemd --user, nautilus-python

**Storage**: rclone VFS cache directory under `~/.cache/kitelink/`; app preferences in XDG config; OAuth tokens in GNOME Keyring/libsecret; no application SQL DB in Phase 1

**Testing**: pytest (unit + contract tests for D-Bus XML/API); manual/integration checklist on Zorin/Ubuntu VM

**Target Platform**: Linux desktop — Zorin OS / Ubuntu LTS with GNOME Files (Nautilus), FUSE 3, systemd user session

**Project Type**: desktop-app (tray/settings + user service + file-manager extension + native `.deb`)

**Performance Goals**: Tray progress for large uncached open ≤ 5s to first visible update; emblem queries answered from local cache without blocking Nautilus; folder browse produces zero progress banners

**Constraints**: RC bound to 127.0.0.1 only; no telemetry by default; emblems best-effort/approximate; Flatpak not primary; restricted Google OAuth scope for public release

**Scale/Scope**: Single Google account per OS user; My Drive focus; one mountpoint; Phase 1 codebase sized for small team / agent-driven SDD increments

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Linux Desktop First | PASS | `.deb` + Nautilus + systemd user; no Flatpak-primary |
| II. Calm Progress, Never Spam | PASS | Aggregated tray + size/duration filters in design |
| III. Swappable Sync Backend | PASS | D-Bus contract + rclone adapter boundary |
| IV. Honest Sync States | PASS | Approximate emblems documented; conservative unknown/cloud |
| V. Secrets Stay Secret | PASS | libsecret; localhost RC; no secret logging |

**Post-design re-check**: PASS — contracts keep UI free of rclone types; progress rules encoded in transfer filter service; packaging plan remains `.deb`-first.

## Project Structure

### Documentation (this feature)

```text
specs/001-kitelink-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dbus-org.kitelink.Service1.xml
│   └── README.md
└── tasks.md
```

### Source Code (repository root)

```text
src/kitelink/
├── __init__.py
├── app/                 # GTK 4 + libadwaita tray / preferences / onboarding
├── service/             # user daemon: D-Bus, mount lifecycle, transfer monitor
│   ├── adapters/
│   │   └── rclone/      # mount unit, RC client, cache heuristics
│   ├── transfer_filter.py
│   └── state.py
├── ipc/                 # D-Bus server/client helpers + interface version
├── auth/                # OAuth loopback + libsecret store
└── util/

extensions/nautilus/
└── kitelink.py          # emblems via D-Bus (nautilus-python)

packaging/debian/        # .deb control, systemd user units, install paths
systemd/user/
├── kitelink.service
└── kitelink-mount.service   # or generated unit managed by service

assets/brand/            # logo + palette (owner-supplied)

tests/
├── unit/
├── contract/            # D-Bus interface expectations
└── integration/         # optional VM scripts / checklists
```

**Structure Decision**: Single Python package monorepo with separate Nautilus extension entry and Debian packaging tree. Keeps Phase 1 cohesive while isolating the rclone adapter for Phase 2 replacement.

## Complexity Tracking

> No constitution violations requiring justification.
