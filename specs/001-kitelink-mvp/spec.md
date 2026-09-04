# Feature Specification: Kitelink Phase 1 MVP

**Feature Branch**: `001-kitelink-mvp`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "Phase 1 MVP of Kitelink — public Linux desktop app (GNOME/Nautilus first) that provides a Google Drive Desktop–like experience: guided Google sign-in, automatic branded folder mount at ~/Kitelink, Nautilus emblems for approximate sync states, calm aggregated tray progress for large file opens (with filters so folder browsing never spams notifications), preferences for cache/diagnostics/sign-out, and .deb packaging. Architecture must keep UI behind a stable local service contract so Phase 2 can replace the sync engine. Upstream product requirements: PRD.md."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign in and get a Drive folder (Priority: P1)

Ana installs Kitelink, opens the app, signs in with her Google account in the browser, and finds a `Kitelink` folder in Files that shows her Drive contents — without using a terminal.

**Why this priority**: Without a working signed-in folder, nothing else matters; this is the core replacement for Windows Drive Desktop setup.

**Independent Test**: On a clean Zorin/Ubuntu VM, install the package, complete sign-in, open Files, and list Drive content under `~/Kitelink`.

**Acceptance Scenarios**:

1. **Given** Kitelink is installed and the user is signed out, **When** they complete Google sign-in from the app, **Then** `~/Kitelink` becomes available in Files with Drive folders/files visible.
2. **Given** the user signed in successfully, **When** they reboot and log into the graphical session, **Then** the Kitelink folder is available again without repeating setup.
3. **Given** sign-in fails or is cancelled, **When** the user returns to the app, **Then** they see a clear error or cancelled state and can retry; no half-broken mount is left unexplained.

---

### User Story 2 - Open a large cloud file with calm progress (Priority: P1)

Ana double-clicks a large PDF that is not yet on this computer. Instead of a frozen silence or a storm of notifications, the tray shows that a download is in progress and when it finishes (or fails).

**Why this priority**: This is the painful gap versus raw mounts and the failed notify-send prototype; it is central to trust.

**Independent Test**: Ensure a ~70 MB file is not locally cached, open it from Files, and observe tray progress within 5 seconds with no notification flood while browsing other folders.

**Acceptance Scenarios**:

1. **Given** a large file is not available locally, **When** the user opens it from Files, **Then** the tray shows aggregated progress within 5 seconds until the file is ready or an error is shown.
2. **Given** the user is browsing a folder that generates many thumbnails, **When** Files reads many small/short transfers, **Then** zero progress banners/notifications appear.
3. **Given** a long transfer is active, **When** the user glances at the tray, **Then** they see a single aggregated status (e.g. count of files / primary file), not N separate interrupting banners.

---

### User Story 3 - See which items look local vs cloud-only (Priority: P2)

Ana browses a project folder and can tell, at a glance, which items appear already available on this PC versus still primarily in the cloud (with documented approximation limits).

**Why this priority**: Visual sync state is a defining Drive Desktop cue; valuable after mount + progress work.

**Independent Test**: Open a mixed folder after opening some files (to populate local availability) and verify emblems differ for recently opened vs untouched large items.

**Acceptance Scenarios**:

1. **Given** a file was recently opened and is available locally, **When** Ana views it in Files, **Then** it shows a “locally available” style emblem.
2. **Given** a file has not been fetched locally (or state is unknown), **When** Ana views it in Files, **Then** it shows a cloud/unknown style emblem rather than a false “synced” mark.
3. **Given** the mount or sync service is in error, **When** Ana views affected items or the tray, **Then** an error state is visible without crashing Files.

---

### User Story 4 - Control the connection from the tray (Priority: P2)

Ana uses the tray/status app to see connection health, open the folder, adjust cache size, view diagnostics, and sign out.

**Why this priority**: Non-technical users need ongoing control without systemd knowledge.

**Independent Test**: From the tray only, open folder, change a cache preference, view status, sign out, and confirm Drive is no longer accessible via the mount.

**Acceptance Scenarios**:

1. **Given** Kitelink is connected, **When** Ana chooses “Open folder”, **Then** Files opens `~/Kitelink`.
2. **Given** Ana opens preferences, **When** she changes the cache size setting and saves, **Then** the new limit is applied for subsequent use (or she is told a restart of the connection is required and how it will happen).
3. **Given** Ana signs out, **When** sign-out completes, **Then** the mount is stopped, Drive content is not reachable at the mountpoint, and stored sign-in material used by Kitelink is removed from the system keyring path.

---

### User Story 5 - Install via package on a clean machine (Priority: P3)

A tester installs a `.deb` on a clean Zorin/Ubuntu system and gets the app, tray integration, and Files emblems support without manual file copying.

**Why this priority**: Public distribution requires installability; can follow core UX slices.

**Independent Test**: Install `.deb` on a clean VM and complete User Story 1.

**Acceptance Scenarios**:

1. **Given** a clean supported distro VM, **When** the `.deb` is installed, **Then** Kitelink appears in the app menu and can be launched.
2. **Given** installation completed, **When** the user enables/uses Files integration as documented, **Then** emblems capability is available without hand-editing obscure paths.

---

### Edge Cases

- What happens when the network drops mid-download of a large file?
- What happens when the mountpoint is busy (Files or apps still inside the folder) during restart/sign-out?
- How does the system behave if Google auth tokens expire or are revoked?
- What if disk space is exhausted relative to the cache limit?
- What if the user renames or deletes `~/Kitelink` while the service expects that path?
- What if Files generates many tiny reads that individually stay under thresholds but collectively load the network?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to complete Google account sign-in from the graphical app without using a terminal.
- **FR-002**: After successful sign-in, the system MUST expose Google Drive content at a branded folder `~/Kitelink` in the file manager.
- **FR-003**: The Drive folder MUST become available automatically on graphical login after initial setup.
- **FR-004**: The system MUST show tray/status states for at least: idle/connected, syncing/transferring, offline/disconnected, and error.
- **FR-005**: Progress feedback for transfers MUST be aggregated and MUST apply minimum size and minimum duration filters before surfacing.
- **FR-006**: Browsing folders in the file manager MUST NOT produce progress notifications/banners for background reads that fail the filters.
- **FR-007**: Opening a large uncached file (~70 MB class) MUST surface tray progress within 5 seconds under normal network conditions, or a clear error if the transfer cannot start.
- **FR-008**: The file manager MUST be able to show emblems for approximate states: cloud-only/unknown, syncing, locally available, and error.
- **FR-009**: Emblem/state queries MUST NOT block the file manager on slow network calls; the local status service answers quickly from local knowledge.
- **FR-010**: Users MUST be able to open the Kitelink folder, view diagnostics (status and recent errors without secrets), and adjust cache size from preferences.
- **FR-011**: Users MUST be able to sign out, which stops access via the mountpoint and removes Kitelink-managed auth material from the keyring.
- **FR-012**: Control interfaces used for transfer stats MUST NOT be reachable from non-localhost network interfaces in default configuration.
- **FR-013**: The product MUST be installable via a `.deb` package on supported Ubuntu-based desktops (Zorin/Ubuntu) including app launch entry and documented Files integration.
- **FR-014**: UI components MUST depend on a stable local service contract so a future engine replacement can preserve tray and emblem behavior.
- **FR-015**: The product MUST document that Phase 1 emblems are approximate and MUST prefer conservative cloud/unknown over false locally-available marks when unsure.

### Key Entities

- **Account session**: Signed-in Google identity bound to this user desktop; auth material in keyring; signed-out clears it.
- **Mounted Drive folder**: User-visible tree at `~/Kitelink` representing Drive content.
- **File availability state**: Approximate per-item state (cloud/unknown, syncing, local, error) for emblems.
- **Transfer activity**: Filtered, aggregated view of in-flight large/long reads or writes for tray UI.
- **User preferences**: Cache size and related settings that affect local retention behavior.
- **Service health**: Mount/connection status and last user-visible error for diagnostics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user on a clean supported desktop completes install + sign-in and sees Drive content in Files in under 10 minutes without terminal commands.
- **SC-002**: Opening an uncached ~70 MB file shows understandable progress in the tray within 5 seconds in moderated tests on a typical broadband link.
- **SC-003**: In moderated tests, browsing folders with thumbnails produces zero progress notifications/banners.
- **SC-004**: At least 8/10 target-persona testers correctly identify “looks local” vs “looks cloud” for a prepared sample folder using emblems (with approximation disclaimer accepted).
- **SC-005**: Sign-out leaves the branded folder without Drive access and removes stored sign-in material used by Kitelink, verified in a checklist test.
- **SC-006**: After reboot, Drive folder availability returns without user re-setup for an already signed-in account.
- **SC-007**: Packaging install on a clean VM reaches the sign-in screen without manual copying of extension or service files.

## Assumptions

- Target desktop is recent Zorin OS or Ubuntu LTS with GNOME Files (Nautilus) and a working graphical keyring.
- Users have a standard Google consumer Drive (My Drive); Shared Drives depth is out of Phase 1.
- Native Google Docs/Sheets are acceptable as browser-oriented items in Phase 1; full offline office parity is out of scope.
- Brand logo/palette may arrive after structural UI; temporary system theme defaults are acceptable until assets land in `assets/brand/`.
- Public OAuth verification may lag the engineering beta; Test-user mode is acceptable for early builds.
- Default progress filters around 20–50 MB and 3–5 seconds are acceptable starting points and may be tuned in preferences later.
- Single Google account per OS user in Phase 1.
- Portuguese (Brazil) and English copy are sufficient for early releases.
