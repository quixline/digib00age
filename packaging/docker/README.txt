digib00age - Docker install
=============================

Additional install option alongside the Windows MSI and Linux installer -
not a replacement for either. Backend + web frontend only: the Flutter app
and the desktop tray launcher are out of scope for a container (a container
doesn't need desktop tray lifecycle management, and Flutter just needs a
server URL to point at).

Copy this folder's docker-compose.yml next to a clone of the repo (or edit
it in place), then from the repo root:

    docker compose -f packaging/docker/docker-compose.yml up -d --build

Nothing to edit first in the common case: the default compose file mounts
the host's whole /mnt tree straight through to the container's /mnt, same
path on both sides - the same approach qBittorrent's own container uses.
Every drive mounted under the host's /mnt (USB or otherwise) shows up inside
the container with its real name, automatically, with no per-drive line to
add. If your host keeps drives somewhere other than /mnt, edit that one
volumes: line to match before starting the container.

First launch has nothing pre-set - open http://<host>:9800/admin, go to
Library Folders, use the Browse picker to navigate to the real path under
/mnt (e.g. /mnt/your-drive-name/Comics), and add it as a Scan Root. Add as
many Scan Roots as you have drives/folders, all from the same picker, no
compose edits or restarts needed. Every install path (Windows MSI, pip,
Docker) starts from the same bare config.json template with no library set.
config/DB/thumbnails persist across restarts and rebuilds via the ./config
and ./data bind mounts next to the compose file.

Docker never auto-detects drives or USB devices itself (true of any
containerized app) - a path only exists inside the container if
docker-compose.yml mounts it there, which is why the default /mnt:/mnt line
covers the common case without further editing. Prefer one folder mounted
directly instead (e.g. a single-drive setup)? Replace that line with
- /path/to/your/comics:/library and it'll be pre-filled as the library
location on first launch automatically, same as before - see the comments
in docker-compose.yml for both options.

There is no gated first-run setup. Password protection is entirely optional
and entirely on you: open http://<host>:9800/admin from any browser on any
machine that can reach the port (or curl it from anywhere) and, if you want
a password, set one there or via:

    curl -X POST http://<host>:9800/api/admin/auth/enable \
      -H 'Content-Type: application/json' \
      -d '{"password":"YOUR_PASSWORD"}'

Until a password is set, Admin, Editor, and every Processing Tool
(convert/rename/move/tag/restart/clear-database/etc.) are open to anyone who
can reach the container's port - same as every other install path, not a
Docker-specific quirk. Set a password if you don't want that. Once set, a
valid login (from any machine) is the only thing required for any of those
actions, including from a browser on a different machine than the one
running the container.

Known limitation, unrelated to auth: Open Logs Folder reveals the logs
folder in a native file-explorer window on the machine running the backend
process - meaningless in a container with no display, so it remains
non-functional regardless of who's calling it or whether they're logged in.
The logs folder path is still shown as plain text in the Admin UI if you need
it. (Restore Database and the Scheduled Backup destination previously had
the same native-dialog limitation but now use the same web-based Browse
picker as Scan Roots and the Processing Tools, so both work normally in
Docker.) Everything else works normally, remotely or locally.

No image is published to a registry yet - build locally from a repo clone
as shown above.
