# ComicVault — v2.4: Build Plan

> **Status: Active — scoping complete, ready to build.** Originally 14 items,
> closed list agreed in full 2026-06-29 — revised 2026-06-30 to pull Item 15
> (Processing Folder Automation) forward from the v2.5 holding list (explicit,
> deliberate exception to the "closed list, no additions" rule, `meta/
> working-rules.md` "Version lifecycle"). Item 8 (Flatten Archive) dropped
> 2026-06-30, superseded by BUG-018. Item 16 (Build: Processing Folder
> Automation) added 2026-07-01 — bookkeeping fix, Item 15 had no matching build
> item unlike every other scoped item in the cluster. Items 1–3 are small
> standalone changes, already built and verified.
>
> **CAPT-tooling cluster (Items 9–13, 16) — scoping phase complete as of
> 2026-07-01.** Items 4–8 and 15 are all scoped (Item 8 scoped to a drop). The
> §12.2/§12.3 backup-model cross-cutting gap that Item 15's scoping surfaced was
> written into the spec 2026-07-01, during a pre-build doc sanity check — no
> longer outstanding. The "dedicated cross-review pass across the whole
> cluster's specs" originally planned as its own step is folded into Code's own
> review-and-Plan-mode pass at the start of the build session instead (Tez's
> call, 2026-07-01) — same intent, just done by Code rather than as a separate
> Chat session. **Build order: Item 9 (Favourites) and Item 10 (Rename) have no
> dependency on the cluster and can go in any order; Items 11 → 12 → 13 → 16
> must go in that sequence** (16 orchestrates 12 and 13's callables directly).
>
> **How to use this document**
> This is the single ordered build queue for v2.4. Paste into a Claude Code session
> alongside the referenced spec files. Items are marked ✅ when built and verified.
> Bugs and minor fixes are tracked separately in `BUGS.md` — don't add them here
> unless they block a build item.
>
> **Always reference items from other docs as "v2.4 Item N", never bare "Item N"**
> — see `meta/working-rules.md` "Version-qualified references."
>
> **Scoping convention (settled 2026-06-29):** scope output for Items 4, 5, 6, 7, 8
> goes directly into its permanent home doc (`ADMIN_SPEC.md` for Items 4/6/7/8,
> `SPEC.md` for Item 5's scanner/format implications) — not into a new standalone
> scoping fragment. See `meta/working-rules.md` "Version lifecycle."
>
> **Specs to paste for most sessions:** `ADMIN_SPEC.md`, `SPEC.md`, and
> `admin-spec-section-12-processing-tools.md` as relevant per item.

---

## Item 1 — Admin: restrict all admin access for remote users when Remote Administration is off ✅

**Change.** When "Allow Remote Administration" is unchecked, the Admin cog
link/page should have no function at all for a non-local request — not just the
individual destructive actions already gated by `is_local_request()` (Clear
Database, Restore Database, the folder/file dialogs, etc.). Needs a quick look at
what's currently gated vs. what isn't before Code starts, since "no function
remotely" is broader than today's per-endpoint gating — likely also means the cog
link/page navigation itself, not just specific buttons within it.

---

## Item 2 — Admin: change the default server port to 9424 ✅

**Change.** Resolves the recurring Windows port-exclusion conflict (`archive/
bugs-fixed-archive.md` BUG-004) at the source, rather than relying on the
user-configurable port workaround (`ADMIN_SPEC.md` §7.3, already built) only being
discovered after a failure. 9424 chosen as a port unlikely to fall inside a
WSL2/Hyper-V dynamic-port exclusion range. Once built, `ROADMAP.md`'s "Resolved
(kept for context)" note on this should be tightened to reflect the new default.

---

## Item 3 — Library: replace the empty-results emoji with the logo image ✅

**Change.** On the no-matching-results state ("No comics match these filters."),
replace `<div class="empty-icon">📚</div>` with the image at
`D:\workshop\comicvault_v2\images\logo1.png`. File confirmed present on disk.

**Built beyond this scope, Tez's call:** the same swap was extended to the other
10 emoji-based empty/error states in `app.js` once the pattern was proven
working — see `progress.md` and `DECISIONS.md` for the rationale.

---

## Item 4 — Scope: Favourites as a Custom Tab category ✅ (scoped 2026-06-30)

**Scope.** Not a new feature so much as an extension of something already partly
in place (the `favorites` field/badge exist; Custom Tabs exist) — but genuinely
needs scoping, not a default. Custom Tabs today are folder-scoped only (`CustomTab`
model has no basis-type concept, unlike `HomeStrip`'s field/folder split). Needs a
real design decision: is a Favourites tab scoped to a folder *and* filtered to
favourites, or library-wide regardless of folder? Resolves `ROADMAP.md`'s deferred
"Favorites browse surface/tab" item once scoped and built — note for whoever
revisits `ROADMAP.md`/`roadmap.html` at v2.4's close, not touched now per Tez's
explicit hold.

**Resolved 2026-06-30:** library-wide, single-criterion (no folder+favourites
combo — rejected as scope creep nobody asked for, matching `HomeStrip`'s existing
rule against combining criteria). New `basis_type` column on `CustomTab`
(`'folder'`/`'favorites'`), one-click "Add Favourites Tab" admin control (max one
such tab, ever), `folder_path` kept `NOT NULL` with `""` stored for favourites-basis
rows rather than risking a nullable-column migration, `view_mode` locked to `flat`,
server-side guards on Folder View endpoints/edits for favourites-basis rows, and a
shared live-removal-on-unfavourite fix. Full design: `CUSTOM_TABS_SPEC.md` §10.
Scoping also surfaced **BUG-017** (existing All-tab Favourites filter misses
favourited issues inside a series — `BUGS.md`), bundled into Item 9's build.

**Spec destination:** `ADMIN_SPEC.md` (Custom Tabs config) + `CUSTOM_TABS_SPEC.md`
(behaviour) — write scope output directly into both, not a new file.

> Deviation from the above destination note: all scope output went into
> `CUSTOM_TABS_SPEC.md` only. `ADMIN_SPEC.md` has never carried any Custom Tabs
> content (the admin-page description has always lived in `CUSTOM_TABS_SPEC.md`
> §5.1) — adding a second, partial description in `ADMIN_SPEC.md` would create the
> exact doc-drift risk the single-authoritative-source principle exists to prevent.

---

## Item 5 — Scope: allow other formats to be added and indexed (CBR) ✅ (scoped 2026-06-30)

**Scope.** Flagged going in as the biggest of the four CAPT-area scoping sessions —
touches the scanner, thumbnail generation, and possibly the reader, not just an
isolated Processing Tools utility. Each candidate format turned out to be a
genuinely separate technical problem, not one decision — eng-reviewed 2026-06-30
before scoping, narrowing the original three-format list to one.

**Resolved 2026-06-30 — EPUB dropped entirely.** Originated from a feature seen in
another app, not a confirmed need; the sample file Tez has opens as a plain archive
of HTML pages, which doesn't generalize to the EPUB spec (reflowable content, no
fixed page sequence) and is structurally incompatible with the page-indexed reading
model (`page_count`, `current_page`, `/issue/{id}/pages`,
`/page/{issue_id}/{page_number}`, Flutter's `comic_page_view.dart`) every other part
of the app is built on. Too much work for a feature that was speculative going in.

**Resolved 2026-06-30 — PDF dropped from scanner/library scope, handled entirely
by Item 6's Convert tool instead.** PDF carries no ComicInfo.xml equivalent, so a
natively-indexed PDF would land with `metadata_source = "filename"` and none of the
genre/writer/story-arc filtering the rest of the app depends on. CAPT's existing
PDF↔CBZ converter (`arc_conv_pdf_proc.py`, PyMuPDF-based) already solves this:
convert to CBZ (with delete-original), tag it properly via the Full Editor, then it
enters the library as a normal, fully-capable CBZ. No PDF-specific scanner/
thumbnail/reader code needed at all — this item contributes nothing further to
PDF support beyond confirming Item 6 covers it.

**Resolved 2026-06-30 — CBR: full native support, read-only at the archive level.**
Original scope assumption ("library is all-CBZ") no longer holds — Tez's direction
has shifted toward a possible public release, and forcing every user with a large
mixed CBZ/CBR collection (some run >100,000 issues) to bulk-convert before their
library is even browsable is not viable. CBR is read **and** scanned/thumbnailed/
served natively everywhere — scanner, web page-serving, Flutter server mode — via
`rarfile` (extraction-only; CAPT's converter already depends on it, no new
library). **CBR is never written.** RAR archive *creation* requires a paid WinRAR
install (confirmed by reading `arc_conv_helpers.py`'s `create_rar_archive()`, which
shells out to a `rar` CLI and errors if it's missing) — not something a public app
can depend on. So editing a CBR's metadata (Basic Editor, Full Editor single-file,
and Full Editor batch/Process All alike — confirmed with Tez, applies uniformly to
all three) rebuilds it as a `.cbz` on save, same as the editor's existing rebuild
path already does for CBZ — only the *extraction* step gains a `rarfile` branch,
the rebuild step is unchanged. The original `.cbr` is deleted once the new `.cbz`
is verified written. This reopens and reverses `EDITOR_SPEC.md` §2/§9's original
"CBR/.rar support... dropped, library is all-CBZ" decision — see that file's
Change Log for the explicit correction, and `DECISIONS.md` for the full rationale.

Flutter **local/offline mode** (the `archive` Dart package has no RAR support) is
a known, accepted gap — a CBR copied to a device for travel reading won't open
locally. Server mode is unaffected (page-serving is already format-agnostic from
the client's perspective). Not addressed by this item; flagged for whoever revisits
mobile reader work (`ROADMAP.md` "Paused indefinitely").

File Rename Tool (Item 10) is already format-agnostic by design and needs no
changes here.

**Spec destination:** `SPEC.md` (scanner/library behaviour, new `container_format`
column, `rarfile` dependency) + `EDITOR_SPEC.md` (CBR read branch, edit-rebuilds-
as-CBZ behaviour, correction to §2/§9) — scope output written directly to both.

---

## Item 6 — Scope: Convert Files ✅ (scoped 2026-06-30)

**Scope.** CAPT's standalone Convert tool — code exists in
`comic_file_editing_toolkit/src/cap_toolkit/`, to be ported following the same
pattern as File Rename Tool's already-completed scoping (local-only gating, in-app
folder-tree picker, audit log).

**Resolved 2026-06-30.** Only two of CAPT's four directions are ported: CBR→CBZ
and PDF→CBZ. CBZ→CBR and CBZ→PDF are dropped entirely — CBR is now read natively
by the scanner (Item 5) so there's no remaining reason to convert CBZ down to CBR,
and PDF was dropped from the scanner/library scope entirely (Item 5) in favour of
always converting to CBZ first via this tool. UI exposes a single "From format"
choice (CBR or PDF); target is always CBZ. Picker filters to content-detected
matching files only (not extension-based). New `PDF_RENDER_DPI = 300` isolated
constant replaces CAPT's hardcoded 72 DPI page rendering. CBR extraction CRC
errors are no longer silent — a damaged page is skipped but the result is flagged
with a `pages_skipped` count rather than CAPT's fully-silent default. Runs as a
background job with live polling (modelled on `backend/scanner.py`'s existing
`scan_progress` pattern), not a blocking request like Rename — conversion work
(extract/rezip/rasterize) is meaningfully slower per-file than Rename's string
operations. Own `convert_log.md` audit log, same pattern as Rename's
`rename_log.md`. Lands in Admin as §12.2 Convert Archives, same Processing Tools
section as Rename (§12.1) — not a separate "Archive Tools" section, to avoid
splitting CAPT-ported tools across two parallel admin sections.

**Spec destination:** `ADMIN_SPEC.md` §12 (Processing Tools) — write scope output
directly there as a new §12.x, not a new file. (This also gives Item 10's eventual
build session the right shape to follow when `admin-spec-section-12-processing-
tools.md`'s content gets folded into `ADMIN_SPEC.md` proper — see `INDEX.md`.)

> Deviation from the above destination note: scope output went into
> `admin-spec-section-12-processing-tools.md` §12.2 directly, not into
> `ADMIN_SPEC.md`. `ADMIN_SPEC.md` currently has its own §11 Processing Tools
> (built 2026-06-27, ahead of the v2.4-era §12 renumbering) — writing a second,
> differently-numbered Processing Tools section into `ADMIN_SPEC.md` now would
> create exactly the kind of doc-drift this project's conventions exist to avoid.
> Full design lives in `admin-spec-section-12-processing-tools.md` §12.2 until
> Item 10's build folds the whole staging doc into `ADMIN_SPEC.md` at once.

---

## Item 7 — Scope: Convert Images ✅ (scoped 2026-06-30)

**Scope.** CAPT's standalone Convert Images tool, same porting pattern as Item 6.

**Resolved 2026-06-30.** Pre-ingest staging only — confirmed not a library-wide
bulk-conversion tool, same positioning as Items 6/10. Both CBZ and CBR accepted
as input (content-detected); CBR images convert normally but the archive always
rebuilds as `.cbz` — CAPT's CBR repack via a `rar` CLI shell-out is dropped
entirely, same WinRAR-dependency problem already ruled out by Item 5/6. CAPT's
hardcoded, internally-inconsistent `quality=95` (docstring claimed "original
quality", in-app label said "90%") becomes a real user-facing setting: lossless
toggle or quality slider, default 95. The archive-flattening side effect is kept
(confirmed still needed — nested-folder archives are a known prior problem) but
is re-pointed at the Editor's existing `_rebuild_archive` flatten logic instead
of carrying CAPT's separate implementation. Biggest decision: backup model. This
tool rewrites the archive in place under the same filename (no separate
new-file-kept-until-confirmed margin like Item 6 has) — resolved as validate
before replacing, then keep the original as a **permanent, never-auto-deleted**
`.bak`. Raised by Tez specifically because of a future, separately-scoped Auto
Processing Folder feature that will run this same conversion unattended on
watched-folder files — an auto-delete-on-success policy only works when a human
is watching, not for a backlog of unattended runs where a bad conversion could
go unnoticed. The core conversion function is specified as a plain,
router-independent callable for that same future feature to invoke directly.
Full design: `admin-spec-section-12-processing-tools.md` §12.3.

**Spec destination:** `ADMIN_SPEC.md` §12 (Processing Tools).

> Deviation from the above destination note, same reasoning as Item 6: scope
> output went into `admin-spec-section-12-processing-tools.md` §12.3 directly,
> not into `ADMIN_SPEC.md` (which still carries its own, differently-numbered
> §11 Processing Tools, built ahead of the v2.4-era §12 renumbering).

---

## Item 8 — Scope: Flatten Archive ❌ DROPPED (2026-06-30)

**Scope.** CAPT's standalone Flatten Archive tool, same porting pattern as Item 6.

**Dropped, not scoped.** Investigating *why* this tool existed (Tez built it for
a reason he couldn't recall) surfaced **BUG-018** (`BUGS.md`): the scanner — not
the editors, not the archive format itself — was folder-blind to nested
`ComicInfo.xml`, which is what Flatten Archive was originally built to work
around. Once BUG-018 is fixed, nested-folder archives read correctly on import
and already self-flatten on first edit (existing `_rebuild_archive` behavior,
unchanged) — there's no remaining case a standalone Flatten tool would still
need to handle. Confirmed with Tez no independent use case exists beyond this.
See `DECISIONS.md` for full rationale.

**Spec destination:** n/a — superseded, nothing written to `ADMIN_SPEC.md` §12.

---

## Item 9 — Build: Favourites as a Custom Tab category ✅

**Implement.** Item 4's scoping is complete — full design in `CUSTOM_TABS_SPEC.md`
§10. Includes the bundled BUG-017 fix (`BUGS.md`) in the same session.

**Built and manually tested 2026-07-01** — see `progress.md` "Session — 2026-07-01:
v2.4 Item 9 — Favourites as a Custom Tab category".

---

## Item 10 — Build: File Rename Tool ✅

**Implement.** Re-scoped 2026-07-01 (`admin-spec-section-12-processing-tools.md`
§12.1.3 Change Log) — three parser bugs fixed (stale hardcoded year ceiling,
zero-issue stripping, volume/subtitle whitespace loss), output separator locked
(`Series - Title #Issue (Year)`), no auto-splitting of Series/Title by design.
**Confirmed manual-only — explicitly excluded from Item 15's automation pipeline**,
see that item's amendment below. **Spec:** `ADMIN_SPEC.md` §11.1 — full design
there, this item is a pointer only.

Batch/single-file renaming based on parsed Series/Issue/Title/Year. In-app
folder-tree picker (not a native dialog — works correctly under Remote
Administration), no recursion, per-field File/All checkbox independence, narrow
auto-increment scope (Issue→All only), live preview with no explicit Preview
button, audit log (`rename_log.md`), no undo.

**Built and manually tested 2026-07-01** — see `progress.md` "Session — 2026-07-01:
v2.4 Item 10 — File Rename Tool". `admin-spec-section-12-processing-tools.md`'s
content folded into `ADMIN_SPEC.md` §11 in this same session, per the resolution
plan in `INDEX.md` — the standalone file is retired.

---

## Item 11 — Build: CBR support ✅

**Implement.** Depends on Item 5's scoping being complete. Scope narrowed to CBR
only 2026-06-30 — see Item 5.

**Built and manually tested 2026-07-01** — see `progress.md` "Session — 2026-07-01:
v2.4 Item 11 — native CBR support (build)". `SPEC.md` §6.1 and `EDITOR_SPEC.md`
§3.1/§3.2 marked built.

---

## Item 12 — Build: Convert Files ✅

**Implement.** Depends on Item 6's scoping being complete.

**Built and manually tested 2026-07-01** — see `progress.md` "Session — 2026-07-01:
v2.4 Item 12 — Convert Archives". `ADMIN_SPEC.md` §11.2 marked built. Bundled the
cross-review fix (picker now excludes `*.bak` files, matching §11.3).

---

## Item 13 — Build: Convert Images ✅

**Implement.** Depends on Item 7's scoping being complete.

**Built and manually tested 2026-07-01** — see `progress.md` "Session — 2026-07-01:
v2.4 Item 13 — Convert Images". `ADMIN_SPEC.md` §11.3 marked built; §11.3.7's stale
audit-log sample corrected to match the unified backup model.

---

## Item 14 — Build: Flatten Archive ❌ DROPPED (2026-06-30)

**Dropped along with Item 8** — see Item 8 and `BUGS.md` BUG-018. Nothing to
build; the underlying problem is fixed by BUG-018's scanner patch instead.

---

## Item 15 — Scope: Processing Folder Automation ✅ (scoped 2026-07-01)

**Pulled forward from the v2.5 holding list, 2026-06-30** — see header note above
for why.

**Resolved 2026-07-01.** No file-system watcher — scheduler + "Run Now" only.
File-watcher model evaluated and rejected: debounce, work-queue, and
restart-survival complexity is not justified for a personal batch-staging workflow
where files arrive in batches, not one at a time. Single unified pipeline (Convert
Archives → Convert Images → Rename, fixed order), one schedule for the whole
pipeline (daily or weekly at a configured wall-clock time), each stage independently
toggleable. New `processing_folder_loop()` in `scheduler.py` using wall-clock
scheduling (differs from `auto_scan_loop`'s elapsed-time model) with
`next_processing_run` persisted in `config.json` to survive server restarts.

Scoping this item surfaced two cross-cutting issues requiring a re-scoping session
before the cluster is built:

1. **§12.1 File Rename re-scope — done 2026-07-01, resolved as manual-only.** Original
   concern was that the CAPT-port model (four fields + checkboxes) is insufficient
   for automation. Re-scoping instead found and fixed three real parser bugs
   (`admin-spec-section-12-processing-tools.md` §12.1.3 Change Log) and concluded
   Rename shouldn't be automated at all — its live-preview review is its only
   correction mechanism, which unattended automation removes, and the genuinely
   ambiguous cases (Series/Title splitting) need a human decision no template could
   supply. The saved-naming-convention-template requirement below is dropped, not
   built.

2. **Unified backup model — amends §12.2 and §12.3.** Item 7 scoped Convert Images
   with a "permanent `.bak`, never auto-deleted" policy, and Item 6 scoped Convert
   Archives with a "Delete Original" checkbox. Item 15 scoping settled a single
   consistent model for both: clean success = auto-delete `.bak`; success-with-
   warnings (`pages_skipped > 0` or `images_skipped > 0`) = keep `.bak`
   permanently; failure = original completely untouched, no `.bak` created. §12.2's
   "Delete Original" checkbox is removed entirely. **Written into §12.2 2026-07-01**
   (pre-build doc sanity check) — no longer outstanding; both §12.2 and §12.3 now
   read consistently in `admin-spec-section-12-processing-tools.md`.

**Known discrepancy resolved:** `ROADMAP.md`'s original v2.5 wording said
"convert-to-cbz via 7zip" — confirmed loose phrasing; Item 6 uses `rarfile` and
PyMuPDF, which is correct.

**"Running custom scripts on the Processing Folder" stays in v2.5**, not moved
forward alongside this item (Tez's explicit call, 2026-06-30).

**Spec destination:** `admin-spec-section-12-processing-tools.md` §12.4 — written
directly there, same pattern as Items 6 and 7.

---

## Item 16 — Build: Processing Folder Automation ✅

**Implement.** Item 15's scoping is complete — full design in `ADMIN_SPEC.md`
§11.4 (folded from the now-retired `admin-spec-section-12-processing-tools.md`
§12.4 during Item 10's build). Added 2026-07-01 (pre-build
doc sanity check) to close a gap: every other scoped item in this cluster (4/5/6/7
→ 9/11/12/13) has a matching numbered build item, but Item 15 didn't — nothing to
mark ✅ against once it's built. No new scope, purely a bookkeeping fix.

**Depends on Items 11–13 being built first** — the pipeline invokes Convert
Archives' and Convert Images' router-independent callables directly (§11.4.10),
so those need to exist before this item can build. Item 10 (Rename) is not a
dependency — it's deliberately excluded from the automation pipeline (§11.1.1,
§11.4.3).

**Built and manually tested 2026-07-01 — closes out the CAPT-tooling cluster
(Items 9-13, 16).** See `progress.md` "Session — 2026-07-01: v2.4 Item 16 —
Processing Folder Automation". `ADMIN_SPEC.md` §11.4 marked built. Bundled a
fix for a response-shape bug found across all three Processing Tools run
endpoints (Items 12/13/16) — see that session's notes and the amendments
added to Items 12/13's own session entries.
