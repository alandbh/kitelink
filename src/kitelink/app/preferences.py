"""S20 Preferences — grouped Adwaita language for Ana, not VFS jargon."""

from __future__ import annotations

from kitelink.app import help_copy as copy
from kitelink.app.widgets import pill_button


def open_preferences(parent, client) -> None:  # type: ignore[no-untyped-def]
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk  # type: ignore

    prefs = client.get_preferences()
    try:
        _conn, mountpoint, _cerr = client.get_connection_status()
    except Exception:
        mountpoint = "~/Kitelink"

    win = Adw.PreferencesWindow(transient_for=parent, modal=True)
    win.set_title(copy.S20_TITLE)
    win.set_search_enabled(False)
    win.set_default_size(480, 560)

    page = Adw.PreferencesPage()
    page.set_title(copy.S20_TITLE)

    storage = Adw.PreferencesGroup(title=copy.S20_STORAGE, description=copy.S20_CACHE_SUB)
    cache_row = Adw.EntryRow(title=copy.S20_CACHE)
    cache_row.set_text(str(prefs.get("vfs_cache_max_size", "10G")))
    storage.add(cache_row)
    page.add(storage)

    progress = Adw.PreferencesGroup(title=copy.S20_PROGRESS, description=copy.S20_PROGRESS_SUB)
    min_mb = Gtk.SpinButton.new_with_range(1, 1024, 1)
    min_mb.set_value(max(1, int(prefs.get("progress_min_bytes", 20 * 1024 * 1024)) // (1024 * 1024)))
    mb_row = Adw.ActionRow(title=copy.S20_MIN_MB)
    mb_row.add_suffix(min_mb)
    min_sec = Gtk.SpinButton.new_with_range(0, 60, 0.5)
    min_sec.set_digits(1)
    min_sec.set_value(float(prefs.get("progress_min_seconds", 3.0)))
    sec_row = Adw.ActionRow(title=copy.S20_MIN_SEC)
    sec_row.add_suffix(min_sec)
    progress.add(mb_row)
    progress.add(sec_row)
    page.add(progress)

    folder = Adw.PreferencesGroup(title=copy.S20_FOLDER)
    folder_row = Adw.ActionRow(title=copy.S20_FOLDER_PATH, subtitle=mountpoint or "~/Kitelink")
    open_btn = Gtk.Button(label=copy.S10_OPEN_FOLDER)
    open_btn.add_css_class("flat")
    open_btn.connect("clicked", lambda *_: _safe_open(client))
    folder_row.add_suffix(open_btn)
    folder.add(folder_row)
    page.add(folder)

    about = Adw.PreferencesGroup(title=copy.S20_ABOUT, description=copy.S20_ABOUT_BODY)
    about.add(Adw.ActionRow(title=copy.APP_NAME, subtitle=copy.APP_VERSION))
    page.add(about)

    actions = Adw.PreferencesGroup()
    status = Gtk.Label(label="")
    save = pill_button(copy.S20_SAVE, suggested=True)
    save_row = Adw.ActionRow(title="")
    save_row.add_suffix(save)
    actions.add(save_row)
    page.add(actions)

    def on_save(_b) -> None:
        payload = {
            "vfs_cache_max_size": cache_row.get_text().strip() or "10G",
            "progress_min_bytes": int(min_mb.get_value()) * 1024 * 1024,
            "progress_min_seconds": float(min_sec.get_value()),
        }
        ok, msg = client.set_preferences(payload)
        status.set_text(msg)
        if ok:
            win.close()

    save.connect("clicked", on_save)
    win.add(page)
    win.present()


def _safe_open(client) -> None:  # type: ignore[no-untyped-def]
    try:
        client.open_mountpoint()
    except Exception:
        pass
