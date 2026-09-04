# digib00age

A personal, local comic book server for a single user on a home network. Serves a CBZ
collection with metadata read from embedded `ComicInfo.xml`.

Start here, then see `dev/docs/INDEX.md` for the full doc map (local working docs,
not part of this repo's public git history — see "Repo layout" below).

## Architecture

A FastAPI + SQLite backend (`src/backend/`) scans a CBZ library, serves a REST API,
and hosts a vanilla-JS web UI (`src/frontend/`) for browsing, the Admin page, and the
metadata editor — all as **one process on one port**. A Flutter app
(`src/flutter_app/`) installs on Android and Windows for actual reading, connecting to
the backend over the home network or falling back to local CBZ files when offline. A
pystray tray app (`src/tray/`) launches the backend on Windows login and keeps it
alive, with menu items for Open Library, Admin, Metadata Editor, Start/Stop Server,
login autostart, and Close.

The metadata editor used to be a separate Flask app ("CAPT") syncing over a webhook —
that's no longer true. Its editing logic (read/parse/rebuild `ComicInfo.xml`) was
ported into this backend (`src/backend/editor/`) and is now exposed as two UIs in the
same FastAPI app:
- **Basic Editor** — quick single-issue edits, popup from `/issue/{id}`
- **Full Editor** — batch tagging of new comics before they enter the library, at
  `/editor`

See `dev/docs/EDITOR_SPEC.md` for the full editor design.

## Repo layout

```
src/            Everything the app needs to run — backend, frontend, flutter_app,
                chrome-extension, tray. This is what's meant to be public.
packaging/      Source for building distributable installers (PyInstaller specs,
                Debian package files, app-menu/icon assets). Not the installers
                themselves — those are build output, not source.
dev/            Local working space (docs, ct_cache) — gitignored, not part
                of this repo's public history.
logs/           Processing/scan tool logs — gitignored, mirrors the installed
                layout (<install-dir>/logs).
config.json     Tracked, bare template — no secrets. Real values (API key,
                session secret, admin password, real library path) live in
                config.json.bak, which stays gitignored; rename it in locally
                when you need to run against real data.
```

## Running it

1. `config.json` at the repo root is a bare template (safe to commit — no
   secrets). To run against real data, rename `config.json.bak` (gitignored,
   holds the real library path and secrets) onto `config.json` locally. If
   `library_root` isn't set, the app still boots fine; set it from the Admin
   page's Library Folders section afterward.
2. Either:
   - Run `start.bat` (Windows) or `start.sh` (Linux) for normal use — launches the
     tray app, which manages the backend and gives you the full tray menu, or
   - Run `python start_server.py` directly for manual/dev use (checks config,
     initializes the DB if needed, then starts uvicorn; Ctrl+C to stop).
3. Open `http://localhost:9800` (or `http://<host-pc-ip>:9800` from another device on
   the network) for the library. `/admin` for the Admin page, `/editor` for the Full
   Editor — both reachable from any device on the network. Set a password (Admin >
   Advanced Settings) if you want to require a login; with no password set, these
   pages and everything behind them are open to anyone who can reach the server.

Python dependencies are in `requirements.txt` (`pip install -r requirements.txt`).

**Linux hosts:** if the mobile reader (or any other device) can't reach
`http://<host-pc-ip>:9800`, check whether a host firewall is blocking the port —
the server itself binds to `0.0.0.0` correctly. For UFW: `sudo ufw allow 9800/tcp`,
then `sudo ufw status verbose` to confirm.

**Linux hosts, tray app:** the venv must be created with `--system-site-packages`
(or have `include-system-site-packages = true` set in an existing venv's
`pyvenv.cfg`), and `python3-gi` + `gir1.2-appindicator3-0.1` (or the ayatana
equivalents) + `libayatana-appindicator3-1` + `gir1.2-gtk-3.0` must be installed
via apt first. Without these, pystray silently falls back to a legacy X11 systray
backend that renders an icon but supports no menu at all — no error, just a tray
icon that does nothing when clicked.

**Docker:** backend + web frontend only (no Flutter app, no tray launcher —
see `packaging/docker/README.txt`). From the repo root:
`docker compose -f packaging/docker/docker-compose.yml up -d --build`.
No gated setup — open `/admin` from any browser that can reach the port and
optionally set a password; everything (including Restart Server, Clear/
Restore Database, and Processing Tools) works the same from any machine as
it does locally. Three specific actions (Open Logs Folder, and the native
file/folder pickers behind Restore Database and Scheduled Backup) open a GUI
dialog on the container's own machine and stay non-functional headless
(no display) — unrelated to auth, flagged for a future web-based redesign.

## Status

V1 is complete. V2 is active — editor integration, Custom Tabs, Home Strips, and a
Genre/Format admin editor have all shipped; see `dev/docs/CHANGELOG.md` for the dated
list. Check `dev/docs/ROADMAP.md` for what's next. No installer yet — setup is manual
(`config.json.bak` → `config.json` + `start.bat`); not currently prioritized.

See `dev/docs/SPEC.md` for the full V1 technical specification and `dev/docs/INDEX.md`
for the complete doc map (what governs what, and the authority order between docs).
