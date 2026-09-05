"""Nautilus extension — emblems via Kitelink D-Bus (no Google calls)."""

from __future__ import annotations

import os
from urllib.parse import unquote, urlparse

try:
    from gi.repository import GObject, Nautilus  # type: ignore
except ImportError:  # pragma: no cover - only loads inside Nautilus
    Nautilus = None
    GObject = object  # type: ignore


BUS_NAME = "org.kitelink.Service"
OBJECT_PATH = "/org/kitelink/Service"
INTERFACE = "org.kitelink.Service1"

# Nautilus looks up "emblem-<name>" (and "<name>-symbolic" on dark themes).
EMBLEM_MAP = {
    "locally_available": "kitelink-local",
    "syncing": "kitelink-sync",
    "cloud_or_unknown": "kitelink-cloud",
    "error": "kitelink-error",
}


def _path_from_fileinfo(file_info) -> str | None:  # type: ignore[no-untyped-def]
    loc = file_info.get_location()
    uri = loc.get_uri()
    if not uri.startswith("file://"):
        return None
    return unquote(urlparse(uri).path)


def _get_path_state(path: str) -> str:
    try:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib  # type: ignore

        proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            BUS_NAME,
            OBJECT_PATH,
            INTERFACE,
            None,
        )
        result = proxy.call_sync(
            "GetPathState",
            GLib.Variant("(s)", (path,)),
            Gio.DBusCallFlags.NONE,
            500,
            None,
        )
        state, _confidence = result.unpack()
        return state
    except Exception:
        return "cloud_or_unknown"


if Nautilus is not None:

    class KitelinkInfoProvider(GObject.GObject, Nautilus.InfoProvider):
        def __init__(self) -> None:
            super().__init__()
            self._infos: dict[str, object] = {}
            try:
                from gi.repository import GLib  # type: ignore

                GLib.idle_add(self._subscribe)
            except Exception:
                pass

        def _subscribe(self) -> bool:
            try:
                import gi

                gi.require_version("Gio", "2.0")
                from gi.repository import Gio  # type: ignore

                conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                conn.signal_subscribe(
                    BUS_NAME,
                    INTERFACE,
                    "PathStateMayHaveChanged",
                    OBJECT_PATH,
                    None,
                    Gio.DBusSignalFlags.NONE,
                    self._on_path_hint,
                )
            except Exception:
                return False
            return False

        def _on_path_hint(self, *_args) -> None:  # type: ignore[no-untyped-def]
            prefix = ""
            if len(_args) >= 6:
                try:
                    prefix = str(_args[5].unpack()[0])
                except Exception:
                    prefix = os.path.expanduser("~/Kitelink")
            try:
                from gi.repository import GLib  # type: ignore

                GLib.idle_add(self._invalidate_prefix, prefix)
            except Exception:
                pass

        def _invalidate_prefix(self, prefix: str) -> bool:
            home = os.path.expanduser("~/Kitelink")
            root = prefix or home
            for path, info in list(self._infos.items()):
                if path == root or path.startswith(root.rstrip("/") + "/") or root.startswith(path + "/"):
                    try:
                        info.invalidate_extension_info()  # type: ignore[attr-defined]
                    except Exception:
                        self._infos.pop(path, None)
            return False

        def update_file_info(self, file_info) -> None:  # type: ignore[no-untyped-def]
            path = _path_from_fileinfo(file_info)
            if not path:
                return
            home = os.path.expanduser("~/Kitelink")
            if not path.startswith(home):
                return
            self._infos[path] = file_info
            state = _get_path_state(path)
            emblem = EMBLEM_MAP.get(state)
            if emblem:
                file_info.add_emblem(emblem)

else:  # pragma: no cover

    class KitelinkInfoProvider:  # type: ignore[no-redef]
        """Placeholder when Nautilus bindings are unavailable."""

        pass
