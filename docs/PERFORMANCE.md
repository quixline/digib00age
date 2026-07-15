# ComicVault — Performance Diagnostics

Standing reference doc for performance investigation, parallel to `TESTING.md`
for correctness verification. First baseline established 2026-07-09 — before
this, the project had no benchmarks, no timing instrumentation anywhere in the
app, and no recorded hypothesis about where it's slow. This doc holds both the
dated baseline and the reusable methodology, so a future re-run isn't starting
from zero.

**Scope of this doc:** measured facts and root-cause hypotheses only. Nothing
in this baseline pass changed application behavior — no code was edited, no
fixes were applied. Deciding what (if anything) to fix, and when, is a
separate triage step against `BUGS.md`/`ROADMAP.md`/a future build queue.

**To re-run this baseline** (after a fix, or just to check for regressions),
use the `perf-diagnostics` skill (`.claude/skills/perf-diagnostics/`) rather
than re-deriving the methodology from §2 below — it packages the same
ground rules, the gotchas this first pass hit and fixed (the `localhost`
DNS artifact, the cold-idle-probe cache-reuse mistake), and the actual
working scripts as reusable starting points.

---

## 1. Baseline — 2026-07-09

Library scale at time of test: 5,427 issues, 2,080 series, 5,436 pre-generated
thumbnails. Server: the live tray-app instance (PID 5868 at test time),
already running and warm (no cold-restart tested this pass). DB
(`backend/comicvault_v2.db`) and thumbnails (`backend/thumbnails/`) live on
local/internal storage; the comic archives themselves live on `L:\Comic
Archives`, a ~2TB bus-powered USB 3.0 external HDD (draws power from the PC,
no wall adapter).

### Ranked findings

| # | Finding | Median / p95 | Query count | Root cause | Fixable-in-code? | User-visible impact |
|---|---|---|---|---|---|---|
| 1 | `GET /api/library` (All library load) | 3.9-4.1s median, p95 4.4s | **7,508 queries** | N+1: `i.genres` accessed per-issue via lazy relationship (no `joinedload`/`selectinload` anywhere in the codebase) across ~5,400 issues, plus one extra `ReadingProgress` query per unique series (2,080 series) | **Yes** — eager-load genres/credits, batch the progress query once | High — hit on nearly every navigation to All/Series/Singles; confirmed identical in-process, over HTTP, and in a real browser load |
| 2 | `GET /api/series/{id}` for a large series (2000 AD, 2,483 issues) | 2.5-2.7s | **4,969 queries** | N+1: one `ReadingProgress` query per issue in the series (no batching, unlike Folder View's `progress_map` pattern) **plus a second, separate N+1 not caught at the time** — the series-wide genre aggregation also lazy-loaded `Issue.genres` per issue (the query count only adds up as two per-issue queries, not one — found and fixed in the Phase 2 re-baseline below) | **Yes** — same batching pattern Folder View already uses, plus `selectinload` for genres | High for large series specifically — confirmed as a real multi-second wait in an actual browser click-through. A typical 25-issue series (Postal) takes 53 queries / 27-40ms — ~94x fewer queries for ~99x fewer issues, i.e. clean linear N+1 scaling |
| 3 | Cover images never honor conditional revalidation | ~~n/a (cumulative cost)~~ **Fixed 2026-07-13** | n/a | No `Cache-Control` header set anywhere (`backend/routers/reader.py`); confirmed live that a byte-exact `If-None-Match` still returns 200 with the full body, 0/15 sampled covers ever got a 304 — root cause: Starlette's `FileResponse` computes an ETag automatically but has no logic to check it against an incoming `If-None-Match`, so a 304 was structurally impossible before this fix | **Done** — see Phase 4 re-baseline below | Medium-high cumulative — every "All library" grid view re-transfers all ~80MB of visible thumbnails from scratch, every visit, forever, even though nothing changed |
| 4 | No page cache in the reader | ~~22.7-22.8ms per page~~ **Fixed 2026-07-13** | n/a | `_sorted_pages()` re-opens the archive and re-enumerates the **entire** namelist on every single `/api/page/{id}/{n}` call; confirmed a never-before-read page costs the same (22.8ms) as re-flipping to an already-viewed page (22.7ms) — genuinely zero caching benefit | **Done** — see Phase 3 re-baseline below | Currently small in absolute terms for typical-sized issues, but scales directly with page-image size/count — will be much more noticeable on the library's larger/higher-res issues |
| 5 | `archive_namelist()` cold-open cost | ~~median 42.5ms cold vs 0.6ms warm~~ **Fixed 2026-07-13** | n/a | Every archive open re-parses the ZIP central directory from scratch (median 42.5ms), while raw sequential disk throughput for the same files is healthy (91.4MB/s median) — this is app-level per-call overhead, not disk speed | **Done** — same fix as #4 (avoid re-opening per request) | Compounds directly into #4; this is the specific mechanism behind it |
| 6 | Full Editor page-preview (`GET /api/editor/full/files/{id}/page/{n}`) | ~~Not measured this pass~~ **Measured and partially fixed 2026-07-13** | n/a | Confirmed live (1,220-page compendium): 25-330ms/page, up to 3.7MB base64 JSON, zero improvement on repeat requests — same root cause as #4/#5 (ZIP central directory re-parsed every call), independently, in `editor_full.py`. Full-resolution image, base64-encoded into JSON, no downscaling — that part deliberately left unfixed (see Phase 5 re-baseline) | **Partially done** — page-list N+1 fixed; full-res/base64 encoding is a separate, more invasive change not done this pass | Confirmed real and significant on large issues — see Phase 5 re-baseline below |
| 7 | Scanner duration | 5-14s across 18 historical runs (24/06-09/07) | n/a | All 18 logged runs were near-no-op incremental scans (`new_files_log.md` shows only 2 new files logged across that whole span) — this is the "walk ~5,500 files, find nothing changed" floor, **not** a representative "process N new files" number. Code shows up to 3 archive-opens per new/changed file | Unknown — untested at real scale this pass | Unmeasured for the case that matters (a real batch of new files); flagged for a dedicated instrumented run with explicit sign-off (writes thumbnails/DB rows) |
| 8 | USB raw sequential throughput | 77-95MB/s median across two independent samples (Phase A1, Phase D1) | n/a | Healthy, consistent USB 3.0 HDD performance — no evidence of a systemic problem | n/a — not a code issue | Low — the drive itself is not the bottleneck for typical reads |
| 9 | Post-idle drive throughput (cold-idle probe) | 1 of 2 valid samples showed ~39MB/s (vs ~84-88MB/s expected for that file size); the other showed 65MB/s (normal range) | n/a | Inconclusive — see §3. Possibly a link-power-state effect, possibly just that specific file's disk location; single differently-sized samples can't separate the two | n/a | Unresolved — see follow-up note in §3 |
| 10 | `localhost` vs `127.0.0.1` on this host | ~2000-2700ms added to **every** request via `localhost`; eliminated entirely via `127.0.0.1` | n/a | Windows resolves `localhost` to IPv6 (`::1`) first; the server binds IPv4 only; the refused IPv6 attempt takes ~2000ms before falling back to IPv4 (confirmed via raw socket test) | No — not a ComicVault issue, a Windows network-stack artifact on this host | None for real browser users (Chrome/Edge/Firefox use Happy Eyeballs and race IPv4/IPv6, so they're not affected) — but any script, curl command, or non-browser tool that hits literal `localhost:9424` on this machine eats a consistent ~2s tax per request. **Use `127.0.0.1` for any future diagnostic scripts on this host.** |
| 11 | Basic Editor popup load (`GET /api/editor/{issue_id}`, `/issue/{id}`'s "Edit XML" button) opened the same archive **3 separate times** per request | ~~3 opens; e.g. 954MB compendium 14.2-15.0ms warm~~ **Fixed 2026-07-15** | n/a | Same redundant-reopen pattern as findings #4/#5/#6 (`find_xml_in_archive` + `extract_xml_from_archive` + a separate `get_archive_page_count`, each re-parsing the ZIP central directory) — just never applied to `backend/editor/archive_io.py`, the one archive-read path those earlier fixes missed | **Done** — see re-baseline below | Low-medium — the *dominant* real-world cost is actually the first cold disk touch on a rarely-opened archive (211-313ms observed — USB HDD seek latency, not fixable in code, matches #8/#9), which this fix doesn't touch. The guaranteed win is the smaller residual overhead once warm: ~1ms on a typical issue, ~9-10ms on a large compendium |

### Re-baselines (fixes applied against this baseline)

- **Finding #1, Phase 1 fix — 2026-07-12.** `GET /api/library`'s two N+1s
  fixed (`selectinload(Issue.genres)` + a single batched `ReadingProgress`
  query instead of one per series) — see `v2.6/comicvault-changes-v2.6.md`
  Item 2 Phase 1 and `v2.6/progress.md` for the full change. In-process
  query-count check: **7,508 → 13 queries, 3.9-4.1s → ~0.63-0.67s median**.
  Manually verified live after a reader-server restart: All Library loads
  visibly faster, no console errors. The remaining ~0.63s is Python-level
  aggregation over ~5,400 issues (grouping, sorting, set comprehensions),
  not DB round-trips — not re-measured at the query level separately since
  it's no longer the dominant cost this finding was flagging.
- **Finding #2, Phase 2 fix — 2026-07-12.** `GET /api/series/{id}`'s
  per-issue `ReadingProgress` N+1 fixed with a batched `progress_map`
  (Folder View's existing pattern); also fixed a second N+1 the original
  pass didn't name as root cause — series-wide genre aggregation lazy-
  loading `Issue.genres` per issue — with `selectinload`. See
  `v2.6/comicvault-changes-v2.6.md` Item 2 Phase 2 and `v2.6/progress.md`.
  In-process query-count check: 2000 AD (2,483 issues) **4,969 → 9
  queries, 2.5-2.7s → ~0.33-0.42s median**; Postal (25 issues) 53 → 5
  queries. Manually verified live after a reader-server restart: 2000 AD
  loads fast, no console errors.
- **Findings #4/#5, Phase 3 fix — 2026-07-13.** `_sorted_pages()`
  (`backend/routers/reader.py`) now caches the sorted page list per archive
  path, keyed on `(mtime, size)` so a rescan/replace invalidates
  automatically. See `v2.6/comicvault-changes-v2.6.md` Item 2 Phase 3 and
  `v2.6/progress.md`. In-process check (issue 11, Four Horsemen #1, same
  file as the original Phase D2): cold parse 5,483ms this run (this
  specific file was genuinely cold-disk, consistent with finding #9's
  known cold-idle drive variance, not a regression) → warm cache-hit
  0.08-0.13ms. Manually verified live: flipping through several pages of a
  comic, no console errors.
- **Finding #3, Phase 4 fix — 2026-07-13.** `GET /api/cover/{id}`
  (`backend/routers/reader.py`) now sends `Cache-Control: public,
  max-age=86400` + an `ETag`, and returns a real `304` on a matching
  `If-None-Match` — root cause was that Starlette's `FileResponse` computes
  an ETag but never checks it against the request, so a 304 was
  structurally impossible before. See `v2.6/comicvault-changes-v2.6.md`
  Item 2 Phase 4 and `v2.6/progress.md`. Verified via `TestClient`
  in-process and direct HTTP against the live already-restarted server:
  fresh request 200 with headers, matching `If-None-Match` → 304 empty
  body. Manually verified live: All Library loads faster, no console
  errors.
- **Finding #6, Phase 5 fix — 2026-07-13.** Measured live for the first
  time (Tez temporarily disabled admin password protection for this).
  1,220-page compendium: 25-330ms per page, up to 3.7MB base64 JSON,
  **zero improvement on repeat requests** (page 0: 68ms→65ms, page 1:
  30ms→25ms) — confirmed the same root cause as findings #4/#5, just
  living independently in `backend/routers/editor_full.py` (doesn't share
  `reader.py`'s Phase 3 cache). **Scope call:** fixed only the page-list
  N+1 (`_cached_image_list()`, same `(mtime, size)` pattern as Phase 3) —
  the full-res/base64 image encoding itself was deliberately left unfixed,
  a separate, more invasive change with editor-UX tradeoffs. Verified via
  direct HTTP against the live server after a restart: repeat requests now
  show a real cache benefit (page 0: 153ms→53ms, page 1: 91ms→16ms)
  instead of the pre-fix flat/no-improvement pattern. See
  `v2.6/comicvault-changes-v2.6.md` Item 2 Phase 5 and `v2.6/progress.md`.
  **v2.6 Item 2 (Performance fixes) is now complete** — all 5 phases from
  this baseline built and verified.
- **Finding #11, fix — 2026-07-15.** Investigated separately from the
  original 2026-07-09 baseline pass, in response to a question about Edit
  XML popup-open latency — the Basic Editor's `GET /api/editor/{issue_id}`
  was never measured before. Found `_read_original_xml()`
  (`find_xml_in_archive` + `extract_xml_from_archive`) plus a separate
  `get_archive_page_count()` call opened the same archive 3 times per
  request. Added `read_xml_and_page_count()`
  (`backend/editor/archive_io.py`) consolidating all 3 into a single
  archive open; `GET`/`POST /api/editor/{issue_id}`
  (`backend/routers/editor_basic.py`) both updated to use it. Also
  parallelized the popup's one-time-per-page-load `GET /api/editor/formats`
  + `GET /api/editor/genres` fetches (`frontend/js/editor_basic.js`) via
  `Promise.all` instead of sequential awaits.
  In-process timing (warm-cache, isolating the redundant-open overhead from
  disk-seek cost): 2000 AD #1 (22MB, 32 pages) 0.9-1.0ms (3 opens) → 0.4ms
  (1 open); Black Science Compendium (954MB, 1024 pages) 14.2-15.0ms
  (3 opens) → 5.2-5.9ms (1 open). **Caveat:** the dominant real-world cost
  is the first cold disk touch on a rarely-opened archive (211-313ms
  observed) — inherent USB HDD seek latency, not fixable in code, consistent
  with findings #8/#9. This fix doesn't address that; it only removes the
  redundant 2nd/3rd opens, already cheap once the OS cache warmed from the
  first open. Verified: in-process timing above; a scratch-copy save-path
  round-trip (never the real file) confirmed unchanged save behaviour; the
  real comparison file confirmed untouched. Manually verified live after a
  server restart: Tez confirmed the popup opens and saves correctly, and
  that the felt experience matches the diagnosis — the first archive opened
  in a session has a noticeable, audible lag (drive spin-up), subsequent
  archives open the editor immediately.

### What's *not* a problem

- Raw USB drive throughput is healthy and consistent (75-95MB/s across ~130
  sampled files of varying sizes, cold and warm) — the drive itself is not
  inherently slow.
- DB and thumbnails already live on local/internal storage, not the USB drive
  — good existing separation that limits how much the drive's characteristics
  can affect the app.
- Thumbnail coverage is ~100% (5,436 files for 5,427 issues) — the slow
  live-extraction cover fallback path is essentially never exercised.
- Folder View's core listing query (3 queries, ~270-320ms) already batches its
  `ReadingProgress` lookup — a pattern the other N+1 endpoints should copy.
- Small/typical-series page loads (`/api/series/4616`, `/api/search`,
  `/api/reading/continue`) are all fast (under 40ms of real work).

---

## 2. Methodology (for re-running this baseline later)

All measurements were taken with **zero application code changes** — every
script was a standalone, read-only tool run from outside the repo (this
project's scratchpad convention, matching `TESTING.md`'s existing "throwaway
scripts outside the repo" pattern), driven against the app's own DB/modules or
the already-running live server. No second server was started. Repeat this
shape for a future comparison:

1. **Raw I/O baseline** — sample real `file_path` values from the DB
   (read-only `sqlite3` connection), time full sequential reads of ~15-40
   files spanning sizes/folders. Compare cold (first touch) vs warm (immediate
   re-read). Report MB/s, not just ms — file size varies too much across this
   library for raw elapsed time to be comparable file-to-file.
2. **In-process query-count + timing** — import the app's own router modules
   (`backend.routers.library`, `backend.routers.home`, etc.) and call the
   route functions directly (they're plain Python functions under FastAPI's
   decorators). Attach a SQLAlchemy `before_cursor_execute` event listener to
   count queries without needing `echo=True`. This isolates pure
   algorithm/query cost from any I/O or network confound, since the DB is
   local.
3. **HTTP-level timing** — hit the live server directly with `urllib.request`
   (stdlib, no extra dependency), 8+ trials per endpoint, report median + p95.
   **Use `127.0.0.1`, not `localhost`** — see finding #10 above.
4. **Archive/page-serving isolation** — time `archive_formats.archive_namelist()`
   and `archive_read_bytes()` directly (cold vs warm), and compare against the
   raw-read baseline for the *same files* to separate disk speed from
   app-level archive-reopen overhead. Follow with an HTTP-level comparison of
   never-before-read pages vs. re-flipping to an already-read page.
5. **Cold-idle drive probe** — pick a target file, let the drive sit
   genuinely untouched for 10-15 minutes (verify no other phase/process
   touches `L:` during the window), then read a **fresh, never-touched** file
   immediately after. **Do not re-read the same file** — this session's first
   attempt did that and got a 1,718MB/s "warm" read, proving Windows' RAM file
   cache survives 12+ minutes regardless of drive power state; that tests
   cache persistence, not drive latency. Use different file-size classes
   across repeats if possible, to separate a genuine idle effect from
   per-file disk-location variance (this session did not fully control for
   that — see §3).
6. **Cover/thumbnail grid load** — fetch every visible cover sequentially,
   time it, and separately verify conditional-GET (`If-None-Match`) behavior
   on a sample to check whether 304s are actually being honored.
7. **Scanner** — check `logs/last_scan_log.md` (and cross-reference
   `new_files_log.md`/`changed_files_log.md`) before running a fresh scan.
   Historical durations are only representative if those logs show a
   meaningful batch was actually processed, not a no-op incremental walk.
8. **Real browser waterfall** — last, as a sanity check. Use
   `performance.getEntriesByType('resource')` in the actual running app (not
   a synthetic script) for the heaviest realistic views. Note: Chrome's
   native `loading="lazy"` did not fire during automated navigation in this
   session without forcing `img.loading = 'eager'` via JS first — a headless/
   automation quirk, not a real-user behavior, but worth knowing if re-running
   this via browser automation.

---

## 3. Open follow-ups (not resolved this pass)

- **Cold-idle drive effect is inconclusive.** Two valid post-idle samples
  (after fixing the cache-reuse mistake above): a 376MB file read at 39.3MB/s
  (roughly half the ~84-88MB/s expected for that size) and a 10.68MB file at
  65.3MB/s (normal range). Different file sizes make these hard to compare
  directly. USB power-management inspection (read-only, via `powercfg` and
  WMI `MSPower_DeviceEnable`) found: whole-disk idle power-off is disabled for
  this drive specifically, but the global Windows "USB selective suspend"
  policy is still enabled and could still apply link-level power states at
  the port/hub level. A definitive answer would need same-size files repeated
  across several genuine idle windows — each rep costs ~12-15 real minutes,
  so this was capped at 2 valid samples this pass.
- **Full Editor page-preview** never measured directly (admin-auth-gated;
  this session deliberately avoided scripting a login with the real admin
  password). Flagged as the highest-risk unmeasured area based on code
  inspection alone (full-res, base64-in-JSON, no caching).
- **Scanner at real scale** never measured — all 18 historical log entries
  were near-no-op incremental runs. A representative "process N new files"
  number would require either a fresh instrumented scan (writes thumbnails/DB
  rows, needs explicit sign-off) or waiting for a natural batch of new files.
- **No cold-server-restart baseline** — this pass measured against the
  already-warm, already-running tray-app server by design (see `CLAUDE.md`
  session request). `main.py`'s `_warmup_db()` exists specifically because a
  prior cold-start slowness was noticed once (for `/api/home/strips`) — true
  first-request-after-boot timing for the endpoints in this baseline is still
  unmeasured.
- **Full Editor's `GET /editor/full/files/{file_id}/xml`
  (`backend/routers/editor_full.py`) has the same redundant-3-archive-opens
  pattern finding #11 just fixed in the Basic Editor** —
  `find_xml_in_archive` + `extract_xml_from_archive` + `get_archive_page_count`
  called separately, same as the pre-fix Basic Editor. Spotted while fixing
  #11 but out of scope for that session (Tez's ask was specifically about
  the Basic Editor's Edit XML button) — flagged here as a straightforward
  follow-up using the same `read_xml_and_page_count()` helper already built.

---

## 4. Raw data appendix

<details>
<summary>Phase A1 — raw I/O baseline (40-file stride sample)</summary>

Cold: median 484.6ms / 77.4 MB/s. Warm: median 442.2ms / 85.0 MB/s. Total 3,231MB
read across 40 files (10MB-520MB range). No anomalous stalls found — an initial
apparent "outlier" (6.2s max) turned out to simply be the largest sampled file
(518.6MB) reading at a normal 84.2MB/s; size, not latency, explained every
value above 1 second.

</details>

<details>
<summary>Phase A2 — cold-idle probe (raw log)</summary>

```
2026-07-09T16:54:08  id=233   size=12.12MB   elapsed=444.4ms   27.3MB/s   (rep 0, no preceding idle)
2026-07-09T17:06:45  id=233   size=12.12MB   elapsed=7.1ms     1718.3MB/s (rep 1, SAME file after 12min — INVALID, OS cache hit)
2026-07-09T17:20:01  id=3063  size=376.58MB  elapsed=9591.1ms  39.3MB/s   (rep 2, fresh file after genuine 12min idle)
2026-07-09T17:32:36  id=4064  size=10.68MB   elapsed=163.7ms   65.3MB/s   (rep 3, fresh file after genuine 12min idle)
```

</details>

<details>
<summary>Phase B — in-process query counts (3 runs, stable)</summary>

| Endpoint | Time (ms, run1/run2/run3) | Queries |
|---|---|---|
| `/api/library` (unfiltered) | 3969 / 3903 / 4140 | 7,508 |
| `/api/series/79` (2000 AD) | 2654 / 2720 / 2580 | 4,969 |
| `/api/series/4616` (Postal) | 25.1 / 27.6 / 28.8 | 53 |
| `/api/issue/79` | 200.5 / 237.5 / 215.6 | 15 |
| `/api/home/strips` | 371.3 / 318.4 / 374.8 | 7 |
| `/api/library/tab/3/folder` | 317.8 / 277.7 / 279.0 | 3 |
| `/api/search?q=batman` | 36.1 / 32.3 / 32.6 | 8 |
| `/api/reading/continue` | 1.1 / 0.6 / 0.6 | 1 |

</details>

<details>
<summary>Phase C — HTTP timing (127.0.0.1, 8 trials each)</summary>

| Endpoint | Median | p95 | Bytes |
|---|---|---|---|
| Library — All | 3932.2ms | 4358.0ms | 2,575,925 |
| Series — 2000 AD | 2544.1ms | 2690.6ms | 2,638,745 |
| Series — Postal | 39.4ms | 70.3ms | 27,152 |
| Issue detail (79) | 227.1ms | 268.6ms | 1,728 |
| Home strips | 377.6ms | 396.5ms | 11,578 |
| Folder View tab 3 | 270.7ms | 355.1ms | 4,277 |
| Search — batman | 34.2ms | 41.3ms | 1,652 |
| Continue reading | 16.9ms | 17.6ms | 2 |

(First run used bare `localhost` and showed a uniform +2000-2700ms floor on
every endpoint, including the sub-millisecond `/api/reading/continue` query —
see finding #10. Re-run against `127.0.0.1` above is the corrected data.)

</details>

<details>
<summary>Phase D — page-serving isolation</summary>

D1 (15-file fresh sample, function-level): cold `archive_namelist()` median
42.5ms, warm 0.6ms. Cold `archive_read_bytes()` (single entry) median 12.9ms,
warm 3.0ms. Raw sequential whole-file read for the same files: median
91.4MB/s — confirms the drive itself is fast; the 42.5ms cold-open cost is
central-directory-parse overhead, not throughput.

D2 (HTTP, issue id=11, 25 pages/4.7MB): forward through 10 never-read pages,
median 22.8ms. Re-flip to an already-read page 3 times, median 22.7ms.
Statistically indistinguishable — confirms zero page-cache benefit end to end.

</details>

<details>
<summary>Phase E — cover/thumbnail grid</summary>

Sequential fetch of all 2,080 series covers: 28.6s total, 79.6MB, median
16.1ms/image, p95 25.1ms, max 52.0ms. Conditional-GET check on 15 covers:
0/15 honored a 304 on a byte-exact `If-None-Match`; no `Cache-Control` header
present on any response.

</details>

<details>
<summary>Phase F — scanner historical data</summary>

`logs/last_scan_log.md`: 18 entries, 24/06/2026 through 09/07/2026, durations
5-14 seconds throughout. `logs/new_files_log.md` shows only 2 new files ever
logged across that span; `logs/changed_files_log.md` shows ~11
metadata-updated entries + 2 archive-changed entries. These are near-no-op
incremental scans, not a representative "process N new files" measurement.

</details>

<details>
<summary>Phase G — real browser (Chrome via automation, 127.0.0.1)</summary>

Home page load: DOMContentLoaded 240.7ms, load event 387.4ms,
`/api/home/strips` 501ms. All Library view: `/api/library` 4080ms (matches
Phase B/C); 50 cover images (native `loading="lazy"` did not fire under
automation without forcing `eager` — see §2 note), 1.9MB total, median 115ms/
image under Chrome's own connection-concurrency queuing. Series 79 (2000 AD)
page: `/api/series/79` 2675ms — a real, user-visible multi-second wait
clicking into the library's largest series. Folder View tab 3 root:
`/api/library/tab/3/folder` 278ms.

</details>

<details>
<summary>USB power-management inspection (read-only)</summary>

`powercfg /query SCHEME_CURRENT SUB_DISK`: "Turn off hard disk after" = Never
on AC power, 10 minutes on DC/battery. `powercfg` USB selective suspend
setting: Enabled on both AC and DC. WMI
`Get-CimInstance -Namespace root\wmi -ClassName MSPower_DeviceEnable`
filtered to the Toshiba drive's two USB instance IDs: `Enable=False` for
both (per-device "allow the computer to turn off this device" is unchecked
for this drive specifically). Net read: per-device full power-off is
disabled, but the global USB link-power-management policy still applies at
the port/hub level — plausible but not proven contributor to finding #9.

</details>
