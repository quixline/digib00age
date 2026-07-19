# ComicVault — Performance Test Plan, 2026-07-18

Zoom-out plan for the post-2000-AD-move re-baseline. Written before running
anything, because the pre-flight check found the DB and disk are out of sync
in a way that would silently corrupt every number this session produces.

Companion to `docs/PERFORMANCE.md` (the dated baseline history) and
`.claude/skills/perf-diagnostics/` (the reusable method). This plan does not
replace either — it sequences one specific run.

---

## 0. What the pre-flight check found

All read-only, no writes, before any measurement phase ran.

| Fact | Value | Source |
|---|---|---|
| Issues in DB (`missing=0`) | 5,424 | `issues` table |
| Distinct series | 2,089 | `issues` table |
| Rows flagged `missing=1` | **0** | `issues` table |
| 2000 AD rows in DB | 2,484 — **all** with `file_path` under `L:\Comic Archives\20000AD\2000AD Progs - 1977-2026\` | `issues` table |
| That old directory on disk | **Does not exist** | filesystem |
| 2000 AD files at the new location | **2,490** under `L:\Comic Archives\#\Series\2000 AD` | filesystem |
| Random 400-issue path sample | **177 dead paths (44%)**, all 2000 AD | filesystem |
| Thumbnails on disk | 7,904 for 5,424 issues (was 5,436 for 5,427 at baseline) | filesystem |
| `custom_tabs` | 1 row, pointing at the old dead folder path | `custom_tabs` table |
| `reading_progress` | 5,424 rows — **33 read, 2 with `current_page > 0`** | `reading_progress` table |

**Net:** every 2000 AD issue in the library is currently unopenable, and the
Folder View tab points at a path that no longer exists.

---

## 1. The scanner will not repair this

This was the assumption worth checking, and it doesn't hold. From
`backend/scanner.py`:

- `scan_single_file()` identifies an existing row **solely** by exact path:
  `db.query(Issue).filter(Issue.file_path == file_path).first()`. There is no
  hash, no filename fallback, no move/rename detection anywhere in the file.
- Any path with no matching row takes the `# INSERT` branch → a brand-new
  `Issue`, new metadata parse, new thumbnail.
- The post-walk sweep in `scan_library()` takes every `missing=0` row not
  found in `disk_paths` and sets `issue.missing = True`. It does **not**
  delete them (deletion only happens for paths inside `SCAN_EXCLUDE`
  folders).

**So a plain scan right now produces:** 2,490 new rows + 2,484 old rows
flagged missing = **7,914 issue rows, ~2,484 of them dead**, plus ~2,490 more
thumbnails on top of the 7,904 already there, and 2000 AD's reading progress
stranded on the orphaned rows.

That's not a state to measure performance against, and not a state to leave
the library in.

---

## 2. Recommendation: wipe and rebuild, and make that *be* the scanner test

Your instinct to wipe was right, and the numbers make it near-free:
**only 33 issues are marked read and 2 have a saved page position.** That is
the entire irreplaceable content of the DB. Everything else — metadata,
genres, credits, thumbnails — is derived from the archives and regenerates.

The bonus: a from-scratch scan of ~5,430 files is *exactly* the measurement
`docs/PERFORMANCE.md` §3 has been carrying as an open follow-up since
2026-07-09 — "scanner at real scale never measured; all 18 historical log
entries were near-no-op incremental runs." Doing the repair and the
measurement as one instrumented run kills both.

### Before the wipe (cheap insurance, ~1 min)

1. Copy `backend\comicvault_v2.db` → `comicvault_v2.db.bak-2026-07-18`.
2. Export the 33 read + 2 in-progress rows to JSON, keyed on **file path**
   (not issue ID, since IDs won't survive) so they can be re-applied after.
3. Note the 1 `custom_tabs` row's settings so you can recreate the tab
   against `L:\Comic Archives\#\Series\2000 AD`.
4. Snapshot `L:` file count + total bytes, to prove afterwards that nothing
   was written to the archives.

---

## 3. Phase order

Sequencing matters more than usual here: the scan itself warms the OS file
cache across the whole library, which contaminates any cold-read measurement
taken after it.

| # | Phase | Why here | Writes? |
|---|---|---|---|
| 0 | Backup + progress export + `L:` snapshot | Insurance | Local only |
| 1 | **Raw I/O baseline** (`1_raw_io_baseline.py`, sampling live paths from disk, not the stale DB) | Must run **before** the scan warms the cache | No |
| 2 | **Wipe DB + instrumented full scan** | The headline new measurement | DB + thumbnails |
| 3 | **Cold-server-restart first-request timing** | Only valid immediately post-restart, before anything warms it | No |
| 4 | Refresh targets (`0_find_targets.py`) → update `TARGETS` in scripts 3/4/5 | IDs will all have changed after the wipe | No |
| 5 | In-process query counts (`3_query_counts.py`) | Cleanest N+1 regression signal | No |
| 6 | HTTP timing (`4_http_timing.py`), page-serving isolation (`5_`), cover grid (`6_`) | Warm-server comparison vs 2026-07-09 | No |
| 7 | Browser waterfall via claude-in-chrome | Real-user sanity check | No |
| 8 | Write dated baseline into `docs/PERFORMANCE.md` | Output convention | Docs |
| 9 | Verify: numbers vs raw output, no source edits, `L:` unchanged | Trust the result | No |

Skipped by your call: the cold-idle drive probe (10-15 min of wall-clock
waiting per rep, finding #9 stays inconclusive).

---

## 4. What the scanner run should actually capture

The historical log only records wall-clock duration, which is why 18 entries
told us nothing. This run should record, at minimum:

- Total duration and **files/second**, plus a breakdown of new/updated/
  skipped/missing/errors.
- Per-file cost split into: archive open + metadata parse, thumbnail
  generation, DB commit. The baseline notes "up to 3 archive-opens per new/
  changed file" from code inspection — this run either confirms or kills that.
- Cost distribution by file size, since the library spans ~5MB to 500MB+ and
  a mean would be meaningless.
- Whether the per-file commit pattern (`db.commit()` inside `scan_single_file`
  for every single file) is a material cost at 5,430 files — a plausible
  finding this run may surface.

---

## 5. Open questions for you

1. **`home_strips` (4 rows)** — is that user-configured homepage layout you'd
   want preserved across the wipe, or is it seeded defaults that regenerate?
   I haven't touched it.
2. **How to wipe** — is there an existing "reset library" path in the app or
   tray launcher you'd rather use than me deleting the DB file and letting
   the app recreate the schema on boot?
3. **The 7,904 thumbnails** — after the wipe the new IDs won't match any of
   them, so they're all orphans and the scan regenerates from scratch. Clear
   the folder first (cleaner, and makes the scan timing honest) or leave them
   and sweep later?
4. **The real bug underneath this** — the move tool updates
   `series_move_log.md` and moves files, but doesn't update `issues.file_path`
   or `custom_tabs.folder_path`. That's a correctness issue, not a
   performance one, and per the perf-diagnostics skill's hard rules it's out
   of scope for this session. Worth a `BUGS.md` entry so the next move
   doesn't do this again?
