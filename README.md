# Kitelink

Linux desktop client that connects Google Drive to your Files app — like the line that keeps a kite in the air.

Kitelink targets a Google Drive Desktop–like experience on GNOME (Zorin OS / Nautilus first): branded folder, sync-state emblems, and calm tray progress for large downloads — without requiring the terminal for daily use.

## Status

Phase 1 MVP **implementation in progress** (Spec Kit feature `001-kitelink-mvp`). Product requirements: [`PRD.md`](PRD.md).

## Develop

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Terminal A — user service (D-Bus)
export KITELINK_GOOGLE_CLIENT_ID="..."
export KITELINK_GOOGLE_CLIENT_SECRET="..."
kitelink-service

# Terminal B — UI
kitelink
```

Also requires system packages: `rclone` (≥ 1.60), `fuse3`, `python3-gi`, GTK 4 / libadwaita typelibs (`gir1.2-gtk-4.0`, `gir1.2-adw-1`), and `python3-nautilus` for emblems. PyGObject is expected from the distro (`python3-gi`), not necessarily from pip.

```bash
pytest
```

## Package

See [`packaging/README.md`](packaging/README.md) for `.deb` build and install notes.

## Docs

| Document | Purpose |
|----------|---------|
| [PRD.md](PRD.md) | Product requirements |
| [specs/001-kitelink-mvp/](specs/001-kitelink-mvp/) | Spec, plan, tasks, contracts |
| [specs/001-kitelink-mvp/quickstart.md](specs/001-kitelink-mvp/quickstart.md) | Manual validation |
| [packaging/README.md](packaging/README.md) | Debian packaging |
| [assets/brand/](assets/brand/) | Logo, palette, emblems |

## Strategy

1. **Phase 1:** GTK + Nautilus extension + tray on `rclone mount` behind D-Bus `org.kitelink.Service1`.
2. **Phase 2:** Native FUSE/Drive API adapter replacing rclone (same D-Bus contract).
