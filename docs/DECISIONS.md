# ComicVault — Decisions Log

Rationale log — *why*, not *what*. Only non-obvious calls go here; routine
implementation choices are covered in `SPEC.md` / `EDITOR_SPEC.md` / the feature
specs and aren't repeated. Newest first.

---

### A scratch DB copy's `file_path` values still point at real, shared files — and ids aren't stable across separate scratch copies
**Decided:** 2026-06-21, during Tier 4 Item 3 Session C verification.
**Why:** Two related mistakes compounded into a real incident. (1) A "scratch DB" is
a disposable copy of the *metadata*, but every `Issue.file_path` inside it still
points at the one real, physical CBZ file on disk — there's only one copy of the
actual library. Testing any feature that *writes to the file* (the metadata editor's
save, specifically) through a scratch DB copy is therefore not actually scratch-safe
the way testing a DB-only feature is — it needs a genuinely fake, disposable CBZ
file with its own throwaway DB row instead. (2) Separately and compoundingly: this
session had already learned, and written down, that Person/Issue ids aren't stable
across different scratch-copy/migration runs — only names are — but a Playwright
test was built using a *remembered* issue id from an earlier scratch copy in the
same session, without re-querying what that id actually pointed to in the *current*
copy. It pointed at a different real file than assumed. Caught immediately via the
discrepancy between "no file changed" (checked the wrong filename) and the DB
showing a real update; root-caused by building a true fake-CBZ fixture and
reproducing the save cleanly, which also definitively proved the actual code path
has no bug — the mistake was entirely in how the test was constructed, not in the
feature being tested. Full incident account in `progress.md` "Session — 2026-06-21:
Tier 4 Item 3 — Session C".
**Where:** No code change — a testing-practice decision. Going forward: any test
that exercises a file-writing endpoint (the editor's save, archive rebuild, etc.)
uses a dedicated fake CBZ + throwaway DB row, never a real `file_path` borrowed from
a copied DB, scratch or otherwise. Always re-query an id's actual identity in the
copy being tested against, rather than reusing one remembered from a different copy.

### Live working-tree edits must stop the running server first, on high-risk sessions
**Decided:** 2026-06-21, during Tier 4 Item 3 (Writer/Artist dedup).
**Why:** Editing `backend/models.py`/`database.py`/`scanner.py` directly in the live
repo, while the actual running ComicVault server was up, let that server pick up the
new code on its own restart (unrelated to anything this session did) and write real
data via not-yet-fully-verified logic — breaking an explicit "this session never
touches the real DB" agreement. The scratch-DB isolation built into this session's
own test scripts protected nothing about the live, already-running process, which
reads shared source files off disk independent of any session's intentions. Tez's
call: for the rest of high-risk sessions like this one, stop the live server before
touching shared source files, rather than the more involved option of isolating the
work in a separate git worktree.
**Where:** Full incident account in `progress.md` "Session — 2026-06-21: Tier 4 Item
3". No code change — a working-practice decision for future sessions.

### One shared `role`-column junction table, not 6 per-role tables, for credit entities
**Decided:** 2026-06-21, building Tier 4 Item 3 (Writer/Artist dedup).
**Why:** `IssueGenre`'s per-field pattern (one junction table, denormalized string
value) doesn't fit people — a Person needs one stable id referenceable across all 6
credit roles (someone can be writer on one issue, colorist on another), which a
6-table split would multiply migration/sync/query code six-fold for no benefit. One
`IssueCredit` table with a `role` column serves both "browse by person across all
roles" (the click-through use case) and "filter by a specific role" equally well.
**Where:** `backend/models.py` `Person`/`IssueCredit`.

### Old raw CSV credit columns kept temporarily after the Writer/Artist migration
**Decided:** 2026-06-21, building Tier 4 Item 3.
**Why:** Dropping `Issue.writer`/`penciller`/etc. immediately (matching exactly how
Genre has no raw column at all) would be a one-way door on a 5,429-row production
table — if the new `people`/`issue_credits` data turns out subtly wrong after the
fact, the original raw strings are gone and the only recovery path is a full DB
restore. Keeping the columns inert for one release cycle costs nothing but a little
schema clutter and gives a free, instant cross-check path if anything's ever found
wrong. Drop them in a separate later session once the new system has run for real
with no issues found.
**Where:** `backend/models.py` (`Issue`'s 6 credit columns, now unused by read
paths once Session C lands), `backend/scanner.py` `_apply_metadata()`.

### `create_all()` doesn't add columns to an existing table — additive-schema assumption corrected
**Decided:** 2026-06-21, building Tier 4 Item 2 (Multi-select + Favorites/Rating).
**Why:** `comicvault-changes.md` assumed the new `favorites`/`personal_rating` Issue
fields would need "no migration of existing data" the same way CustomTab/HomeStrip
didn't — but those were whole new *tables*, and SQLAlchemy's `Base.metadata.create_all()`
only creates tables that don't exist yet; it never diffs columns on a table that's
already there. Proved this with a throwaway SQLite file before writing any real code
(column stayed absent from `PRAGMA table_info` after `create_all()` re-ran with the
column added to the model). This is the first time this project's "additive fields
need no migration" assumption didn't hold — first real additive *column* on an
existing table, as opposed to a new table. Fixed with a small idempotent
`ALTER TABLE` step in `init_db()`, verified against a scratch copy of the real
~5,500-row DB before trusting it.
**Where:** `backend/database.py` `_add_missing_issue_columns()`, `SPEC.md` §7 / §21.

### Bulk endpoints over a client-side fetch loop, for the multi-select toolbar
**Decided:** 2026-06-21, building Tier 4 Item 2.
**Why:** The series-detail page's existing "Mark all read" button (`markAllRead()`)
loops `Promise.allSettled()` over one `fetch()` per issue — fine for that button's
existing scope, but a multi-select bulk action could cover many more cards at once, so
N round-trips don't scale the same way. Built real bulk endpoints
(`POST /api/progress/bulk/...`) instead, following the existing
`PATCH /api/admin/home-strips/reorder` pattern (fetch all matching rows in one query,
loop, single `db.commit()`). `markAllRead()` itself was left untouched — a separate,
already-shipped feature, not retrofitted to the new endpoints.
**Where:** `backend/routers/progress.py` bulk endpoints, `frontend/js/app.js`
`runBulkAction()`.

### Auto-save confirmation message — dropped, deferred to admin redesign
**Decided:** 2026-06-20, reconciling `comicvault-changes.md` against `DECISIONS.md`.
**Why:** Originally planned for both Custom Tabs and Home Strips admin sections
(UI-consistency assumption — three sections, three buttons — not a functional need;
both already auto-save on every action, confirmed by direct testing). Purely
cosmetic, and the whole admin area is slated for a redesign once remaining
functionality work is done — adding a one-off message now would likely be redone
anyway. Deferred to that redesign rather than tracked as a standalone backlog item.
**Where:** `comicvault-changes.md` Tier 3 (item removed), `CUSTOM_TABS_SPEC.md` /
`HOME_STRIPS_SPEC.md` admin sections (future redesign).

### ComicInfo.xml is the sole source of truth when MetronInfo.xml also exists
**Decided:** 2026-06-20, discovered via `thanksgiving.cbz` / `tales of ruination.cbz`
already being in the library with both XML schemas present.
**Why:** The editor (`EDITOR_SPEC.md` §3.1/3.5) only ever reads/writes ComicInfo.xml —
it was never designed to reconcile two metadata schemas. Originally assumed to be rare
pre-library debris and folded into the Full Editor's existing multi-XML detection as a
test case; turned out to affect files **already scanned into the library**, where
`EDITOR_SPEC.md` §3.5 explicitly assumed "the existing library is already known to be
clean." That assumption is now known to be false. Rather than build dual-schema
reconciliation, ComicInfo.xml is confirmed as the single authoritative source —
matches the editor's existing scope exactly, no new logic needed. MetronInfo.xml is
treated as stale/ignorable wherever both exist. Confirmed working as designed for new
intake (Full Editor's side-by-side picker already lets Tez choose per-file before a
comic ever reaches the DB) — the gap was only ever already-scanned library files.
Cleanup of those handled via a one-off script run outside this project, not a
ComicVault feature (script should be report-first/dry-run, only act where ComicInfo.xml
is actually present and valid, to avoid stripping the only metadata source from a file
that happens to only have MetronInfo.xml).
**Where:** `EDITOR_SPEC.md` §3.5 (assumption correction below), cleanup via external
script — no project code changes.

### Writer/Artist: people table + search/link, not an enforced dropdown
**Decided:** sequencing/design confirmed across multiple sessions, formalized in
`comicvault-changes.md` Tier 4 Item 3.
**Why:** Genre/Format got the dropdown fix because each issue carries one short,
single value from a small fixed vocabulary. Writer/Artist are different on two counts:
(1) they're multi-value per issue — anthology titles (2000 AD, etc.) credit many
contributors on one issue, so a dropdown can't represent "this issue's credits" as a
single selectable value the way Genre/Format can; (2) even a fully deduplicated list of
individual names would be too long to be a usable dropdown — it's a search problem, not
a selection-from-a-short-list problem. Both issues point to the same fix: a real people
table (solves duplicate-name data integrity, e.g. spelling variants of the same person)
plus search + click-through linking (solves the UI volume problem), same pattern as the
clickable Genre tags on `/issue/{id}`. Sequenced last because it requires a one-time
migration/merge pass across ~5,500 real issues — highest risk item in the backlog,
needs its own short spec before any code is written.
**Where:** `comicvault-changes.md` Tier 4 Item 3.

### Genre/Format admin-list deletion: confirm-with-count, hard-block on emptying the list
**Decided:** 2026-06-20, building the Genre/Format admin editor (`comicvault-changes.md`
Tier 4 Item 1).
**Why:** Both fields are enforced, non-blank-required per issue. A silent delete could
orphan hundreds of issues' worth of tagging with no warning; an emptied list would make
every future save fail validation with no valid option left to pick. Confirm-with-count
mirrors the existing Custom Tabs delete pattern rather than inventing a new one.
**Where:** `backend/editor/editable_lists.py`, `frontend/js/admin.js`.

### Format flipped from locked constant to admin-editable list
**Decided:** 2026-06-20, reversing `EDITOR_SPEC.md` Section 4.2's original "locked,
no editing mechanism needed" call.
**Why:** Tier 5 cleanup (adding Anthology/Comic/Omnibus to Genre) was blocked on having
an admin editor at all, and the original rationale for locking Format ("the list
shouldn't change") turned out not to hold — Tez needed to add values for real library
data. Mirrors Genre's existing file-backed-list mechanism rather than building a second
pattern.
**Where:** `EDITOR_SPEC.md` §4.2 deviation note, `backend/editor/formats.json`.

### Home Strips' cap is on total stored strips, not just visible
**Decided:** during Home Strips build, 2026-06-19.
**Why:** Custom Tabs caps *visible* tabs (4) because the cost is nav-bar space — hidden
tabs are free. Home Strips caps *total* (5) because the cost is a DB query per strip on
every home-page load, whether visible or not — hiding a strip doesn't remove its cost.
Recorded here because the two caps look like the same rule by analogy and aren't —
a future session "fixing" Home Strips to match Custom Tabs' visible-only cap would
reintroduce a real performance problem.
**Where:** `HOME_STRIPS_SPEC.md` §3 vs `CUSTOM_TABS_SPEC.md` §3.

### Editor sync: webhook → in-process call
**Decided:** evolved across the V1→V2 editor integration (2026-06-18).
**Why:** V1's `SPEC.md` described the metadata editor as a separate Flask process that
called `POST /api/scan/file` over HTTP to tell ComicVault to rescan a changed file —
necessary because the two apps were genuinely separate processes on separate ports.
Once the editor's logic was ported into the same FastAPI app (`EDITOR_SPEC.md` §6.1),
the same rescan became a plain in-process function call — no HTTP round-trip, no
separate port. This is *why* any documentation written before 2026-06-18 (the original
`README.md`) describing a webhook/separate-app architecture is now wrong, not just
out of date.
**Where:** `SPEC.md` §17 (original) vs `EDITOR_SPEC.md` §6.1 (current).

### Genre/Format enforced dropdowns instead of free text
**Decided:** during editor integration design, `EDITOR_SPEC.md` §4.1.
**Why:** Direct fix for a real CAPT bug — its "dropdown" was actually free-text with
autocomplete suggestions and never validated anything, which is how the library ended
up with inconsistent values needing a pre-migration cleanup pass in the first place.
**Where:** `EDITOR_SPEC.md` §4.1, `backend/editor/validation.py`.

### Full Editor uses a server-side path picker, not browser file upload
**Decided:** `EDITOR_SPEC.md` §5.1 correction log, 2026-06-18.
**Why:** Browsers never expose a real filesystem path for an uploaded file, and the
editor needs to write a rebuilt archive back to a real path on disk — uploaded bytes
would have nowhere correct to land. Ported CAPT's existing server-side directory
browser instead of building a new upload-based flow.
**Where:** `EDITOR_SPEC.md` §5.1.

### Editor core: full overwrite + full archive rebuild, not incremental patching
**Decided:** `EDITOR_SPEC.md` §3.2/3.3, during editor-core porting.
**Why:** Simplicity-over-performance trade, deliberately — the collection isn't large
enough per-file for save latency to matter, and a full rebuild is more robust against
partial-write corruption than in-place patching. Every editor-exposed XML tag is fully
overwritten on save; tags the editor doesn't expose are preserved untouched rather than
merged field-by-field.
**Where:** `EDITOR_SPEC.md` §3.2 (archive rebuild), §3.3 (XML field merge).

### Format-group ("Series" vs "Singles") comes from folder path, not the XML Format field
**Decided:** V1 scanner design, `SPEC.md` §6.
**Why:** The XML `Format` field (Graphic Novel, One Shot, etc.) and the folder-based
Series/Singles split are answering different questions — where a comic *physically
lives* in the library vs. what *kind* of release it is. Using the folder path for
routing means moving a file between folders changes its routing immediately, without
needing an edit to its metadata.
**Where:** `SPEC.md` §6, `backend/scanner.py` `_format_group()`.

### Flutter over a web-based reader for the mobile/tablet app
**Decided:** mid-V1-build deviation, `SPEC.md` §21 change log.
**Why:** A web reader couldn't satisfy the "installed app" requirement on Android, and
a single Flutter codebase covers both Android and Windows rather than building two
separate native readers.
**Where:** `SPEC.md` §21 change log (2026-06-12 entry), `flutter_app/`.
