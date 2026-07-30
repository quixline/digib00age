# Public repo / pre-packaging plan (DRAFT — under discussion, not yet actioned)

Status: draft for chat discussion. Nothing has been moved, copied, or committed yet.
This doc exists so Tez and Claude can discuss the approach with the full plan in view,
not tucked away in a plan-mode file. Once agreed, this becomes either an entry in
`DECISIONS.md` (if the call is non-obvious) or just gets actioned and this file can be
deleted.

## Context

The dev repo (`D:\workshop\comicvault_v2`) has accumulated a lot that's specific to
the Claude-Code-driven dev workflow: `docs/` (build queues, progress logs, bug
history), `.claude/` (session config), `design_handoff_tablet_app/` (a design-mockup
artifact, not app code), `graphify-out/` (regenerable knowledge-graph cache),
`logs/` (runtime admin logs), `ct_cache/` (ComicVine lookup cache), `chrome-extension/`
(added 2026-07-30 — a personal Chrome extension hardcoded to Tez's own
`localhost:9424` instance, see `docs/goodreads-extension-scope.md`; not meant for
other installs), plus dev-only junk that lives on disk but isn't git-tracked (real
`.db` files, `thumbnails/`, `__pycache__/`, tray `.log` files, the real `config.json`
with a live ComicVine API key and session secret).

Tez wants a second, clean location — proposed at `D:\workshop\digib00age\public-repo`
— that becomes a new public git repo: source only (backend, frontend, tray, Flutter
app source — following the ComicTagger precedent of publishing source without the
internal dev-process docs), plus the already-built Flutter release binaries
(APK + Windows exe) as installable artifacts, with no personal data, no secrets, and
no dev-process history. The current repo stays untouched as the dev location.

## What decides "in" vs "out"

`git ls-files` on the current repo is already a clean manifest: `.gitignore` here
already excludes the real `.db`/`.db-wal`/`.db-shm`/`.bak` files, `backend/thumbnails/`,
`__pycache__/`, tray logs, `ct_cache/`, `logs/`, `graphify-out/`, and `config.json`
itself. Verified by grep that no tracked file outside `docs/` contains a hardcoded
secret, API key, or personal path — every hit (`SESSION_SECRET`, `comicvine_api_key`,
etc.) is a config-key *name*, read from `config.json` at runtime, never a literal
value.

So: **base the copy on `git ls-files`, then remove the top-level dirs Tez named**
(`docs/`, `.claude/` — already gitignored so absent anyway, `design_handoff_tablet_app/`,
`chrome-extension/`), **then add back** the two Flutter release build outputs, which
are gitignored (under `flutter_app/build/`) and so wouldn't come along automatically.

## Proposed steps

1. **Create `D:\workshop\digib00age\public-repo\`.**

2. **Copy git-tracked files**, from `git ls-files` in `D:\workshop\comicvault_v2`,
   excluding anything under:
   - `docs/`
   - `.claude/` (not actually tracked, but confirm none slip through)
   - `design_handoff_tablet_app/`
   - `chrome-extension/` (personal, single-instance tool — see Context above)

   This carries over as-is (already git-clean, no personal data):
   - `backend/` — all `.py` source, `backend/editor/` (incl. `formats.json`,
     `genres.json` — read at runtime), `backend/routers/`. No `.db` files,
     no `thumbnails/`, no `__pycache__/` (none are tracked).
   - `frontend/` — all `.html`/`.css`/`.js`, `images/`, `manifest.json`, `sw.js`.
   - `tray/tray_app.py` (no `.log` files — not tracked).
   - `flutter_app/` source tree as `git ls-files flutter_app` returns it (94 files:
     `lib/`, `android/` source — not `.gradle`/`.kotlin`, `windows/` source — not
     the `build/` CMake tree, `assets/`, `pubspec.yaml`, `pubspec.lock`,
     `analysis_options.yaml`, `.metadata`).
   - Root files: `README.md`, `LICENSE`, `requirements.txt`, `start.bat`,
     `start_server.py`, `config.example.json`, `.gitignore` (trimmed — see step 4).

3. **Add the two Flutter release build outputs** (not git-tracked today, under
   gitignored `flutter_app/build/`), placed in a clearly separate `releases/` folder
   so they read as prebuilt installable artifacts, not source:
   - `releases/android/app-release.apk` (from
     `flutter_app/build/app/outputs/flutter-apk/app-release.apk`, 53 MB)
   - `releases/windows/` — the full contents of
     `flutter_app/build/windows/x64/runner/Release/` (31 MB: `digib00age.exe` +
     its 4 DLLs + `data/` folder — the exe alone won't run without these)

   No debug builds, no CMake/Gradle intermediate build trees.

4. **Explicitly excluded / not carried over:**
   - `docs/`, `.claude/`, `design_handoff_tablet_app/`, `graphify-out/`, `logs/`,
     `ct_cache/` — per Tez's request.
   - `chrome-extension/` — personal, single-instance tool hardcoded to Tez's own
     `localhost:9424`, not portable to other installs (see
     `docs/goodreads-extension-scope.md`).
   - Real `config.json` (has a live ComicVine API key, `SESSION_SECRET`, real
     library/backup paths) — only `config.example.json` goes in the new repo.
   - Any `.db`/`.db-wal`/`.db-shm`/`.bak` file, `backend/thumbnails/`,
     `__pycache__/` dirs, `tray/*.log`.
   - Rest of `flutter_app/build/` (debug APK, all CMake/Gradle cache/intermediate
     dirs) beyond the two release outputs pulled out in step 3.
   - Write a new `.gitignore` for the new repo (same shape as the current one,
     minus rules for things that no longer exist there — `docs/`-related lines,
     `graphify-out/`, `logs/`, `build-plan.html`, Cowork-era entries).

5. **Sanity pass on the copied tree** before treating it as done:
   - Confirm no `.db`, `config.json`, or `*.log` file made it across.
   - Confirm `git ls-files flutter_app` count (94) matches what got copied under
     `flutter_app/`.
   - Confirm `releases/windows/digib00age.exe` and its 4 DLLs + `data/` are present
     together (it won't launch missing any one of them).
   - Spot check a couple of backend files for the config-key-name-only pattern
     already verified above (no literal secret values).

6. Report the final folder back to Tez with a file count / size summary. Actual
   `git init` + first commit on `public-repo`, and any decision about whether the
   release binaries live in git history vs. GitHub Releases long-term, is a separate
   step Tez should explicitly greenlight.

## Open questions raised so far

- **Flutter source in the public repo:** Tez wants source included (ComicTagger
  precedent) but excluded from the eventual `.msi` install package. This plan copies
  Flutter source into the public repo as normal source; the `.msi`-building step
  (separate, later) would need to package only the prebuilt binaries, not `lib/`
  etc. — not designed yet.
- **Where release binaries live long-term:** committed into repo history vs.
  attached to GitHub Releases — not decided, flagged for later.
- **Destination path:** proposed `D:\workshop\digib00age\public-repo` — confirm
  before creating.

## Not in scope for this pass

- Building an `.msi` installer.
- Touching the current dev repo in any way — it remains the working copy with full
  docs/history.
