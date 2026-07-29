# digib00age — Performance Diagnostics

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

| #   | Finding                                                                                                                                            | Median / p95                                                                                                            | Query count       | Root cause                                                                                                                                                                                                                                                                                                                                                                                     | Fixable-in-code?                                                                                                          | User-visible impact                                                                                                                                                                                                                                                                                                                               |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `GET /api/library` (All library load)                                                                                                              | 3.9-4.1s median, p95 4.4s                                                                                               | **7,508 queries** | N+1: `i.genres` accessed per-issue via lazy relationship (no `joinedload`/`selectinload` anywhere in the codebase) across ~5,400 issues, plus one extra `ReadingProgress` query per unique series (2,080 series)                                                                                                                                                                               | **Yes** — eager-load genres/credits, batch the progress query once                                                        | High — hit on nearly every navigation to All/Series/Singles; confirmed identical in-process, over HTTP, and in a real browser load                                                                                                                                                                                                                |
| 2   | `GET /api/series/{id}` for a large series (2000 AD, 2,483 issues)                                                                                  | 2.5-2.7s                                                                                                                | **4,969 queries** | N+1: one `ReadingProgress` query per issue in the series (no batching, unlike Folder View's `progress_map` pattern) **plus a second, separate N+1 not caught at the time** — the series-wide genre aggregation also lazy-loaded `Issue.genres` per issue (the query count only adds up as two per-issue queries, not one — found and fixed in the Phase 2 re-baseline below)                   | **Yes** — same batching pattern Folder View already uses, plus `selectinload` for genres                                  | High for large series specifically — confirmed as a real multi-second wait in an actual browser click-through. A typical 25-issue series (Postal) takes 53 queries / 27-40ms — ~94x fewer queries for ~99x fewer issues, i.e. clean linear N+1 scaling                                                                                            |
| 3   | Cover images never honor conditional revalidation                                                                                                  | ~~n/a (cumulative cost)~~ **Fixed 2026-07-13**                                                                          | n/a               | No `Cache-Control` header set anywhere (`backend/routers/reader.py`); confirmed live that a byte-exact `If-None-Match` still returns 200 with the full body, 0/15 sampled covers ever got a 304 — root cause: Starlette's `FileResponse` computes an ETag automatically but has no logic to check it against an incoming `If-None-Match`, so a 304 was structurally impossible before this fix | **Done** — see Phase 4 re-baseline below                                                                                  | Medium-high cumulative — every "All library" grid view re-transfers all ~80MB of visible thumbnails from scratch, every visit, forever, even though nothing changed                                                                                                                                                                               |
| 4   | No page cache in the reader                                                                                                                        | ~~22.7-22.8ms per page~~ **Fixed 2026-07-13**                                                                           | n/a               | `_sorted_pages()` re-opens the archive and re-enumerates the **entire** namelist on every single `/api/page/{id}/{n}` call; confirmed a never-before-read page costs the same (22.8ms) as re-flipping to an already-viewed page (22.7ms) — genuinely zero caching benefit                                                                                                                      | **Done** — see Phase 3 re-baseline below                                                                                  | Currently small in absolute terms for typical-sized issues, but scales directly with page-image size/count — will be much more noticeable on the library's larger/higher-res issues                                                                                                                                                               |
| 5   | `archive_namelist()` cold-open cost                                                                                                                | ~~median 42.5ms cold vs 0.6ms warm~~ **Fixed 2026-07-13**                                                               | n/a               | Every archive open re-parses the ZIP central directory from scratch (median 42.5ms), while raw sequential disk throughput for the same files is healthy (91.4MB/s median) — this is app-level per-call overhead, not disk speed                                                                                                                                                                | **Done** — same fix as #4 (avoid re-opening per request)                                                                  | Compounds directly into #4; this is the specific mechanism behind it                                                                                                                                                                                                                                                                              |
| 6   | Full Editor page-preview (`GET /api/editor/full/files/{id}/page/{n}`)                                                                              | ~~Not measured this pass~~ **Measured and partially fixed 2026-07-13**                                                  | n/a               | Confirmed live (1,220-page compendium): 25-330ms/page, up to 3.7MB base64 JSON, zero improvement on repeat requests — same root cause as #4/#5 (ZIP central directory re-parsed every call), independently, in `editor_full.py`. Full-resolution image, base64-encoded into JSON, no downscaling — that part deliberately left unfixed (see Phase 5 re-baseline)                               | **Partially done** — page-list N+1 fixed; full-res/base64 encoding is a separate, more invasive change not done this pass | Confirmed real and significant on large issues — see Phase 5 re-baseline below                                                                                                                                                                                                                                                                    |
| 7   | Scanner duration                                                                                                                                   | 5-14s across 18 historical runs (24/06-09/07)                                                                           | n/a               | All 18 logged runs were near-no-op incremental scans (`new_files_log.md` shows only 2 new files logged across that whole span) — this is the "walk ~5,500 files, find nothing changed" floor, **not** a representative "process N new files" number. Code shows up to 3 archive-opens per new/changed file                                                                                     | Unknown — untested at real scale this pass                                                                                | Unmeasured for the case that matters (a real batch of new files); flagged for a dedicated instrumented run with explicit sign-off (writes thumbnails/DB rows)                                                                                                                                                                                     |
| 8   | USB raw sequential throughput                                                                                                                      | 77-95MB/s median across two independent samples (Phase A1, Phase D1)                                                    | n/a               | Healthy, consistent USB 3.0 HDD performance — no evidence of a systemic problem                                                                                                                                                                                                                                                                                                                | n/a — not a code issue                                                                                                    | Low — the drive itself is not the bottleneck for typical reads                                                                                                                                                                                                                                                                                    |
| 9   | Post-idle drive throughput (cold-idle probe)                                                                                                       | 1 of 2 valid samples showed ~39MB/s (vs ~84-88MB/s expected for that file size); the other showed 65MB/s (normal range) | n/a               | Inconclusive — see §3. Possibly a link-power-state effect, possibly just that specific file's disk location; single differently-sized samples can't separate the two                                                                                                                                                                                                                           | n/a                                                                                                                       | Unresolved — see follow-up note in §3                                                                                                                                                                                                                                                                                                             |
| 10  | `localhost` vs `127.0.0.1` on this host                                                                                                            | ~2000-2700ms added to **every** request via `localhost`; eliminated entirely via `127.0.0.1`                            | n/a               | Windows resolves `localhost` to IPv6 (`::1`) first; the server binds IPv4 only; the refused IPv6 attempt takes ~2000ms before falling back to IPv4 (confirmed via raw socket test)                                                                                                                                                                                                             | No — not a ComicVault issue, a Windows network-stack artifact on this host                                                | None for real browser users (Chrome/Edge/Firefox use Happy Eyeballs and race IPv4/IPv6, so they're not affected) — but any script, curl command, or non-browser tool that hits literal `localhost:9424` on this machine eats a consistent ~2s tax per request. **Use `127.0.0.1` for any future diagnostic scripts on this host.**                |
| 11  | Basic Editor popup load (`GET /api/editor/{issue_id}`, `/issue/{id}`'s "Edit XML" button) opened the same archive **3 separate times** per request | ~~3 opens; e.g. 954MB compendium 14.2-15.0ms warm~~ **Fixed 2026-07-15**                                                | n/a               | Same redundant-reopen pattern as findings #4/#5/#6 (`find_xml_in_archive` + `extract_xml_from_archive` + a separate `get_archive_page_count`, each re-parsing the ZIP central directory) — just never applied to `backend/editor/archive_io.py`, the one archive-read path those earlier fixes missed                                                                                          | **Done** — see re-baseline below                                                                                          | Low-medium — the *dominant* real-world cost is actually the first cold disk touch on a rarely-opened archive (211-313ms observed — USB HDD seek latency, not fixable in code, matches #8/#9), which this fix doesn't touch. The guaranteed win is the smaller residual overhead once warm: ~1ms on a typical issue, ~9-10ms on a large compendium |

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

## 1B. Baseline — 2026-07-18 (post-2000 AD move, post-rebuild)

*Numbering note: further baselines append as 1B, 1C, … so that references to
§2 (Methodology), §3 (Open follow-ups) and §4 (Raw data) stay stable across
re-runs.*

**Why this run:** the 2000 AD series was moved on disk and ~2,500 new issues
added — neither covered by the 2026-07-09 baseline. Two of that baseline's
open follow-ups (scanner at real scale, cold-server-restart) were also closed
here.

**Library scale:** 5,452 issues / 2,102 series / **562.5 GB** across 5,452
archives (was 5,427 / 2,080). Thumbnails 7,968 on disk — 5,452 live,
**2,516 orphaned** (BUG-026). Same hardware and paths as 2026-07-09.

**Important context — the DB was cleared and rebuilt from scratch mid-session.**
The series move updated the files but not the DB rows pointing at them
(BUG-025), leaving 2,484 dead `file_path`s; a plain rescan would have produced
duplicates rather than repairing them, because `scan_single_file()` identifies
rows by exact path only. So every issue ID in this baseline differs from
2026-07-09's, and endpoint targets were re-resolved rather than reused.

### Headline deltas vs 2026-07-09

| Metric                             | 2026-07-09                  | 2026-07-18               | Note                    |
| ---------------------------------- | --------------------------- | ------------------------ | ----------------------- |
| `/api/library` queries             | 7,508                       | **13**                   | fix holds at +25 issues |
| `/api/library` in-process          | 3.9–4.1s                    | **0.65–0.70s**           |                         |
| `/api/library` over HTTP           | 3,932ms                     | **935ms**                |                         |
| `/api/series` (2000 AD) queries    | 4,969                       | **9**                    | now 2,490 issues        |
| `/api/series` (2000 AD) in-process | 2.5–2.7s                    | **0.39–0.42s**           |                         |
| `/api/series` (2000 AD) over HTTP  | 2,544ms                     | **606ms**                |                         |
| Cover conditional-GET              | 0/15 honored 304            | **15/15**                | Phase 4 fix intact      |
| Reader page re-flip                | no benefit (22.8 vs 22.7ms) | **2.0x (40.5 → 20.4ms)** | Phase 3 fix intact      |
| `/api/home/strips` queries         | 7                           | **39–52**                | ← new N+1, see below    |

The v2.6 Phase 1–5 fixes all hold at the rebuilt library's scale. Nothing
regressed.

### New findings

| #   | Finding                                                                                   | Measured                                                                                                                                                                    | Root cause                                                                                                                                                                                 | Fixable-in-code?                                     | Impact                                                                                                        |
| --- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 12  | **Scanner at real scale — first ever measurement.** Full from-scratch scan of 5,452 files | **21.5 min, 4.23 files/s, 0 reported errors**                                                                                                                               | n/a — this is the baseline number, not a defect                                                                                                                                            | n/a                                                  | Closes the §3 follow-up. All 18 historical log entries (5–14s) were no-op walks and were never representative |
| 13  | **Thumbnail generation dominates the scan**                                               | median 104.7ms/file, **677.6s total = 53.0%** of scan runtime                                                                                                               | Cover extract + resize per file                                                                                                                                                            | Likely — parallelism, or cheaper decode path         | Highest-value scanner optimisation by a wide margin                                                           |
| 14  | **Per-file `db.commit()`**                                                                | 5,452 commits, median 35.1ms, **234.2s total = 18.3%**                                                                                                                      | `scan_single_file()` commits once per file                                                                                                                                                 | **Yes** — batch every N files                        | ~3.9 min of a 21.5 min scan                                                                                   |
| 15  | **4 archive opens per file, not 3**                                                       | 5,448 files at exactly 4 opens; 4 files at 2                                                                                                                                | Same redundant-reopen family as findings #4/#5/#6/#11, never applied to the scan path                                                                                                      | **Yes**                                              | Code inspection undercounted this on 2026-07-09                                                               |
| 16  | **Scanner is not I/O-bound**                                                              | median cost 189ms (0–10MB) → 289ms (250MB+) — 1.5x across a 25x size range                                                                                                  | Fixed per-file overhead, not throughput. Apparent 1,318MB/s on large files vs the drive's real 85MB/s confirms it only reads the ZIP directory + one cover                                 | n/a                                                  | Explains why scan time tracks file *count*, not library size                                                  |
| 17  | **Third instance of the `Issue.genres` N+1, in `home.py`**                                | `/api/home/strips` 39–52 queries (varies — two strips pick randomly), ~345ms. Fingerprint: **32 identical `issue_genres` queries**, one per issue across two 15-item strips | `_strip_recently_added` (16q) and `_strip_random_unread` (16q, 245.8ms) lazy-load `Issue.genres` per issue. Findings #1/#2 fixed exactly this in `library.py`; `home.py` was never touched | **Yes** — `selectinload(Issue.genres)`, same pattern | Medium — it's the homepage, hit first on every visit                                                          |
| 18  | **No cold-start penalty** (follow-up closed, negative result)                             | cold/warm ratio **0.9–1.2x** across all 8 endpoints, measured on the true first request after a tray-app restart                                                            | `_warmup_db()` appears to be doing its job                                                                                                                                                 | n/a                                                  | The §3 concern doesn't generalise beyond the one `/api/home/strips` case that originally prompted it          |

### What's *not* a problem

- **Raw USB throughput unchanged and healthy** — cold median 85.1MB/s, warm
  86.8MB/s across a 40-file / 3.2GB stride sample (2026-07-09: 77–95MB/s).
  Cold ≈ warm again, because a 3.2GB sample far exceeds what the OS cache
  holds — expected, not a fault.
- **Both N+1 fixes scale** — see the delta table. `/api/library`'s remaining
  ~0.65s is Python-level aggregation over 5,452 issues, exactly as the
  2026-07-09 entry predicted; it is no longer DB-bound.
- **Cover caching works** — 15/15 `Cache-Control: public, max-age=86400,
  immutable` + ETag, 15/15 return a real 304 on a matching `If-None-Match`
  (43.6ms → 2.3ms). 300 covers fetched sequentially: median 16.7ms, p95
  43.8ms.
- **Reader page cache works** — 2.0x benefit on re-flip, against no measurable
  benefit before the Phase 3 fix.
- Small/typical page loads remain fast: Postal (25 issues) 5.6ms in-process /
  15.8ms HTTP, issue detail 3.7ms, search 28.6ms, continue-reading 0.6ms.

### Correctness issues surfaced by this pass (not performance)

Logged rather than fixed, per this doc's scope and the perf-diagnostics
skill's hard rules:

- **BUG-025** — series move doesn't update `issues.file_path` /
  `custom_tabs.folder_path`. Forced the rebuild this session.
- **BUG-026** — Clear Database leaves orphaned thumbnails (2,516, 354MB) and
  doesn't `VACUUM`.
- **BUG-027** — no safe DB-reset sequence: Clear Database lives on the Admin
  page, which the server must be up to serve.
- **BUG-028** — macOS resource-fork entries (`._*.jpg`) inside archives break
  cover extraction *and* double `page_count` (64 reported vs 32 real), with
  `errors=0` reported. Full-library sweep: **22 of 5,452 issues affected**.

### Caveats on this run's numbers

- **The D1 archive-level "cold" numbers are not cold.** `archive_namelist()`
  measured 0.7ms here vs 42.5ms on 2026-07-09 — that is *not* a 60x
  improvement. The instrumented full scan had just read every archive's
  central directory minutes earlier, so Windows' file cache was warm across
  the whole library. Treat this run's D1 as a warm-only measurement; the
  2026-07-09 figure remains the honest cold number.
- **Full Editor page preview is still unmeasured**, for a new reason. Admin
  auth is currently off (`admin_password_hash: null`), so the 2026-07-09
  blocker is gone — but `GET /api/editor/full/files` returns `{"files":[]}`
  because that endpoint works from a staged file list, not the library. It
  needs files staged before it can be measured.
- Cold-idle drive probe skipped by request (10–15 min of wall-clock per rep);
  finding #9 remains inconclusive.

---

## 1C. Re-baseline — 2026-07-26 (finding #14 fix) + new CT finding

**Why this run:** picked up `docs/INBOX.md`'s "Scanner speedups... inc recheck
of CT function" line. Finding #14 (per-file `db.commit()`) is fixed and
verified below. The CT recheck surfaced a new, unrelated, much larger finding
(#19) — scoped, not yet fixed (Tez's call: "scope it for now").

### Finding #14 fix — commit-batching (built and verified)

`scan_single_file()` (`backend/scanner.py`) gained a `commit: bool = True`
parameter gating its 4 internal `db.commit()` calls; `scan_library()`'s
per-file loop now calls it with `commit=False` and commits every 50 files
(`COMMIT_BATCH_SIZE`) instead of once per file, plus a final commit after the
loop. The three single-file callers (editor post-save rescans,
`POST /api/scan/file`) keep the default `commit=True` — they need an
immediate, synchronous commit and aren't part of this scope.

**Verified two ways** (never against the real library/Processing folder for
the timing run):

- **Scratch test** — 120 synthetic `.cbz` files in an isolated scratch DB and
  library folder (script not committed, session-scratchpad only): commits
  dropped from a would-be 121 (old per-file behaviour) to **4**
  (⌈120/50⌉ = 3 batch commits + 1 final), with correct `new`/`skipped`/
  `updated` detection verified across three passes (from-scratch, unchanged
  rescan, one file touched). The commit-count math is deterministic
  (⌈N/50⌉+1 regardless of N), so this generalises cleanly to the real
  library's scale (⌈5,452/50⌉+1 = 110 commits, down from 5,452 — matching
  finding #14's original ~3.9 min estimate) without needing to re-run a full
  from-scratch timing pass against the real 5,452-file library this session.
- **Live scan** — real library, real DB, triggered via `POST /api/scan` after
  a tray-app restart to pick up the change: 5,453 files, `new=0 updated=0
  skipped=5453 errors=0`, ~16s wall clock — matches the historical no-op-scan
  baseline (5–14s pre-fix), no regression.

`.claude/skills/perf-diagnostics/scripts/7_instrumented_scan.py` (the
finding-#12/#13/#14 measurement harness) was updated to match the new
`scan_single_file()` signature — its per-file commit timing is now a global
wrap around the whole run instead of a per-call swap-in/out, since individual
calls no longer commit during a full scan.

### Finding #19 — CT "Select Issue" list scales badly with series size, warm-cache path never fires for large series

| Series | search_series() (Select Series) | list_issues_for_series() cold (Select Issue / "Issues" button) | list_issues_for_series() warm (immediate repeat) |
| --- | --- | --- | --- |
| Postal (25 issues) | 2.5s | 3.0s | 0.08s |
| 2000 AD (2,492 issues, library's own largest) | 0.09s | **221s (3.7 min)** | **80s** |

Measured with a new read-only script,
`.claude/skills/perf-diagnostics/scripts/11_ct_series_issue_timing.py`, timing
`backend/ct_bridge.py` calls directly against live ComicVine data — the same
shared codepath `GET /editor/full/search/series` and `/search/issues`
(`backend/routers/editor_full.py`) use for the Full Editor's Search Online →
Select Series/Select Issue modal (`EDITOR_SPEC.md` §9.6).

**Root cause** (found by reading the vendored
`comictalker/talkers/comicvine.py`): `_fetch_issues_in_series()`'s warm-cache
fast path only fires when the cached issue count exactly equals ComicVine's
own reported `count_of_issues` for the series. For 2000 AD, ComicVine reports
**2,489** but **2,492** issues actually come back — the mismatch means the
fast path never triggers, so a full per-issue reprocessing pass reruns in
full on *every* call, cold or warm. That pass also does a redundant per-issue
series re-lookup (`_fetch_series_data()` called once per issue in the result
set, for a series ID already fetched moments earlier) — vendored library
code, not something in `backend/`.

**Not the cause:** a personal ComicVine API key is configured and confirmed
selected at runtime (`custom_limiter`, 10 req/10s per-endpoint-type buckets)
rather than the shared 1-req/10s default — rate limiting was a candidate
hypothesis, ruled out.

**Partial live comparison:** Tez timed the **Select Series** step live
(editor → Search Online → series list appears): ~4s first click, ~1.5s
second — consistent with the table above (this step is fine, doesn't scale
with series size). He didn't click through to **Select Issue** for 2000 AD
specifically, so the 221s/80s numbers above aren't yet independently
confirmed "felt" against the standalone desktop CT app — they stand on their
own as ComicVault-side measurements regardless.

**Fixable-in-code?** Likely, once picked up — see §3 for candidate
approaches. **Not built this session** (scoped only, per Tez).

---

## 1D. Reader scroll-mode load test — 2026-07-29

**Why this run:** a decision gate, not a routine re-baseline. Tez is weighing
replacing the Windows Flutter desktop reader with a browser-popout reader (new
`frontend/reader.html`/`reader.js` consuming the existing `/api/issue/{id}/pages`
and `/api/page/{issue_id}/{n}` endpoints) — see the plan at
`the-windows-reader-is-lively-octopus.md`. Page mode (one image at a time) is a
non-question — same cost the current Flutter reader already pays. Scroll mode
(continuous vertical read-through) was the open question: does mounting many
full-resolution comic-page images in a browser tab at once actually work, or does
it need to be built as a virtualized/windowed component from day one. This run
answers that before any reader code gets written, per the plan's explicit
prerequisite gate.

**No application code was touched.** Measurements: (1) a Python script sampling
real page-image bytes via the live server's existing `/api/page/{id}/{n}`
endpoint (no new endpoint, no code change), and (2) a standalone scratch HTML/JS
test page (`session scratchpad`, not committed) served by a throwaway
`python -m http.server` on port 8899 — a different port from the app's 9424, not
a second instance of the app — loaded in a real browser tab via
`claude-in-chrome` to measure actual mount/load/decode behaviour.

### Finding — full-resolution page images are large enough that eager "mount the whole issue" scroll mode is not viable; a windowed/virtualized approach is required, not optional

| Issue | Pages | Avg page size | Estimated total transfer if all pages mounted at once | Decoded (uncompressed) memory per page |
| --- | --- | --- | --- | --- |
| Four Horsemen #1 (id=11, typical single issue) | 25 | 2,140 KB | 52.3 MB | not sampled — pages this size aren't the risk case |
| Starseeds #1 (id=4915, mid-large single issue) | 250 | 1,858 KB | 453.5 MB | 6.8 MB (1163×1538 PNG) |
| East of West Compendium (id=3464, library's largest issue) | 1,220 | 2,218 KB | **2,642.7 MB (2.6 GB)** | 23.2 MB (1988×3056 JPEG) |
| (for scale) id=11 page 0 | — | — | — | **54.2 MB** (3288×4320 WebP — largest sampled pixel dimensions in the library, despite a mid-size file) |

Sampled 12 pages per issue via direct HTTP (`urllib`) against the live server;
decoded-memory figures computed from actual pixel dimensions (`width × height ×
4 bytes` for an RGBA bitmap) via Pillow, not inferred from file size — file size
and decoded memory don't track each other (id=11's page 0 is a "moderate" 1.8MB
JPEG file but decodes to 54MB in memory, because of its very high native
resolution).

**Live browser confirmation** (East of West compendium, id=3464):

- **Windowed** (20 images mounted, matching a "≈±10 pages around current
  position" virtualization window — the same recycling behaviour Flutter's
  `ListView.builder` already gives the current reader for free): all 20 loaded
  in **4.8s**, page stayed responsive throughout.
- **Naive eager mount** (200 images mounted at once, simulating a "just render
  the whole scroll strip" implementation): took **14.4s** just to finish
  loading — before the reader would even be usable — for roughly 440MB of
  network transfer. The full 1,220-page case (not run live — the math alone is
  conclusive) would be ~6x that: an estimated 2.6GB transfer and, worse, up to
  **~28GB of decoded image memory** if every mounted `<img>` stayed fully
  decoded and resident, which is not a viable browser tab under any
  circumstance.

**Conclusion:** this is a real, numbers-backed constraint, not a hypothetical —
but it doesn't kill Option B (the browser-popout reader) in the migration plan.
It does add one concrete requirement to `reader.js`'s Scroll mode: it must be
built as a **virtualized window** from the start (mount only the current page ±
a small margin, e.g. ~10 pages either side, via `IntersectionObserver` — clearing
`img.src`/removing the element once a page scrolls far enough out of view rather
than relying on native `loading="lazy"` alone, since lazy-loading only defers the
initial fetch and doesn't guarantee the browser releases decoded memory for
images that are still in the DOM once they've scrolled off-screen). This is
extra scope beyond "port `reader_screen.dart`'s two modes 1:1" and should be
folded into migration step 1 of the plan, not treated as a later optimization
pass — Scroll mode without it would be genuinely broken on the library's largest
issues, not just slow.

**Go/no-go read:** this does not block Option B. Page mode is unaffected and
trivial. Scroll mode is buildable, just with virtualization as a first-class
requirement rather than an afterthought — a well-understood pattern
(`IntersectionObserver` mount/unmount window), not a research problem.

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

- ~~**Reader scroll-mode virtualization**~~ — **moot, 2026-07-29.** §1D's
  finding (naive eager-mount isn't viable, a windowed component would be
  required) directly informed a follow-up scope decision the same day: Scroll
  mode is being dropped from the Windows browser reader entirely (Tez rarely
  used it even on the tablet where it already exists), so no virtualized
  component will be built and there's nothing to re-measure. Page mode (one
  image at a time) was never affected by this finding. See `docs/v2.6/
  progress.md`'s 2026-07-29 "Windows reader review" entry for the full
  decision trail.
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
- **Full Editor page-preview** still never measured under controlled
  conditions. Originally blocked by admin auth; that blocker is gone (admin
  auth is currently off), but as of 2026-07-18 `GET /api/editor/full/files`
  returns `{"files":[]}` — the endpoint works from a staged file list, not
  the library, so files must be staged first. Note the 2026-07-13 Phase 5 fix
  *was* verified live against a real 1,220-page compendium at the time; what's
  missing is a repeatable measurement in the standard harness.
- ~~**Scanner at real scale** never measured~~ — **RESOLVED 2026-07-18**, see
  §1B findings #12–#16. 5,452 files from scratch: 21.5 min, 4.23 files/s,
  with thumbnail generation (53%), per-file commits (18%) and 4 archive opens
  per file as the cost drivers.
- ~~**No cold-server-restart baseline**~~ — **RESOLVED 2026-07-18**, see §1B
  finding #18. Negative result: cold/warm ratio 0.9–1.2x across all eight
  endpoints, i.e. no measurable first-request penalty.
- ~~**Scanner cost drivers are measured but untested against a fix**~~ —
  **finding #14 (commit-batching) fixed and verified 2026-07-26**, see §1C.
  Finding #13 (thumbnail generation, ~11.3 min potential) remains unbuilt —
  it's the largest remaining candidate and the most invasive (parallelising
  across threads, touching the main scan loop's structure); explicitly
  deferred to its own future session rather than attempted alongside the
  commit-batching fix.
- **Finding #19 (CT "Select Issue" list scales badly with series size) is
  scoped but not built** — see §1C for the full diagnosis (2000 AD: 221s
  cold / 80s warm for a 2,492-issue series, root cause is a `count_of_issues`
  mismatch defeating the vendored library's warm-cache fast path, plus a
  redundant per-issue series re-lookup inside it). Candidate fixes: tolerate
  the count mismatch so the fast path fires anyway, or short-circuit the
  redundant per-issue re-lookup via a runtime monkeypatch in `ct_bridge.py`
  (same "monkeypatch at runtime, no source edits" pattern the
  `perf-diagnostics` scripts already use for scanner instrumentation). Also
  still open: an independent live timing of the same 2000 AD "Issues" lookup
  in the standalone ComicTagger desktop app, for a true side-by-side number
  against the 221s/80s figures above (Tez's own live timing this session
  covered the faster Select Series step only, not Select Issue).
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

### Where the raw files live

The 2026-07-18 run's raw data is committed to
**`docs/archive/perf-2026-07-18/`**:

| File                           | What it is                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `phase2_scan_perfile.csv`      | Per-file scanner timing, all 5,452 rows — total/parse/thumbnail/commit ms, archive opens, query count, size |
| `phase2_scan_summary.json`     | Scan totals (wall clock, counts, queries, commits)                                                          |
| `macjunk_affected.csv`         | The 22 BUG-028 issues with real vs recorded page counts                                                     |
| `L_snapshot_prescan.json`      | Pre-scan snapshot of all 5,452 archive paths + sizes, used to prove `L:` was never written to               |
| `scan_raw_output.txt`          | Full stdout of the instrumented scan, incl. the cover-failure lines                                         |
| `cold_start_raw_output.txt`    | Cold vs warm endpoint timings                                                                               |
| `page_serving_raw_output.txt`  | Page-flip, cover grid, Full Editor probe                                                                    |
| `perf-test-plan-2026-07-18.md` | The plan this run followed, incl. the pre-flight findings that changed it                                   |

Three new reusable scripts were added to
`.claude/skills/perf-diagnostics/scripts/` from this run:
`7_instrumented_scan.py` (the scanner harness — monkeypatches timing onto
`backend.scanner` at runtime, no source edits), `8_macos_junk_sweep.py`
(BUG-028 detection; re-run after a fix to confirm the count drops to 0), and
`9_cold_start.py` (fires one shot per endpoint immediately after a restart,
then 8 warm trials).

### 2026-07-18 run

<details>
<summary>Phase 1 — snapshot + raw I/O baseline (40-file stride, pre-scan)</summary>

Library snapshot before the scan: **5,452 files, 562.47 GB**, `os.walk` +
`getsize` in 0.42s. Stride sample of 40 files, 3,393MB:

| Pass | median time | p95       | max       | median MB/s | slowest 5% |
| ---- | ----------- | --------- | --------- | ----------- | ---------- |
| Cold | 480.8ms     | 3,168.6ms | 8,400.7ms | 85.1        | 70.0       |
| Warm | 486.3ms     | 3,172.6ms | 8,384.7ms | 86.8        | 76.4       |

Sampled from disk, not from the DB — 2,484 DB paths were dead at this point
(BUG-025) and the stock script's `os.path.exists` guard would have silently
dropped the entire 2000 AD series from the sample.

</details>

<details>
<summary>Phase 2 — instrumented full scan (5,452 files from empty DB)</summary>

Wall clock **1,289.2s (21.5 min)**. `new=5452, updated=0, skipped=0,
missing=0, errors=0`. Throughput 4.23 files/s. 116,871 SQL queries total
(~21.4/file), 5,452 commits (exactly 1/file).

Per-file cost, all 5,452 `new`:

| Stage     | median  | p95     | max       | total    | share |
| --------- | ------- | ------- | --------- | -------- | ----- |
| total     | 208.3ms | 412.6ms | 5,811.8ms | 1,278.9s | 100%  |
| parse     | 51.8ms  | 105.5ms | 5,426.6ms | 305.3s   | 23.9% |
| thumbnail | 104.7ms | 265.5ms | 1,168.5ms | 677.6s   | 53.0% |
| commit    | 35.1ms  | 67.8ms  | 391.2ms   | 234.2s   | 18.3% |

Archive opens per file: 4 (5,448 files), 2 (4 files).

Cost by file size — note how flat this is:

| band      | n     | med total | med parse | med thumb | med MB/s |
| --------- | ----- | --------- | --------- | --------- | -------- |
| 0–10MB    | 328   | 189.3ms   | 51.6ms    | 84.8ms    | 43.5     |
| 10–25MB   | 1,849 | 165.1ms   | 49.6ms    | 61.4ms    | 100.2    |
| 25–50MB   | 868   | 230.4ms   | 54.5ms    | 119.2ms   | 161.6    |
| 50–100MB  | 769   | 255.7ms   | 55.1ms    | 149.9ms   | 276.8    |
| 100–250MB | 1,053 | 259.2ms   | 52.3ms    | 153.5ms   | 619.8    |
| 250MB+    | 585   | 288.7ms   | 54.2ms    | 180.3ms   | 1,318.8  |

The single 5,811.8ms outlier ('68 Homefront #1, parse=5,426.6ms) was the
first file touched in the run — cold-disk seek, consistent with findings
#9/#11, not a code path.

Throughput decayed steadily through the run: 5.4 files/s at 1,750 files →
4.2 files/s at 5,250. Not investigated; candidates include growing index
maintenance cost as the tables fill, and the size distribution of files
encountered later in the walk.

</details>

<details>
<summary>Phase 3 — cold-server-restart (one shot per endpoint, then 8 warm trials)</summary>

| Endpoint                 | cold (1st ever request) | warm median | warm p95 | cold/warm |
| ------------------------ | ----------------------- | ----------- | -------- | --------- |
| Library — All            | 1,109.1ms               | 935.5ms     | 971.9ms  | 1.2x      |
| Series — 2000 AD (2,490) | 643.6ms                 | 605.6ms     | 663.9ms  | 1.1x      |
| Series — Postal (25)     | 17.6ms                  | 15.8ms      | 16.8ms   | 1.1x      |
| Home strips              | 306.8ms                 | 335.3ms     | 369.1ms  | 0.9x      |
| Folder View tab          | 196.4ms                 | 202.4ms     | 263.0ms  | 1.0x      |
| Issue detail             | 16.5ms                  | 16.6ms      | 17.4ms   | 1.0x      |
| Search — batman          | 37.0ms                  | 33.3ms      | 34.1ms   | 1.1x      |
| Continue reading         | 20.7ms                  | 16.7ms      | 16.8ms   | 1.2x      |

All 8 cold requests completed within 2.4s of the first. The Folder View tab
returned 46 bytes — it was still pointing at the pre-move path (BUG-025) and
has since been removed by Tez.

</details>

<details>
<summary>Phase 4 — in-process query counts (3 runs, stable)</summary>

| Endpoint                          | Time (run1/2/3)       | Queries | 2026-07-09 |
| --------------------------------- | --------------------- | ------- | ---------- |
| `/api/library` (unfiltered)       | 699.7 / 648.8 / 658.1 | **13**  | 7,508      |
| `/api/series/29` (2000 AD, 2,490) | 385.6 / 402.4 / 421.3 | **9**   | 4,969      |
| `/api/series/4618` (Postal, 25)   | 6.8 / 5.6 / 5.6       | 5       | 53         |
| `/api/issue/1`                    | 7.0 / 4.7 / 3.7       | 8       | 15         |
| `/api/home/strips`                | 347.0 / 345.8 / 292.7 | **52**  | 7          |
| `/api/library/tab/1/folder`       | 193.8 / 192.0 / 234.9 | 3       | 3          |
| `/api/search?q=batman`            | 30.3 / 28.6 / 28.6    | 8       | 8          |
| `/api/reading/continue`           | 1.8 / 0.6 / 0.6       | 1       | 1          |

Per-helper attribution for `/api/home/strips` (finding #17):

```
_load_progress_map         1 query     67.5ms
_strip_continue_reading    1 query      4.3ms
_strip_recently_added     16 queries   40.9ms
_strip_random_unread      16 queries  245.8ms
_strip_random_genre        4 queries   10.1ms
```

Statement fingerprint: 32x `SELECT issue_genres.issue_id, issue_genres.genre_name
FROM issue_genres WHERE ... = ?` — one per issue across the two 15-item strips.

</details>

<details>
<summary>Phase 5 — page serving, covers, Full Editor</summary>

D1 (archive-level, n=15) — **warm-only, see caveat**: namelist 0.7ms
"cold" / 0.6ms warm; read_bytes 22.6ms / 3.9ms; raw sequential 89.9MB/s.

D2 (page flip, id=1, 28 pages): 10 never-read pages median **40.5ms**;
re-flip to page 0 3x median **20.4ms** — 2.0x, cache working. Compare
2026-07-09: 22.8ms vs 22.7ms, no benefit.

E (covers): 300 sequential fetches, median 16.7ms, p95 43.8ms, 15.5MB.
Conditional-GET 15/15 `Cache-Control: public, max-age=86400, immutable` +
ETag present, **15/15 returned 304** on a matching `If-None-Match`
(43.6ms → 2.3ms).

*Method note:* a first pass reported 0/15 on both. That was a harness bug —
uvicorn emits header names lowercase and the check was case-sensitive. Worth
knowing for future runs: always compare header names case-insensitively.

F (Full Editor): `GET /api/editor/full/files` → 200, `{"files":[]}`.
Page-preview endpoints return 404 for library issue ids, since `editor_full.py`
mints its own file ids. Not measurable without staging files first.

</details>

<details>
<summary>macOS resource-fork sweep (BUG-028)</summary>

All 5,452 issues opened and their image-entry lists inspected; 0 unreadable.
**22 issues contain `._`-prefixed AppleDouble entries, and all 22 have a wrong
`page_count`** — verified cases report exactly double (64 vs 32 real pages),
one junk sidecar per real page. 21 are 2000 AD (progs #2464–#2491, the same
set whose cover extraction failed); 1 is in `Judge Dredd - One-Eyed Jacks`,
whose cover happened to extract successfully and so shows no visible symptom.

</details>

### 2026-07-09 run

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

| Endpoint                    | Time (ms, run1/run2/run3) | Queries |
| --------------------------- | ------------------------- | ------- |
| `/api/library` (unfiltered) | 3969 / 3903 / 4140        | 7,508   |
| `/api/series/79` (2000 AD)  | 2654 / 2720 / 2580        | 4,969   |
| `/api/series/4616` (Postal) | 25.1 / 27.6 / 28.8        | 53      |
| `/api/issue/79`             | 200.5 / 237.5 / 215.6     | 15      |
| `/api/home/strips`          | 371.3 / 318.4 / 374.8     | 7       |
| `/api/library/tab/3/folder` | 317.8 / 277.7 / 279.0     | 3       |
| `/api/search?q=batman`      | 36.1 / 32.3 / 32.6        | 8       |
| `/api/reading/continue`     | 1.1 / 0.6 / 0.6           | 1       |

</details>

<details>
<summary>Phase C — HTTP timing (127.0.0.1, 8 trials each)</summary>

| Endpoint          | Median   | p95      | Bytes     |
| ----------------- | -------- | -------- | --------- |
| Library — All     | 3932.2ms | 4358.0ms | 2,575,925 |
| Series — 2000 AD  | 2544.1ms | 2690.6ms | 2,638,745 |
| Series — Postal   | 39.4ms   | 70.3ms   | 27,152    |
| Issue detail (79) | 227.1ms  | 268.6ms  | 1,728     |
| Home strips       | 377.6ms  | 396.5ms  | 11,578    |
| Folder View tab 3 | 270.7ms  | 355.1ms  | 4,277     |
| Search — batman   | 34.2ms   | 41.3ms   | 1,652     |
| Continue reading  | 16.9ms   | 17.6ms   | 2         |

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
