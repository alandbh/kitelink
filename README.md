# Kitelink

Linux desktop client that connects Google Drive to your Files app — like the line that keeps a kite in the air.

Kitelink targets a Google Drive Desktop–like experience on GNOME (Zorin OS / Nautilus first): branded folder, sync-state emblems, and calm tray progress for large downloads — without requiring the terminal for daily use.

## Status

Early product definition. See the full product requirements in [`PRD.md`](PRD.md).

Development follows **Spec-Driven Development** via [GitHub Spec Kit](https://github.com/github/spec-kit) (constitution → specify → plan → tasks → implement).

## Docs

| Document | Purpose |
|----------|---------|
| [PRD.md](PRD.md) | Product requirements (source of truth) |
| [specs/001-kitelink-mvp/](specs/001-kitelink-mvp/) | Phase 1 Spec Kit feature (spec, plan, tasks) |
| [.specify/memory/constitution.md](.specify/memory/constitution.md) | Project constitution |
| [assets/brand/](assets/brand/) | Logo / palette drop zone |
| [readme-1.md](readme-1.md) | rclone prototype notes |
| [readme-2.md](readme-2.md) | Feasibility / stack notes |

### Spec Kit workflow (Cursor)

Skills are installed under `.cursor/skills/`. Typical order:

1. `/speckit-constitution` (done → v1.0.0)
2. `/speckit-specify` (done → `specs/001-kitelink-mvp`)
3. `/speckit-plan` / `/speckit-tasks` (done)
4. `/speckit-implement` when ready to build code

## Strategy (short)

1. **Phase 1 (MVP):** GTK shell + Nautilus extension + tray UX on top of `rclone mount`.
2. **Phase 2:** Replace rclone with a Kitelink FUSE daemon + Drive API behind the same D-Bus contract.

## Brand assets

Drop logo SVG/PNG and the final palette into [`assets/brand/`](assets/brand/). Placeholder palette notes live in [`assets/brand/palette.md`](assets/brand/palette.md).
