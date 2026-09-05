"""Shared GTK/Adwaita chrome for Kitelink screens."""

from __future__ import annotations

from pathlib import Path

from kitelink.app.brand import apply_brand_css
from kitelink.app.help_copy import APP_NAME


def _repo_logo() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "assets" / "brand" / "logo" / "icon-positive.svg"
        if candidate.is_file():
            return candidate
    return None


def load_logo(size: int = 64):
    from gi.repository import Gtk  # type: ignore

    pic = Gtk.Picture()
    pic.set_size_request(size, size)
    pic.set_content_fit(Gtk.ContentFit.CONTAIN)
    path = _repo_logo()
    if path is not None:
        pic.set_filename(str(path))
        pic.set_can_shrink(True)
    return pic


def pill_button(label: str, *, suggested: bool = False, destructive: bool = False):
    from gi.repository import Gtk  # type: ignore

    btn = Gtk.Button(label=label)
    btn.add_css_class("pill")
    if suggested:
        btn.add_css_class("suggested-action")
    if destructive:
        btn.add_css_class("destructive-action")
    return btn


def wrap_margins(child, margin: int = 24):
    from gi.repository import Gtk  # type: ignore

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    box.set_margin_top(margin)
    box.set_margin_bottom(margin)
    box.set_margin_start(margin)
    box.set_margin_end(margin)
    box.append(child)
    return box


def prepare_window(window) -> None:  # type: ignore[no-untyped-def]
    apply_brand_css()
    window.set_title(APP_NAME)
