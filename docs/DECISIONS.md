# ComicVault — Decisions Log

Rationale log — *why*, not *what*. Only non-obvious calls go here; routine
implementation choices are covered in `SPEC.md` / `EDITOR_SPEC.md` / the feature
specs and aren't repeated. Newest first.

### v2.4 Item 10/15 — File Rename dropped from Processing Folder Automation

**Decided:** 2026-07-01, dedicated re-scoping session (Chat + Tez).
**Why:** Item 15 flagged §12.1 File Rename as needing a bigger re-scope before Item
10 could build, on the assumption automation needed a saved naming-convention
template system. Before building that, the session tested the actual parser
(`filename_parser.py`) against two real filename sets pulled from the library (323
periodical-style releases, 319 creator-prefixed OGN/collection files) rather than
reasoning about it in the abstract.

That testing found the re-scope's real problem wasn't missing features, it was a
live bug: `extract_year()` has a hardcoded `present_year = 2025` validity ceiling,
so every 2026-dated file silently fails year extraction — which cascades into
series/issue extraction failing too, since a rejected year's bracket never gets
stripped from the series string. Measured against the sample: 64% failure rate.
Two smaller bugs also found (a zero-issue string collapsing to empty via
`lstrip('0')`; whitespace/text artifacts left behind by volume+subtitle patterns
like `v05 - Twisting Loyalties`). All three are fixed in the §12.1.3 Change Log.

The creator-prefixed sample also confirmed something structural, not a bug:
`"Cyberpunk 2077 - Chrome 03"` and `"Abby Howard - The Crossroads at Midnight"` are
structurally identical strings to a regex parser — there's no reliable way to know
one is an umbrella-series/sub-title pair and the other is an author/book-title
pair. Trying to auto-split these was the actual source of "too many variables" —
the fix wasn't smarter parsing, it was accepting the parser can't resolve this
class of ambiguity and routing it to the existing manual Title field + All
checkbox instead (which already existed for exactly this purpose).

Once that was settled, the automation question answered itself: Rename's *only*
correction mechanism is the human reviewing its live preview before committing (no
undo — §12.1.6). That's specifically the thing Processing Folder Automation
removes by running unattended. And the ambiguous Series/Title cases above need a
human decision no saved template could supply — automating Rename would mean
silently applying the "good enough" fallback output to every file that would have
benefited from a manual Title entry, with no signal in the log distinguishing which
files got which treatment. Tez agreed dropping Rename from automation entirely was
the right call rather than trying to make both work — matches the session's
recurring theme of catching scope before it compounded (see "Pattern worth naming"
below).

**Knock-on effect:** §12.4 Processing Folder Automation is amended from a
three-stage to a two-stage pipeline (Convert Archives → Convert Images). The
saved-naming-convention-template requirement raised in Item 15 scoping (`INBOX.md`)
is dropped entirely, not deferred — nothing to build. `INBOX.md`'s §12.1 re-scope
entry is struck as resolved; the separate §12.2 backup-model re-scope entry is
unrelated to this decision and remains open.

**Pattern worth naming:** the session started as "make the rename parser smarter"
and nearly expanded to cover ComicTagger-integration timing and XML-driven
renaming before Tez caught it and pulled back to KISS. The eventual real fix (one
hardcoded constant) was far smaller than the scope that was almost built instead —
worth remembering next time a "just needs to be smarter" feeling shows up: test
against real data before assuming the gap is in the logic rather than a stale
constant or a genuinely unparseable ambiguity.

### v2.4 Item 8 — Flatten Archive dropped, reclassified as BUG-018

**Decided:** 2026-06-30, mid-scoping session (Chat + Code).
**Why:** Item 8 went in as a routine CAPT-tool port, same pattern as Items 6/7.
Scoping it started with the normal "why does this tool exist" check, and Tez
couldn't recall the original reason — he knew he'd built Flatten Archive for a
concrete problem, just not which one. Handed to Code to investigate; Code traced
it to a real, still-open scanner bug (BUG-018, `BUGS.md`): `_parse_cbz()` only
matches `ComicInfo.xml` at the zip root, so archives with the xml nested inside a
subfolder import with filename-guessed metadata instead of real data. That
symptom — exactly what a Flatten tool would visually "fix" by restructuring the
archive — was the actual reason the tool got built originally.

Once that was clear, the question stopped being "how do we scope this tool" and
became "does this tool still have a job once the bug's fixed." It doesn't:
editors already read nested xml correctly (`find_xml_in_archive()` matches any
depth) and already flatten on save (`_rebuild_archive()`, existing behavior,
unchanged) — so a fixed scanner means nested archives import correctly without
any manual intervention, and editing one (for any reason) flattens it as a side
effect anyway. Confirmed with Tez no independent use case survives this (e.g. no
bulk-hygiene or Flutter-local-mode need distinct from the bug). Item 8 and Item
14 (its build counterpart) are both struck from `comicvault-changes-v2.4.md`
rather than scoped/built.

**Knock-on effect:** Item 15 (Processing Folder Automation) listed Item 8 as a
hard dependency and counted Flatten Archive as one of four CAPT tools it would
orchestrate unattended. With Item 8 gone, Item 15's dependency note was revised
to drop that blocker — it now depends only on Items 10–13. Whether unattended
automation still needs a flatten step (and if so, calling `_rebuild_archive`
directly the way Item 7 already does, with no standalone tool behind it) is left
for Item 15's own scoping session, not decided here.

**Pattern worth naming:** a CAPT tool's original existence is itself a strong
signal there was a real problem behind it — "why was this built" is now a
standing first question for any remaining unscoped CAPT-tool item, not just a
one-off for Item 8.

### v2.4 Item 5 — CBR support reversed back in, EPUB and PDF dropped from scope

**Decided:** 2026-06-30, eng-review + scoping session (Chat).
**Why:** Item 5 went in scoped as one decision ("add CBR/PDF/EPUB"). An eng-review
pass before scoping (`/eng-review`) surfaced that each format is actually a
separate problem with a different right answer, and that two of the original three
had a materially cheaper existing solution the original scope didn't weigh against
native support — read `cap_toolkit/processors/arc_conv_cb_proc.py` and
`arc_conv_pdf_proc.py` directly before concluding this, both already exist and
work.
- **EPUB dropped entirely.** Confirmed with Tez it was a speculative carry-over
  from another app, not a confirmed need, and the sample file he has (HTML pages +
  cover.jpg inside a plain archive) doesn't generalize to the EPUB spec anyway.
  Structurally incompatible with the page-indexed reading model every other part
  of the app depends on (`page_count`, `/issue/{id}/pages`,
  `/page/{issue_id}/{page_number}`, Flutter's `comic_page_view.dart`) — supporting
  it for real would mean a second, genuinely different reader, not an extension of
  the existing one. Too much cost for a feature that was never confirmed wanted.
- **PDF dropped from native scanner/library scope**, redirected entirely to CAPT's
  existing PDF↔CBZ converter (delete-original option already built) plus the Full
  Editor for tagging. PDF has no ComicInfo.xml-equivalent metadata standard —
  natively indexed, every PDF would land `metadata_source = "filename"` with none
  of the genre/writer/story-arc filtering working. Converting first gets a fully-
  capable CBZ for free; native PDF support would have meant real scanner/thumbnail
  work for a permanently second-class result.
- **CBR reinstated as full native support, read-only at the archive level.** The
  original "library is all-CBZ" decision (`EDITOR_SPEC.md` §2/§9, made when CAPT
  was ported) was correct *for that scope* — personal project, already-converted
  collection. It no longer fits the current goal: Tez's thinking has shifted toward
  a possible public release, and he knows from seeing other users' collections that
  large mixed CBZ/CBR libraries are common (some over 100,000 issues). Forcing a
  bulk pre-conversion before the library is even browsable isn't viable at that
  scale or for a public audience who didn't curate their collection the way Tez
  curated his own.
  - **Read CBR everywhere, never write it.** `rarfile` (extraction-only) is already
    a proven dependency via CAPT's own CBR↔CBZ converter — no new library, and no
    `7-Zip` dependency either, contrary to the original v2.4 doc's note (verified
    by reading `arc_conv_helpers.py` directly: it's `rarfile`/`unrar` for
    extraction, a `rar` CLI shell-out for creation).
  - **Why never write:** RAR archive *creation* requires a paid WinRAR install —
    confirmed by reading `create_rar_archive()`, which shells out to `rar` and
    raises if it's missing. That's not a dependency a public app can carry.
  - **So editing a CBR's metadata rebuilds it as `.cbz`, not `.cbr`.** This isn't
    new code — the editor's rebuild path (`shutil.make_archive(..., "zip", ...)`)
    already only ever produces a zip, even before this change. Adding CBR support
    only meant adding a `rarfile` *read* branch; the existing rebuild path needed
    no change at all, it just now sometimes has a `.cbr` source feeding into the
    same zip-only output. Confirmed with Tez this applies uniformly across Basic
    Editor, Full Editor single-file, and Full Editor batch/Process All — no
    per-surface exception.
  - **Net effect, confirmed as the actual goal:** a user's library is fully
    browsable/readable on day one regardless of CBZ/CBR mix, no bulk conversion
    required: the library trends toward all-CBZ over time as files happen to get
    edited, rather than needing a separate batch-conversion pass.
  - **Known accepted gap:** Flutter local/offline mode (the `archive` Dart package
    has no RAR support) won't open a `.cbr` copied to a device for travel reading.
    Server mode is unaffected — page-serving already abstracts the container format
    away from the client. Left for whoever revisits Mobile Reader work
    (`ROADMAP.md` "Paused indefinitely"), not addressed by this item.
**Where:** `SPEC.md` §6/§6.1/§7/§13/§17/§21, `EDITOR_SPEC.md` §2/§3.1/3.2/§9 +
Change Log, `v2.4/comicvault-changes-v2.4.md` Item 5/11.

### v2.4 Item 3 (empty-results logo) extended to all emoji empty/error states

**Decided:** 2026-06-29, build session (Code), Tez's explicit call after seeing
the original item work.
**Why:** Item 3 as scoped only covered the "No comics match these filters."
state's `📚` icon. Once built and manually tested, the same `.empty-icon`
pattern turned out to cover 10 more states in `app.js` — some genuinely
"no content" (`📚` on "No content yet."), others error/warning states (`⚠️`
on server-unreachable, search failure, series/issue not found, etc.). Tez
asked for the same logo swap across all of them rather than leaving a mix of
emoji and logo. This is a judgment call worth a paper trail specifically
because it repurposes the logo for warning/error states too, not just
"library has nothing to show" — a different semantic than the original item
text described, decided live rather than scoped in advance.
**Where:** `frontend/js/app.js` (11 spots total), `frontend/css/style.css`
(`.empty-logo` class, shared by all of them). See `v2.4/progress.md` "Session
— 2026-06-29: v2.4 Item 3" for the full list of states touched.

### BUG-016 root cause confirmed; INBOX.md, ROADMAP.md/INDEX.md/roadmap.html reconciled with the 2026-06-28 manual test pass

**Decided:** 2026-06-28, doc-handling review session (Chat).
**Why:** BUG-016 (Restore Database) was logged with two competing theories —
connection-teardown race vs. path mismatch. Read `backend/database.py` and
`backend/routers/admin.py` directly: confirmed it's neither a race nor a path bug.
SQLite runs in WAL mode (`PRAGMA journal_mode=WAL`); `restore_database()` copies the
backup over the main `.db` file but never clears the existing `-wal`/`-shm` sidecar
files, so writes made after the backup (sitting in the pre-restore WAL) get replayed
back in on the next connection, undoing the restore. Path mismatch ruled out —
`db_path` resolves identically in both the restore and backup functions. Confidence
is now "confirmed by reading the exact mechanism," not "plausible theory" — worth
noting for whoever picks up the fix, since the recommended fix (checkpoint + clear
WAL files before the copy) follows directly from this, not from further
investigation.
**Where:** `BUGS.md` BUG-016 (root cause section rewritten, old hedge removed).
Also reconciled `INDEX.md` and `meta/roadmap.html`, which still said "10–13 not yet
manually tested" — stale relative to the test pass another session had already run
and logged; `ROADMAP.md` and `comicvault-changes-v2.3.md` were already current.
`INBOX.md`'s "Unprocessed" section also turned out to be fully triaged already (every
line had a destination annotation) — moved to "Processed" under a new "Triaged
2026-06-28" heading; no actual triage decisions were needed, just the move.

---

### Doc folder restructure (`docs/historical/`, `docs/meta/`) + CLAUDE.md status-line fix + git tag convention

**Decided:** 2026-06-28, doc-handling review session (Chat).
**Why:** Two separate problems surfaced together. (1) Cowork's nightly scan only
rechecks *changed* files — a closed-out doc that stops changing drops out of scope
permanently, so anything it was quietly still tracking (e.g. Admin Card Size, found
at the bottom of `comicvault-changes-2.1.md`, never carried into `ADMIN_SPEC.md`
until backfilled 2026-06-27) can sit invisible indefinitely. Splitting closed-out/
one-time docs into `docs/historical/` makes "out of scope" mechanical (a path Cowork
can skip by rule) rather than something relying on per-file judgement — doesn't fix
the omission-detection gap itself (flagged in `INDEX.md`'s historical section as
still open), but stops the folder from growing more ambiguous. (2) `CLAUDE.md`
Section 5 had been silently hardcoding the active feature name ("Custom Tabs (done)
→ Home Strips (in progress)") since before v2.2 even existed — the same failure
shape as `doc-scan-issues.md` ISSUE-005/006/007 (a status fact restated in a second
place, with no automated check on this particular copy since Cowork doesn't read
`CLAUDE.md`). Fixed by having Section 5 point at `comicvault-changes-vN.M.md`'s own
status block instead of restating it, removing the redundant copy rather than just
refreshing it. Also added a git tag convention (tag `vN.M` on build-queue close-out)
rather than adopting finer-grained SemVer-style versioning — the project has one
deployment and one user, so there's no compatibility surface that finer granularity
would serve; the existing doc version label just needed an actual git ref tied to it.
**Where:** `INDEX.md` (folder structure section, full doc table), `CLAUDE.md`
(Section 2 doc table + folder note, Section 5 rewritten, Section 7 git tag
convention added), `meta/working-rules.md` (new Versioning section). `meta/
build-plan.html` also moved from `historical/` to `meta/` during the same pass —
it's the live build tracker, not a closed-out doc, and was misfiled in the initial
move.

---

### v2.3 Item 14 moved to `ROADMAP.md`; v2.3 kept open rather than formally closed

**Decided:** 2026-06-28, doc-handling review session (Chat).
**Why:** Item 14 (site-wide header unification) is blocked on the same dependency
(Claude Design UI redesign direction) as an existing `ROADMAP.md` item, so it no
longer belongs in an active build queue — moved there, merged with that context,
rather than sitting in `comicvault-changes-v2.3.md` looking like queued work. Tez's
call on the broader question (is v2.3 "done"): explicitly **not** closing it out
despite Items 1–13 being complete — `INBOX.md` still has unprocessed items that
might reasonably land under v2.3 once triaged, and closing the doc now would force
a premature decision about where those go. Separately noted but not yet acted on:
Items 10–13 were each Code-verified live in their own session but never went
through the kind of dedicated manual test pass Items 1–9 got — flagged to Tez,
especially Item 12 (Restore Database), where Code's own session notes confirm the
actual restore-and-restart path was never exercised against a real file.
**Where:** `comicvault-changes-v2.3.md` Item 14 entry (now a pointer),
`ROADMAP.md` (new "Blocked on Claude Design UI redesign exploration" section),
`ADMIN_SPEC.md` status block, `INDEX.md` (two rows).

---

### Doc folder restructure round two: `historical/` → `archive/`, per-version `docs/vN.M/` working folders, `BUGS.md` split (open vs. fixed), v2.3 fully consolidated, v2.4 started

**Decided:** 2026-06-29, doc-handling review session (Chat), refining the
2026-06-28 restructure above.
**Why:** As the project grows, the root doc set keeps growing too — more token
cost per session, more surface area for drift. Tez's first instinct was to archive
everything except `ADMIN_SPEC.md`, the Processing Tools spec, and the cowork docs.
Pushed back on that specifically: feature specs (`SPEC.md`, `EDITOR_SPEC.md`,
`CUSTOM_TABS_SPEC.md`, `HOME_STRIPS_SPEC.md`, `MENU_BAR_SPEC.md`), `ROADMAP.md`, and
`TESTING.md` describe what the app currently *does* or standing process — they're
not version-scoped, and archiving them the moment a build queue closes would mean
every spec goes stale-by-relocation on every release, forcing future sessions to
re-derive current behaviour from source instead of reading a maintained reference.
Landed on a narrower, sharper cut instead:
- **`historical/` renamed `archive/`** — same contents, different framing: "out of
  focus, not out of mind." Code/Chat retain full read access any time something
  needs revisiting; only Cowork's nightly scan treats it as out of scope.
- **`docs/vN.M/` working folders**, new pattern starting with v2.4 — each version
  gets its own `comicvault-changes-vN.M.md` + scoped `progress.md`, bundled
  together and moved into `archive/vN.M/` as one unit on close. Bundling (not
  separately rotating each file) means a version's full story stays in one place.
- **`BUGS.md` split into open-only (stays at `docs/` root) + `archive/
  bugs-fixed-archive.md`** (flat, not version-scoped — a bug found in one version
  can get fixed in a later one, so tying its fixed record to either version's
  folder would be the wrong cut). 11 fixed entries moved out 2026-06-29, leaving 5
  open (`BUGS.md` BUG-016/015/014/013/008).
- **v2.3 fully consolidated into `archive/v2.3/`**: its build queue, the full
  pre-v2.4 `progress.md` (covers V1 through v2.3 — predates the per-version
  pattern, archived as one snapshot rather than split further), and the
  2026-06-26 test-session artifacts.
- **`comicvault-changes-v2.4.md` created**, Item 1 = File Rename Tool (already
  fully scoped in `admin-spec-section-12-processing-tools.md` §12.1).
- **`ROADMAP.md` cleanup, same pass:** removed two already-resolved sections (port
  8000 workaround, BUG-003) that had accumulated informal "edit: Tez, fixed" notes
  instead of being removed; corrected a stale `ADMIN_SPEC.md` section reference for
  Rename (was §11.1, now §12.1); flagged an unresolved ambiguity rather than
  guessing — a note in the file said "13 added to bugs.md" but Item 13 (Card Size)
  passed its test; the actual `BUGS.md` entry is Item 12. Tez confirmed Card Size
  was never a bug but couldn't explain the mismatch — left as an open flag, not
  resolved here. Also flagged Tier 5's Genre-additions/draw.io-video items as
  unconfirmed (only the `.ico` item got an explicit answer: deferred, not done).
- **`DECISIONS.md` deliberately not touched** — flagged in `INDEX.md` as needing
  its own entry-by-entry pass (some entries are closed-chapter, others are standing
  rationale current specs still point back to) rather than a blanket move.
**Where:** `docs/historical/` → `docs/archive/`, `docs/archive/v2.3/` (new,
consolidated), `docs/v2.4/` (new), `BUGS.md` (trimmed), `archive/
bugs-fixed-archive.md` (new), `ROADMAP.md`, `INDEX.md`, `CLAUDE.md` (Section 2
table + folder note, Section 4 checklist, Section 5, Section 7), `meta/
working-rules.md` (doc-structure section rewritten), `meta/roadmap.html` (Now/Next
lanes updated, bug count), `CHANGELOG.md` (intro note on which `progress.md` old
vs. new entries point to).

---

### Restore Database: auto-snapshot the current DB before every restore

**Decided:** 2026-06-27, Item 12 scoping session.
**Why:** Restore is strictly more destructive than Clear Database (§7.4) — it
replaces the entire DB file, including Custom Tabs/Home Strips that Clear Database
deliberately preserves — and has no undo once committed. Tez's call: take a
throwaway snapshot of the *current* DB (reusing the existing `run_database_backup()`
helper already shared by manual + scheduled backup, so this is a filename, not new
code) immediately before overwriting it. "Can't hurt and extra safety is worth it."
**Where:** `comicvault-changes-v2.3.md` Item 12.

### BUG-014: root cause is the four main surface tabs never updating the URL, not a regression of the Tier 1 back-button fix

**Decided:** 2026-06-27, found while scoping `comicvault-changes-v2.3.md` Item 14
(read `app.js`/`issue.html`/`series.html` directly rather than guessing).
**Why:** Initially logged as a possible regression of the Tier 1 fix
(`comicvault-changes-2.1.md`, 2026-06-21/22). Direct code reading showed that fix
is still intact — `initIssue()`/`initSeries()` correctly call `window.history.back()`.
The real gap: the four main surface tabs (Home/All/Singles/Series) never call
`pushState`, so the URL never reflects which tab is active, while Folder View
already does this correctly via `pushFolderViewUrl()`. Recorded as a decision rather
than just a bug note because it reframes the fix — extend an existing, proven
pattern to the main tabs, not write a new one — and because it links BUG-014 and
Item 14 (header unification) as one piece of work rather than two.
**Where:** `BUGS.md` BUG-014, `comicvault-changes-v2.3.md` Item 14.

### Inbox triage 2026-06-27: treated as v2.3 continuation, not a v2.3 close-out + v2.4 open

**Decided:** 2026-06-27, inbox triage session (`doc-scan-issues.md` ISSUE-007 follow-up).
**Why:** Tez's explicit call — before closing out v2.3 (all 9 original items built and
manually tested 2026-06-26), the 7 new inbox lines were folded in as Items 10–14 of
the same `comicvault-changes-v2.3.md` queue rather than starting a fresh
`comicvault-changes-v2.4.md`. v2.3 stays "Active" until Items 10–14 are also built.
**Where:** `comicvault-changes-v2.3.md` (status block, Items 10–14), `INDEX.md`,
`ROADMAP.md` active-queue line.

### BUG-014: three back-button reports merged into one regression entry

**Decided:** 2026-06-27, inbox triage session.
**Why:** Three separate inbox lines (`?from=all`, `?from=series`, `?from=singles`)
all described the identical symptom — back navigation landing on Home instead of
the originating tab. Logged as one `BUGS.md` entry with three repro cases rather
than three separate bug numbers, and explicitly flagged as a **regression** of the
Tier 1 "Back button inconsistency" fix already closed out twice in
`comicvault-changes-2.1.md` (2026-06-21, then a follow-up correction 2026-06-22) —
worth flagging as a regression rather than a fresh bug, since it changes what Code
needs to check first (did the old fix get undone, vs. is this a new code path the
old fix never covered).
**Where:** `BUGS.md` BUG-014.

### File Rename: in-app picker, no recursion, per-field checkbox independence, narrow auto-increment scope, no undo

**Decided:** 2026-06-27, dedicated Rename scoping session.
**Why:** Several deliberate departures from precedent worth recording the reasoning
for, not just the outcome (full detail lives in `ADMIN_SPEC.md` §11.1, this is the
*why*):
- **In-app folder-tree picker, not a native OS dialog** — breaks the pattern set by
  the Scheduled Backup folder picker (§9), which gets away with a native dialog only
  because frontend and backend currently share a machine. That assumption doesn't
  hold under Remote Administration (the dialog would pop open on the server's own
  screen, not the remote browser), so Rename uses the same in-app HTTP/JSON picker
  pattern as the Editor and Custom Tabs instead.
- **No recursion into subfolders** — a deliberate divergence from both CAPT's
  original `rglob()` behaviour and the Editor's recursive folder-add, to keep a
  batch rename scoped to exactly what the user can see when they select a folder.
- **Per-field File/All checkbox independence, no column auto-select** — fixes a real
  CAPT bug where ticking one File (or All) checkbox auto-selected the entire column
  regardless of field.
- **Auto-Increment Issue Numbers gated specifically on Issue→All**, not any-All
  checkbox — fixes another CAPT bug where it activated regardless of which field's
  All box was ticked.
- **No undo** — consistent with the tool being a basic audit log, not a transaction
  system; the live preview is the only safety net before committing, matching
  CAPT's own behaviour.
**Where:** `ADMIN_SPEC.md` §11.1.1–§11.1.6.

---

### Clear Database scope: library data only, not Custom Tabs/Home Strips; same confirm() as Delete Tab; local-only gate

**Decided:** 2026-06-24, Item 9 build session.
**Why:** `ADMIN_SPEC.md` §7.4's literal wording ("wipes all records from the DB")
doesn't say whether Custom Tabs / Home Strip configuration counts as "all
records." Checked the schema directly: neither table has any FK relationship to
Issue, so wiping Issues has zero effect on them either way — the real question
was whether to *also* write code to explicitly delete them. Tez's call: library
data only (issues, genres, credits, reading progress, the now-orphaned People
rows) — Custom Tabs/Home Strips stay intact, since a "start fresh" library reset
shouldn't force rebuilding unrelated nav/home-page configuration.

Confirmation: the spec says "confirmation warning/modal," but Tez confirmed
reusing the exact same plain `confirm()` mechanism already used for deleting a
Custom Tab, not a custom modal — consistency with existing UX over literal spec
wording.

Gating: both Clear Database and Clear Reading Progress got the same
`is_local_request()` gate already used for Restart Server and the backup folder
dialog, on top of the existing blanket admin-password gate — a full library wipe
was judged at least as disruptive as either of those, and shouldn't be
triggerable over an authenticated Remote Administration session.

**Where:** `backend/routers/admin.py`'s `clear_database()` / `clear_reading_progress()`.

### Backup destination uses a native OS folder dialog, not the existing library-scoped picker

**Decided:** 2026-06-24, Item 8 build session.
**Why:** `ADMIN_SPEC.md` §9 originally said the backup folder picker should reuse
"the same mechanism as the Scan Roots Add button / Full Editor's path picker."
Checked both existing browse endpoints (`GET /api/admin/browse`,
`GET /editor/full/browse`) directly — both hard-reject any path outside the
configured library roots. A backup destination is explicitly meant to live
*outside* the library (a different drive, USB, or cloud-sync folder), so that
restriction makes the existing picker unusable here, not just inconvenient.

Tez's direction: use a real native OS folder dialog instead, opened by the
backend itself. This works because frontend and backend always run on the same
machine for this app — `tkinter.filedialog.askdirectory()` (stdlib, no new
dependency) run in a thread executor so it doesn't block the async event loop.
Gated to local-only sessions (`is_local_request()`, same helper already built
for the admin password feature) since a remote-admin session would otherwise
pop the dialog open on the server machine, not the remote user's screen — a
confusing, effectively broken result for that one case.

**Where:** `backend/routers/admin.py`'s `browse_folder_dialog()` /
`_show_folder_dialog()`.

### Server port change restarts via deliberate self-exit, relying on the tray app's existing crash-recovery

**Decided:** 2026-06-24, Item 8 build session.
**Why:** `reader_port` is read once at process start (`backend/config.py`'s
module-level `READER_PORT` constant, plus `start_server.py`'s `uvicorn.run()`
call) — there's no live-rebind path, a real process restart is required.
Rather than building new restart-orchestration code, `POST /api/admin/restart`
just saves the new port then calls `os._exit(0)` after a short delay (long
enough for the HTTP response to actually reach the client). The tray app's
`tray/tray_app.py` `health_check_loop()` already auto-relaunches the reader
subprocess on any unexpected exit — and a freshly-spawned process reads
`config.json` from scratch, picking up the new port with zero extra code.

Confirmed by live testing: when the server isn't running under the tray app
(e.g. started directly via `uvicorn`, as in this session's own scratch
verification), the process exits and **stays down** — there's no other
supervisor to relaunch it. This is a known, accepted limitation: the user gets
the same "you need to restart it" outcome either way, just automatically under
the tray app and manually otherwise. The frontend shows a confirmation dialog
before submitting a port change (it disconnects active LAN users) and the
field's hint text states the restart consequence up front.

**Where:** `backend/routers/admin.py`'s `restart_server()`,
`frontend/js/admin.js`'s `initServerPort()`.

### Backup frequency dict separate from the Auto Scan frequency dict

**Decided:** 2026-06-24, Item 8 build session.
**Why:** `ADMIN_SPEC.md` §9's 22 backup intervals (down to 1hr/2hr/4hr
granularity, up to 12 months) don't overlap cleanly with §4's 8-option scan
frequency set. Built a second `_BACKUP_FREQUENCY_SECONDS` dict in
`backend/scheduler.py` and a parallel `backup_loop()` following the exact same
polling/skip/re-read-config pattern as `auto_scan_loop()`, rather than trying
to force one shared frequency vocabulary onto two features with different
granularity needs.

**Where:** `backend/scheduler.py`.

### Scan log truncation, last-viewed state, and Explorer-reveal — Item 7 judgment calls

**Decided:** 2026-06-24, Item 7 build session.
**Why:** Three small implementation choices `ADMIN_SPEC.md` §4/§8 left open:

1. **Log truncation** — when a log file exceeds its configured size limit, the
   oldest ~10% of lines are dropped and the file rewritten, rather than rotating
   to `.1`/`.2` backups. The spec doesn't mention rotation, and a single
   append-only file that quietly drops its oldest entries is simpler and matches
   the "log", not "archive", framing of the feature.
2. **Last-viewed state** (drives each card's green-border indicator) lives in
   `config.json`'s new `log_last_viewed` object rather than a separate state
   file — it's UI state, but small and config-shaped, and reuses
   `config.save_config()` directly with no new file format to introduce.
3. **"View Logs Folder"** displays/copies the path rather than having the
   backend call `os.startfile()` to open Explorer directly. Even though this
   app always runs frontend and backend on the same machine (so it would work),
   no precedent exists yet for a web API spawning a native OS window, and
   display+copy achieves the same practical outcome without introducing one.

**Where:** `backend/scan_logs.py` (truncation), `backend/routers/admin.py`
(`mark_log_viewed`, `get_logs_folder_path`), `frontend/js/admin.js`
(`initLogsSection()`).

### `autostart_scan` config key reused verbatim for "Scan on launch"

**Decided:** 2026-06-24, Item 7 build session.
**Why:** `config.json` already had an `autostart_scan: false` key, present since
an earlier session but read nowhere in the codebase — clearly a stub left for
exactly this feature. Reused it directly for ADMIN_SPEC.md §4's "Scan on
launch" checkbox rather than introducing a new, differently-named key.

**Where:** `backend/scheduler.py`'s `maybe_scan_on_launch()`,
`frontend/admin.html`'s `#scanOnLaunchCheckbox`.

### Admin password gate: client-side popup instead of server-side redirect; global fetch wrap for 401 interception

**Decided:** 2026-06-24, Item 6 build session.
**Why:** `ADMIN_SPEC.md` §7.1.2 says an unauthenticated page request is "shown the
password popup." Two ways to get there: (a) always serve the page HTML/JS and let a
JS bootstrap show a blocking overlay if unauthenticated, or (b) check the session
cookie server-side in `main.py`'s page routes and redirect to a dedicated login page.
(b) is more airtight (unauthenticated HTML/JS never reaches the browser) but this
codebase has no templating engine — page routes are plain `FileResponse` — so it would
need a new login page and a redirect-back-after-login flow. Chose (a): simpler, reuses
one popup component for both page bootstraps and API 401s, and the actual security
cost is minor given the spec's own threat model (closed home LAN, not defending
against a hostile client reading static JS).

To catch 401s from every caller — `apiFetch()` in `app.js` plus the many raw
`fetch()` call sites in `editor_basic.js`/`editor_full.js` — without rewriting each
one, `auth.js` monkey-patches `window.fetch` globally to watch for 401 responses and
trigger the login popup. This is more "magic" than this codebase's usual explicit
style, but the alternative (touching dozens of call sites) was judged more invasive
and more error-prone to keep in sync over time.

After a successful login, the popup does a full `location.reload()` rather than
transparently retrying the original failed request — simpler given the interception
point doesn't have a handle back to the original caller's promise chain.

**Where:** `ADMIN_SPEC.md` §7.1/§7.2. Implementation: `frontend/js/auth.js`,
`frontend/login_popup.html`, `backend/auth.py` (`require_admin_auth` dependency, not
global middleware — kept per-router so the gate stays auditable per `main.py`'s
router-registration block, and so `/api/editor/genres`/`/formats` are caught
alongside the issue-specific editor routes without special-casing a path regex).

### Disabling password protection clears the stored hash outright

**Decided:** 2026-06-24, Item 6 build session.
**Why:** `ADMIN_SPEC.md` §7.1.1 says the stored hash "may remain on disk" after
disabling — ambiguous on whether enforcement state needs its own separate flag.
Chose to clear `admin_password_hash`/`admin_password_salt` on disable instead, so
`is_protection_enabled()` stays a one-line "hash present" check rather than needing a
second boolean to keep in sync (especially relevant given §7.1.1's force-disable-
remote-admin rule already has to update two fields atomically).

**Where:** `backend/routers/admin_auth.py`'s `disable_protection`.

### Multi-select scope corrected to include Series and Singles aggregate cards

**Decided:** 2026-06-23, inbox triage.
**Why:** Original scoping (`SPEC.md` §20.15, `comicvault-changes.md` Tier 4 Item 2)
deliberately limited card-hold multi-select to elements that map 1:1 to a single
issue — Singles surface cards, series-detail issue rows, Folder View flat file cards.
Series-aggregate cards were explicitly excluded on the reasoning that Favorites should
apply at the issue level and that a bulk action's meaning across a whole series
(mark read? favorite? rate?) would be ambiguous.

After using the library in practice, Tez found issue-only selection too limiting —
Series and Singles cards should be selectable on the same terms as issues, with the
same read/unread/favorite/rate bulk actions available. The "ambiguous meaning across
many issues" concern was weighed and overridden: bulk-marking a series as read or
favourited is a natural, common action and the ambiguity argument applies equally to
the existing "Mark all read" series-detail button, which has always been there and is
never confusing in practice.

**Where:** `SPEC.md` §20.15 (scope boundary definition) — treat this entry as the
correction before implementation begins. `SPEC.md` §20.15's explicit exclusion of
Series-aggregate cards is superseded by this decision.

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

### Menu bar redesign: treated Item 2's inline bullets as the complete sort spec
**Decided:** 2026-06-23, start of v2.3 build plan Item 2.
**Why:** `comicvault-changes-v2.3.md` Item 2 pointed to a "sort controls section
below" that doesn't exist anywhere in the doc — a dangling cross-reference, not an
intentional placeholder. Rather than pause the session to draft that missing section,
Tez chose to proceed using Item 2's own bullet list (A–Z / Newest / Recent / # of
Issues / # of Pages + ascend/descend toggle) together with `MENU_BAR_SPEC.md` as the
full spec.
**Where:** `comicvault-changes-v2.3.md` Item 2, `MENU_BAR_SPEC.md`.

### Convert Archives: background-job progress instead of Rename's blocking pattern
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** Rename's apply step blocks the request and shows a summary modal at the
end, which works because renaming is a near-instant string operation. Archive
conversion does real per-file work (extract, rezip, PDF page rasterization at
300 DPI) that can take meaningful time over a batch — a blocking request risked
long hangs or timeouts on larger batches. Rather than invent new infrastructure,
reused the module-level progress-singleton + polling-endpoint pattern
`backend/scanner.py` already established for scan jobs.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2.5, `backend/scanner.py`
`scan_progress`.

### Convert Archives: CBR CRC errors surfaced, not silently skipped
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** CAPT's original RAR extraction silently drops unreadable pages and still
reports the conversion as a clean success. That's inconsistent with the
no-partial-silent-failure principle already established for Rename (§12.1.6) —
carrying it over unchanged would mean a damaged CBR could convert to an
incomplete CBZ with no indication anything was lost. Kept the tolerant
extraction itself (still produces a CBZ rather than failing outright) but added
a `pages_skipped` count surfaced in both the result summary and the audit log.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2.4.

### Convert Archives: PDF render DPI as an isolated constant, not an Admin setting
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** CAPT's original PDF→CBZ rendering used 72 DPI (`fitz.Matrix(1,1)`),
which produces visibly blurry pages compared to native CBR/CBZ scans, and isn't
fixable after the fact short of re-converting from the source PDF. Raised to 300
DPI (Tez's call, print-scan-grade sharpness over file size). Deliberately kept as
a single code constant (`PDF_RENDER_DPI`) rather than an Admin-UI setting — a
rarely-changed technical knob doesn't need a settings-table entry, and an
isolated constant is already a one-line change if the value needs revisiting.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2.4.

### Convert Archives lands in the existing Processing Tools section, not a new "Archive Tools" section
**Decided:** 2026-06-30, v2.4 Item 6 scoping session.
**Why:** Tez's initial framing proposed a new "Archive Tools" admin section. The
Processing Tools section (§12) already exists for exactly this category of work —
CAPT-ported, pre-ingest filesystem utilities — and File Rename already lives
there as §12.1, with Convert Images and Flatten Archive (Items 7/8) also slated
for the same section. A second parallel section would split functionally
identical tools across two admin headers for no structural reason.
**Where:** `admin-spec-section-12-processing-tools.md` §12.2 (placed under the
existing §12 header), `comicvault-changes-v2.4.md` Item 6.
