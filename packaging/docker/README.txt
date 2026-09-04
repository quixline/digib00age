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

Known limitation: Restart Server, Clear/Restore Database, and all Processing
Tools (convert/rename/move/tag/etc.) are unavailable from a browser on a
different machine than the one running the container - same local-only
boundary that already applies to any other LAN client accessing digib00age
today, not something specific to Docker. Everyday use (browsing, reading,
scanning, editing metadata, and the Admin UI's own library-folder setup) is
unaffected: enable password protection + "Allow remote administration" in
Admin Settings to reach the Admin/Editor UI itself from another machine.

No image is published to a registry yet - build locally from a repo clone
as shown above.
