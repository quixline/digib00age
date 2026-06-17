# ComicVault

A personal, local comic book server for a single user on a home network. Serves a CBZ
collection with metadata read from embedded `ComicInfo.xml`.

## Architecture

A FastAPI + SQLite backend (`backend/`) scans a CBZ library, serves a REST API, and hosts
a vanilla-JS web UI (`frontend/`) for browsing. A Flutter app (`flutter_app/`) installs on
Android and Windows for actual reading, connecting to the backend over the home network or
falling back to local CBZ files when offline. A pystray tray app (`tray/`) launches the
backend on Windows login and keeps it alive.

A separate metadata editor (not part of this repo) writes `ComicInfo.xml` back into CBZ
files and calls `POST /api/scan/file` on the backend to sync changes immediately — the two
apps share the same SQLite database but run as independent processes.

## Running it

1. Copy `config.example.json` to `config.json` and set `library_root` to your comic
   collection's path.
2. Either:
   - Run `start.bat` (normal use — launches the tray app, which starts the backend), or
   - Run `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000` directly for
     manual/dev use.
3. Open `http://localhost:8000` (or `http://<host-pc-ip>:8000` from another device on the
   network).

## Status

V1 complete — all six build phases (scanner/DB, REST API, web UI, issue detail page,
Flutter app, tray app + admin page) are built and live-tested on real hardware (Windows
desktop, Android tablet). No installer yet — setup is manual; an installer is a planned V2
item.

See `SPEC.md` for the full technical specification and decision log.
