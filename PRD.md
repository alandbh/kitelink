# Kitelink — Product Requirements Document (PRD)

**Version:** 0.1  
**Status:** Draft for SDD  
**Last updated:** 2026-09-03  
**Codename / product name:** Kitelink

---

## 1. Vision

Kitelink is a Linux desktop application that brings a Google Drive Desktop–like experience to GNOME-based desktops (starting with Zorin OS / Nautilus).

The name is a deliberate wordplay: **kite** (pipa) + **link** (conexão). The “link” is literally the line that keeps the kite connected — the same role the app plays between the user’s local folder and Google Drive in the cloud.

### Product promise

A non-technical user who used Google Drive on Windows should be able to:

1. Sign in with Google once.
2. Open a familiar folder in Nautilus.
3. See which files are available locally vs only in the cloud.
4. Open a large file and get clear progress feedback — without a flood of desktop notifications.
5. Never need the terminal for day-to-day use.

---

## 2. Problem statement

Existing Linux approaches (including `rclone mount`) can expose Google Drive as a folder in Nautilus, but they fall short of Google Drive Desktop on Windows/macOS:

| Gap | Impact |
|-----|--------|
| No clear per-file sync state in the file manager | User cannot tell cloud-only vs cached locally |
| No trustworthy progress UI when opening large uncached files | App appears frozen (e.g. 70 MB PDF) |
| Naive transfer monitors spam notifications | Nautilus thumbnail/MIME reads look like user downloads |
| Setup requires terminal, systemd, and rclone knowledge | Unsuitable for the target persona |

**Lesson learned (prototype):** A `notify-send` monitor polling rclone Remote Control (`core/stats`) without filters treated every Nautilus background read as a user transfer and flooded the desktop. That approach is rejected for Kitelink.

Background research and the working rclone mount recipe live in [`readme-1.md`](readme-1.md) and [`readme-2.md`](readme-2.md).

---

## 3. Goals and non-goals

### Goals (product)

- Deliver a **public** Linux desktop app that feels like Drive Desktop for GNOME/Nautilus.
- Ship a **phased** architecture: validate UX on rclone first, then replace the sync engine without rewriting the shell.
- Keep day-to-day use **terminal-free**.
- Respect privacy: tokens in the system keyring; no silent telemetry in MVP.

### Non-goals (explicit)

- Feature parity with Windows/macOS Google Drive Desktop on day one.
- KDE / Dolphin support in Phase 1.
- Flatpak as the primary distribution channel (FUSE, Nautilus extension, and systemd user services conflict with sandbox boundaries).
- Full offline editing of native Google Docs/Sheets/Slides (browser shortcut or limited export only).
- Advanced Shared Drive / Workspace admin features in MVP.
- Replacing Google Drive as a cloud product — Kitelink is a **client**, not a storage backend.

---

## 4. Personas and jobs-to-be-done

### Primary persona — “Ana”

- Uses Zorin OS or similar Ubuntu-based GNOME desktop.
- Previously used Google Drive Desktop on Windows.
- Comfortable with Files (Nautilus), browser login, and system tray icons.
- Uncomfortable with terminal, systemd units, and OAuth client setup.

### Jobs-to-be-done

1. **Mount & browse:** “When I log in, I want my Drive folder ready in Files so I can work like on Windows.”
2. **See availability:** “When I look at a folder, I want to know what is already on this PC and what is only in the cloud.”
3. **Open large files safely:** “When I open a big PDF that is not cached, I want to see that it is downloading — without the whole desktop screaming at me.”
4. **Stay in control:** “I want to sign out, pause, or check connection status from a small tray app.”

---

## 5. Product strategy — phased delivery

```text
Phase 1 (MVP)     Phase 2 (engine)     Phase 3+ (depth)
─────────────     ────────────────     ────────────────
rclone mount      Own FUSE daemon      Pin policies,
+ GTK shell       + Drive API          Shared Drives,
+ Nautilus emblems + SQLite metadata   richer conflict UX
+ tray progress   Same D-Bus contract
```

### Phase 1 — MVP (validate UX)

Orchestrate **rclone** (`mount` + Remote Control) behind a branded Kitelink experience:

- Guided Google sign-in (OAuth loopback).
- Automatic `systemd --user` mount service.
- Default mountpoint: `~/Kitelink` (branded; configurable later if needed).
- Nautilus emblems for approximate sync states.
- Tray / status app with **aggregated, filtered** transfer feedback.
- Preferences: cache size, open folder, connection status, diagnostics, sign out.
- Packaging: `.deb` for Zorin/Ubuntu first.

**Important honesty:** Phase 1 states are **approximations** derived from rclone VFS cache + RC stats, not true placeholder (“ghost”) files owned by Kitelink.

### Phase 2 — own sync engine

Replace rclone with a Kitelink daemon:

- FUSE 3 filesystem with true on-demand (“ghost”) files.
- Google Drive API (`files`, `changes.list`, upload/download, conflict policy).
- SQLite metadata + sparse/block cache + pin-for-offline.
- **Same** session D-Bus contract so GTK shell and Nautilus extension keep working.

### Phase 3+ (later)

- Stronger offline pin UX, conflict resolution UI, Shared Drives, multi-account, RPM packages, optional Dolphin support.

---

## 6. Functional requirements

### 6.1 Phase 1 (MVP) — must have

| ID | Requirement |
|----|-------------|
| FR-1 | User can complete Google OAuth from the GUI without using a terminal. |
| FR-2 | After sign-in, Kitelink creates/starts a user systemd service that mounts Drive at `~/Kitelink`. |
| FR-3 | Mount starts automatically on graphical login. |
| FR-4 | Nautilus shows emblems for at least: cloud-only / syncing / locally available / error (best-effort accuracy on rclone). |
| FR-5 | Tray indicator shows idle / syncing / offline / error. |
| FR-6 | Transfer UI is **aggregated** (e.g. “3 files transferring”) with optional detail for the active large transfer. |
| FR-7 | Progress feedback uses filters: minimum size threshold, minimum duration threshold, no per-file spam on folder browse. |
| FR-8 | Opening a large uncached file shows progress in the tray within a few seconds (see acceptance criteria). |
| FR-9 | Preferences allow adjusting VFS cache max size and viewing diagnostics (service status, last error). |
| FR-10 | Sign-out stops the mount, clears local OAuth tokens from the keyring (and rclone config secrets as designed), and leaves a clear empty/unmounted state. |
| FR-11 | App depends on a bundled or clearly declared rclone version compatible with required RC/VFS options. |

### 6.2 Phase 1 — should have

| ID | Requirement |
|----|-------------|
| FR-12 | One-click “Open Kitelink folder” and optional Nautilus bookmark helper. |
| FR-13 | Quiet completion signal for long transfers (update same tray surface; avoid notification storms). |
| FR-14 | Basic conflict/error surfacing when rclone reports mount failure (retry + open logs). |

### 6.3 Phase 2 — must have (engine)

| ID | Requirement |
|----|-------------|
| FR-20 | True cloud-only placeholders with correct logical size via FUSE. |
| FR-21 | On-demand hydration on read; pin/unpin for offline. |
| FR-22 | Incremental remote change sync via Drive `changes.list`. |
| FR-23 | Conflict policy that never silently overwrites (e.g. `name (conflict …).ext`). |
| FR-24 | Native Google Docs represented as browser links or explicit export — not fake binary files. |
| FR-25 | D-Bus API remains compatible with Phase 1 clients (versioned interface). |

### 6.4 Explicitly out of Phase 1

- Exact Dropbox/Drive-style always-correct badges for every edge case.
- Native Google Docs offline editing.
- Multi-account.
- KDE emblems.

---

## 7. Transfer / progress UX rules (critical)

Derived from the failed notify-send prototype:

1. **Do not** notify on every rclone `transferring` entry.
2. Ignore transfers below a configurable size floor (default suggestion: 20–50 MB).
3. Ignore transfers shorter than a duration floor (default suggestion: 3–5 s).
4. Prefer **one aggregated tray state** over N parallel banners.
5. Do not show “complete” for short or cancelled background reads (thumbnails, MIME sniffing).
6. Nautilus itself will not show a native download bar for FUSE reads; Kitelink’s tray is the primary progress surface in Phase 1.

---

## 8. Nautilus integration

- Extension via `nautilus-python` (Phase 1).
- Extension talks **only** to the local Kitelink service (D-Bus), never directly to Google.
- Emblems: cloud (gray), syncing, local check (green), error.
- Extension must not block the file manager on network I/O.

---

## 9. Architecture principles (for SDD)

```text
Nautilus ──► Extension ──► D-Bus ──► Kitelink service
Files apps ──► ~/Kitelink (FUSE mount)
Tray / Settings ──► D-Bus ──► Kitelink service
Kitelink service ──► backend (Phase 1: rclone | Phase 2: own daemon)
```

- **Stable IPC:** versioned D-Bus interface from day one.
- **Backend swappable:** UI and extension must not embed rclone-specific assumptions beyond an adapter layer.
- **Secrets:** OAuth tokens in libsecret / GNOME Keyring; never plain-text in tickets or logs.
- **Linux-first public `.deb`:** host-integrated install for FUSE + Nautilus + systemd.

### Suggested Phase 1 stack

| Layer | Choice |
|-------|--------|
| Shell / tray / settings | GTK 4 + libadwaita (Python) |
| Nautilus extension | Python (`nautilus-python`) |
| Backend | rclone mount + RC |
| IPC | D-Bus session bus |
| Secrets | libsecret |
| Auth | OAuth 2 desktop loopback |
| Packaging | `.deb` |

### Suggested Phase 2 stack

| Layer | Choice |
|-------|--------|
| Daemon | Rust + Tokio + FUSE 3 + SQLite |
| Drive access | Google Drive API v3 |
| UI / extension | Unchanged consumers of D-Bus |

---

## 10. Non-functional requirements

| ID | Area | Requirement |
|----|------|-------------|
| NFR-1 | Usability | Primary flows completable without terminal. |
| NFR-2 | Performance | Folder navigation remains usable; cache settings documented. |
| NFR-3 | Reliability | Mount service restarts on failure; clear error state in tray. |
| NFR-4 | Security | Tokens in keyring; RC bound to localhost only; no broad network exposure of control API. |
| NFR-5 | Privacy | No telemetry by default in MVP (if added later: explicit opt-in). |
| NFR-6 | Compatibility | Target: recent Zorin OS / Ubuntu LTS with GNOME Files (Nautilus) and FUSE 3. |
| NFR-7 | Observability | User-accessible diagnostics (status + recent logs), without dumping secrets. |
| NFR-8 | Maintainability | Adapter boundary so Phase 2 can replace rclone without UI rewrite. |

---

## 11. Distribution, OAuth, and compliance (public product)

Kitelink is intended for **public distribution**, not only private Client IDs.

### Implications

- Full Drive mirroring needs a **restricted** OAuth scope such as `https://www.googleapis.com/auth/drive`.
- Scope `drive.file` is **insufficient** for a transparent whole-Drive client.
- Public apps require Google OAuth verification, a hosted privacy policy, and possibly a security assessment.
- The project must ship its own OAuth client configuration (never commit real client secrets to public docs; use build-time / packaging secrets strategy).
- Quota and rate limiting are product risks; document user-visible backoff/errors.

### Packaging stance

- Primary: native `.deb` with Nautilus extension and systemd user units.
- Flatpak is **not** the primary channel for MVP.

---

## 12. Acceptance criteria (Phase 1 MVP)

| ID | Criterion |
|----|-----------|
| AC-1 | Fresh install → sign-in → `~/Kitelink` visible in Nautilus without terminal steps. |
| AC-2 | After reboot/login, mount is available without user action (systemd user service). |
| AC-3 | Browsing a folder with many thumbnails produces **zero** progress notifications/banners. |
| AC-4 | Opening an uncached ~70 MB PDF shows aggregated tray progress within **≤ 5 seconds** and updates until ready (or clearly errors). |
| AC-5 | Emblems appear for a sample of cloud-only vs recently opened (cached) files (documented approximation limits OK). |
| AC-6 | Sign-out leaves Drive inaccessible via the mountpoint and removes stored auth material from the keyring path used by Kitelink. |
| AC-7 | RC / control interface is not listening on non-localhost interfaces. |
| AC-8 | `.deb` installs app, extension hook, and dependencies declarations needed on a clean Zorin/Ubuntu test VM. |

---

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Google OAuth verification delay/rejection | Cannot ship public auth | Start verification early; privacy policy + limited scopes narrative; beta with Test users meanwhile |
| rclone VFS state too coarse for accurate emblems | Misleading badges | Document approximation; prefer conservative “unknown/cloud” over false “synced” |
| Nautilus background I/O looks like downloads | UX spam | Hard filters + tray aggregation (see §7) |
| FUSE + permissions + busy mountpoints | Support burden | Clear diagnostics; safe unmount; documented “close apps using folder” |
| Restricted scope scrutiny | Legal/compliance cost | Budget time; minimize data collection; open docs |
| Phase 2 rewrite temptation mid-MVP | Delay | Enforce adapter + D-Bus contract; ship Phase 1 first |

---

## 14. Success metrics (qualitative for early releases)

- Target persona completes setup unassisted in a moderated usability test.
- Zero “notification flood” reports in Phase 1 beta when browsing folders.
- Large-file open feedback rated as understandable vs “frozen” baseline with raw rclone.
- Architecture review confirms UI has no hard rclone dependency outside the adapter.

---

## 15. Brand and assets

| Item | Location / notes |
|------|------------------|
| Product name | **Kitelink** |
| Metaphor | Kite + link (line) = connection to the cloud |
| Logo (SVG/PNG) | [`assets/brand/`](assets/brand/) — *to be supplied by product owner* |
| Color palette | [`assets/brand/palette.md`](assets/brand/palette.md) — placeholder until brand kit arrives |
| App icon | Derived from logo; follow GNOME icon guidelines when implementing |

UI implementation must wait for brand assets where color/logo are load-bearing; structure and copy can proceed from this PRD.

---

## 16. Documentation map

| Doc | Role |
|-----|------|
| [`PRD.md`](PRD.md) | Product source of truth (this file) |
| Spec Kit constitution / specs / plans / tasks | Executable SDD artifacts derived from this PRD |
| [`readme-1.md`](readme-1.md) | Historical rclone setup + failed notification experiment |
| [`readme-2.md`](readme-2.md) | Feasibility notes (APIs, FUSE, stacks) |
| [`README.md`](README.md) | Short project entry point |

---

## 17. Open questions (non-blocking for Phase 1 spec)

1. Final default cache size (rclone used 10 G in the prototype).
2. Exact emblem artwork vs GNOME symbolic emblems.
3. Whether to vendor rclone binary or depend on distro package with a minimum version gate.
4. Localization languages beyond pt-BR / en for MVP.

---

## 18. Approval

| Role | Name | Date |
|------|------|------|
| Product | — | — |
| Engineering | — | — |

This PRD feeds Spec-Driven Development (GitHub Spec Kit): constitution → specify → plan → tasks → implement.
