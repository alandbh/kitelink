# Kitelink Phase 1 — manual VM validation checklist (quickstart companion)

Use with [quickstart.md](./quickstart.md). Record results while testing.

| ID | Scenario | Pass? | Notes |
|----|----------|-------|-------|
| Q1 | Sign-in + `~/Kitelink` | | |
| Q2 | Large file tray progress ≤5s; no browse spam | | |
| Q3 | Emblems differ local vs cloud | | |
| Q4 | Tray prefs / diagnostics / sign-out | | |
| Q5 | Fresh `.deb` install | | |
| Q6 | RC localhost-only | | |

## Known gaps before first VM pass (T047)

- Full OAuth requires real `KITELINK_GOOGLE_CLIENT_ID` / `SECRET` (Google Cloud Desktop client).
- Emblem themes may need `gtk-update-icon-cache` after package install.
- Nautilus must be restarted to load the Python extension.
- Tray UI is a compact status window (StatusNotifierItem can be added later).
