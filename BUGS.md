# ComicVault — Known Bugs Log

Tracks real defects found during development, separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration design).
Add new entries at the top. Mark fixed entries with the date and what was changed.

---

## FIXED

### BUG-004 — Tray app shows "Start ComicVault at login" ticked but server doesn't start on login; manual Start also fails

**Found:** 2026-06-19, first login after an OS restart following the prior session's
tray app changes (split Stop/Start, add Close, dark menu, login autostart toggle —
commit `6fc1840`). That session's testing was done but the OS restart + fresh login
happened afterward, outside the tested window.

**What happened:** Tray app started automatically at login as expected, and the
"Start ComicVault at login" menu item correctly showed as ticked. However the backend
server subprocess kept exiting immediately. Manually invoking Start from the tray menu
also failed — not a tray-app or autostart bug at all.

**Root cause — not in ComicVault's code.** `tray/reader_stdout.log` showed the actual
uvicorn error on every restart attempt:
`ERROR: [Errno 13] ... [winerror 10013] an attempt was made to access a socket in a
way forbidden by its access permissions` when binding `0.0.0.0:8000`.
`netsh interface ipv4 show excludedportrange protocol=tcp` confirmed port 8000 fell
inside a Windows TCP port-exclusion range (`7981–8080`) — `netstat` showed nothing
actually listening on 8000, i.e. Windows itself was refusing the bind, not a
competing process. `hns`/`vmms`(Hyper-V)/`WSL Service` were all running on this
machine; WSL2/Hyper-V's networking stack reserves blocks of TCP ports for NAT at
boot, and on this particular boot the reserved block happened to swallow port 8000.
This explains why manual Start also failed: it's an OS-level bind refusal, independent
of how the process is launched.

**Fix applied this session:** Restarted the `winnat` service (`net stop winnat` /
`net start winnat`) to force Windows to recompute its port-exclusion ranges. Confirmed
8000 was no longer excluded afterward, and the tray app's own health-check loop
(30s interval) picked this up on its next retry without any further action — log
shows `Reader server is up.` at 18:46:28, `netstat` confirmed `0.0.0.0:8000 LISTENING`,
and `GET /api/admin/stats` returned 200.

**Not a recurring code defect, but a recurring environmental risk:** any future
reboot can reproduce this if WSL2/Hyper-V's networking service happens to claim a
range overlapping port 8000 again. There is no permanent code-level fix being applied
in this session (would require either changing ComicVault's port to one outside
commonly-claimed ranges, or scripting a winnat restart into the startup sequence —
neither attempted here; flagging as a possible `ROADMAP.md` item rather than doing it
under this bug ticket).

**Status:** Resolved for this session by restarting `winnat`. Tray app and
`start_server.py` both behaved correctly throughout — no code changes were needed or
made.

---

### BUG-003 — Dead duplicate route: `GET /api/reading/continue` defined twice

**Found:** 2026-06-19, while building the Home Strips feature (`HOME_STRIPS_SPEC.md`)
and tracing how "Continue Reading" was resolved before folding it into the unified
`GET /api/home/strips` endpoint.

**Where:** The route is defined in both `backend/routers/progress.py` (line ~137) and
`backend/routers/library.py` (line ~455) — identical path, same query intent, slightly
different implementation. `main.py` registers `library.router` before `progress.router`,
so `library.py`'s version always wins; `progress.py`'s copy is unreachable dead code.

**Impact:** None currently — the live version (`library.py`) is correct and is what
the Flutter app and (until this session) the web frontend both called. Purely a
maintenance hazard: a future edit to the dead copy would silently do nothing.

**Not fixed in this session** — out of scope for the Home Strips build; flagging per
session convention rather than absorbing an unrelated cleanup into this session's scope.

---

## FIXED

### BUG-002 — Full Editor's Queue button stayed disabled for any file whose existing Genre/Format/AgeRating wasn't already enforced-valid

**Found:** 2026-06-18, during Tez's first manual test pass after the Full Editor build.

**Where:** `frontend/js/editor_full.js`, `updateValidityGate()` (now renamed
`updateActionButtonStates()`).

**What happened:** Queue (and Process All) were gated on the same Genre/Format/
AgeRating validity check as the Basic Editor's Save button. For any loaded file whose
current values didn't already pass (e.g. a genre like "Zombie" not in the enforced
list — the exact kind of file the pre-migration report exists to flag), Queue was
disabled immediately on focus, before Tez had a chance to fix anything. Reported as
"the Queue button is dead."

**Root cause:** `EDITOR_SPEC.md` Section 4.4 ("Existing-value mismatch behaviour") is
explicitly titled **Basic Editor only** — the hard validation gate was never meant to
apply to Full Editor. It got carried over by extension when building Full Editor's
form, which shares the same field markup/JS patterns as Basic Editor's popup.

**Fix:** Queue is now only gated on whether a file is focused; Process All only on
whether any files are loaded; Process Queue only on whether the queue is non-empty.
Validity enforcement for Full Editor happens server-side at process time only
(`backend/editor/validation.py`, already in place) — invalid fields are reported as
per-file errors without aborting the rest of the batch, matching the intended
workflow (queue first, fix fields, process after). The now-pointless
genre/format/agerating `change` listeners that only existed to re-run this check were
removed.

**Status:** Fixed in `editor_full.js`. Basic Editor's Save button is unaffected — its
gate is correctly scoped per Section 4.4.

### BUG-001 — Scanner skips thumbnail generation for unchanged-mtime files, even if the thumbnail file is missing

**Found:** 2026-06-18, during V2 migration setup.

**Where:** `backend/scanner.py`, incremental scan logic (~line 419), "skip if unchanged"
branch based on `date_modified` comparison against the DB.

**What happens:** The scanner only generates a thumbnail on the new-file or
updated-file branches. If a file's `date_modified` in the DB already matches its
on-disk mtime, the scanner skips it entirely — including thumbnail generation — even
if no thumbnail file actually exists on disk for that issue.

**How it surfaced:** V2 was set up from a copied database (`comicvault.db` copy) but
without copying `thumbnails/` (deliberately, since thumbnails are gitignored and
assumed regenerable). Every file's `date_modified` in the copied DB still matched disk
mtime, so the scan treated all 5,429 files as "skipped" and none of them got a
thumbnail — `thumbnails/` was left at 0 files despite a full scan reporting 0 errors.

**Why it matters beyond this one case:** This isn't specific to the migration. Any
future scenario where the DB is restored/copied without its thumbnails — backup
restore, disk recovery, fresh deploy from a DB dump — will hit the same silent gap.
The scan reports success (0 new, 0 updated, 0 errors) with no indication that cover
art is missing.

**Proper fix (applied 2026-06-18):** The skip-if-unchanged branch in `scan_single_file`
now checks whether the expected thumbnail file (`{issue.id}.jpg`) exists on disk before
skipping. If missing, it calls `_generate_thumbnail` and updates `cover_path` even
though the DB row's metadata is otherwise unchanged — the file still counts as
"skipped" in scan stats, it just no longer silently leaves a missing thumbnail behind.

Applied to **V2 only** (`comicvault_v2/backend/scanner.py`). V1's `scanner.py` is
unmodified — V1 is being kept as-is and is not being changed going forward.

**Workaround applied for V2's existing data (does not by itself fix the bug):** Cleared
`date_modified` for all rows in `comicvault_v2.db` only (V1 untouched), then re-ran the
scan so every file was treated as updated and thumbnails generated. This got V2's
existing copied DB into a correct state; the scanner fix above is what prevents the
same gap from recurring on any future DB copy/restore.

**Verification:** Deleted one issue's thumbnail file manually, ran a scan — confirmed
only that issue regenerated its thumbnail while the rest of the library (5,428 other
issues, unchanged, thumbnails present) was still skipped quickly. Full-library scan
timing was unaffected by the fix (~5 seconds for all 5,429 files, matching pre-fix
skip-path timing).

**Status:** Fixed in V2. V1 retains the original (unfixed) logic by design.
