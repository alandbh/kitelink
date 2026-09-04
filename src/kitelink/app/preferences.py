"""Preferences dialog."""

from __future__ import annotations


def open_preferences(parent, client) -> None:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk  # type: ignore

    prefs = client.get_preferences()
    dialog = Adw.Window(title="Kitelink Preferences", transient_for=parent, modal=True)
    dialog.set_default_size(420, 320)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    box.set_margin_top(20)
    box.set_margin_bottom(20)
    box.set_margin_start(20)
    box.set_margin_end(20)

    cache_entry = Gtk.Entry()
    cache_entry.set_text(str(prefs.get("vfs_cache_max_size", "10G")))
    cache_entry.set_placeholder_text("e.g. 10G")

    min_mb = Gtk.SpinButton.new_with_range(1, 1024, 1)
    min_mb.set_value(max(1, int(prefs.get("progress_min_bytes", 20 * 1024 * 1024)) // (1024 * 1024)))

    min_sec = Gtk.SpinButton.new_with_range(0, 60, 0.5)
    min_sec.set_digits(1)
    min_sec.set_value(float(prefs.get("progress_min_seconds", 3.0)))

    def row(label: str, widget) -> Gtk.Box:  # type: ignore[no-untyped-def]
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        r.append(Gtk.Label(label=label, xalign=0, hexpand=True))
        r.append(widget)
        return r

    box.append(row("VFS cache max size", cache_entry))
    box.append(row("Progress min size (MB)", min_mb))
    box.append(row("Progress min duration (s)", min_sec))

    status = Gtk.Label(label="")
    save = Gtk.Button(label="Save")
    save.add_css_class("suggested-action")

    def on_save(_b) -> None:  # type: ignore[no-untyped-def]
        payload = {
            "vfs_cache_max_size": cache_entry.get_text().strip() or "10G",
            "progress_min_bytes": int(min_mb.get_value()) * 1024 * 1024,
            "progress_min_seconds": float(min_sec.get_value()),
        }
        ok, msg = client.set_preferences(payload)
        status.set_text(msg)
        if ok:
            dialog.close()

    save.connect("clicked", on_save)
    box.append(status)
    box.append(save)
    dialog.set_content(box)
    dialog.present()
