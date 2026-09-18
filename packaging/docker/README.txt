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

This build-from-clone path is the only *confirmed working* install path
end to end. See the note below before using the other files in this
folder.

------------------------------------------------------------------------
PENDING (2026-09-09): a second, pull-based install path
------------------------------------------------------------------------
This folder also has docker-compose.dist.yml, publish.ps1, setup.sh, and
setup.ps1 - a second install path where a maintainer publishes a
pre-built image once, and target machines then install with a one-line
curl, no git/source/build required there. See dev/docs/DECISIONS.md
"Docker distribution: self-hosted registry + curl install, no git on
target machines" for the full design.

quixy's registry and install site (digib00age.tech) are up, and an image
(digib00age.tech:5000/digib00age:v2.6-dev1 and :latest) has been
published and pulls successfully. Still marked PENDING because the
pulled image hasn't yet been confirmed to actually run correctly
end-to-end (container starts, app reachable on :9800, Library Folders
picker works). Don't rely on setup.sh/setup.ps1 as the documented path
until dev/docs/SPEC.md's "Install paths" Docker section no longer says
PENDING - use the build-from-clone instructions above until then.

**This is two different jobs - don't conflate them:**

MAINTAINER, one-time per release, on the machine building the image
(windy) - a real end user never does this or sees publish.ps1:

  1. Docker Desktop must trust digib00age.tech:5000 as an insecure
     (plain-HTTP) registry, since it has no TLS (LAN-only). Settings >
     Docker Engine, add to the JSON:

         "insecure-registries": ["digib00age.tech:5000"]

     then Apply & Restart. (Editing %USERPROFILE%\.docker\daemon.json
     directly does NOT work - Docker Desktop treats its own settings
     store as the source of truth and silently overwrites daemon.json
     from it in the background whenever it starts. This setting has to
     go through the Settings UI, not a text editor.)

  2. From the repo root:

         .\packaging\docker\publish.ps1 -Tag v2.6-dev1

     Builds the image and pushes both that tag and :latest to
     digib00age.tech:5000. Pick a real version tag once this stops being
     a dev rehearsal.

END USER, every time they install - this is the actual pitch, and it is
NOT just the curl line by itself:

  1. Install Docker Desktop, make sure it's running.
  2. Same insecure-registries setting as above (Settings > Docker Engine
     > Apply & Restart) - required on every machine that will *pull*,
     not just the one that published. The registry is plain HTTP with no
     TLS cert (LAN-only), so Docker refuses the pull without this.
  3. Open a terminal in a normal, definitely-writable folder - don't
     trust whatever directory a shortcut/pinned icon happens to open in.
     Easiest way: in File Explorer, go to a normal folder (Documents,
     Desktop, etc.), then right-click inside it and choose "Open in
     Terminal" (Windows 11) or shift-right-click > "Open PowerShell
     window here" (Windows 10). Works whether that gives you cmd.exe or
     PowerShell - see why that no longer matters, next. Don't run it
     elevated ("Run as administrator") - Docker Desktop doesn't need it
     (just the current user in the docker-users group), and an elevated
     shell's cwd more often defaults to C:\Windows\System32 regardless of
     which folder you right-clicked in.

     setup.ps1 installs to .\digib00age relative to wherever it's run
     from, with no warning if that's a bad location. Installing into
     System32 in particular breaks it: Docker Desktop's WSL2 file
     sharing can't get proper bind-mount write access to a path under
     System32, so the container crash-loops with "PermissionError:
     /config/digib00age" even though it runs as root inside the
     container.

  4. Run these two lines (not chained with `;` or `&&` - deliberately
     two separate commands, since PowerShell 5.1 doesn't support `&&`
     and cmd.exe doesn't support `;`, so no single chained one-liner
     works in both). Both lines work as-is in cmd.exe, Windows
     PowerShell, and PowerShell 7+ - no need to know or care which shell
     you're in:

         curl.exe -fsSL http://digib00age.tech/setup.ps1 -o setup.ps1
         powershell -ExecutionPolicy Bypass -File setup.ps1

     `curl.exe` is used explicitly rather than plain `curl` because in
     PowerShell, `curl` can resolve to the built-in `Invoke-WebRequest`
     alias instead of the real curl.exe on PATH, and that alias doesn't
     understand `-fsSL` ("A parameter cannot be found that matches
     parameter name 'fsSL'" means you hit the alias). `powershell -File`
     is used instead of `.\setup.ps1` because cmd.exe can't execute a
     .ps1 directly, and -ExecutionPolicy Bypass avoids a default
     execution-policy prompt/block on running an unsigned script -
     scoped to this one process only, not a system-wide policy change.
     Read setup.ps1 before running it if you want to check it first
     (same as any curl-fetched installer) - it's a small file, open it
     in a text editor or `Get-Content .\setup.ps1` from PowerShell.

  If step 2 was skipped, `docker compose pull` fails with "server gave
  HTTP response to HTTPS client" (or, if nothing has ever been published
  yet, "failed to resolve reference ... not found" - that one means the
  maintainer's publish.ps1 hasn't run, not a problem on the user's end).

Windy's Docker Desktop originally wouldn't start at all ("virtualization
not enabled") - that turned out not to be a BIOS/UEFI setting (firmware
virtualization was already on) but two disabled Windows optional features:
Microsoft-Windows-Subsystem-Linux and VirtualMachinePlatform. Fixed via:

    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

(exit code 194 = reboot required, not an error) then reboot, then
`wsl --update` before launching Docker Desktop. This was a one-off fix
for windy specifically, not part of the regular install flow above -
noted here in case another test machine hits the same "virtualization
not enabled" message despite BIOS already being correct.
