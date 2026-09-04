digib00age - Docker install
=============================

Additional install option alongside the Windows MSI and Linux installer -
not a replacement for either. Backend + web frontend only: the Flutter app
and the desktop tray launcher are out of scope for a container (a container
doesn't need desktop tray lifecycle management, and Flutter just needs a
server URL to point at).

Copy this folder's docker-compose.yml next to a clone of the repo (or edit
it in place), open it and change the /path/to/your/comics line to your real
library path, then from the repo root:

    docker compose -f packaging/docker/docker-compose.yml up -d --build

First launch starts with the same bare config.json template every install
path ships with - open the Admin UI (http://<host>:9800/admin) and set the
library location to /library (the in-container mount point set in
docker-compose.yml, not your host path). config/DB/thumbnails persist across
restarts and rebuilds via the ./config and ./data bind mounts next to the
compose file.

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

Known limitation, unrelated to auth: three specific actions (Open Logs
Folder, and the native file/folder pickers behind Restore Database and the
Scheduled Backup destination) open a GUI dialog on the machine running the
backend process. In a container that has no display, so these three remain
non-functional regardless of who's calling them or whether they're logged
in - this needs a web-based alternative, scoped as its own future session
(see dev/docs/ROADMAP.md). Everything else works normally, remotely or
locally.

No image is published to a registry yet - build locally from a repo clone
as shown above.
