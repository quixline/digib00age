# ComicVault — Documentation Index

One-page map of every doc in this repo and what it governs. See `CLAUDE.md` Section 2
for the authority-order rule this index follows: a more specific doc wins over a more
general one on conflict (e.g. `EDITOR_SPEC.md` governs editor behaviour over `SPEC.md`);
within a single doc, a later-dated or higher-numbered section overrides an earlier one.

---

## Active / authoritative

| Doc | Governs | Status |
|---|---|---|
| `SPEC.md` | V1 architecture — authoritative for web UI / V1 behaviour | V1 complete |
| `EDITOR_SPEC.md` | Editor integration (Basic + Full editor) | Built and verified (2026-06-18) |
| `CUSTOM_TABS_SPEC.md` | Custom Tabs feature | Built and verified (2026-06-19) |
| `HOME_STRIPS_SPEC.md` | Home Page Strips feature | Built and verified (2026-06-19) |
| `comicvault-changes-2.1.md` | Planning backlog / build queue, 2.1 — closed out 2026-06-22, kept for history | Closed |
| `BUGS.md` | Live bug/issue register (separate from applied-decision logs) | Active |
| `progress.md` | Narrative build history, per-session detail and verification notes | Active, append-only |

`comicvault-changes-2.1.md` (renamed from `comicvault-changes.md` on close-out) itself
supersedes a now-removed file, `v2_1-main-new-features.md`, that `CUSTOM_TABS_SPEC.md`
and `HOME_STRIPS_SPEC.md` used to point to — if you find an older reference to either
filename anywhere, treat it as a typo for `comicvault-changes-2.1.md`. A successor doc,
`comicvault-changes-2.2.md`, will become the active planning reference once Tez creates
it — until then, there is no active backlog doc; check with Tez for what's next.

## Reference docs (this index + the five built alongside it, 2026-06-20)

| Doc | Purpose |
|---|---|
| `INDEX.md` | This file |
| `README.md` | Orientation — how to run things, repo map, where to start reading |
| `CHANGELOG.md` | Terse one-line-per-entry index, points back to `progress.md` |
| `DECISIONS.md` | Rationale log — *why*, not *what*, non-obvious calls only |
| `ROADMAP.md` | Paused/future work, explicitly out of scope until unblocked |
| `TESTING.md` | Standing verification approach/runbook |

## Historical only — not governing anything going forward

These were one-time setup/research docs, already executed. Kept for reference in case
the reasoning behind a past decision is needed again; do not treat as current.

| Doc | What it was for |
|---|---|
| `v2_investigation_report.md` | Pre-port investigation of the standalone CAPT metadata editor (architecture, bugs, what was worth porting). Referenced by `EDITOR_SPEC.md` §1 for background. |
| `V2_MIGRATION_SETUP.md` | One-time filesystem/git task: clone V1 into the `comicvault_v2` folder and repoint to its own GitHub remote. Executed 2026-06-18. |
| `V2_FOLLOWUP_COMMIT_AND_SCANNER_FIX.md` | One-time follow-up: commit migration housekeeping + fix the scanner thumbnail-skip bug (now `BUGS.md` BUG-001, fixed). Executed 2026-06-18. |
| `pre_migration_report.csv` | Data artifact, not a doc — output of `backend/editor/migration_report.py`'s one-time data-hygiene scan. |

## Meta

| Doc | Purpose |
|---|---|
| `CLAUDE.md` | Session instructions — how Claude Code sessions on this repo should run. Read before any other doc. |
