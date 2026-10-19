# digib00age

A personal, local comic book server to run on a home network. Serves a CBZ
collection with metadata read from embedded `ComicInfo.xml`.

## Architecture

A FastAPI + SQLite backend (src/backend/) scans a CBZ library, serves a REST API, and hosts a vanilla-JS web UI (src/frontend/) for browsing, the Admin page, and the metadata editor — all as one process on one port. A Flutter app (src/flutter_app/) installs on Android and Windows for actual reading, connecting to the backend over the home network or falling back to local CBZ files when offline. A pystray tray app (src/tray/) launches the backend on Windows login and keeps it alive, with menu items for Open Library, Admin, Metadata Editor, Start/Stop Server, login autostart, and Close.

The metadata editor used to be a separate Flask app ("CAPT") syncing over a webhook — that's no longer true. Its editing logic (read/parse/rebuild ComicInfo.xml) was ported into this backend (src/backend/editor/) and is now exposed as two UIs in the same FastAPI app:

Basic Editor — quick single-issue edits, popup from /issue/{id}
Full Editor — batch tagging of new comics before they enter the library, at /editor

## Running it

**Most users:** download a prebuilt installer from **[digib00age.cc](https://digib00age.cc)**
— Windows MSI, Linux zip, or a one-line Docker setup, with full install
instructions on the site. Installers are also available directly from this
repo's [Releases](../../releases) page.

**Running from source** (cloning this repo):

1. Install Python dependencies: `pip install -r requirements.txt`.
2. Run `start.bat` (Windows) or `start.sh` (Linux) for normal use — launches the
   tray app, which manages the backend and gives you the full tray menu, or
   run `python start_server.py` directly (checks config, initializes the DB if
   needed, then starts uvicorn; Ctrl+C to stop) for a headless server — no
   tray, no GUI required, confirmed working as a standing deployment (e.g.
   wrapped in a systemd unit). It's fine to start it with no library configured yet.
3. Open `http://localhost:9800` (or `http://<host-pc-ip>:9800` from another device on
   the network) for the library, `/admin` for the Admin page, `/editor` for the Full
   Editor — all reachable from any device on the network. On Admin, go to **Library
   Management → Library Folders** to add one or more library paths (and scan them) —
   this, along with most other settings (port, scan excludes, backups, log limits),
   is configured live from the Admin UI now rather than by hand-editing
   `config.json`. Editing `config.json` directly is still needed only for a few
   low-level settings with no UI exposure (`thumbnail_size`, `thumbnail_dir`,
   `db_path`). Set a password (Admin > Advanced Settings) if you want to require a
   login; with no password set, these pages and everything behind them are open to
   anyone who can reach the server.

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

**Linux hosts, encrypted home directories:** if the library shows a blank or
permanently "Loading" page the *very first* time you open it right after a
reboot, just refresh or close/reopen the window — it clears immediately and
won't recur until the next reboot. This only shows up if your home directory
is encrypted (e.g. Ubuntu/Mint's eCryptfs "Encrypt my home folder" option):
the browser's first cold read of its own profile data can collide with the
encryption layer and stall the page before any request reaches the server.
It's an OS/kernel-level interaction, not anything in this app — any browser,
on any similarly encrypted Linux home directory, is liable to hit the same
thing once per boot.

**Linux hosts, installed-app icon:** if you install digib00age as a desktop app
(Admin page → Install App, or your browser's own install icon) and it shows a
generic browser icon instead of digib00age's own in Alt-Tab/the taskbar, your
desktop's icon cache likely just hasn't picked up the new icon yet — GTK-based
desktops (Cinnamon, GNOME, COSMIC, etc.) don't always refresh it automatically
on install. Run `gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor`,
then log out and back in (or restart your desktop panel) and it should show
correctly.

This repo contains the full application source. Packaging/deployment tooling
and internal working docs are intentionally left out of the public repo to
keep it minimal — open an issue if you need something that isn't here.

**BUILT WITH AI**
