# digib00age — Stress Test (Load / Concurrency) Diagnostics

Standing reference doc for concurrency/load investigation, parallel to
`PERFORMANCE.md` (speed) and `TESTING.md` (correctness). First baseline
established 2026-07-29 — before this, every verification pass on this app
assumed one person, one device, one action at a time. In real use it isn't:
the tablet, the web browser, the desktop reader, and background jobs (the
scanner, scheduled Processing Folder automation) can all be touching the
same database and the same comic files at the same moment.

**Scope of this doc:** measured facts and root-cause findings only. Nothing
in this baseline pass changed application behavior — every scenario ran
against an isolated scratch copy (its own `backend/`/`frontend/` source
copy, its own synthetic library, its own SQLite DB), never the real DB,
real `config.json`, or `L:\Comic Archives`. Deciding what (if anything) to
fix, and when, is a separate triage step against `BUGS.md`/`ROADMAP.md`/a
future build queue — same convention `PERFORMANCE.md` uses.

**To re-run this baseline**, use the `stress-test` skill
(`.claude/skills/stress-test/`) rather than re-deriving the methodology —
it packages the ground rules, the scratch-environment setup, and the 6
phase scripts as reusable starting points. Raw per-phase JSON results and
the collision traceback excerpt for the 2026-07-29 run are in
`archive/stress-test-2026-07-29/` (same convention as
`archive/perf-2026-07-18/` for `PERFORMANCE.md`).

---

## 1. Baseline — 2026-07-29

Scratch environment: 19 synthetic CBZs (3 series x 5 issues + 4 singles),
generated fresh by `0_setup_scratch.py`, entirely fabricated content — zero
dependency on the real library. Scratch server on `127.0.0.1:9427`, real
`backend`/`frontend` source copied in unmodified. Goal confirmed with Tez:
**realistic concurrent-device usage** (tablet + browser + desktop reader +
unattended background jobs), not raw throughput capacity, long-running soak
testing, or deliberate failure-injection — those are out of scope for this
pass (see `ROADMAP.md` if a later pass wants to pick them up).

### Ranked findings

| # | Finding | Evidence | Root cause | Fixable-in-code? | User-visible impact |
|---|---|---|---|---|---|
| 1 | **Reading a page/cover while an editor rebuild is in flight on the same issue can 500 with a `PermissionError`, or truncate mid-response** | Reproduced in 4 of 5 runs of `5_reader_vs_rebuild_collision.py` (6 reader threads + 1 rebuild thread hammering one issue for 6s, ~1300-1600 requests/run): `GET /api/page/{id}/{n}` → `500`, server log shows `PermissionError: [Errno 13] Permission denied: '...Concurrency Quarterly #001 (2021).cbz'` at `backend/archive_formats.py:32` (`zipfile.ZipFile(file_path, "r")`) — the reader tried to open the archive at the exact moment the editor rebuild's `os.replace()` (`backend/editor/archive_io.py:157`) was mid-swap on that same path. Separately, `GET /api/cover/{id}` produced a client-side `IncompleteRead` / server-side `RuntimeError: Response content shorter than Content-Length` — the thumbnail file (`backend/scanner.py`'s `_generate_thumbnail`, `img.save(str(thumb_path), ...)` at `scanner.py:257`) is overwritten **non-atomically** (a direct write, not a temp-file-then-rename like the archive rebuild), so a `FileResponse` mid-stream can get truncated by a concurrent regeneration. Error rate across 5 runs: 0, 1, 7, 2, 2 errors per ~1300-1600 requests (roughly 0-0.5%) — rare but real, exactly the "looks random, never repros manually" shape this pass exists to catch. | Windows file-sharing semantics (`os.replace` isn't guaranteed atomic against a concurrent open-for-read on Windows the way it is on POSIX) + a genuinely non-atomic thumbnail write, colliding with the reader's per-request archive-open pattern (`reader.py`/`archive_formats.py`) | **Yes** — two independent fixes: (a) retry-on-`PermissionError` with a short backoff in the archive-open path, or open with `FILE_SHARE_DELETE` semantics; (b) make thumbnail writes atomic (write to a temp file, then `os.replace()`, same pattern the archive rebuild already uses) | **Confirmed real** — this is exactly what a Process All batch on a big series, run while comics are being read elsewhere in the house, could intermittently surface as. Logged as `BUG-033`. |
| 2 | Concurrent reading-progress writes + mobile-sync writes on the same issue, under burst load | `2_writer_lock_contention.py`: 650 requests (500 mixed progress/sync writes on 2 contended issue ids + 150 concurrent reads), 80 concurrent workers — **0 errors, 0 `database is locked`** | WAL mode is enabled (`backend/database.py`) and Python sqlite3's default 5s `busy_timeout` comfortably absorbed this burst size against a small (19-issue) scratch DB | n/a this run | **Not reproduced at this scale.** The architecture read that prompted this test still stands (no explicit `busy_timeout` configured, no retry/backoff logic anywhere) — this is a real gap, just not one that manifested under a burst this size against a small DB. Flagged as an open question, not a bug — see §3. |
| 3 | Scanner running concurrently with Basic Editor saves + Full Editor Process All | `3_scan_vs_edit_collision.py`: repeated `POST /api/scan` + repeated Basic Editor saves + repeated Process All runs, all firing concurrently for 6s — **0 HTTP errors, 0 issue-count drift (19 before, 19 after), 0 tracebacks in the server log** | `scan_progress.running` is genuinely only checked by the 3 scan-trigger call sites (confirmed by code reading) — but the collision itself didn't surface an observable problem at this library size/duration | n/a this run | **Not reproduced.** The lack of mutual exclusion between scanner and editor saves is still real in the code, but this pass didn't catch a concrete failure mode from it — flagged as an open question, not a bug. |
| 4 | Full Editor "Process All" holding the SQLite writer role during a large batch | `4_process_all_lock_holding.py`: one 19-item Process All batch (every item already had a matching `Issue` row, so each one hit `scan_single_file`+commit — the worst-case path for this risk) took 1.353s total; a background reading-progress-write + issue-read loop running throughout showed **no latency spike or errors during the batch window** (median 0.011s during vs 0.024-0.027s before/after — if anything, faster, well within noise for a 20-sample bucket) | 19 tiny synthetic files finished the whole batch in ~1.4s — too fast and too small a batch to meaningfully hold the writer role | n/a this run | **Not reproduced at this scale.** A real Process All batch (hundreds of full-size archives) would hold the writer role far longer per item (larger XML rebuild, more page-count verification) — this pass's synthetic library is too small to speak to that case either way. Flagged as an open question, not a bug — see §3. |
| 5 | Plain concurrent read load (control) | `1_concurrent_read_load.py`: 40 requests each at concurrency 1/5/15/30 — **0 errors at every level**, median latency scaled from 6.5ms (serial) to 133ms (30-way concurrent), no error/crash at any level | Expected — FastAPI/Starlette's thread-pool dispatch for sync `def` routes handles this cleanly; latency growth is just queueing, not a fault | n/a | **Not a problem.** Confirms plain read concurrency isn't the risk — everything interesting in this pass came from write/rebuild collisions, not raw read volume. |
| 6 | Combined realistic simulation (tablet + browser + desktop reader + background scan, 15s) | `6_combined_simulation.py`: 524 total requests across 4 simulated "devices" — **0 errors on any device, 0 tracebacks** | As scoped, this simulation didn't include editor/rebuild activity (see caveat below), so it couldn't have caught finding #1 even though that's the more realistic day-to-day trigger (Tez editing a comic while it's also open for reading elsewhere) | n/a this run | **Caveat, not a finding:** this phase's device mix (tablet sync, browser browsing, desktop reads, background scan) doesn't include an editing device, so it's a real but incomplete "everything at once" test. Finding #1 needed phase 5's dedicated read/rebuild hammering to surface — a future run extending phase 6 to include editor activity would be a more complete single scenario. |

### What's not a problem

- Plain concurrent reads at up to 30-way concurrency: clean.
- Reading-progress + mobile-sync writes under burst load against a small
  DB: no lock errors observed.
- Scanner running concurrently with edits: no corruption or drift observed
  at this library size.
- A full Process All batch running alongside other DB activity: no
  measurable stall at this batch size.

### Open follow-ups (not reproduced this run, not ruled out either)

- **No `busy_timeout` configured** beyond Python sqlite3's 5s default, and
  **no retry/backoff logic anywhere in the codebase** for `database is
  locked` (confirmed by code reading, `backend/database.py`) — a genuine
  gap that a larger/slower DB or a much bigger concurrent burst could still
  surface. Worth a re-run with a bigger scratch DB (hundreds/thousands of
  issues, matching the real library's scale) if this becomes a live concern.
- **Scanner/editor mutual exclusion** — `scan_progress.running` isn't
  checked by Basic Editor save, Full Editor Process All, or Processing
  Folder Automation. Not observed to cause a problem this run, but the gap
  is real in the code and worth revisiting if the scanner's real-library
  runtime (minutes, not the scratch library's sub-second run) increases the
  collision window.
- **Process All holding the writer role at real scale** — this pass's
  19-item, all-tiny-file batch isn't representative of a real Process All
  run over hundreds of full-size archives. Re-run phase 4 against a larger
  synthetic library if this becomes a live concern.
- **Phase 6 doesn't include editor activity** — extend it to interleave
  Basic Editor saves into the combined simulation for a single scenario
  that could catch finding #1 without needing phase 5's dedicated,
  narrower hammering.

<details>
<summary>Raw phase results (scripts/_results/*.json)</summary>

**Phase 1 — concurrent read load**
```json
{
  "1":  {"requests": 40, "errors": 0, "median_s": 0.0065, "p95_s": 0.0243, "max_s": 0.029},
  "5":  {"requests": 40, "errors": 0, "median_s": 0.0267, "p95_s": 0.0421, "max_s": 0.0476},
  "15": {"requests": 40, "errors": 0, "median_s": 0.0826, "p95_s": 0.1382, "max_s": 0.1729},
  "30": {"requests": 40, "errors": 0, "median_s": 0.1334, "p95_s": 0.1804, "max_s": 0.187}
}
```

**Phase 2 — writer lock contention**
```json
{
  "total_requests": 650, "total_elapsed_s": 3.417,
  "error_count": 0, "lock_error_count": 0,
  "contended_issue_final_state": {
    "1": {"current_page": 25, "read_status": "reading"},
    "2": {"current_page": 0, "read_status": "reading"}
  }
}
```

**Phase 3 — scan vs. edit collision**
```json
{
  "burst_seconds": 6, "pre_burst_issue_count": 19, "post_burst_issue_count": 19,
  "issue_count_drift": 0, "http_errors_during_burst": [], "server_log_traceback_count": 0
}
```

**Phase 4 — Process All lock holding**
```json
{
  "process_all_status": 200, "process_all_elapsed_s": 1.353, "process_all_body_processed": 19,
  "background_before_batch":  {"count": 20, "errors": 0, "max_elapsed_s": 0.0308, "median_elapsed_s": 0.0272},
  "background_during_batch":  {"count": 22, "errors": 0, "max_elapsed_s": 0.0357, "median_elapsed_s": 0.0107},
  "background_after_batch":   {"count": 22, "errors": 0, "max_elapsed_s": 0.033,  "median_elapsed_s": 0.0243}
}
```

**Phase 5 — reader vs. rebuild collision (5 runs, same 6-reader/1-rebuild-thread setup)**

| Run | Total reads | Errors |
|---|---|---|
| 1 | 1,360 | 1 (client-side `IncompleteRead`/`http.client` crash, harness bug — see below) |
| 2 (harness fixed) | 1,608 | 0 |
| 3 | 1,368 | 1 |
| 4 | 1,518 | 7 |
| 5 | 1,542 | 2 |
| 6 | 1,298 | 2 |

Run 1's reader threads crashed on an uncaught `http.client.IncompleteRead`
instead of recording it as a result — `scripts/_common.py`'s `http_get` was
fixed mid-session to catch this and report a synthetic `599` status instead
of killing the thread (see `SKILL.md` gotcha notes). Runs 3-6 use the fixed
harness; run 2 (0 errors) shows the race doesn't reproduce every single
time, consistent with a genuine timing-dependent collision rather than a
deterministic failure. Server-log excerpts backing the `PermissionError`
and `RuntimeError: Response content shorter than Content-Length` findings
are preserved at `archive/stress-test-2026-07-29/phase5-collision-tracebacks-excerpt.log`
(5 occurrences of the `RuntimeError`, 2 of the `PermissionError`, from a
single 6-second run) — the same two error shapes were also seen in the
original (unpreserved) run-1 log before the harness fix above.

**Phase 6 — combined simulation**
```json
{
  "burst_seconds": 15,
  "requests_by_device": {"tablet": 84, "browser": 210, "desktop_reader": 222, "automation": 8},
  "errors_by_device": {"tablet": 0, "browser": 0, "desktop_reader": 0, "automation": 0},
  "server_log_traceback_count": 0
}
```

</details>

---

## 2. Methodology

See `.claude/skills/stress-test/SKILL.md` for the full phased methodology,
ground rules, and known gotchas. Summary: an isolated scratch copy of
`backend/`/`frontend/` runs as a real second server on port 9427 against a
synthetic, fabricated library — never the real DB, config, or archives.
Six phases test (1) plain concurrent reads as a control, (2) writer-lock
contention on shared rows, (3) scanner-vs-editor collision, (4) Process
All's writer-role hold time, (5) reader-vs-rebuild file collision, and (6)
a combined realistic device simulation.

## 3. Open follow-ups

See "Open follow-ups" under §1 above — kept inline with the baseline that
found them rather than duplicated here, since this is currently the only
baseline. Future re-runs should remove anything a fix resolves and add
anything newly discovered, same convention as `PERFORMANCE.md` §3.
