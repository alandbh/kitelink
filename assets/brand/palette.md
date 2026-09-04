# Kitelink color palette

## Tokens

| Token | Hex | Usage |
|-------|-----|-------|
| `--kitelink-bg` | #F1F7FF | Window / content background |
| `--kitelink-fg` | #3A3A3A | Primary text |
| `--kitelink-accent` | #1E77FC | Primary actions, focus |
| `--kitelink-accent-fg` | #D2E4FF | Text on accent |
| `--kitelink-success` | #0EBF17 | Locally available / synced emblem |
| `--kitelink-cloud` | #B2D2FE | Cloud-only emblem |
| `--kitelink-sync` | #ABF1AF | Syncing / in-progress |
| `--kitelink-danger` | #FD0A0A | Error / conflict |

## Emblem mapping (Phase 1)

| State | Emblem intent |
|-------|----------------|
| cloud-only | Graen cloud |
| syncing | Sync arrows |
| locally-available | Green check |
| error | Warning / error mark |

## Notes

- Prefer symbolic emblems compatible with Nautilus/GNOME where possible.
- Avoid relying on purple-on-white AI-default palettes; final kit decides the look.
- Keep contrast WCAG-friendly for tray labels and settings copy.
