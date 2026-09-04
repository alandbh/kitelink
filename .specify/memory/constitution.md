<!--
Sync Impact Report
- Version change: (none) → 1.0.0
- Modified principles: N/A (initial ratification)
- Added sections: Core Principles (I–V), Product Constraints, Security & Privacy, Development Workflow, Governance
- Removed sections: N/A
- Follow-up TODOs: none
-->
# Kitelink Constitution

## Core Principles

### I. Linux Desktop First
Kitelink MUST target Linux desktop users on GNOME-based environments
(Zorin OS / Nautilus first). Day-to-day flows MUST be completable without
a terminal. Distribution MUST prefer host-integrated packages (`.deb` first)
so FUSE mounts, Nautilus extensions, and systemd user services work reliably.
Flatpak MUST NOT be the primary distribution channel while those integrations
remain sandbox-hostile.

Rationale: The product succeeds only if it feels like Drive Desktop on a
real Linux desktop, not like a sandboxed toy or a CLI wrapper.

### II. Calm Progress, Never Spam
Transfer and sync feedback MUST use aggregated tray/status UI with filters
(minimum size, minimum duration). The product MUST NOT emit per-file desktop
notifications for background file-manager reads (thumbnails, MIME sniffing,
folder enumeration). “Complete” signals MUST NOT fire for short or cancelled
background reads.

Rationale: A naive Remote Control monitor flooded the desktop; calm UX is
a non-negotiable product differentiator.

### III. Swappable Sync Backend
UI shell, tray, and file-manager extension MUST talk to a versioned local
IPC contract (D-Bus session). Backend-specific logic (e.g. rclone in Phase 1)
MUST live behind an adapter. Phase 2 MAY replace the engine (own FUSE + Drive
API) without rewriting consumers. Breaking IPC changes MUST bump the interface
version and ship a migration note.

Rationale: Phased delivery validates UX early without trapping the product
in a permanent rclone dependency.

### IV. Honest Sync States
Phase 1 MAY approximate cloud-only vs local availability from cache metadata.
The product MUST NOT claim perfect Drive Desktop parity for emblems while
using an approximate backend. True on-demand “ghost” files with authoritative
states are a Phase 2 requirement. Conservative “unknown/cloud” MUST be preferred
over false “synced” badges.

Rationale: Misleading badges destroy trust faster than missing badges.

### V. Secrets Stay Secret
OAuth tokens and refresh credentials MUST be stored in the system keyring
(libsecret / GNOME Keyring). Control interfaces MUST bind to localhost only.
Logs, diagnostics, issue reports, and public docs MUST NEVER include tokens,
client secrets, or full auth config dumps. Telemetry is OFF by default in MVP;
any future telemetry MUST be explicit opt-in.

Rationale: Public OAuth + Drive access is high-trust; leakage ends the product.

## Product Constraints

- Product name is **Kitelink**; branding assets live under `assets/brand/`.
- Product requirements in `PRD.md` are upstream of Spec Kit artifacts.
- Phase 1 scope: branded mount, emblems (best-effort), tray progress, preferences,
  `.deb` install — on top of an orchestrated mount backend.
- Phase 1 MUST NOT include: KDE/Dolphin, multi-account, native Google Docs offline
  editing, Advanced Shared Drive admin features, or Flatpak-primary packaging.
- Public distribution implies restricted Google OAuth scope work (verification,
  privacy policy). Engineering MUST plan for verification latency; Test-user
  betas are allowed before public auth.

## Security & Privacy

- Prefer least data collection; no silent analytics in MVP.
- Remote control / admin APIs for the sync engine MUST NOT listen on non-loopback
  addresses without authenticated, reviewed exception.
- Sign-out MUST stop the mount and remove Kitelink-managed auth material from
  the keyring path used by the product.
- Dependency and OAuth client packaging MUST avoid committing live secrets to git.

## Development Workflow

- Spec-Driven Development via GitHub Spec Kit is mandatory for features:
  constitution → specify → plan → tasks → implement (clarify/analyze/checklist
  as quality gates when ambiguity or risk is high).
- `PRD.md` MUST be updated when product scope or acceptance criteria change;
  specs MUST not silently diverge from the PRD.
- Contract tests for the local IPC API are required whenever the interface changes.
- Prefer small, reviewable increments that keep Phase 1 shippable.

## Governance

This constitution supersedes informal practice when conflicts arise. Amendments
require: (1) documented change in this file with version bump, (2) sync note in
the Sync Impact Report comment, (3) update to `PRD.md` if product rules change.
Versioning: MAJOR for incompatible principle removals/redefinitions; MINOR for
new principles or material expansion; PATCH for clarifications.

All implementation plans and PRs MUST be reviewable against these principles.
Complexity beyond Phase needs MUST be justified against Principle III and the PRD
non-goals.

**Version**: 1.0.0 | **Ratified**: 2026-09-03 | **Last Amended**: 2026-09-03
