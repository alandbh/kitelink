# Packaging Kitelink (.deb)

## Dependencies

- **rclone ≥ 1.60** (declared in `debian/control`) — provides the Phase 1 mount/VFS backend.
- GNOME stack: GTK 4, libadwaita, python3-gi, python3-nautilus, fuse3.
- OAuth: set at runtime (do not bake secrets into the package):

```bash
export KITELINK_GOOGLE_CLIENT_ID="..."
export KITELINK_GOOGLE_CLIENT_SECRET="..."
```

Prefer dropping a drop-in env file for the user service, e.g.  
`~/.config/environment.d/kitelink.conf` or a systemd user drop-in.

## Build (from repo root)

```bash
# Option A: local editable install (development)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Option B: Debian package (on Ubuntu/Zorin build host)
sudo apt install debhelper dh-python python3-setuptools
cp -a packaging/debian ./debian
dpkg-buildpackage -us -uc -b
```

The produced `.deb` installs:

- `kitelink` / `kitelink-service` entry points
- `systemd --user` unit `kitelink.service`
- Nautilus extension
- Emblem SVGs and app icon

## After install

```bash
systemctl --user daemon-reload
systemctl --user enable --now kitelink.service
# Restart Files to load the extension:
nautilus -q || true
kitelink
```

## rclone version gate

If `rclone` is older than 1.60, some VFS/RC flags used by the mount unit may be missing.
The package Depends field enforces `rclone (>= 1.60)`.
