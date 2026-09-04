"""Brand-aligned CSS helpers from assets/brand/palette.md."""

from __future__ import annotations

PALETTE = {
    "bg": "#F1F7FF",
    "fg": "#3A3A3A",
    "accent": "#1E77FC",
    "accent_fg": "#D2E4FF",
    "success": "#0EBF17",
    "cloud": "#B2D2FE",
    "sync": "#ABF1AF",
    "danger": "#FD0A0A",
}

APP_CSS = f"""
window {{
  background-color: {PALETTE["bg"]};
  color: {PALETTE["fg"]};
}}
.kitelink-accent {{
  background-color: {PALETTE["accent"]};
  color: {PALETTE["accent_fg"]};
}}
"""


def apply_brand_css(display=None) -> None:  # type: ignore[no-untyped-def]
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gdk, Gtk  # type: ignore

        css = Gtk.CssProvider()
        css.load_from_data(APP_CSS.encode("utf-8"))
        display = display or Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
    except Exception:
        pass
