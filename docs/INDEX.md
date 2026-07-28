# digib00age — Documentation Index

One-page map of every doc in this repo and what it governs. See `CLAUDE.md` Section 2
for the authority-order rule this index follows: a more specific doc wins over a more
general one on conflict (e.g. `EDITOR_SPEC.md` governs editor behaviour over `SPEC.md`);
within a single doc, a later-dated or higher-numbered section overrides an earlier one.

---

## Folder structure (as of 2026-06-29 doc cleanup)

- **`docs/` (root)** — active, not version-scoped: feature specs, `BUGS.md` (open
  only), `ROADMAP.md`, `INBOX.md`, `TESTING.md`, `CHANGELOG.md`, `INDEX.md`.
- **`docs/vN.M/`** — the *current* version's own working set, created fresh each
  version: `comicvault-changes-vN.M.md` (the build queue) and `progress.md`
  (narrative log, scoped to just this version's sessions). When a version closes,
  the whole folder moves into `docs/archive/vN.M/` as one bundle. **v2.5 closed
  2026-07-05** (Items 1–3: ComicTagger + ComicVine integration, Sort by Filename,
  Mobile ↔ Server Reading-State Sync — all built and manually verified).
  **`docs/v2.6/` is the current active version folder**, created 2026-07-06 (Item
  1 — Web UI Redesign — built and closed out 2026-07-08; the folder has stayed
  active since for follow-ups and bug fixes logged against v2.6).
- **`docs/archive/`** (renamed from `historical/` 2026-06-29) — closed-out build
  queues, their matching `progress.md`, one-time setup/research docs, and the fixed
  bug history. **Out of focus, not out of reach** — Code still has full access
  any time something needs revisiting; this folder is a "less
  frequently needed" shelf, not a deleted one.
- **`docs/meta/`** — Claude/working-process docs (not project architecture):
  `working-rules.md`, `voice-and-style.md`, `about-me.md`, `build-plan.html`,
  `roadmap.html`.

`CLAUDE.md` and `README.md` stay at the repo root, outside `docs/` entirely — see
`CLAUDE.md` Section 2 for why.

**Why feature specs aren't version-scoped:** `SPEC.md`, `EDITOR_SPEC.md`,
`CUSTOM_TABS_SPEC.md`, `HOME_STRIPS_SPEC.md`, `MENU_BAR_SPEC.md`, `ADMIN_SPEC.md`,
and the Processing Tools spec describe what the app currently *does*, independent of
which build queue introduced it. They expire when the feature they describe is
replaced or removed — not when a version closes. `ROADMAP.md` and `TESTING.md` are
the same: both span every version by design.

---

## Active / authoritative (not version-scoped)

| Doc | Governs | Status |
|---|---|---|
| `SPEC.md` | V1 architecture — authoritative for web UI / V1 behaviour | V1 complete |
| `EDITOR_SPEC.md` | Editor integration (Basic + Full editor) | Built and verified (2026-06-18) |
| `CUSTOM_TABS_SPEC.md` | Custom Tabs feature | Built and verified (2026-06-19) |
| `HOME_STRIPS_SPEC.md` | Home Page Strips feature | Built and verified (2026-06-19) |
| `ADMIN_SPEC.md` | Admin page — existing behaviour + new items (password, logs, backup scheduling, Processing Tools §11, etc.) | Items 1–13 (admin scope) built and code-verified (2026-06-24/27); manually tested 2026-06-28, one failure — Restore Database, fixed 2026-07-18 (`archive/bugs-fixed-archive.md` BUG-016). §11 Processing Tools all built and manually verified: §11.1 File Rename (v2.4 Item 10, 2026-07-01; queue workflow and Auto-Increment field-wiping bug both corrected 2026-07-02), §11.2 Convert Archives and §11.3 Convert Images (v2.4 Items 12/13, 2026-07-01), §11.4 Processing Folder Automation (v2.4 Item 16, 2026-07-01; scheduler verified correct 2026-07-02 after a false-alarm "not firing" report — see `archive/v2.4/progress.md`; CT Auto-Tag stage added v2.5 Item 1, 2026-07-03/04), §11.5 Sort by Filename (v2.5 Item 2, 2026-07-05, built and manually tested), §11.6 XML Tagging (v2.6 Item 1 Phase C2b, 2026-07-07), §11.7 Move Series Folders / Move Singles Folders (v2.6 Item 10, 2026-07-18, built and manually tested). |
| `MENU_BAR_SPEC.md` | Unified menu bar (sort, filters, search, view toggle) across Flat and Folder View | Built (2026-06-23) |
| `BUGS.md` | Live, **open-only** bug register | Active — **0 open**. **BUG-032 (page routes/`/static` mount sent no `Cache-Control`; the real culprit was the Service Worker's cache-first strategy for page navigations, letting a stale HTML shell survive a same-origin edit) fixed 2026-07-28** — `backend/main.py` gained explicit `no-cache` headers, `frontend/sw.js` switched navigation requests to network-first; verified live via the new `browser-verify` skill — see `archive/bugs-fixed-archive.md`. **BUG-031 (Full Editor Process All wrote Increment # numbers in raw file-arrival order instead of the tree's natural-sorted order) fixed 2026-07-19** — see `archive/bugs-fixed-archive.md`. **BUG-029 (scanner rename/move detection) fixed 2026-07-18** — content-hash matching, forward-only (hashes new/updated files going forward, no retroactive backfill of the existing library — dev DB will be wiped again before production) — see `archive/bugs-fixed-archive.md`, `DECISIONS.md`. **BUG-026/BUG-027 (Clear Database orphaned thumbnails/no VACUUM; no safe DB-reset path) fixed 2026-07-18** — Clear Database now sweeps thumbnails, resets scan logs/timestamps, VACUUMs, and restarts itself automatically (reusing BUG-016's checkpoint/dispose pattern) — see `archive/bugs-fixed-archive.md`, `ADMIN_SPEC.md` §7.4, `DECISIONS.md`. **BUG-016 (Restore Database not reverting DB state — WAL replay) fixed 2026-07-18** — see `archive/bugs-fixed-archive.md`, `ADMIN_SPEC.md` §9.2, `DECISIONS.md`. **BUG-028 (macOS resource-fork entries breaking covers + doubling `page_count`, also found 2026-07-18) fixed same day**; **BUG-013 (scanner missed a same-mtime, different-size re-save) fixed 2026-07-18**, with its rename/move blind spot split out into **BUG-029** (fixed same day, see above) — see `archive/bugs-fixed-archive.md`. Fixed-bug history split out 2026-06-29; BUG-018 fixed 2026-07-02 (off-cycle, after v2.4's close); BUG-019/BUG-020/BUG-008 (Flutter mobile-app connectivity, CBZ-select crash, 2000 AD tab) all fixed 2026-07-04; BUG-017 (Android `.cbz` file association) fixed 2026-07-05; BUG-014/BUG-015 (back-button regression, genre-filter clearing) fixed 2026-07-08; BUG-021 (no working reader outside Flutter) fixed 2026-07-14 (Windows Desktop Reader, v2.6 Item 5). |
| `ROADMAP.md` | Paused/future work, explicitly out of scope until unblocked | Active |
| `INBOX.md` | Raw, untriaged capture (bugs/changes/features) before they're placed in the docs above | Active — see `meta/working-rules.md` for the full workflow |
| `TESTING.md` | Standing verification approach/runbook | Active |
| `PERFORMANCE.md` | Standing performance-diagnostics baseline + reusable methodology (parallel to `TESTING.md`, for speed/load rather than correctness) | Active — three baselines: §1 (2026-07-09, first), §1B (2026-07-18, post-2000 AD move / post-rebuild), §1C (2026-07-26, scanner commit-batching fix + new CT issue-list finding). Raw data for the 2026-07-18 run is in `archive/perf-2026-07-18/`; scripts in `.claude/skills/perf-diagnostics/scripts/`. Baselines append as §1B/§1C so §2–§4 references stay stable |
| `CHANGELOG.md` | Terse one-line-per-entry index, points back to the current version's `progress.md` | Active |

**`admin-spec-section-12-processing-tools.md` retired 2026-07-01** — folded into
`ADMIN_SPEC.md` §11 (renumbered from its own §12.1–§12.4 to §11.1–§11.4) as part of
v2.4 Item 10's build, per the resolution plan settled 2026-06-29. No longer a
separate file; `ADMIN_SPEC.md` is the sole authority for Processing Tools now.

## Reference docs

| Doc | Purpose |
|---|---|
| `INDEX.md` | This file |
| `README.md` | Orientation — how to run things, repo map, where to start reading (repo root, not `docs/`) |
| `DECISIONS.md` | Rationale log — *why*, not *what*, non-obvious calls only. **Pending a dedicated entry-by-entry review (flagged 2026-06-29)** — some entries are closed-chapter, others are standing rationale current specs still point back to; needs sorting before any of it moves to archive. |

## Doc-scan automation (Cowork) — retired 2026-07-12, cancelled for good

Cowork's nightly drift-scan depended on `docs/` being a Google Drive-synced
junction (see `CLAUDE.md` Section 2). That junction has been removed — `docs/`
is now a plain repo folder — and **the scan itself was cancelled and won't be
running again**, not paused pending a replacement. All four files below have
been moved into `docs/archive/` as a point-in-time record; see
`meta/working-rules.md` "Master controller" and "Cowork nightly doc-scan
(retired 2026-07-12)" for the full note. Claude Code is now the master
controller for doc consistency directly — no scanning mechanism in the loop
at all. Session continuity comes from two other layers instead: a
`SessionEnd` hook (personal, cross-project summary capture, outside this
repo) and this project's own doc set (`progress.md`, `CHANGELOG.md`,
`DECISIONS.md`), unchanged from how they've always worked.

## `docs/archive/` — out of focus, not out of reach

Closed-out build queues, their matching `progress.md`, one-time setup/research docs,
and fixed-bug history. Code reads these directly whenever something needs
revisiting — nothing here is gone, it's just not part of the day-to-day working set.

| Doc | What it was for |
|---|---|
| `bugs-fixed-archive.md` | Fixed-bug history, split out of `BUGS.md` 2026-06-29 to keep the live file lean. Not version-scoped — append-only, any fixed bug lands here regardless of which version found or fixed it. |
| `v2.5/comicvault-changes-v2.5.md` | v2.5's build queue — closed 2026-07-05. Item 1 (ComicTagger + ComicVine, 2026-07-04), Item 2 (Sort by Filename, 2026-07-05), Item 3 (Mobile ↔ Server Reading-State Sync, 2026-07-05) all built and manually verified. |
| `v2.5/progress.md` | Narrative build history, scoped to v2.5 sessions (2026-07-03 through 2026-07-05). |
| `v2.4/comicvault-changes-v2.4.md` | v2.4's build queue — closed 2026-07-02. Items 1–7, 9–13, 15–16 built and manually verified; Items 8/14 dropped, superseded by BUG-018 (open, tracked independently — not blocking this close-out). |
| `v2.4/progress.md` | Narrative build history, scoped to v2.4 sessions (2026-06-29 through 2026-07-02) — the first version to use the per-version `progress.md` pattern. |
| `v2.4/code-handoffs/bug-018-nested-comicinfo-scanner-fix.md` | BUG-018's scoped fix plan — moved here with the rest of the v2.4 folder; the bug itself stays open and tracked in `BUGS.md`, unaffected by the archive move. |
| `v2.3/comicvault-changes-v2.3.md` | v2.3's build queue — closed 2026-06-29. Items 1–13 built; Item 14 moved to `ROADMAP.md`. |
| `v2.3/progress.md` | Full project narrative history through v2.3's close (covers V1 through v2.3 — predates the per-version `progress.md` pattern, which starts with v2.4). |
| `v2.3/2.3-testing-notes.md` | Manual test pass notes from the 2026-06-26 v2.3 test session |
| `v2.3/2.3-fixes.md` | The 9 post-test fixes implemented same day as the above, 2026-06-26 |
| `comicvault-changes-2.1.md` | Planning backlog / build queue, 2.1 — closed out 2026-06-22 |
| `comicvault-changes-v2.2.md` | v2.2: remove 2000 AD fixed tab + Folder View for Custom Tabs — closed out 2026-06-22 |
| `cowork-doc-scan-instructions.md` | The nightly-scan instruction text last pasted into Cowork's scheduled-task config, dated 2026-06-29. Moved here 2026-07-12 when the scan itself was retired (see "Doc-scan automation (Cowork) — retired" above) — point-in-time record only. |
| `v2_investigation_report.md` | Pre-port investigation of the standalone CAPT metadata editor (architecture, bugs, what was worth porting). Referenced by `EDITOR_SPEC.md` §1 for background. |
| `flutter-ui-sync-plan.md` | Gap analysis + prioritized task list for syncing Flutter's library card UI to the web redesign, generated 2026-07-23. Closed out 2026-07-28 (see its own "Closing status" section) — most of it shipped via Tez's own direct ask (`mobile-reader-changes.txt`, closed in `INBOX.md`) rather than by working this doc's list in order; Folder View (its largest item) fully built; a couple of real gaps found during the closeout review (list-view read overlay, Singles progress-percent using page-level data like the web does) were fixed same session. Several of the doc's own web-parity ideas (genre ribbon, card rating stars, flag badge, etc.) were never actually requested and were left unbuilt on purpose. |
| `V2_MIGRATION_SETUP.md` | One-time filesystem/git task: clone V1 into the `comicvault_v2` folder and repoint to its own GitHub remote. Executed 2026-06-18. |
| `V2_FOLLOWUP_COMMIT_AND_SCANNER_FIX.md` | One-time follow-up: commit migration housekeeping + fix the scanner thumbnail-skip bug (`bugs-fixed-archive.md` BUG-001). Executed 2026-06-18. |
| `pre_migration_report.csv` | Data artifact, not a doc — output of `backend/editor/migration_report.py`'s one-time data-hygiene scan. |
| `doc-scan-issues.md` | Append-only log of drift/contradictions Cowork's nightly scan found, back when that scan ran. Retired 2026-07-12 alongside the Drive junction it depended on. |
| `doc-scan-issues-archive.md` | Sunday-prune archive of the above. |
| `doc-scan-state.md` | Cowork's internal scan-state tracking (last-scanned timestamps etc.) — dead now the scan is retired. |
| `cowork-notes.md` | Cowork session log from when Cowork had direct Drive access to `docs/`. |

`comicvault-changes-2.1.md` (renamed from `comicvault-changes.md` on close-out) itself
supersedes a now-removed file, `v2_1-main-new-features.md`, that `CUSTOM_TABS_SPEC.md`
and `HOME_STRIPS_SPEC.md` used to point to — if you find an older reference to either
filename anywhere, treat it as a typo for `comicvault-changes-2.1.md`.

**Historical note (found 2026-06-27, moot since the 2026-07-12 scan retirement):** a
closed-out doc dropping out of the active scan meant anything it was quietly still
tracking (e.g. the Admin Card Size control, found at the bottom of
`comicvault-changes-2.1.md`, never carried into `ADMIN_SPEC.md` until backfilled
2026-06-27) could sit invisible indefinitely, since Cowork's scan only re-checked
*changed* files. No live scan exists anymore, so this specific gap no longer
applies — kept here as a lesson if any future drift-checking mechanism gets built.

## `docs/meta/` — Claude-facing process docs, not project architecture

| Doc | Purpose |
|---|---|
| `CLAUDE.md` | Session instructions — how Claude Code sessions on this repo should run. Read before any other doc. Lives at the repo root, not in `docs/meta/` — see `CLAUDE.md` Section 2. |
| `working-rules.md` | Shared working habits and conventions for how Claude and Tez operate on this project — decision-making, doc structure, inbox workflow, quality bar, scope discipline. Claude Code should read this and update it if working practices change. |
| `voice-and-style.md` | How docs/communication should read |
| `about-me.md` | Background context on Tez relevant to how sessions run |
| `build-plan.html` | Visual build tracker for the current active version — open in browser, tick items off as built. State persists via localStorage. Claude Code should update the item list here when a build round closes out or new items are added to the current `comicvault-changes-vN.M.md`. |
| `roadmap.html` | Now / Next / Later / Launch visual roadmap — sequence, not dates. Regenerated wholesale at each triage session (never hand-edited piecemeal), and revisited after a Code session if it changes what's Now or Next. See `meta/working-rules.md` for when/how it updates. |
