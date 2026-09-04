# Quickstart validation: Kitelink Phase 1 MVP

**Purpose**: Prove the Phase 1 feature end-to-end on a supported desktop after implementation.  
**Not**: a full automated suite — use as a manual/VM gate alongside unit/contract tests.

## Prerequisites

- Zorin OS or Ubuntu LTS with GNOME Files (Nautilus)
- FUSE 3, systemd user session, libsecret/GNOME Keyring unlocked
- Google account available for OAuth Test users (or verified app)
- Built `.deb` or editable install from this repo (see [`packaging/README.md`](../../packaging/README.md))
- `KITELINK_GOOGLE_CLIENT_ID` / `KITELINK_GOOGLE_CLIENT_SECRET` set for the user session
- Network access to Google

Printable result sheet: [vm-validation-checklist.md](./vm-validation-checklist.md) (scenario Q5).

## Setup

1. Install package (or development install) so that:
   - `kitelink` app is launchable
   - user service units are installed
   - Nautilus extension is on the expected path
2. Confirm no stale mounts: `~/Kitelink` absent or empty and not busy.
3. Launch Kitelink from the app menu.

## Scenarios

### Q1 — Sign-in and folder (US1)

1. Choose sign-in; complete Google consent in the browser.
2. Expect `~/Kitelink` to appear with Drive content in Files.
3. Reboot or re-login to the graphical session.
4. Expect folder available without repeating OAuth.

**Pass**: SC-001, SC-006 related checks.

### Q2 — Calm large-file progress (US2)

1. Pick an uncached file ≈ 70 MB under `~/Kitelink`.
2. Open it from Files.
3. Within 5 seconds, tray shows aggregated progress (not a flood of banners).
4. Browse another folder with thumbnails during/after; expect **zero** progress spam.

**Pass**: SC-002, SC-003.

### Q3 — Emblems (US3)

1. Note emblems on untouched large items (cloud/unknown).
2. Open one file until available; return to folder.
3. Expect a locally-available style emblem on that item (approximation OK).

**Pass**: SC-004 ( moderated judgment ).

### Q4 — Tray controls & sign-out (US4)

1. From tray: Open folder → Files focuses `~/Kitelink`.
2. Change cache size preference; apply/restart connection if prompted.
3. Open diagnostics; confirm no tokens/secrets visible.
4. Sign out; confirm mount stopped and Drive not reachable at mountpoint; keyring item removed.

**Pass**: SC-005.

### Q5 — Fresh package install (US5)

1. On a clean VM, install `.deb` only.
2. Launch app → reach sign-in without manual file copies.

**Pass**: SC-007.

### Q6 — Security smoke

1. While connected, verify control/RC ports listen on localhost only (`ss`/`lsof`).
2. Confirm non-loopback bind absent.

**Pass**: FR-012 / constitution V.

## Reference contracts

- D-Bus methods/signals: [contracts/dbus-org.kitelink.Service1.xml](./contracts/dbus-org.kitelink.Service1.xml)
- Entities: [data-model.md](./data-model.md)

## After failures

Collect user-safe diagnostics from the app only. Do not paste `rclone.conf`, keyring exports, or OAuth tokens into issues.
