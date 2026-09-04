---
description: "Task list for Kitelink Phase 1 MVP"
---

# Tasks: Kitelink Phase 1 MVP

**Input**: Design documents from `/specs/001-kitelink-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Optional contract/unit tests included for D-Bus and transfer filters (high-risk calm-UX path). Full UI E2E remains manual via quickstart.md.

**Organization**: Tasks grouped by user story for incremental delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1…US5 maps to spec.md user stories
- Exact file paths included

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton and tooling

- [x] T001 Create source tree per plan (`src/kitelink/{app,service,ipc,auth,util}`, `extensions/nautilus/`, `packaging/debian/`, `systemd/user/`, `tests/{unit,contract,integration}`)
- [x] T002 Initialize Python project packaging in `pyproject.toml` with GTK/PyGObject, dbus, libsecret, pytest dependencies
- [x] T003 [P] Add lint/format config in `pyproject.toml` / `ruff.toml` (or equivalent)
- [x] T004 [P] Add `.gitignore` entries for Python, secrets, rclone conf copies, and build artifacts (keep Spec Kit notes in mind for `.cursor/`)
- [x] T005 [P] Add placeholder desktop entry template in `packaging/debian/kitelink.desktop`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared service, IPC, auth, rclone adapter shell — blocks all stories

**⚠️ CRITICAL**: No user story work until this phase completes

- [x] T006 Define shared enums/models in `src/kitelink/service/state.py` (auth, connection, path state, preferences)
- [x] T007 [P] Implement preferences load/save under XDG in `src/kitelink/util/preferences.py`
- [x] T008 [P] Implement user-safe logging helpers in `src/kitelink/util/logging.py` (never log secrets)
- [x] T009 Implement D-Bus interface skeleton matching `specs/001-kitelink-mvp/contracts/dbus-org.kitelink.Service1.xml` in `src/kitelink/ipc/service1.py`
- [x] T010 Implement Kitelink user service entrypoint that owns the D-Bus name in `src/kitelink/service/main.py`
- [x] T011 [P] Create systemd user unit template in `systemd/user/kitelink.service`
- [x] T012 Implement rclone adapter stubs (mount lifecycle + RC client interfaces) in `src/kitelink/service/adapters/rclone/`
- [x] T013 Implement libsecret-backed credential store API in `src/kitelink/auth/keyring_store.py`
- [x] T014 [P] Add contract test scaffolding for D-Bus method presence in `tests/contract/test_service1_iface.py`

**Checkpoint**: Service starts, claims D-Bus name, answers stub methods; no Google mount required yet

---

## Phase 3: User Story 1 - Sign in and get a Drive folder (Priority: P1) 🎯 MVP

**Goal**: Guided OAuth + automatic `~/Kitelink` mount on login

**Independent Test**: Clean machine/VM → sign-in → Drive visible in Files at `~/Kitelink` → survives re-login

### Implementation for User Story 1

- [x] T015 [US1] Implement OAuth loopback sign-in flow in `src/kitelink/auth/oauth.py`
- [x] T016 [US1] Wire `StartSignIn` / `GetAuthStatus` / `SignOut` (partial) in `src/kitelink/ipc/service1.py` to auth modules
- [x] T017 [US1] Implement rclone remote ensure + mount start/stop in `src/kitelink/service/adapters/rclone/mount.py`
- [x] T018 [US1] Generate/manage mount systemd user unit with localhost RC flags in `src/kitelink/service/adapters/rclone/unit.py`
- [x] T019 [US1] Implement connection status + `OpenMountpoint` in `src/kitelink/service/connection.py`
- [x] T020 [US1] Build onboarding/sign-in GTK window in `src/kitelink/app/onboarding.py`
- [x] T021 [US1] Wire app launch to ensure user service is running in `src/kitelink/app/main.py`
- [x] T022 [US1] Persist session email + map tokens into rclone config securely via adapter in `src/kitelink/service/adapters/rclone/auth_bridge.py`

**Checkpoint**: US1 demoable — signed-in mount without terminal

---

## Phase 4: User Story 2 - Calm large-file progress (Priority: P1)

**Goal**: Aggregated tray progress with anti-spam filters

**Independent Test**: Open uncached ~70 MB file → tray progress ≤5s; browse thumbs → zero banners

### Implementation for User Story 2

- [x] T023 [P] [US2] Implement transfer filter (min bytes, min duration, aggregate) in `src/kitelink/service/transfer_filter.py`
- [x] T024 [P] [US2] Add unit tests for filter edge cases in `tests/unit/test_transfer_filter.py`
- [x] T025 [US2] Implement RC poller producing `TransferActivity` in `src/kitelink/service/adapters/rclone/rc_stats.py`
- [x] T026 [US2] Expose `GetAggregatedTransfers` + `TransfersChanged` signal in `src/kitelink/ipc/service1.py`
- [x] T027 [US2] Implement tray indicator UI (idle/syncing/error + headline) in `src/kitelink/app/tray.py`
- [x] T028 [US2] Ensure default UX never uses per-file `notify-send` storms (document + code path) in `src/kitelink/app/notifications.py`

**Checkpoint**: US2 validated against quickstart Q2

---

## Phase 5: User Story 3 - Sync-state emblems (Priority: P2)

**Goal**: Nautilus emblems for approximate availability

**Independent Test**: Mixed folder shows different emblems for untouched vs recently opened files

### Implementation for User Story 3

- [x] T029 [US3] Implement path-state heuristics from VFS cache + transferring set in `src/kitelink/service/adapters/rclone/path_state.py`
- [x] T030 [US3] Implement `GetPathState` + `PathStateMayHaveChanged` in `src/kitelink/ipc/service1.py`
- [x] T031 [P] [US3] Create Nautilus extension calling D-Bus in `extensions/nautilus/kitelink.py`
- [x] T032 [P] [US3] Add emblem icon assets placeholders under `assets/brand/emblems/` (swap when brand kit arrives)
- [x] T033 [US3] Document approximation limits in-app help blurb in `src/kitelink/app/help_copy.py`

**Checkpoint**: US3 emblems visible without blocking Nautilus

---

## Phase 6: User Story 4 - Tray controls & preferences (Priority: P2)

**Goal**: Open folder, cache prefs, diagnostics, full sign-out

**Independent Test**: Tray-only control of folder/prefs/diagnostics/sign-out

### Implementation for User Story 4

- [x] T034 [US4] Build preferences dialog (cache size, filter thresholds) in `src/kitelink/app/preferences.py`
- [x] T035 [US4] Implement `GetPreferences` / `SetPreferences` applying to rclone unit/restart policy in `src/kitelink/service/preferences_apply.py`
- [x] T036 [US4] Implement user-safe `GetDiagnostics` JSON in `src/kitelink/service/diagnostics.py`
- [x] T037 [US4] Complete sign-out: stop mount, clear keyring, clear adapter secrets in `src/kitelink/auth/session.py`
- [x] T038 [US4] Add tray menu actions (open folder, preferences, diagnostics, sign out, quit) in `src/kitelink/app/tray.py`

**Checkpoint**: US4 matches quickstart Q4

---

## Phase 7: User Story 5 - `.deb` packaging (Priority: P3)

**Goal**: Clean VM install reaches sign-in without manual copies

**Independent Test**: Install `.deb` on clean Zorin/Ubuntu VM → launch app

### Implementation for User Story 5

- [x] T039 [US5] Author Debian packaging metadata in `packaging/debian/control` and related files
- [x] T040 [US5] Install systemd user units and Nautilus extension paths via package rules in `packaging/debian/kitelink.install`
- [x] T041 [US5] Declare rclone dependency or bundle strategy + minimum version gate in `packaging/debian/control` / docs
- [x] T042 [US5] Add package build instructions in `packaging/README.md`
- [x] T043 [US5] Smoke-test install script/checklist linked from `specs/001-kitelink-mvp/quickstart.md` scenario Q5

**Checkpoint**: US5 packaging path documented and reproducible

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Hardening across stories

- [x] T044 [P] Verify RC/control bind is localhost-only; add regression check in `tests/unit/test_bind_localhost.py`
- [x] T045 [P] Update root `README.md` with build/run pointers to specs and packaging
- [x] T046 Align in-app strings with brand name Kitelink; keep hooks for `assets/brand/` palette
- [x] T047 Run full `specs/001-kitelink-mvp/quickstart.md` on a VM and file gaps
- [x] T048 Add Phase 2 adapter boundary note in `src/kitelink/service/adapters/README.md` (how to replace rclone)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: start immediately
- **Foundational (Phase 2)**: after Setup — **blocks all stories**
- **US1 then US2** recommended sequentially (both P1; progress needs mount)
- **US3 / US4** after US1 (need connection); can proceed in parallel after US2 if staffed
- **US5** can start packaging drafts early but finalize after US1–US4 paths exist
- **Polish**: after desired stories complete

### User Story Dependencies

- **US1**: after Foundational
- **US2**: after US1 mount+RC available
- **US3**: after Foundational + path state from adapter (practically after US1)
- **US4**: after US1 (sign-out/prefs); better after US2 tray exists
- **US5**: packaging can parallelize docs early; install verification after binaries exist

### Parallel Opportunities

- T003–T005 in Setup
- T007–T008, T011, T014 in Foundational
- T023–T024 in US2
- T031–T032 in US3
- T044–T045 in Polish

---

## Parallel Example: User Story 2

```bash
# In parallel:
Task: "Implement transfer filter in src/kitelink/service/transfer_filter.py"
Task: "Add unit tests in tests/unit/test_transfer_filter.py"

# Then sequential:
Task: "RC poller in src/kitelink/service/adapters/rclone/rc_stats.py"
Task: "D-Bus aggregated transfers + tray UI"
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Setup + Foundational
2. US1 sign-in + mount
3. **STOP** — validate quickstart Q1
4. Demo folder-in-Files value

### Incremental Delivery

1. US1 → mounted Drive
2. US2 → calm progress (kills the #1 pain)
3. US3 → emblems
4. US4 → control/sign-out polish
5. US5 → public-ready `.deb`

### Suggested agent MVP cut

Implement through **US1 + US2** before emblems/packaging for fastest user-visible win.

---

## Notes

- Do not reintroduce unfiltered `notify-send` per RC transfer.
- Keep rclone types inside `service/adapters/rclone/`.
- Never commit real OAuth client secrets; use env/packaging secrets strategy.
- Brand SVG/PNG may arrive later — use placeholders without blocking structure.
