# ComicVault

A personal, local comic book server for a single user on a home network. Serves a CBZ
collection with metadata read from embedded `ComicInfo.xml`.

Start here, then see `docs/INDEX.md` for the full doc map. (`docs/` is a directory
junction into a Google Drive-synced folder, used for Claude Cowork planning access —
see `CLAUDE.md` Section 2.)

## Architecture

A FastAPI + SQLite backend (`backend/`) scans a CBZ library, serves a REST API, and
hosts a vanilla-JS web UI (`frontend/`) for browsing, the Admin page, and the metadata
editor — all as **one process on one port**. A Flutter app (`flutter_app/`) installs
on Android and Windows for actual reading, connecting to the backend over the home
network or falling back to local CBZ files when offline. A pystray tray app (`tray/`)
launches the backend on Windows login and keeps it alive, with menu items for Open
Library, Admin, Metadata Editor, Start/Stop Server, login autostart, and Close.

The metadata editor used to be a separate Flask app ("CAPT") syncing over a webhook —
that's no longer true. Its editing logic (read/parse/rebuild `ComicInfo.xml`) was
ported into this backend (`backend/editor/`) and is now exposed as two UIs in the same
FastAPI app:
- **Basic Editor** — quick single-issue edits, popup from `/issue/{id}`
- **Full Editor** — batch tagging of new comics before they enter the library, at
  `/editor`

See `docs/EDITOR_SPEC.md` for the full editor design.

## Running it

1. Copy `config.example.json` to `config.json` and set `library_root` to your comic
   collection's path.
2. Either:
   - Run `start.bat` (normal use — launches the tray app, which manages the backend
     and gives you the full tray menu), or
   - Run `python start_server.py` directly for manual/dev use (validates config,
     initializes the DB if needed, then starts uvicorn; Ctrl+C to stop).
3. Open `http://localhost:8000` (or `http://<host-pc-ip>:8000` from another device on
   the network) for the library. `/admin` for the Admin page, `/editor` for the Full
   Editor — both intended for localhost use only.

Python dependencies are in `requirements.txt` (`pip install -r requirements.txt`).

## Status

V1 is complete. V2 is active — editor integration, Custom Tabs, Home Strips, and a
Genre/Format admin editor have all shipped; see `docs/CHANGELOG.md` for the dated list.
The 2.1 planning backlog (`docs/comicvault-changes-2.1.md`) closed out 2026-06-22 with
everything in it done; check `docs/ROADMAP.md` for what's next. No installer yet — setup
is manual (`config.json` + `start.bat`); not currently prioritized.

See `docs/SPEC.md` for the full V1 technical specification and `docs/INDEX.md` for the
complete doc map (what governs what, and the authority order between docs).
