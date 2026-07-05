# ComicVault — v2.5: Build Plan

> **Status: Item 1 built and fully tested 2026-07-04 — closed.** `docs/v2.5/`
> created this session (Code, per `ROADMAP.md`'s note that the working
> folder gets created alongside implementation rather than ahead of it —
> real v2.5 triage/scoping for the remaining holding-list items hasn't
> happened yet, this queue currently holds Item 1 only). OPDS / 3rd-party
> reader connection was scoped 2026-07-04 and **ruled out** (see
> `DECISIONS.md` and `ROADMAP.md`) — not built here, removed from the
> holding list. That same session surfaced two Flutter bugs (`BUGS.md`
> BUG-019, BUG-020) plus a reactivated one (BUG-008) — all three fixed and
> closed the same day (`archive/bugs-fixed-archive.md`, `ROADMAP.md`
> "Mobile app connectivity fix"). No open Flutter bugs remain.
>
> **How to use this document**
> This is the ordered build queue for v2.5. Paste into a Claude Code session
> alongside the referenced spec files. Items are marked ✅ when built and
> verified. Bugs and minor fixes are tracked separately in `BUGS.md` — don't
> add them here unless they block a build item.
>
> **Always reference items from other docs as "v2.5 Item N", never bare
> "Item N"** — see `meta/working-rules.md` "Version-qualified references."

---

## Item 1 — ComicTagger + ComicVine integration ✅

**Feature.** Full Editor "Search Online" (manual match against ComicVine,
two-step Select Series/Select Issue modal) and Processing Folder
Automation's new CT Auto-Tag stage (Convert Archives → **CT Auto-Tag** →
Convert Images), per `EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4 — both
scoped and decision-locked in four sessions 2026-07-03 (`DECISIONS.md`),
built and manually verified 2026-07-03/04.

**Built:**
- `backend/ct_bridge.py` (new) — bridge into ComicTagger's `comicapi`/
  `comictalker`/`comictaggerlib.issueidentifier` libraries. Series/issue
  search, single-issue full-detail fetch, `GenericMetadata` → ComicVault
  field-dict mapping, the CT Auto-Tag automation's identify pipeline.
- `backend/ct_autotag.py` + `backend/ct_autotag_log.py` (new) — the CT
  Auto-Tag stage's core callable and its audit log.
- `NeedsReview` XML tag added to `COMICINFO_TAGS`, with explicit
  clear-on-save wired into both `editor_basic.py` and `editor_full.py`.
- `backend/routers/editor_full.py` — three new Search Online endpoints
  (series search, issue list, confirm-match).
- `backend/routers/processing_folder.py` — amended to the 3-stage pipeline,
  new settings keys (`processing_folder_ct_autotag_enabled`,
  `processing_folder_ct_save_low_confidence`, `comicvine_api_key`), new
  Save & Test endpoint.
- Frontend: Full Editor gained a "Search Online" toolbar button, the
  two-step modal, and a red-border/"N Low Confidence" indicator on Column 1
  cards (reuses the existing favourited-card border technique). Admin
  gained the CT Auto-Tag toggle, Save on Low Confidence toggle, and
  ComicVine API key field with live Save & Test feedback.
- `requirements.txt` — `comictagger` pinned to a specific `develop`-branch
  commit (not PyPI's published release — see `DECISIONS.md`).

**Found and fixed during/after build (all same cluster, not separately
logged in `BUGS.md` since found and closed within this build):**
- `identify_file()` didn't fall back to filename parsing when an archive
  had no embedded `ComicInfo.xml` — a file with no tags short-circuited to
  `no_match` before ever calling ComicVine. Now falls back to
  `backend/rename_tool.py`'s `parse_comic_filename()`, defaulting the issue
  number to "1" for one-shots with no issue number in the filename
  (matches ComicTagger's own default-on "If no issue number, assume 1"
  option).
- Match thresholds lowered from CT's own CLI defaults (90/91) to 80,
  matching what Tez had already found worked well in his own standalone
  ComicTagger testing.
- `ct_autotag_file()` was mapping fields from `IssueIdentifier`'s bulk
  candidate-search metadata, which ComicVine's lighter multi-issue endpoint
  doesn't include credits in — Writer/Penciller/etc. were silently empty.
  Fixed with a follow-up single-issue fetch (the same full-detail endpoint
  Search Online's confirm step already used).
- `metadata_to_field_dict()` originally only mapped the subset of fields
  ComicVault's own editor UI exposes. Live testing surfaced this as real
  data loss against Tez's expectation of capturing everything CT/ComicVine
  supplies (even fields the editor doesn't display) — expanded to mirror
  `comicapi/tags/comicrack.py`'s own write mapping field-for-field (Month,
  Day, Notes, Inker, Colorist, Letterer, CoverArtist, Editor, Web, Volume,
  AlternateSeries/Number/Count, SeriesGroup, Characters, Teams, Locations).
  Genre/Format/AgeRating/BlackAndWhite remain deliberately excluded — not
  an "editor doesn't show it" exclusion like the rest, but a correctness
  one (enforced-dropdown validation integrity for the first three;
  a real `"on"` vs `"Yes"` semantic mismatch for the last).
- `Summary` was writing ComicVine's raw HTML markup as literal escaped text
  (`&lt;p&gt;&lt;em&gt;...`) instead of clean plain text — CT's own
  pipeline runs descriptions through `comictalker.talker_utils.cleanup_html()`
  before writing tags; this call was missing. Now applied, including
  correct conversion of embedded `<table>` credit lists to plain text.

**Follow-up work, same item, added 2026-07-04 after the first round of live
testing above:**
- New **Match Ratio Threshold** slider (10–100%, 1% steps) in Admin →
  Processing Folder Automation, right after "Save on Low Confidence" —
  `processing_folder_ct_match_threshold` (default 80, matching the
  previously-hardcoded value). `identify_file()` now reads this at
  call-time instead of hardcoding `series_match_search_thresh`/
  `series_match_identify_thresh`. Added once Tez had more real-world match
  data and wanted to tune it himself rather than rely on a fixed value.
- Found and fixed a misleading-results bug during the low-confidence test
  pass below: the Processing Folder Automation run-complete summary
  reported "N of M succeeded" by counting every non-`failed` status,
  which includes legitimate `no_match`/skipped-low-confidence outcomes
  (correctly `success=True` at the code level — the stage didn't error).
  A 5-file test run that tagged 4 files and correctly no-matched the 5th
  was reported as "5 of 5 succeeded", reading as if all 5 got tagged. Fixed
  with a CT-Auto-Tag-specific summary line breaking out tagged/no-match/
  skipped-low-confidence/failed counts explicitly
  (`frontend/js/processingTools.js` `pollPfStatus()`). The underlying
  `ct_autotag_log.md` audit log was accurate the whole time — this was a
  UI rollup-message bug only.
- Added a brief "Saved" toast (reusing the existing `showToast()` from
  `admin.js`) to `savePfSetting()` — applies to every auto-save control in
  this section, not just the new slider, since they all share this one
  helper. No control on this page previously gave any save confirmation
  except the ComicVine key's deliberate "Save & Test" exception.

**Low-confidence / real-world match-quality testing, completed 2026-07-04
(the item previously tracked as outstanding):** Tez ran a 5-file real-world
comparison test — his standalone ComicTagger 1.5.5 (30% match ratio, Save
on Low Confidence off) successfully tagged 1 of 5 files; the same 5 files
through ComicVault's CT Auto-Tag (actually run at the 80% default, since
the new threshold setting hadn't persisted yet at the time — a sequencing
issue, not a bug) tagged 4 of 5, correctly no-matching the 5th
(`Hard Bargain (2025).cbz`, a one-shot with no issue number in its
filename or on ComicVine). Investigated the discrepancy: all 4 of
ComicVault's successful matches came from filenames with clean, explicit,
unambiguous issue numbers — no evidence of risky guessing. Root cause of
CT's own lower hit-rate was **not conclusively identified** — leading
hypotheses (standalone CT possibly using ComicVine's shared rate-limited
key rather than a personal one; CT 1.5.5 being a genuinely different,
older codebase than the git-commit-pinned dev-branch version ComicVault
runs) were not confirmed with Tez before session close. Not treated as a
ComicVault defect — nothing in ComicVault's own matches was found to be
wrong — but worth revisiting if a similar gap recurs.

**Fully verified by Tez, live, against real files — item closed:** API key
Save & Test; a confident match pulling full/correct data (cross-checked
against an external source); the credits/HTML fixes; the scheduled
Auto-Tag stage run against real titles; the Match Ratio Threshold slider's
save/persist behaviour; and the low-confidence/real-world match-quality
pass above. `meta/roadmap.html`'s Now #1 card removed 2026-07-04 (item
complete). **Note, added later the same day:** OPDS was scoped next as
originally planned, but ruled out (see `DECISIONS.md`/`ROADMAP.md`) — the
Flutter mobile-bugs fixes took its place as Now #1 and are also now closed;
the remaining v2.5 holding-list items still need their own triage session.

---

## Item 2 — Sort by Filename Processing Tool ✅

**Feature.** New Processing Tool (`ADMIN_SPEC.md` §11.5), ported from the
standalone `create-folders-from-file.py` script — moves each CBZ/CBR file
directly inside a chosen folder into its own same-named subfolder. Arrived
as a build brief handed directly to Code (a pre-scoped spec, not sourced
from `INBOX.md`/`ROADMAP.md`'s holding list), built and manually tested
2026-07-05.

**Built:**
- `backend/filename_sort.py` (new) — pure `sort_by_filename(folder)`
  callable, no router/logging concerns.
- `backend/filename_sort_log.py` (new) — audit log, thin wrapper over
  `tool_logs.py`, same shape as `convert_log.py`.
- `backend/routers/filename_sort.py` (new) — `browse`/`drives` (shared
  `file_picker.py`), `run`/`status` mirroring `processing_folder.py`'s
  background-job + polling shape. Registered in `main.py`.
- Frontend: new "Sort by Filename" card in Admin → Processing Tools
  (`frontend/admin.html`) — folder picker, Run button, terse result line,
  expandable failure detail — and its wiring in
  `frontend/js/processingTools.js`.

**Found and fixed during build, before the manual test pass (see
`DECISIONS.md`):** the collision rule for "target folder already exists
with different content in it" was first implemented as a plain
exact-destination-path check, which a scratch-folder test (built
specifically to exercise the brief's named edge cases) showed let a file
move into a folder that already held unrelated content, silently. Fixed to
check whether the target folder holds any entry that isn't this file's own
basename-matching sibling before allowing the move — a same-basename
CBZ+CBR pair still passes through unchanged, only genuinely unrelated
folder content is rejected.

**Verified — core logic and router layer tested directly against a scratch
folder** (CBZ+CBR same-basename pair, an unrelated-content collision, a
non-CBZ/CBR file, and a missing-folder case, all before the live UI pass;
test artefacts and the log file they generated were deleted afterward, no
real files touched) **— then Tez confirmed "test passed"** via the live
Admin UI.

---

## Item 3 — Mobile ↔ Server Reading-State Sync ✅

**Feature.** Reading progress on the tablet's downloaded-comics mode now
persists back to the ComicVault DB, closing the gap `mobile-server-sync-scope.md`
(Cowork discovery session, 2026-07-05) and `ROADMAP.md`'s "v2.5 — holding
list" Item 2 flagged. Scoped and built same-session by Code, 2026-07-05.
Full technical plan (backend endpoints, conflict algorithm, Flutter service
design) written before build; see `docs/v2.5/progress.md` for the narrative
and the file-by-file detail.

**Gap found during scoping, not anticipated by the discovery-session doc:**
the Flutter app had no way to download a comic from the server for offline
reading at all — its "local file" mode only opened arbitrary CBZs copied
onto the device manually, with no link to a server `issue_id`. Confirmed
with Tez to build a proper download-for-offline feature as part of this
item rather than a filename-matching heuristic or deferring it — without
that link there was nothing concrete to sync for the scope doc's actual
scenario ("tablet with comics downloaded for a trip").

**Built:**
- `backend/routers/reader.py` — new `GET /api/issue/{id}/download`, serves
  the whole CBZ/CBR file (the only whole-archive endpoint in the API;
  everything else serves one page at a time).
- `backend/routers/sync.py` (new) — `POST /api/sync/progress`, batch
  reconciliation with last-write-wins by timestamp (confirmed with Tez over
  highest-page-wins, so a deliberate rewind/re-read can move progress
  backward). Registered in `main.py` alongside `progress.router`, same
  ungated tier. No `reading_progress` schema change — one canonical row per
  issue already fit the model; last-write-wins is a write-time comparison,
  not a schema concept.
- Flutter: `DownloadedIssue` model + `DownloadService` (download-for-offline,
  manifest in `SharedPreferences`, same pattern as `SettingsService`'s
  existing `recentLocalFiles`), a download/delete affordance on each issue
  row in `series_screen.dart`, and a "Downloaded" section in
  `library_screen.dart`'s offline view, kept separate from the existing
  ad-hoc "Recent files" list.
- Flutter: `SyncStore` (per-issue pending-progress record with a dirty flag)
  + `SyncService.syncNow()` (push dirty records, apply the server's
  conflict-resolution result). `LocalReaderScreen` extended with an optional
  `issueId`/`syncStore` — arbitrary local files (picked via file picker or
  "Open With") keep working exactly as before, only downloaded/issue_id-linked
  files get a timestamped sync record. New `LocalReaderArgs` route-argument
  type replaces the old bare `String filePath` for `/reader/local`.
- Flutter: manual "Sync now" button in `LibraryScreen`'s AppBar; a
  reconnect/foreground trigger piggybacked on the existing
  `_checkAndLoad()`/`checkConnection()` call, plus a new `RouteObserver`
  (`lib/route_observer.dart`) + `RouteAware.didPopNext()` so returning to
  the library after closing the reader also triggers a sync check —
  `LibraryScreen` sits at the app root and is only pushed once, so its own
  `initState()` never re-fires on back-navigation otherwise. No
  `connectivity_plus` dependency added — deliberately not needed.
  "Synced Xm ago"/"Never synced" label in the AppBar, "Not synced" marker on
  any downloaded issue with unpushed local progress.

**Correctness catch during the build, before any device testing:** Dart's
`DateTime.now()` is local time, and `.toIso8601String()` on a local
`DateTime` emits no "Z"/offset suffix at all — if the client ever captured a
sync timestamp that way, the server would misinterpret a local timestamp as
UTC, skewing every last-write-wins comparison by the tablet's UTC offset.
Fixed by always capturing sync-relevant timestamps via
`DateTime.now().toUtc()` on the Flutter side (`sync_store.dart`), with a
defensive naive-to-UTC fallback + explicit "Z" handling on the backend
(`sync.py`'s `_parse_client_ts()`) as a safety net, not a substitute.

**Verified:**
- Backend — both endpoints tested directly (function calls, no full app
  boot) against a scratch SQLite DB and scratch CBZ/CBR files: download's
  404s (unknown issue, `missing=True`, file absent from disk) and correct
  media type per extension; sync's `client_applied`/`server_kept`/`not_found`
  outcomes, an exact-timestamp tie resolving to the incoming write, and the
  actual DB row state after each (not just the response body). All scratch
  files deleted afterward, no real DB or library touched.
- Flutter — `flutter analyze` clean, a debug APK built successfully,
  `SyncStore`'s dirty-flag logic covered by 4 isolated unit tests (deleted
  after passing, matching this project's scratch-test convention rather
  than adding a permanent suite).
- **Tez's manual test, on the real Lenovo tablet against the real server:**
  downloaded an issue, read it with the server stopped, reconnected, and
  confirmed the sync pushed correctly — **signed off "passed."** One planned
  check (mark an issue further along from the web UI, then confirm
  `server_kept` doesn't get clobbered by reopening the stale downloaded
  copy) could not be run — see BUG-021 below, found during this pass, out
  of scope for this item.

**Found during the manual pass, logged not fixed here (`BUGS.md` BUG-021):**
neither the web UI nor a Windows desktop reader currently works as a way to
view/re-mark progress on a comic outside the Flutter app — the web UI has
no reader by design (`SPEC.md` §11, deep-links into Flutter instead), and
the standalone Windows reader EXE built in V1 was never rebuilt/carried
across into this V2 checkout. This blocked one verification step (the
`server_kept` reverse-conflict check) but doesn't affect this item's actual
correctness, since that exact code path (server timestamp newer than an
incoming stale client push) is covered by the backend's own scratch tests
above. Flagged as its own follow-up, not absorbed into this item.

**Also installed during this session's on-device pass, not a code
change:** installing a debug-signed build over a previously release-signed
one forced Android to uninstall first, wiping the app's local
`SharedPreferences` (server URL reset to default, recent-files list
cleared) — Tez reconfigured the server URL by hand afterward. Worth
knowing next time a differently-signed build goes onto the same device.

**One more bug caught after Tez's sign-off, while finishing doc close-out —
not covered by the passed manual test, since that test used a CBZ issue:**
`DownloadService.download()` always wrote the downloaded bytes to a
hardcoded `{issueId}.cbz` path regardless of the issue's actual format. A
CBR issue would have been saved under the wrong extension and then failed
opaquely at the page-count step (`LocalCbzService` only supports
`ZipDecoder`, per `SPEC.md`'s already-documented "Flutter local/offline mode
is a known, accepted gap" for CBR). Fixed: `ApiService.downloadIssue()` now
returns the real extension from the download response's `Content-Type`
(which the backend already sets correctly per file), and a failed
page-count read now deletes the partially-written file and raises a clear
"CBR issues can't be read offline yet" message instead of leaving an
unreadable file + manifest entry behind. Doesn't change the already-tested
CBZ path (content-type still resolves to `.cbz` there, byte-for-byte the
same behavior) — verified via `flutter analyze` (clean) and a fresh debug
build; not re-tested on-device since the tablet was disconnected by this
point, and the fix is scoped to a path Tez's sign-off didn't exercise.

---
