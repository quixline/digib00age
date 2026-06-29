# ComicVault — Documentation Index

One-page map of every doc in this repo and what it governs. See `CLAUDE.md` Section 2
for the authority-order rule this index follows: a more specific doc wins over a more
general one on conflict (e.g. `EDITOR_SPEC.md` governs editor behaviour over `SPEC.md`);
within a single doc, a later-dated or higher-numbered section overrides an earlier one.

---

## Folder structure (as of 2026-06-29 doc cleanup)

- **`docs/` (root)** — active, not version-scoped: feature specs, `BUGS.md` (open
  only), `ROADMAP.md`, `INBOX.md`, `TESTING.md`, `CHANGELOG.md`, `INDEX.md`. In
  scope for Cowork's nightly scan.
- **`docs/vN.M/`** — the *current* version's own working set, created fresh each
  version: `comicvault-changes-vN.M.md` (the build queue) and `progress.md`
  (narrative log, scoped to just this version's sessions). When a version closes,
  the whole folder moves into `docs/archive/vN.M/` as one bundle. Currently:
  `docs/v2.4/`.
- **`docs/archive/`** (renamed from `historical/` 2026-06-29) — closed-out build
  queues, their matching `progress.md`, one-time setup/research docs, and the fixed
  bug history. **Out of focus for Cowork's nightly scan, not out of reach** —
  Code and Chat both still have full access any time something needs revisiting;
  this folder is a "less frequently needed" shelf, not a deleted one.
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
| `ADMIN_SPEC.md` | Admin page — existing behaviour + new items (password, logs, backup scheduling, etc.) | Items 1–13 (admin scope) built and code-verified (2026-06-24/27); manually tested 2026-06-28, one failure — Restore Database (`BUGS.md` BUG-016) |
| `admin-spec-section-12-processing-tools.md` | Processing Tools (§12) — File Rename fully scoped 2026-06-27 | §12.1 File Rename is v2.4 Item 1, ready for Code. Convert/Convert Images/Flatten not yet scoped. Orphan fragment — see note below. |
| `MENU_BAR_SPEC.md` | Unified menu bar (sort, filters, search, view toggle) across Flat and Folder View | Built (2026-06-23) |
| `BUGS.md` | Live, **open-only** bug register | Active — 5 open (BUG-016, 015, 014, 013, 008). Fixed-bug history split out 2026-06-29, see `archive/bugs-fixed-archive.md` |
| `ROADMAP.md` | Paused/future work, explicitly out of scope until unblocked | Active |
| `INBOX.md` | Raw, untriaged capture (bugs/changes/features) before they're placed in the docs above | Active — see `meta/working-rules.md` for the full workflow |
| `TESTING.md` | Standing verification approach/runbook | Active |
| `CHANGELOG.md` | Terse one-line-per-entry index, points back to the current version's `progress.md` | Active |

*`admin-spec-section-12-processing-tools.md` is logically part of `ADMIN_SPEC.md` §12
but lives as a separate file — treat as authoritative for §12 until it's merged into
`ADMIN_SPEC.md` proper. Flagged as a pending cleanup item, not a contradiction.*

## `docs/v2.4/` — current version's working set

| Doc | Purpose | Status |
|---|---|---|
| `comicvault-changes-v2.4.md` | v2.4: active build queue | Item 1 (File Rename Tool) scoped, ready for Code. No items built yet. |
| `progress.md` | Narrative build history, scoped to v2.4 sessions only | Active, append-only, just started 2026-06-29 |

## Reference docs

| Doc | Purpose |
|---|---|
| `INDEX.md` | This file |
| `README.md` | Orientation — how to run things, repo map, where to start reading (repo root, not `docs/`) |
| `DECISIONS.md` | Rationale log — *why*, not *what*, non-obvious calls only. **Pending a dedicated entry-by-entry review (flagged 2026-06-29)** — some entries are closed-chapter, others are standing rationale current specs still point back to; needs sorting before any of it moves to archive. |

## Doc-scan automation (Cowork)

| Doc | Purpose |
|---|---|
| `doc-scan-issues.md` | Append-only log of drift/contradictions Cowork's nightly scan finds. Sunday prune to `doc-scan-issues-archive.md`. |
| `doc-scan-state.md` | Cowork's internal scan-state tracking (last-scanned timestamps etc.) |
| `cowork-notes.md` | Cowork session log |

Cowork's actual scheduled-task instructions live in the Cowork task config itself, not
in this folder — see `archive/cowork-doc-scan-instructions.md` for the most recent
copy pasted in (2026-06-28), kept as a point-in-time record only.

## `docs/archive/` — out of focus, not out of reach

Closed-out build queues, their matching `progress.md`, one-time setup/research docs,
and fixed-bug history. **Excluded from Cowork's nightly scan** by default, but Code
and Chat read these directly whenever something needs revisiting — nothing here is
gone, it's just not part of the day-to-day working set.

| Doc | What it was for |
|---|---|
| `bugs-fixed-archive.md` | Fixed-bug history, split out of `BUGS.md` 2026-06-29 to keep the live file lean. Not version-scoped — append-only, any fixed bug lands here regardless of which version found or fixed it. |
| `v2.3/comicvault-changes-v2.3.md` | v2.3's build queue — closed 2026-06-29. Items 1–13 built; Item 14 moved to `ROADMAP.md`. |
| `v2.3/progress.md` | Full project narrative history through v2.3's close (covers V1 through v2.3 — predates the per-version `progress.md` pattern, which starts with v2.4). |
| `v2.3/2.3-testing-notes.md` | Manual test pass notes from the 2026-06-26 v2.3 test session |
| `v2.3/2.3-fixes.md` | The 9 post-test fixes implemented same day as the above, 2026-06-26 |
| `comicvault-changes-2.1.md` | Planning backlog / build queue, 2.1 — closed out 2026-06-22 |
| `comicvault-changes-v2.2.md` | v2.2: remove 2000 AD fixed tab + Folder View for Custom Tabs — closed out 2026-06-22 |
| `cowork-doc-scan-instructions.md` | The instruction text pasted into Cowork's live scheduled-task config on 2026-06-28. Archived once copied over — the live copy lives in the Cowork task itself, not here; this file is a point-in-time record, not something to keep editing. |
| `v2_investigation_report.md` | Pre-port investigation of the standalone CAPT metadata editor (architecture, bugs, what was worth porting). Referenced by `EDITOR_SPEC.md` §1 for background. |
| `V2_MIGRATION_SETUP.md` | One-time filesystem/git task: clone V1 into the `comicvault_v2` folder and repoint to its own GitHub remote. Executed 2026-06-18. |
| `V2_FOLLOWUP_COMMIT_AND_SCANNER_FIX.md` | One-time follow-up: commit migration housekeeping + fix the scanner thumbnail-skip bug (`bugs-fixed-archive.md` BUG-001). Executed 2026-06-18. |
| `pre_migration_report.csv` | Data artifact, not a doc — output of `backend/editor/migration_report.py`'s one-time data-hygiene scan. |

`comicvault-changes-2.1.md` (renamed from `comicvault-changes.md` on close-out) itself
supersedes a now-removed file, `v2_1-main-new-features.md`, that `CUSTOM_TABS_SPEC.md`
and `HOME_STRIPS_SPEC.md` used to point to — if you find an older reference to either
filename anywhere, treat it as a typo for `comicvault-changes-2.1.md`.

**Known gap (found 2026-06-27, not yet fully addressed):** a closed-out doc dropping
out of the active scan means anything it was quietly still tracking (e.g. the Admin
Card Size control, found at the bottom of `comicvault-changes-2.1.md`, never carried
into `ADMIN_SPEC.md` until backfilled 2026-06-27) can sit invisible indefinitely.
Cowork's scan only re-checks *changed* files — a closed doc that stops changing drops
out of scope permanently. No fix in place yet; flagged for a dedicated pass.

## `docs/meta/` — Claude-facing process docs, not project architecture

| Doc | Purpose |
|---|---|
| `CLAUDE.md` | Session instructions — how Claude Code sessions on this repo should run. Read before any other doc. Lives at the repo root, not in `docs/meta/` — see `CLAUDE.md` Section 2. |
| `working-rules.md` | Shared working habits and conventions for how Claude and Tez operate on this project — decision-making, doc structure, inbox workflow, quality bar, scope discipline. Claude Code should read this and update it if working practices change. |
| `voice-and-style.md` | How docs/communication should read |
| `about-me.md` | Background context on Tez relevant to how sessions run |
| `build-plan.html` | Visual build tracker for the current active version — open in browser, tick items off as built. State persists via localStorage. Claude Code should update the item list here when a build round closes out or new items are added to the current `comicvault-changes-vN.M.md`. |
| `roadmap.html` | Now / Next / Later / Launch visual roadmap — sequence, not dates. Regenerated wholesale at each triage session (never hand-edited piecemeal), and revisited after a Code session if it changes what's Now or Next. See `meta/working-rules.md` for when/how it updates. |
