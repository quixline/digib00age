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

On a headless host (no browser on the machine running the container), you
cannot complete first-run password setup from the Admin UI at all - setting
a password and enabling remote admin are both hard-gated to a genuine
loopback (127.0.0.1) request, with no override, by design (this is
intentional: the thing that grants remote trust must never itself be
grantable remotely). Do it once from a shell on the host instead:

    curl -X POST http://localhost:9800/api/admin/auth/enable \
      -H 'Content-Type: application/json' \
      -d '{"password":"YOUR_PASSWORD"}'
    curl -X POST http://localhost:9800/api/admin/auth/remote-toggle \
      -H 'Content-Type: application/json' \
      -d '{"enabled":true}'

After that, http://<host>:9800/admin works normally from any LAN browser,
logging in with the password just set. Changing the password later
(POST /api/admin/auth/change-password) requires the same local-shell access,
permanently - not just for this first bootstrap step.

KNOWN GAP, FLAGGED FOR REWORK (2026-09-04): this shell-only bootstrap is
real friction on a genuinely headless box - there's no way for the person
setting the machine up to just open a browser and pick their own password
the way every other install path works. See DECISIONS.md's Docker entries
for the full reasoning and dev/docs/ROADMAP.md for the flagged follow-up.

Known limitation: Restart Server, Clear/Restore Database, and all Processing
Tools (convert/rename/move/tag/etc.) are unavailable from a browser on a
different machine than the one running the container - same local-only
boundary that already applies to any other LAN client accessing digib00age
today, not something specific to Docker. Everyday use (browsing, reading,
scanning, editing metadata, and the Admin UI's own library-folder setup) is
unaffected once the bootstrap above is done.

No image is published to a registry yet - build locally from a repo clone
as shown above.
