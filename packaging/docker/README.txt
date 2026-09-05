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

First launch pre-fills the library location as /library (the in-container
mount point set in docker-compose.yml, not your host path) - if you kept that
mount as-is, there's nothing further to configure. Every other install path
still starts from the same bare config.json template with no library set.
config/DB/thumbnails persist across restarts and rebuilds via the ./config
and ./data bind mounts next to the compose file.

/library is just this compose file's example mount name, not a hard limit -
Docker doesn't auto-detect drives or USB devices (true of any containerized
app), so a folder only exists inside the container if docker-compose.yml
mounts it there. To use a different or additional location (e.g. a USB
drive), give it a stable mount point on the host first, add another line
under volumes: with whatever container-side name you like, restart the
container, then use the Admin UI's Browse button (Library Folders) to reach
it and add it as a Scan Root - same web-based picker used everywhere else in
the app, not a native OS dialog, so it works the same whether the container
has a display or not.

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
