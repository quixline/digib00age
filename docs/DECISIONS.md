# ComicVault — Decisions Log

Rationale log — *why*, not *what*. Only non-obvious calls go here; routine
implementation choices are covered in `SPEC.md` / `EDITOR_SPEC.md` / the feature
specs and aren't repeated. Newest first.

### BUG-017 fix scoped to .cbz only, not .cbr

**Decided:** 2026-07-05, before building the Android file-association fix.

**Why:** The bug was originally logged covering both `.cbz`/`.cbr`, but
`LocalCbzService` (`flutter_app/lib/services/local_cbz_service.dart`) decodes
exclusively via `ZipDecoder()` — there is no RAR support anywhere in the
Flutter app. Associating `.cbr` in the Android manifest would have put
ComicVault in the "Open With" list for a format it can't actually read,
which just trades "no app can open this" for a different, equally unhelpful
failure once tapped.

**Decision:** intent-filters registered for `.cbz` only. `.cbr` stays
unassociated — exactly as unopenable as before, no regression introduced.

**How to apply:** if CBR reading support is ever added to the Flutter reader,
revisit extending the same intent-filter/`resolveSharedUri` mechanism to
`.cbr` — the plumbing (native URI resolution, `_handleLink` routing) would
carry over unchanged; only the manifest's MIME-type/pathPattern list and the
archive-decoding side would need to grow.

### Flutter's `shouldHandleDeeplinking()` disabled to fix a route-push crash found during BUG-017 testing

**Decided:** 2026-07-05, mid-session, after live testing on Tez's tablet
surfaced a crash the plan hadn't anticipated.

**Why:** `FlutterActivity`'s default Android embedding behaviour
auto-converts any incoming `ACTION_VIEW` intent into a raw
`Navigator.pushNamed()` call using the intent URI's literal path as the
route name — this happens *before* the `app_links` package's own
`uriLinkStream` (what `main.dart`'s `_handleLink` listens on) ever sees the
intent. A path like `/storage/emulated/0/Download/foo.cbz` isn't a
registered route, so this crashed with "Could not find a generator for
route" and silently swallowed the intent — meaning the manifest change
alone would have gotten ComicVault into the Open With list, but tapping it
would have crashed rather than opened anything. Confirmed via `adb logcat`
against a plain installed APK first (no visible crash in that log, wrongly
suggesting no problem), then conclusively by attaching `flutter run`
directly to the tablet and reading the live Dart exception — the lesson
being that `adb logcat` alone isn't sufficient for diagnosing Dart-level
widget exceptions; a debugger-attached run surfaces them far more reliably.

**Decision:** override `shouldHandleDeeplinking()` to return `false` in
`MainActivity.kt`, leaving `app_links` as the sole path that receives
incoming intents (native `VIEW` intent handling, not anything specific to
CBZ files).

**How to apply:** this affects *all* incoming `VIEW` intents to this app,
including the pre-existing `comicvault://read/{id}` deep link — worth
knowing if a future deep-linking change behaves unexpectedly, since Flutter's
own automatic route-push is now deliberately off, not just quietly present.

### OPDS / 3rd-party reader connectivity ruled out — continue Flutter app development instead

**Decided:** 2026-07-04, first scoping session for the v2.5 "OPDS" holding-list item.

**Why:** Research carried out ahead of/during scoping found CDisplayEx (the
target reader, Android tablet) doesn't support OPDS at all — it only connects to
Komga or Kavita via their own proprietary, undocumented REST APIs. So "add OPDS"
as originally conceived wouldn't have delivered CDisplayEx support anyway; the
only path would have been reverse-engineering and maintaining a Komga-API-shim
against another project's private, unstable surface — a materially different
and riskier build than a standards-based OPDS server.

Tez's own stated reasoning tipped it beyond just the CDisplayEx-specific
mismatch: this is a single-connection use case (his own tablet), so building and
maintaining a generic reader-compatibility layer isn't worth the effort even
before the CDisplayEx finding. He also raised the possibility of ComicVault
going public eventually, and concluded that if it does, maintaining ComicVault's
own client apps will be easier than supporting third-party readers whose
behaviour/versions/API expectations he can't control — i.e. this isn't just
"not worth it now," it's "not worth it even in the public-release scenario that
would otherwise be the strongest argument for it."

**Decision:** no OPDS server, no Komga-API-compatibility shim. Development effort
goes into the existing Flutter app instead — which turns out to need it anyway
(see BUG-019/BUG-020, surfaced in this same session: the Flutter app currently
fails to connect to the server and crashes when selecting a CBZ on the tablet).

**How to apply:** if third-party reader connectivity comes up again later
(e.g. a different target reader that does speak real OPDS), this decision
doesn't rule that out categorically — it rules out this specific
CDisplayEx-driven path. Re-scope fresh against whatever reader/use-case is
actually being asked for rather than reviving this research wholesale.

### CT Auto-Tag's "N of M succeeded" summary needed its own outcome breakdown, not a status-semantics change

**Decided:** 2026-07-04, diagnosing a misleading result reported during Tez's
low-confidence real-world test (5 files, 4 tagged, 1 correctly no-matched,
reported as "5 of 5 succeeded").

**Why:** `ct_autotag_file()` correctly returns `success=True` for a `no_match` or
a skipped-low-confidence outcome — deciding not to tag a file is a legitimate,
intentional result (per ADMIN_SPEC.md §11.4.3's "distinct from low confidence"
framing), not an error, so `success=False` would be the wrong signal to reuse
here. The bug wasn't in that status value — it was that
`pollPfStatus()`'s run-complete summary (`frontend/js/processingTools.js`)
reused Convert Archives/Images' generic `results.filter(r => r.status !==
'failed').length` framing for every stage, which fits a simple two-outcome
model (converted vs. failed) but silently swallows CT Auto-Tag's real
four-outcome model (tagged confident / tagged low-confidence / correctly
skipped / failed) into a misleading two-bucket "succeeded/failed" count. The
underlying `ct_autotag_log.md` audit log was accurate throughout — this was a
UI rollup-message bug only, not a data-integrity issue.

**How to apply:** Don't "fix" this by changing `ct_autotag_file()`'s
`success`/`status` semantics to make `no_match` count as something other than
success — that would break the correct, already-established design. Instead,
any stage whose outcome model doesn't fit the simple succeeded-vs-failed
framing needs its own summary branch in `pollPfStatus()`, using the per-file
result fields already available (`tags_written`, `confidence`) rather than
the generic `status` field alone. `ADMIN_SPEC.md` §11.4.4/§11.4.9 and
`v2.5/progress.md`'s 2026-07-04 close-of-session entry have the full detail.

### ComicTagger integration — field mapping expanded to capture everything CT/ComicVine supplies, not just editor-exposed fields

**Decided:** 2026-07-04, during Tez's live testing of v2.5 Item 1's build.

**Why:** The build's `metadata_to_field_dict()` (`backend/ct_bridge.py`) originally
only mapped the subset of ComicInfo.xml fields ComicVault's own Basic/Full Editor
UI exposes (Series, Number, Title, Year, Summary, Publisher, Count, StoryArc,
Language, Writer, Penciller) — a judgment call made during the build, not confirmed
with Tez in advance. Live testing surfaced this as real data loss: Tez compared a
ComicVault-tagged file against the same file tagged by his standalone ComicTagger
1.5.5 and found Month, Day, Notes, Inker, Colorist, Letterer, and CoverArtist all
missing. His stated intent: "pull it all... just save the current fields to the db
and display them in the library" — i.e. capture everything CT/ComicVine supplies
into the archive's XML, even fields ComicVault's own UI doesn't display, matching
what a proper auto-tagging tool does. Fixed by reading
`comicapi/tags/comicrack.py`'s own write mapping directly and mirroring it
field-for-field, rather than continuing to guess at scope.

**Genre/Format/AgeRating/BlackAndWhite stay excluded — confirmed as a different
category, not swept up in this reversal.** These were never a "the editor doesn't
show it" exclusion like the fields above — Genre/Format/AgeRating are
ComicVault-enforced dropdown fields with a validation gate (`EDITOR_SPEC.md` §4.4);
ComicVine doesn't reliably supply values matching that vocabulary (confirmed
2026-07-03 that `md.genres` is never even set by ComicVine's own issue mapper).
BlackAndWhite has a real semantic-correctness problem: ComicVault's convention is
the literal text `"on"` for checked (`EDITOR_SPEC.md` §3.3), while CT's own writer
uses `"Yes"` — writing CT's value would silently fail to register as checked
anywhere the Editor reads this tag.

A second, related bug surfaced in the same testing pass: ComicVine's `description`
field is raw HTML, and CT's own pipeline runs it through
`comictalker.talker_utils.cleanup_html()` (BeautifulSoup-based) before ever writing
it to `Summary` — this call was missing, so raw markup was landing as literal
escaped text (`&lt;p&gt;&lt;em&gt;...`) instead of clean plain text.

**How to apply:** `backend/ct_bridge.py`'s `metadata_to_field_dict()` now maps
Series, Number, Count, Title, Volume, Summary (via `cleanup_html()`),
AlternateSeries/Number/Count, StoryArc, SeriesGroup, Publisher, Imprint, Day,
Month, Year, Language, Web, Manga, Characters, Teams, Locations, Notes
(self-generated, mirroring CT's own "Tagged with..." convention), and all seven
credit-role fields (Writer/Penciller/Inker/Colorist/Letterer/CoverArtist/Editor) —
Genre/Format/AgeRating/BlackAndWhite/PageCount remain the only exclusions. Written
into `EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4's Change Logs, 2026-07-04 — both
surfaces share this one mapping function, so the fix applies identically to Search
Online and the CT Auto-Tag automation stage.

### ComicTagger integration — identify() needs a filename-parsing fallback, and 80% match thresholds, confirmed after live testing failures

**Decided:** 2026-07-04, diagnosing two consecutive failed live tests of v2.5
Item 1's CT Auto-Tag stage.

**Why:** Tez's first real test — a file with `ComicInfo.xml` deliberately removed,
run through "Run Now" — came back `[skipped: no match]` in the audit log
immediately (implausibly fast for a real ComicVine search). Diagnosis: `ct_bridge.
identify_file()` only ever seeded its search from `ComicArchive.read_tags("cr")`;
with no embedded XML, `Series`/`Issue#` were both empty and the function
short-circuited before ever calling ComicVine — a gap flagged as an open judgment
call during planning but never actually built or confirmed. Separately, ComicVine
genuinely did have the series (confirmed via direct search), but the real issue
had no explicit number in the filename — a one-shot-style release. Tez's own
standalone ComicTagger successfully tagged the same file using its own
default-on "If no issue number, assume 1" Auto-Tag option, which ComicVault had no
equivalent of.

**How to apply:** `identify_file()` now falls back to `backend/rename_tool.py`'s
`parse_comic_filename()` (the tested, scene-release-tolerant parser — not
`scanner.py`'s weaker one, which was confirmed via direct testing to leave scene
tags unstripped for this exact filename shape) when the archive has no
Series/Issue# embedded, and defaults the issue number to "1" when the filename
itself has none — confirmed with Tez as the right call, matching CT's own default.
Separately, match thresholds (`series_match_search_thresh`/
`series_match_identify_thresh`) were lowered from CT's own CLI defaults of 90/91
to **80**, matching what Tez had already found worked well in his own standalone
ComicTagger testing (`_DEFAULT_IIO_KWARGS`, `backend/ct_bridge.py`) — confirmed
this is still a hardcoded value with no Admin UI to tune it, per the locked spec's
"simpler two-outcome model" framing; revisit if 80% proves too loose in practice
once Tez's low-confidence sample testing (still pending) surfaces false positives.

### ComicTagger dependency pinned to a GitHub commit, not the published PyPI release

**Decided:** 2026-07-03, during v2.5 Item 1's build (Step 1 smoke test).

**Why:** `pip install comictagger` resolves to PyPI's published release
(1.5.5 at the time), which predates the `comictalker` plugin-talker architecture
the entire integration plan was researched and built against (that split only
exists on ComicTagger's `develop` branch — confirmed via `pip show`, RECORD
inspection, and comparing the local research clone's `git describe` output,
`1.6.0-beta.10-45-g0cc9e76`, against 1.5.5's actual installed file layout, which
has no `comictalker` package at all, just a single legacy
`comictaggerlib/comicvinetalker.py`). Installing from an agent-chosen external git
URL tripped Claude Code's auto-mode safety classifier, correctly — this needed
explicit sign-off before proceeding, not a silent workaround.

**How to apply:** `requirements.txt` pins `comictagger` to
`git+https://github.com/comictagger/comictagger.git@0cc9e76f8d45d3ef27bcf2feabb676e124412abf`
— an exact commit, not a branch name, so a fresh install can't drift even if
`develop` moves on. Confirmed with Tez as the right tradeoff over two alternatives:
installing from the local research clone's path (rejected — couples
`requirements.txt` to that exact folder surviving on this one machine, the same
personal-environment coupling this project has deliberately cut elsewhere, e.g.
the `rar.exe` decision below) or rewriting the whole integration against 1.5.5's
older API (rejected — throws away already-completed, verified research, and 1.5.5
lacks the dual rate-limiter split this integration depends on). Revisit once
ComicTagger publishes a PyPI release that includes the `comictalker` split.

### ComicTagger integration — "Save on Low Confidence" toggle and ComicVine key field behaviour locked (session 4)

**Decided:** 2026-07-03, ComicTagger integration scoping session 4 (Chat +
Tez), following up two items introduced under "Processing Folder Automation
addition" that weren't actually in any prior entry.

**Why:**

1. **"Save on Low Confidence" toggle, in §11.4 alongside the CT Auto-Tag
   stage toggle.** Confirmed new — not present in session 1–3 scoping, so
   this is the first time its behaviour is defined, not a recap. **OFF:**
   skip writing tags for a low-confidence CT match entirely — the file
   passes through the stage untagged and unflagged, as if CT Auto-Tag hadn't
   run on it. **ON (default):** unchanged from session 1/2 — write the
   best-guess tags, set `NeedsReview`, let Full Editor's Search Online
   resolve it later. This is deliberately a cheap branch inside the CT
   Auto-Tag stage itself, not a pipeline-flow change — the alternative
   (holding a low-confidence file back from continuing to Convert Images /
   the library) was ruled out on this pass: §11.4 is explicitly
   **folder-level, not per-file chaining** ("Stage 2 simply picks up
   whatever CBZ/CBR files are present... it does not receive an explicit
   list from the previous stage"), so "hold this one file back" would need
   new per-file tracking infrastructure that doesn't exist anywhere in this
   pipeline today. Confirmed not worth building for this.

2. **ComicVine key field gets a "Save & Test" button**, not auto-save and
   not a bare manual Save — the one deliberate exception to this section's
   auto-save convention, justified because CT's own `comicvine.py` already
   ships `check_status()` (hits `team/1/`, detects ComicVine's "Invalid API
   Key" error 100) giving real pass/fail feedback a plain auto-save
   couldn't. Distinct from the Schedule/Time/Day manual-save control
   (`INBOX.md`, deferred to v2.6 as a bug) — that one has no such
   justification and stays logged as an inconsistency to fix; this one does
   the extra step because it earns it.
   **Recommended (not yet asked, low-stakes default):** the button always
   persists whatever's typed to `comicvine_api_key` in `config.json` on
   click, with the test result shown as separate pass/fail feedback rather
   than gating the save — losing a just-typed key because the test call
   itself timed out would be worse than saving a key that later turns out
   to be wrong and is easy to re-edit.

**How to apply:** `ADMIN_SPEC.md` §11.4 needs: the CT Auto-Tag toggle row, the
Save on Low Confidence toggle row (both matching the existing Convert
Archives/Convert Images toggle pattern), and the `comicvine_api_key` field
with its Save & Test button and `check_status()` wiring. **Written up
2026-07-03**, same session — see `EDITOR_SPEC.md` §9 and
`ADMIN_SPEC.md` §11.4. (Correction: the three earlier entries below cite a
"standing hold — nothing goes to Code until reviewed with the §12 CAPT tool
ports" as blocking this. That was wrong — the §12 cluster was already built
and verified before this scoping began; v2.4 closed 2026-07-02. No hold ever
applied to this work; see the correction note at the end of this entry's
neighbours below and `ROADMAP.md`.)

### ComicTagger integration — search/select UI detail locked (session 3); reverses part of session 2's trigger design

**Decided:** 2026-07-03, ComicTagger integration scoping session 3 (Chat +
Tez), working from two CT screenshots (`images/search-online-manual-
selection-from-results.PNG`, `images/series-page-search-issue-list.PNG`) and
`taggerwindow.py`/`issueidentifier.py` read directly.

**Why — this reverses part of the previous entry, not a refinement:**
Session 2 had the `NeedsReview` badge itself as a click-to-open trigger for
the search modal, with a second trigger beside the Series field, and assumed
the badge would reuse §3.5's read-only side-by-side view as its resolution
UI. None of that survives contact with the actual design:

- **Card indicator is now a plain colour-coded border, not a text badge** —
  reuses the existing favourited-card gold-border convention (`SPEC.md`) with
  a different colour/condition, not §3.5's pattern. Purely passive — clicking
  it does nothing beyond the existing unified focus/load mechanic (§5.2); it
  does not open the modal.
- **One global trigger only:** a "Search Online" button in the Full Editor's
  toolbar, next to the existing Admin-cog link (`(log in)` in Tez's original
  note refers to that area's unrelated Allow-Remote-Admin login control, not
  a gate on this button — confirmed, no relation to the ComicVine key).
  Operates on whichever file is currently focused/loaded into the form.
- **Column 1 gains one inline count**, "N Low Confidence," placed after the
  Clear List button in the action row, same text style as the "N File(s)
  Loaded" line but a different line/position — not folded into that count.

**Search field source, verified against CT source rather than assumed:**
Two different CT code paths use different keys — worth being precise since
they don't match:
- Automated Auto-Tag (`issueidentifier.py::identify`) requires **Series and
  Issue #** at minimum ("Not enough info for a search!" if either's blank),
  then uses Year/Publisher/Month/Issue Count to filter and score candidates,
  plus cover-image hashing for confidence. No Title anywhere in the key set.
- Manual Search Online (`taggerwindow.py::query_online`, the function behind
  the ported dialog) only **requires Series** ("Need to enter a series name
  to search" if blank, search stops there) — Issue #, Year, and Issue Count
  are read from the form and passed through to pre-filter/sort results, but
  none of them block the search if empty. **Title is not used in either
  path** — Tez's original assumption included it; confirmed absent from both
  `SearchKeys` (`issueidentifier.py`) and `query_online`'s field reads.

  ComicVault's Search Online button follows the manual-path behaviour: reads
  Series/Issue #/Year/Issue Count directly from the currently-focused file's
  form fields at click time (no separate input, no state duplication),
  blocked with a message if Series is empty (matching CT's own guard).

**Select Series dialog — deliberately trimmed from CT's native version**
(per screenshot): no editable search box, no Re-Search button, no Show
Issues button, no Filter Publishers checkbox — all present in CT's dialog,
all dropped here since the read-from-form behaviour above replaces them (to
retry, edit the Series field in the main form and click Search Online
again). Kept: results table (Series/Year/Issues/Publisher), cover-art
preview and description panel that both update on row selection, double-click
a row to proceed.

**Select Issue dialog** (second screenshot): issue list (Issue #/Date/Title)
with cover preview and description, both updating on row selection — no
changes from the screenshot's own layout.

**Two-window question resolved as one modal, two internal steps, not two
stacked windows.** CT's split into separate `QDialog`s is a desktop-toolkit
artifact — independently movable/resizable windows are a native-app
affordance that doesn't carry over to a browser modal. Stacking two overlays
would mean nested focus-traps, a second backdrop, and rebuilding a whole
overlay just to go "back" to already-fetched series results, for no offsetting
benefit — nothing else in ComicVault has a stacked-modal precedent either.
Built as one modal container; a "← Back to Series" control returns to the
cached results list from the issue step.

**Confirming a match still fully overwrites the mapped form fields and still
only clears the `NeedsReview` XML tag on save** (session 2, unchanged) — the
border/count are read live off in-memory form state, so they update the
moment fields are populated, same as every other field in this editor; they
don't wait for a save round-trip.

**Not yet decided, flagging for a future pass, not blocking:** whether
Search Online should also warn/disable if no `comicvine_api_key` is
configured in Admin, rather than surfacing a raw network failure on first
use. Worth doing, doesn't affect anything else here.

**How to apply:** Written into `EDITOR_SPEC.md` §9, 2026-07-03 (session 4's
doc-update pass). No hold applied — see the correction note in the session 4
entry above.

### ComicTagger integration — search/select dialog locked as a modal overlay; ComicVine API key gets a home; 2000 AD parser fix deferred

**Decided:** 2026-07-03, ComicTagger integration scoping session 2 (Chat + Tez) —
eng-review pass on session 1's two open questions, plus one gap the review
surfaced.
**Why:** Three related calls:

1. **Modal overlay confirmed** for the CT search/select dialog (not an
   in-column panel swap in Column 2). A modal cleanly blocks the rest of the
   Full Editor while it's open — in particular Column 1's existing
   hover/arrow-key "focused card" mechanic (§5.2), which would otherwise fight
   with an open search dialog over which file is "current." An in-column swap
   would have had to solve that conflict from scratch; a modal gets it for
   free by definition.

   Design details locked in the same pass, all chosen for consistency with
   existing Full Editor conventions rather than inventing new ones:
   - Re-Search field pre-fills with the form's current Series value (not
     blank) — matches the already-confirmed "editable search field, not a
     passive candidate list" workflow (`INBOX.md`, session 1).
   - Confirming a selected issue **fully overwrites** the mapped fields in
     the form — same "not a smart merge" rule §3.3 already established for
     saves generally (every exposed tag is fully overwritten by whatever's in
     the form). One rule for the whole editor, not a special case for this
     dialog.
   - Modal traps focus, blocking Column 1's card-swap and Process
     Queue/Process All while open.
   - Two trigger points open the same modal instance: a button beside the
     Series field (always available), and clicking a `NeedsReview`-flagged
     card's warning badge in Column 1. The badge reuses §3.5's warning visual
     pattern but the click target opens this modal directly, not §3.5's
     read-only side-by-side view — different problem (wrong/blank field vs.
     duplicate XML) doesn't need the same resolution UI.
   - No auto-advance to the next flagged file after confirming a match —
     closes back to normal state, Tez picks the next one manually, matching
     the existing "walk the list" batch workflow rather than a new
     guided-queue mechanic.
   - Series/issue search must go through **one shared backend function**,
     called by both this manual modal and the eventual CT Auto-Tag automation
     stage (session 1) — same router-independent-callable principle already
     applied to Convert Archives/Convert Images (`ADMIN_SPEC.md`
     §11.2/§11.3), not two codepaths hitting ComicVine.

2. **ComicVine API key gets a home.** Reading
   `comictalker/talkers/comicvine.py` directly (in the CT clone) found the
   talker ships with a hardcoded shared default key
   (`27431e6787042105bd3e47e169a624521f89f3a4`) rate-limited to **1
   request/10s, 100/hour** — versus **10 req/10s, 200/hour** on a personal key
   (`custom_limiter` vs `default_limiter`, same file). That shared key is used
   by every ComicTagger install that hasn't configured its own, so a
   Processing-folder batch running on it would stall for hours and compete
   with unrelated users worldwide. Nothing in `config.json` or
   `ADMIN_SPEC.md` currently holds a personal key — this blocks the CT
   Auto-Tag automation stage from session 1 as much as it blocks this modal,
   not something either can quietly work around. **Confirmed with Tez:** new
   `comicvine_api_key` field in `config.json` (same trust model already
   applied to `SESSION_SECRET`, stored there in plaintext today), with an
   Admin UI field placed near Processing Folder Automation, since that's the
   section it unblocks.

3. **2000 AD "progs"-to-issue filename pattern fix deferred**, logged as a
   `[change]` not a `[bug]`. The manual Re-Search field (above) already
   covers this workflow today at no extra cost — re-typing the issue number
   into the search string was already the confirmed real-world habit
   (session 1). Automating the upstream parser is a precision improvement for
   later, not a gap blocking anything now.

**How to apply:** Written into `EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4,
2026-07-03 (session 4's doc-update pass). **Correction, same pass:** this
entry originally cited "per the standing rule nothing in the CAPT cluster
goes to Code until the whole set is reviewed together" as a blocker. That
was wrong — checked against `ROADMAP.md`'s own v2.4 close-out note and
`ADMIN_SPEC.md`'s per-section build-status text, the §12 CAPT cluster (Items
4–7/9–13/15–16) was already built and verified before this scoping began;
v2.4 closed 2026-07-02. No such hold ever applied here — I was working from
stale memory instead of checking. `EDITOR_SPEC.md` got a new CT
Integration section (§9) covering the modal (data flow, both triggers, overwrite
semantics, focus trap) alongside the existing §3.5/§5.2 material it reuses;
`ADMIN_SPEC.md` got the `comicvine_api_key` field documented alongside
§11.4's automation settings, plus the three-stage pipeline amendment already
noted in the entry below.

### ComicTagger integration — Rename moves after Full Editor review; low-confidence flag stays an in-file XML tag

**Decided:** 2026-07-03, ComicTagger integration scoping session (Chat + Tez),
continuing from the CBR write-back decision above.
**Why:** Two related calls made in the same session:

1. **Manual workflow order changes.** Tez's original stated pipeline was convert
   → CT tag → convert images → rename → open in Full Editor. Rename sitting
   between tagging and review meant any "needs review" signal correlated by
   filename/path would break exactly at that step. Tez agreed to reorder:
   convert → CT tag → convert images → **open in Full Editor (review/confirm/
   search-fallback)** → rename → move to library. This doesn't change
   `ADMIN_SPEC.md` §11.4's built automation (Rename was already excluded from
   automation, for a separate reason — no undo, needs a human at the live
   preview) — it changes the order Tez runs Rename manually, after the Editor
   step rather than before.
2. **Low-confidence match flag stays an XML tag, not a dump/log-file
   correlation**, even after the reorder removed the original objection
   (filename changing mid-window). Reason: the Full Editor already parses each
   file's XML on load — reading a new tag out of that same parse costs nothing.
   A log-file approach still needs new write code, new read code, and a
   path-correlation step, none of which are free. The "must be explicitly
   cleared/resolved on save, or it lingers" problem applies equally to both
   approaches, so it isn't a differentiator. A separate **aggregate audit-run
   log** ("12 converted, 11 confident, 1 flagged") is still worth building —
   Tez confirmed this explicitly — but as a future addition alongside whatever
   job-progress logging the eventual CT automation stage needs, not as the
   mechanism the Editor itself reads.

**How to apply:** When CT integration is actually scoped for build, it becomes
a **new middle stage** in `ADMIN_SPEC.md` §11.4's pipeline — Convert Archives →
CT Auto-Tag → Convert Images — following the exact same architecture already
established twice (§11.2/§11.3): a plain router-independent callable, its own
progress singleton, its own audit log using the existing `[AUTO]`-prefix
convention rather than a new log format. The low-confidence flag is a new XML
tag (name TBD, e.g. `NeedsReview`) added to `COMICINFO_TAGS`
(`backend/editor/xml_parser.py`) with special handling in the Editor's save
routes to explicitly clear it on every successful save — `build_xml_from_fields`
only touches tags present in the submitted payload, so this tag will never
self-clear via the normal field-preservation mechanism (`field_merge.py`) the
way a text field would. **Confirmed whole-file, not per-field** (same
session, follow-up) — Tez's stated need was "flag the file," and Genre is
irrelevant to this either way since CT/ComicVine doesn't supply Genre data at
all, so there's no per-field case being lost by keeping this simple.

### ComicTagger integration — CBR write-back stays out of scope even though `rar.exe` is present on Tez's machine

**Decided:** 2026-07-03, ComicTagger integration scoping session (Chat + Tez).
**Why:** While scoping CT integration, Tez asked whether the existing CBR→CBZ
conversion requirement (Item 6, `admin-spec-section-12-processing-tools.md`
§12.2) might no longer be needed, since CBR is now natively DB-supported
read-only (Item 5) and CAPT already has a CBZ→CBR converter. Reading
`comicapi/archivers/rar.py` (in the CT clone at
`D:\workshop\3rd_party_apps\ComicTagger`) confirmed all RAR write operations
(`write_file`, `remove_file`, `set_comment`) shell out to an external `rar`
executable located via `shutil.which()` — no pure-Python or free fallback
exists. CAPT's own `create_rar_archive()` (`arc_conv_helpers.py`) does the
identical thing. Tez then confirmed `rar.exe` (the WinRAR CLI component) is
in fact installed on his machine, which is why CAPT's CBZ→CBR button has
apparently worked before.

That finding doesn't change the decision: Convert Archives (CBR→CBZ) stays a
hard requirement ahead of CT tagging, and CBZ→CBR / any CBR write-back stays
permanently out of scope. Depending on one specific machine happening to have
a paid tool's CLI binary on PATH is exactly the kind of personal-environment
coupling the project has been deliberately cutting elsewhere (Flatten
Archive, saved rename templates). It's not portable, not guaranteed to
survive a reinstall/migration, and isn't something Code should build a
dependency on.

**How to apply:** CAPT's `create_rar_archive()` / CBZ→CBR feature is now dead
code from ComicVault's perspective — candidate for removal from CAPT, not for
porting into ComicVault's Admin UI. If CBR write-back is ever reconsidered,
it needs its own decision (and would still require documenting the WinRAR
dependency explicitly, not assuming it away), not a quiet re-add.

### File Rename — kept Year over the mockup's Publisher field; added per-item queue removal

**Decided:** 2026-07-02, planning session with Tez ahead of the "Add to Queue" fix
(see `progress.md` "Session — 2026-07-02").
**Why:** Restoring the queue workflow surfaced two mismatches against the original
mockup (`images/Filename-Editor.pdf`) that needed a call, not just a mechanical
port:
- The mockup's 4th field is "Publisher"; the shipped build (and `ADMIN_SPEC.md`
  §11.1.4) uses "Year". Publisher isn't parsed by `filename_parser.py` or included
  in the `Series - Title #Issue (Year)` output format — adopting it would mean new
  backend parsing work, not just a frontend relabel. Tez chose to keep Year,
  since it matches what the parser and output format already do; Publisher stays
  unbuilt rather than half-matched to the mockup.
- The mockup only shows a whole-queue "Clear Preview" control, no per-row removal.
  Tez chose to add per-item removal anyway, since without it a single mis-added
  file would force clearing (and re-queuing) everything else in the batch.

**How to apply:** If Publisher ever gets scoped in, it needs its own parsing +
output-format decision first — don't just add a text field. The per-item queue
removal control is intentional scope beyond the mockup, not an oversight to trim
back toward it.

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
