# ComicVault — Progress Log (v2.5)

Narrative build history for v2.5 — per-session detail, what was actually built,
verification notes. Append-only, written by Claude Code at the close of each
session. Full project history through v2.4's close lives in
`archive/v2.4/progress.md` — not duplicated here.

---

## Session — 2026-07-03/04: v2.5 Item 1 — ComicTagger + ComicVine integration

**Goal.** Build EDITOR_SPEC.md §9 (Full Editor Search Online) and
ADMIN_SPEC.md §11.4's third pipeline stage (CT Auto-Tag), both fully scoped
and decision-locked across four Chat sessions on 2026-07-03. Nine-step
build order from the implementation plan, each step verified before moving
to the next.

**Dependency setup.** `pip install comictagger` pulled PyPI's published
release (1.5.5), which predates the `comictalker` plugin-talker split the
whole plan was researched against (that architecture only exists on
ComicTagger's `develop` branch, not yet released). Confirmed with Tez and
pinned `requirements.txt` to the exact `develop`-branch commit already
researched (`comictagger @ git+https://github.com/comictagger/comictagger.git@0cc9e76...`).
Smoke-tested against a real CBZ and CBR: `RarArchiver` correctly resolved
via ComicVault's existing `rarfile` install (the flagged risk point), no
PyQt6 pulled in by the base install.

**Backend built, each piece live-verified against real ComicVine data
before moving on:**
- `backend/ct_bridge.py` — talker/rate-limiter setup, series search, issue
  list, single-issue fetch, `GenericMetadata` → field-dict mapping, and the
  `identify_file()` auto-tag pipeline (Result enum → confident/
  low-confidence/no-match classification).
- `NeedsReview` tag added to `COMICINFO_TAGS`; explicit
  `field_values["NeedsReview"] = ""` added to both `editor_basic.py`'s and
  `editor_full.py`'s save paths, verified by hand-injecting the tag into a
  scratch archive and confirming a simulated save strips it.
- `backend/ct_autotag.py` + `ct_autotag_log.py` — verified against 4 cases
  (confident/no-match/low-confidence-saved/low-confidence-skipped) with
  real ComicVine lookups; log line formats confirmed matching
  ADMIN_SPEC.md §11.4.9 exactly.
- `processing_folder.py` amended to the 3-stage pipeline — settings
  round-trip and a real "Run Now" verified against a scratch folder with
  only CT Auto-Tag enabled (Convert Archives/Images correctly stayed
  off), Tez's real `config.json`/library/Processing folder confirmed
  byte-identical afterward.
- `editor_full.py` gained the three Search Online endpoints, verified via
  live calls against real series/issue searches before any frontend work
  started.

**Frontend built and verified live in a real browser** (a scratch test
library, never the real one, per an early permission denial that correctly
caught an attempt to write a test folder into the real `Processing`
directory — reworked to temporarily repoint `library_root` at a scratch
folder instead, restored exactly afterward): Admin's three new controls
(toggle, toggle, key field + Save & Test with live pass/fail feedback);
Full Editor's Search Online button, two-step modal (Select Series → Select
Issue, double-click to proceed/confirm), and the NeedsReview red-border/
count indicator (confirmed lazy-on-focus per Tez's choice, and confirmed
clearing immediately on a confirmed match without needing a save).

**Post-build issues found during Tez's own live testing, all fixed same
session:**

1. **`identify_file()` never attempted a search when a file had no
   embedded XML.** Tez's first real test (a file with `ComicInfo.xml`
   removed) came back `[skipped: no match]` immediately. Root cause: the
   function only seeded from `ca.read_tags("cr")`, never fell back to
   filename parsing. Fixed by adding a fallback through
   `backend/rename_tool.py`'s `parse_comic_filename()` (the tested,
   scene-release-tolerant parser — not the weaker one in `scanner.py`),
   defaulting the issue number to "1" when the filename has none (matches
   ComicTagger's own default-on "assume issue 1" option, confirmed with
   Tez as the right call). Also lowered the match thresholds from CT's own
   CLI defaults (90/91) to 80, matching what Tez had already found worked
   in his own standalone ComicTagger testing.

2. **Second real test still failed the same way.** Diagnosed live against
   Tez's actual file (explicit permission granted — a test copy). Traced
   through `IssueIdentifier.identify()`'s internals step by step
   (`_check_requirements` → `_get_search_terms` → `_search_for_issues` →
   `_cover_matching`): every individual piece worked correctly in
   isolation (series found, issue found, cover-hash score of 7 — a very
   strong match), but the full `identify()` call still returned
   `no_matches`. Root cause: a stale cached "no results" entry in
   ComicVineTalker's local SQLite cache (`ct_cache/comic_cache.db`) from
   an earlier lookup during this same debugging session. Not a code bug —
   confirmed by re-running `identify_file()` fresh once the cache held
   correct data, which returned `confident` with the same score-7 match.

3. **Data loss reported after a successful tag write** — Tez compared the
   ComicVault-written XML against the same file re-tagged with his
   standalone ComicTagger 1.5.5 and found Month/Day/Notes/Inker/Colorist/
   Letterer/CoverArtist all missing, and `Summary` containing literal
   `&lt;p&gt;&lt;em&gt;` instead of clean text. Two separate causes:
   - `ct_autotag_file()` was mapping fields from the `IssueResult.md` that
     `IssueIdentifier`'s bulk candidate search returns — ComicVine's
     lighter multi-issue endpoint doesn't include `person_credits` in that
     payload. Fixed with a follow-up `ct_bridge.fetch_issue_metadata()`
     call (the full single-issue endpoint, already correctly used by
     Search Online's confirm step) before mapping fields.
   - `metadata_to_field_dict()` had only ever mapped the subset of fields
     ComicVault's own editor exposes — a scope decision made unilaterally
     during planning, not confirmed with Tez, and it turned out to not
     match his actual intent ("pull it all... save the current fields to
     the db and display them in the library" even for fields the UI
     doesn't show). Read `comicapi/tags/comicrack.py`'s own write mapping
     directly and mirrored it field-for-field, rather than guessing.
     Genre/Format/AgeRating/BlackAndWhite stayed excluded — confirmed
     these are a different category (validation-integrity / semantic
     correctness, not "editor doesn't show it").
   - `Summary`'s raw-HTML issue: ComicVine's `description` field is raw
     HTML; CT's own pipeline runs it through
     `comictalker.talker_utils.cleanup_html()` (BeautifulSoup-based, also
     converts embedded `<table>` credit lists into a readable plain-text
     table) before ever writing it. That call was missing — added.

All three fixes verified against the real file (explicit permission
granted, confirmed a disposable test copy) before Tez's own final
confirmation pass. The very last write attempt hit a transient Windows
file lock (`WinError 5`) caused by Tez having the archive open on his end
— not a code issue; cleaned up the harmless leftover staging file and
confirmed once he closed it.

**Final verification (Tez, live):** API key Save & Test; a confident match
pulling complete data, cross-checked correct against an external source;
the credits and HTML-cleanup fixes; the scheduled Auto-Tag stage run
against a couple of real titles via "Run Now". **Explicitly deferred to
Tez, not blocking this item's close-out:** testing low-confidence matches
and how the Full Editor's Search Online/`NeedsReview` flow handles
resolving them — needs varied real sample material he's still sourcing.
Tracked as `meta/roadmap.html`'s current Now #1 item.

**Docs updated this session:** `EDITOR_SPEC.md` §9's status marked built;
`ADMIN_SPEC.md` §11.4's status marked built; four `DECISIONS.md` entries
for the git-commit pinning, the 80% threshold, the filename-fallback/
assume-issue-1 default, and the comprehensive field-mapping reversal;
`CHANGELOG.md`; `docs/v2.5/` created (this file + the build queue);
`meta/roadmap.html`'s Now #1 card updated to reflect the build is done and
what's left is Tez's own low-confidence sample testing.

---

## Session — 2026-07-04 (close-of-session): Match Ratio Threshold slider + low-confidence real-world test — v2.5 Item 1 closed

**Goal.** Tez wanted the CT Auto-Tag match-confidence threshold (hardcoded
at 80 the previous session) tunable from the Admin page, then ran his
deferred low-confidence real-world test — a 5-file comparison against his
standalone ComicTagger install.

**Built:** new Match Ratio Threshold slider (10–100%, 1% steps) in Admin →
Processing Folder Automation, immediately after "Save on Low Confidence" —
mirrors the existing Convert Images Quality slider's markup/JS pattern
exactly. New `processing_folder_ct_match_threshold` config key (default
80). `backend/ct_bridge.py`'s `identify_file()` now reads this from config
at call-time and overrides both `series_match_search_thresh`/
`series_match_identify_thresh` (kept tied to one value, matching CT's own
single "match ratio" concept and the existing 2026-07-03 decision to unify
both). Verified live: markup and JS served correctly from Tez's own
already-running server (frontend files serve fresh without a restart);
backend logic confirmed via direct import checks, pending his own restart
for the live config round-trip.

**Bug found during Tez's low-confidence test pass.** He ran a real 5-file
comparison: standalone ComicTagger 1.5.5 (30% match ratio, Save on Low
Confidence off) tagged 1 of 5; the same 5 files through ComicVault's Run
Now returned "successfully tagged 5 files" but only 4 were actually
tagged. Diagnosis (via the audit log, which was accurate throughout — this
was a UI-only bug): `ct_autotag_file()`'s `no_match`/skipped-low-confidence
outcomes correctly return `success=True` at the code level (the stage
didn't error — deciding not to tag is a legitimate outcome, not a
failure), but `pollPfStatus()`'s run-complete summary counted any
non-`failed` status as "succeeded" without distinguishing "tagged" from
"correctly decided not to tag." Fixed with a CT-Auto-Tag-specific summary
branch reporting tagged/no-match/skipped-low-confidence/failed counts
separately, rather than reusing Convert Archives/Images' generic
succeeded-vs-failed framing (which fits their simpler two-outcome model,
but not CT Auto-Tag's four-outcome one).

**Investigated but not conclusively resolved:** why the standalone app
(1/5) underperformed ComicVault (4/5), especially since ComicVault's
actual run used the *stricter* 80% default (the 30% setting hadn't
persisted yet — sequencing issue, not a bug: Tez had dragged the slider
before restarting his server past the point where the backend recognised
the new config key). Checked all 4 of ComicVault's successful matches
against their source filenames — all had clean, explicit, unambiguous
issue numbers, no evidence of risky guessing; the one no-match
(`Hard Bargain (2025).cbz`) is a one-shot with no issue number anywhere
(filename or ComicVine), correctly not force-guessed. Leading hypotheses
for CT's lower hit-rate (shared vs. personal ComicVine API key on the
standalone install; CT 1.5.5 being a different, older codebase entirely
from the git-commit-pinned dev-branch version ComicVault runs) were raised
but not confirmed with Tez before session close — flagged for a future
session if the gap recurs, not treated as a ComicVault defect since
nothing in ComicVault's own behaviour was found to be wrong.

**Also added:** a brief "Saved" toast (`showToast()`, already used
elsewhere on the Admin page) to `savePfSetting()` — applies to every
auto-save control in Processing Folder Automation, not just the new
slider, since they all share this one helper and none of them previously
gave any save confirmation.

**Session close-out — v2.5 Item 1 fully tested and closed.** Tez confirmed
"built and fully tested" — the low-confidence/real-world match-quality
pass that was the item's one remaining open question is done.
`meta/roadmap.html`'s Now #1 card removed entirely (not greyed out — per
the completed-item convention), remaining two Now cards renumbered 1–2,
OPDS scoping now Now #1. Docs updated: this file, `comicvault-changes-v2.5.md`
(Item 1's final status), `ADMIN_SPEC.md` §11.4.4 (new slider documented),
`EDITOR_SPEC.md` §9 (status line), `CHANGELOG.md`, `meta/roadmap.html`.


---

## 2026-07-04 (later same day) — OPDS scoping session: ruled out; mobile app bugs surfaced

**Chat session, no Code/build work.** First scoping pass on the v2.5 "OPDS —
connecting 3rd-party readers" holding-list item, target reader CDisplayEx on
Android tablet.

**Research finding that reframed the session:** CDisplayEx doesn't support OPDS
— it only connects to Komga or Kavita via their own proprietary REST APIs.
"Add OPDS" as originally conceived wouldn't have gotten CDisplayEx connected at
all; the only route would've been a Komga-API-compatibility shim against
another project's undocumented, unstable surface.

**Decision (Tez's call, full reasoning in `DECISIONS.md`):** rule out OPDS and
the Komga-shim alternative entirely, not just defer them. Reasoning wasn't only
the CDisplayEx mismatch — this is a single-connection use case, and Tez
concluded that even in a future public-release scenario, maintaining
ComicVault's own client apps beats supporting third-party readers he can't
control. Decision: keep developing the existing Flutter app instead.

**Mobile app bugs surfaced during the same conversation, previously unreported:**
Tez confirmed the Flutter app currently fails to connect to the server and
crashes when selecting a CBZ on the tablet — logged as `BUGS.md` BUG-019 and
BUG-020. Neither is a new regression as far as anyone knows; they weren't
caught earlier because recent attention was on server/web dev, not Flutter.
Tez flagged a possible network change as a separate contributing factor for
BUG-019, explicitly not confirmed and needing its own investigation rather than
being assumed as the cause. Also reactivated BUG-008 (Flutter's 2000 AD tab
still calling endpoints removed in v2.2) — dormant since 2026-06-29 pending
"if Flutter dev starts," which it now is.

**Docs updated this session:** `DECISIONS.md` (OPDS ruling + reasoning),
`BUGS.md` (BUG-019, BUG-020 added; BUG-008 reactivated), `ROADMAP.md` (Mobile
Reader entry corrected and moved from "Paused indefinitely" to a new "Next
session" section; OPDS holding-list entry marked ruled out and removed),
`comicvault-changes-v2.5.md` (header status updated), this file.
`meta/roadmap.html` still needs Code to regenerate it to drop the OPDS Now-card
and add the mobile connectivity fix — not hand-edited here per convention.

**Next session:** root-cause BUG-019/BUG-020 (ruling the network-change theory
in or out on its own first), then scope the Flutter fixes — likely including
real UI work since the removed 2000 AD tab now needs a Custom Tabs equivalent
that didn't exist when the tab was first built. Tez's framing: "there is a lot
to scope" — expect this to need its own dedicated scoping session before any
of it goes to Code.

---

## Session — 2026-07-04 (later same day): BUG-019 on-device verification — fixed and closed

**Goal.** Tez's Lenovo tablet was physically connected this session, unblocking
the on-device confirmation that BUG-019's code-level fix (from earlier the same
day — see previous session entry) had been waiting on.

**Tablet connection sequence:** `flutter devices` initially showed the tablet
(`HGR3SJY1`) as detected but "not authorized" — Windows could see it over USB
but the tablet hadn't approved this computer for debugging yet. Tez accepted
the on-device USB-debugging authorization prompt; the device then showed as a
normal authorized target.

**Build detour:** `flutter build apk --release` ran for ~25 minutes with no
sign of failure — confirmed via `tasklist`/CPU-time deltas that Gradle/Java
was genuinely still compiling, not hung, but this is far outside normal for
this project. Killed it (`TaskStop`) and switched to `flutter build apk
--debug` instead, which is sufficient for a manual verification pass and skips
R8 minification/resource shrinking. Discovered mid-swap that stopping the
release build's CLI wrapper hadn't stopped the underlying Gradle daemon — it
kept running the interrupted release task in the background (`./gradlew
--status` showed it `BUSY`), which was silently blocking the new debug build
from starting. Ran `./gradlew --stop` to free the daemon, then the debug build
completed normally. (Both APKs, oddly, ended up finished on disk afterward —
the abandoned release build had apparently kept running to completion via the
daemon despite the CLI kill.) **Worth knowing for next time:** if a Flutter/
Gradle build seems to hang after switching build modes mid-session, check
`gradlew --status` for a stuck daemon before assuming the new build itself is
broken.

**First on-device test still failed** — installed the debug build (with the
`/api/ping` fix from the earlier session) and the app still showed "Server
offline". Reading the tablet's actual saved preferences (`adb shell run-as
com.comicvault.comicvault cat .../shared_prefs/FlutterSharedPreferences.xml`)
found the real cause of *this* failure: `flutter.server_url` was saved as
`http://192.168.0.151:8000` — port 8000, not 9424 where the server actually
listens (confirmed via `netstat` that nothing is listening on 8000 at all).
This was a second, independent problem stacked on top of the auth-gating bug
— the earlier session's curl-based verification tested the correct port
directly and never exercised the app's actual stored configuration, so it
couldn't have caught this.

**Fixed via the app's own Settings screen** (not a raw prefs edit) — corrected
the server URL field to `http://192.168.0.151:9424`, tapped "Test connection"
(confirmed "Connected successfully"), then Save. Force-stopped and relaunched
the app fresh: the offline banner was gone, the Series/Singles/All/2000 AD
tabs appeared, and the library loaded real cover thumbnails from the server
over the LAN — full end-to-end confirmation on the real device. Scratch
screenshots taken during verification (tablet_check.png etc., in the repo
root) were deleted afterward per the close-of-session cleanup step.

**BUG-019 is fixed and closed** — moved from `BUGS.md` to
`archive/bugs-fixed-archive.md` with both root causes documented. `BUG-020`
(CBZ-select crash) remains open and undiagnosed; nothing in this session's fix
touched the CBZ-open path, so it isn't expected to have been incidentally
resolved. `BUG-008` (2000 AD tab calling removed endpoints) also remains open.

**Docs updated this session:** `BUGS.md` (BUG-019 entry removed, BUG-020's
cross-reference updated to point at the archive), `archive/bugs-fixed-archive.md`
(BUG-019 fixed entry appended, both root causes documented), `CHANGELOG.md`,
`ROADMAP.md` ("Next session" section updated to reflect BUG-019 done), this
file. `meta/roadmap.html` not touched — bug fixes don't get their own
Now/Next lane card per `working-rules.md`'s Inbox-workflow note ("a bug can go
straight into `BUGS.md` without touching the roadmap at all"), and no existing
card referenced BUG-019 specifically to remove.

**Next session:** BUG-020 (CBZ-select crash) is the next open Flutter item —
still fully undiagnosed, no stack trace or repro detail beyond "select a CBZ,
it crashes." BUG-008 (2000 AD tab) and the broader Custom-Tabs-equivalent
scoping question are still parked behind it, per the previous session's
scoping note.

---

## Session — 2026-07-04 (later same day): BUG-020 diagnosis and fix — CBZ-select crash

**Goal.** Diagnose BUG-020 (Flutter app crashes selecting a CBZ on the tablet).
Tez asked directly whether it could be a file-association problem.

**Diagnosis, by live repro on the tablet with logcat capture** — reachable via
the "Open local CBZ file" button (`library_screen.dart`), the app's only
local-file path, shown whenever the server reads offline. Forced the tablet
offline (`svc wifi disable`) to reach it. Two independent, both-real bugs:

- **Cause 1 (the actual crash):** picking a real 346MB CBZ from the tablet's
  own library died instantly — captured `FATAL EXCEPTION:
  java.lang.OutOfMemoryError` inside `file_selector_android`'s
  `FileSelectorApiImpl.toFileResponse`. That plugin loads the entire picked
  document into one Java byte array before returning it to Dart; Android's
  default per-app heap ceiling is 256MB, so any CBZ over ~200–250MB blew it
  every time.
- **Cause 2 (Tez's "file association" hunch, confirmed correct):**
  `content query` against `content://media/external/file` showed two `.cbz`
  files on the same device carrying two different OS-assigned MIME types
  (`application/x-cbz` vs `application/vnd.comicbook+zip`), depending on
  when/how each was indexed. The picker's `XTypeGroup(extensions: ['cbz'])`
  filter only matched one — files with the other MIME type showed in the
  picker (generic icon, no thumbnail) but tapping them did nothing at all,
  confirmed via `uiautomator dump` (real clickable grid item) and
  `dumpsys activity activities` (tap never left the picker activity).

**Fix, three rounds, each round caught by testing on the real tablet rather
than by reasoning alone:**

1. Replaced `file_selector` with a native `MethodChannel`
   (`comicvault/local_file_picker`, handled in `MainActivity.kt`): launches
   `ACTION_OPEN_DOCUMENT` with `type = "*/*"` (fixes Cause 2 — no OS MIME
   filter left to drift) and streams the result to a cache file in fixed
   64KB chunks via `ContentResolver.openInputStream()` (fixes Cause 1 — flat
   memory regardless of file size). Removed `file_selector` and its platform
   packages from `pubspec.yaml`.
2. Testing round 1 revealed a second problem: `LocalCbzService` re-read and
   re-decoded the *entire* archive from disk on every `listPages()`/
   `readPage()` call — 136 full reads of a 346MB file for a 136-page issue,
   not 136 reads of one page. This was invisible before because the old
   picker crashed before this code ever ran. Fixed by caching the decoded
   `Archive` per file path, decoding once and reusing it.
3. Testing round 2 revealed a third problem: even with the archive cached,
   `LocalReaderScreen._load()` still eagerly extracted every page into a
   `List<Uint8List>` up front — all 136 pages' decompressed bytes held in
   memory at once, which was enough sustained pressure that Android's
   system-wide low-memory killer terminated the app ~30–45s after opening
   (not an app-level crash — `dumpsys` showed ~2GB RSS at kill time, "device
   is not responding"). Fixed by making `LocalComicPageView` read each page
   on demand inside its `itemBuilder`s instead of pre-loading everything, and
   capping `Image.memory`'s `cacheWidth` to the device's physical screen
   width (this issue's pages were 1988×3056px — ~24MB per page once decoded
   at full source resolution, which Flutter uses by default regardless of
   display size). Added `LocalCbzService.clear()`, called from
   `LocalReaderScreen.dispose()`, so the cached archive doesn't outlive the
   reader screen.

**Verification — an honest, not-entirely-clean result.** All fixes tested
against both the original 346MB/136-page file and the MIME-mismatched 56MB
Cyberpunk file. Both causes are confirmed fixed — MIME mismatch no longer
blocks selection, and the instant pick-time crash is gone. But a **debug**
build of the fully-fixed code still got killed by the OS on the 346MB file
after ~20–45s (~2GB RSS) — the round-3 fix alone wasn't sufficient in debug
mode. Rebuilt as a **release** build (162.6s, R8/minification) and re-tested
the same file on the same device: RSS held flat at ~200–212MB through 80+
seconds idle and through normal-paced scrolling — no kill. Debug builds carry
substantially heavier baseline memory overhead than release builds (JIT
runtime, debug metadata, no tree-shaking); that gap explains most of the
difference. **This was a real, deliberate scope decision made mid-session
with Tez** (see `AskUserQuestion` exchange) — offered to stop after the first
two fixes and log the memory issue separately, or push through with a
release-build verification; Tez chose to push through.

**Caveat for future sessions, written down because it cost real time this
session:** if a debug build (`flutter run`, `flutter build apk --debug`)
seems to still struggle with a large local CBZ, that alone isn't evidence the
fix regressed — verify against a release build first. This tablet's 3.7GB
total RAM is also unusually tight for its device class; a large enough scan,
or a lower-RAM device, could in principle still hit this ceiling. The fix
removes the *reliable, every-time* crash for realistic file sizes — it isn't
a hard guaranteed ceiling for arbitrarily large files.

**Gradle build slowness (unrelated aside, noted for future sessions):**
both this session's release build and an earlier one (during BUG-019's
on-device work) ran unusually slowly at times, apparently I/O-bound rather
than CPU-bound in the slow stretches (CPU-time deltas near zero while the
Gradle daemon reported BUSY). Root cause not confirmed — Windows Defender
real-time scanning of build output is the leading suspect but wasn't
verified (no admin access to check exclusions this session). A stuck/BUSY
daemon left over from a killed build (via `TaskStop`) also silently blocked
a subsequent build from starting once this session — `./gradlew --stop`
before retrying a build after killing one mid-flight avoids this.

**BUG-020 is fixed and closed** — moved from `BUGS.md` to
`archive/bugs-fixed-archive.md` with both causes and all three fix rounds
documented, including the debug-vs-release caveat.

**Docs updated this session:** `BUGS.md` (BUG-020 entry removed, BUG-008's
cross-reference updated), `archive/bugs-fixed-archive.md` (BUG-020 fixed
entry appended), `CHANGELOG.md`, `ROADMAP.md`, this file.

**Next session:** `BUG-008` (Flutter's 2000 AD tab calling endpoints removed
in v2.2) is the last open item from the original mobile-bugs report. The
broader Custom-Tabs-equivalent scoping question for Flutter (replacing the
hardcoded 2000 AD tab) is still parked behind it, per earlier sessions'
scoping notes.

---

## Session — 2026-07-04 (later same day): BUG-008 fix — 2000 AD tab removed

**Goal.** Fix BUG-008, the last open item from the mobile-bugs report. Tez's
explicit call up front: remove the 2000 AD tab completely rather than build a
Custom Tabs equivalent for Flutter — it was removed from the main web library
when Custom Tabs shipped, and Flutter never got its own version of that
feature to replace it with.

**Scope check before building:** grepped the whole `lib/` tree for `2000ad`/
`TwoThousandAd` — confirmed all references were contained in exactly three
files (`two_thousand_ad_screen.dart`, `library_screen.dart`,
`api_service.dart`), nothing in `main.dart`'s routes, no test references.
Clean, self-contained removal.

**Built:**
- Deleted `flutter_app/lib/screens/two_thousand_ad_screen.dart` entirely
  (`TwoThousandAdTab`, `TwoThousandAdYearScreen`, `_YearCard`, `_ProgTile`).
- `library_screen.dart`: `TabController(length: 4, ...)` → `length: 3`;
  removed `Tab(text: '2000 AD')` from the `TabBar` and the `TwoThousandAdTab`
  child from the `TabBarView`; removed the now-dead import.
- `api_service.dart`: removed `get2000adYears()`/`get2000adYear()` — the two
  methods that called the already-removed backend endpoints.
- `flutter analyze lib/` — no issues.

**Verified on Tez's real Lenovo tablet** (debug build): library screen now
shows exactly three tabs — Series, Singles, All — no 2000 AD tab. Confirmed
2000 AD issues (2000 AD, 2000 AD Sci-Fi Special, 2000 AD Yearbook, 30 Days of
Night, etc.) still show up normally in Series and All — they're ordinary
library issues, unaffected by removing the special tab. Tapped through all
three tabs with no errors or crashes.

**Aside, not a regression:** reinstalling the app during this session's
testing (`flutter install` uninstalls before reinstalling) reset the saved
server URL back to a stale value via Android's own auto-backup/restore —
same as it did once during the BUG-020 session. Fixed the same simple way,
through the app's own Settings screen. Noting it again here since it'll keep
happening on every fresh install/uninstall cycle during testing — expected
platform behaviour, not a code bug.

**BUG-008 is fixed and closed** — moved from `BUGS.md` to
`archive/bugs-fixed-archive.md`. **This closes out the entire 2026-07-04
mobile-bugs report** — BUG-019 (connection failure), BUG-020 (CBZ-select
crash), and BUG-008 (2000 AD tab) were all found in the same report and are
now all fixed.

**Docs updated this session:** `BUGS.md` (BUG-008 entry removed),
`archive/bugs-fixed-archive.md` (BUG-008 fixed entry appended),
`CHANGELOG.md`, `ROADMAP.md`, this file.

**Next session:** no open Flutter bugs remain from this report. Two
previously-parked future-scope items remain, not urgent: (1) Reader → Server
progress sync for local/offline mode; (2) a Custom-Tabs-equivalent for
Flutter, if that's ever wanted (not committed to — this session deliberately
chose removal over building a replacement).

---

## Session — 2026-07-05: BUG-017 fix — Android .cbz file association

**Goal.** Fix BUG-017 (inbox capture from 2026-07-04/05 Sunday triage):
tapping a `.cbz` file on Android and choosing "Open With" never offered
ComicVault as a handler at all.

**Scope decision, confirmed with Tez before building:** the bug was logged
as "cbz/r," but `LocalCbzService` only ever decodes via `ZipDecoder()` —
there's no RAR support anywhere in the app. Scoped the fix to `.cbz` only;
`.cbr` stays exactly as unassociated as before (no regression, just not
fixed) rather than adding an association that would just trade one error
message for another.

**Built:**
- `AndroidManifest.xml` — two new `<intent-filter>` blocks on `.MainActivity`
  for `ACTION_VIEW`: a MIME-type-based one (`application/vnd.comicbook+zip`,
  `application/x-cbz`, `application/zip`) and a `pathPattern`-based fallback
  (`mimeType="*/*"` + `.*\.cbz`) for file managers that send
  `application/octet-stream` or no useful type.
- `MainActivity.kt` — new `resolveSharedUri` method on the existing
  `comicvault/local_file_picker` channel, reusing the `copyToCache()` helper
  already written for the local file picker (BUG-020) to resolve an incoming
  `content://`/`file://` URI to a real cache-file path.
- `local_cbz_service.dart` — thin `resolveSharedUri()` Dart wrapper.
- `main.dart` — `_handleLink()` extended: a `content://`/`file://` URI (as
  opposed to the existing `comicvault://read/{id}` case) now resolves via
  `resolveSharedUri()` and pushes `/reader/local`, the same route the in-app
  file picker already uses.

**Real bug found during testing, not anticipated in the plan.**
`FlutterActivity`'s default Android embedding behavior auto-converts any
incoming `ACTION_VIEW` intent into a raw `Navigator.pushNamed()` call using
the URI's literal path as the route name — this runs *before* `app_links`'
own `uriLinkStream` (what `_handleLink` listens on) ever sees the intent.
Since a path like `/storage/emulated/0/Download/foo.cbz` isn't a registered
route, this crashed with "Could not find a generator for route" and
silently swallowed the intent — meaning the manifest change alone would
have gotten ComicVault into the Open With list, but tapping it would have
crashed instead of opening. Root-caused by attaching `flutter run` directly
to Tez's tablet and reading the live Dart exception (plain `adb logcat`
against an already-installed APK didn't surface it clearly). Fixed by
overriding `shouldHandleDeeplinking()` to return `false` in `MainActivity`,
leaving `app_links` as the sole path handling incoming intents — this is a
stock Flutter/Android interaction, not specific to anything else in this
codebase.

**Verified, extensively, via `adb` against Tez's real tablet before any
manual step:**
- `pm resolve-activity` / `dumpsys package com.comicvault.comicvault`
  confirmed Android now resolves ComicVault as a matching `.cbz` handler for
  all three registered MIME types plus the extension-pattern fallback.
- Firing real `VIEW` intents confirmed the crash was gone post-fix.
- Temporarily added debug prints (removed before the final build) traced the
  intent all the way through `_handleLink` → `resolveSharedUri` → the native
  method, with no exceptions in the Dart/native bridge.
- The one thing `adb` couldn't fully simulate: a real, permission-granted
  `content://` URI. A hand-built `file://` URI correctly failed with
  `EACCES` (Android's scoped storage doing exactly what it's supposed to),
  and MediaStore's raw path querying is itself locked down for the same
  reason — both expected platform behavior, not app bugs, but they meant the
  very last step needed a real tap-through rather than another adb
  workaround.

**Tez's manual test passed:** tapped a `.cbz` in the file manager, ComicVault
now appears under Open With, selected it, opened correctly into the reader.

**Aside — bug-numbering collision noticed, not touched:** `archive/bugs-fixed-archive.md`
already has an unrelated, earlier-fixed bug also numbered BUG-017 ("All-tab
Favourites filter only checks one issue per series," fixed 2026-07-01). This
fix's entry was appended using the same "BUG-017" label the live `BUGS.md`/
`ROADMAP.md`/`meta/roadmap.html` all already referenced it by — didn't
renumber the historical entry, since that's outside this session's scope and
risks its own confusion. Worth a glance next time bug numbers are assigned.

**Docs updated this session:** `BUGS.md` (BUG-017 entry removed),
`archive/bugs-fixed-archive.md` (BUG-017 fixed entry appended), `CHANGELOG.md`,
`ROADMAP.md` (stale BUG-017 cross-reference under the Mobile → Server Sync
item corrected), `meta/roadmap.html` (same cross-reference corrected), this
file.

---

## Session — 2026-07-05: Sort by Filename Processing Tool built — v2.5 Item 2

**Goal.** Build a new Processing Tool from a build brief handed directly to
Code — "FINAL SPEC: Sort by Filename Processing Tool (handoff to Code)" —
porting the standalone `create-folders-from-file.py` script (found at
`D:\workshop\Scripts\Python\create-folders-from-file.py`) into ComicVault
following the existing `rename_tool.py`/`archive_convert.py` pattern.

**Built**, following the established Processing Tool shape exactly:
`backend/filename_sort.py` (pure `sort_by_filename(folder)` core logic),
`backend/filename_sort_log.py` (audit log, `convert_log.py`'s shape),
`backend/routers/filename_sort.py` (`browse`/`drives`/`run`/`status`,
mirroring `processing_folder.py`), registered in `main.py`. Frontend: new
"Sort by Filename" card in Admin → Processing Tools (folder picker, Run,
terse result line, expandable failure detail), wired into
`processingTools.js`.

**Bug found and fixed before the manual test pass, via direct testing —
not found by inspection.** The brief named three edge cases: a same-basename
CBZ+CBR pair should both move into one folder with no error; a pre-existing
target folder holding a *different* file should fail that one file with a
clear reason; a missing/unreachable folder should fail cleanly with nothing
logged. Built a scratch folder covering exactly these cases and ran
`sort_by_filename()` directly (no server needed) before touching the UI.
The first-pass collision check only compared the exact destination path
(`folder\filename`) — it let a file move into a folder that already held
something else entirely, as long as that unrelated file didn't happen to
share the exact same name. Fixed by checking whether the target folder
(if it already exists) holds any entry whose own basename doesn't match
the folder's name, before allowing the move — this correctly lets a
same-basename sibling through while rejecting genuinely unrelated content.
Re-ran the same scratch test afterward to confirm all three named cases now
behave as specified (see `DECISIONS.md` for the full reasoning).

**Verification order, following the port-then-test-then-log discipline this
project uses:** import/syntax checks; `sort_by_filename()` run directly
against a scratch folder (same-basename pair, unrelated-folder-content
collision, a `Thumbs.db`/`.txt` pair confirming the extension filter, and a
missing-folder case); the router's background-task function (`_run()`) run
directly to confirm the concurrency guard, result shape, and that a
folder-not-found error writes nothing to the log. All test artifacts —
the scratch folder and the `filename_sort_log.md` file the router test
created — were deleted afterward; nothing in the real library, config, or
Processing folder was touched. Server restart for the live UI pass was
Tez's own action (a live tray-managed server was already running on the
configured port; rather than restart it mid-session, Code asked and Tez
chose to restart it himself when convenient). **Tez confirmed "test
passed"** afterward via the live Admin UI — this is the gate this session's
doc updates were held for.

**Scope, per the brief — explicitly deferred, not built:** automation/
scheduling wiring into `scheduler.py`/Processing Folder Automation; a second
script (move-to-library, not yet written); a dirty-folder cleanup tool
(flagged as a plausible future tool, not scoped); `.bak` file handling
(tied to the separate Convert Archives review, not touched here — moot
today since `.bak` never matches the CBZ/CBR extension filter anyway); any
registry/dropdown UI for multiple scripts (stays a single fixed
disabled-`<select>` until a second script exists).

**Docs updated this session:** `ADMIN_SPEC.md` (new §11.5 Sort by Filename,
Change Log entry), `comicvault-changes-v2.5.md` (new Item 2), `DECISIONS.md`
(collision-rule correction), `CHANGELOG.md`, this file.

---

## Session — 2026-07-05: Mobile ↔ Server Reading-State Sync built — v2.5 Item 3

**Goal.** Close the gap `mobile-server-sync-scope.md` (Cowork discovery
session, same day) and `ROADMAP.md`'s "v2.5 — holding list" Item 2 flagged:
reading progress made offline on the tablet never reached the ComicVault DB.
A full technical plan was written before build (backend endpoints, conflict
algorithm, Flutter service design), reviewed and approved, then built
end-to-end same session.

**Scope decision, before any code:** research surfaced that the Flutter app
had no way to download a comic from the server for offline reading at all —
its existing "local file" mode only opened arbitrary CBZs copied onto the
device manually or via Android "Open With," tracked by file path only, with
no timestamp and no link to any server `issue_id`. Without that link there
was nothing concrete to sync for the scope doc's actual scenario ("tablet
with comics downloaded for a trip"). Confirmed with Tez: build a proper
download-for-offline feature as part of this item (not a filename-matching
heuristic, not deferred). Also confirmed: last-write-wins by timestamp over
highest-page-wins, matching the scope doc's recommended default.

**Backend built and scratch-tested before any Flutter work:**
- `GET /api/issue/{id}/download` (`backend/routers/reader.py`) — whole
  CBZ/CBR file via `FileResponse`, modeled on `get_cover`'s pattern. Tested
  directly (function call, no app boot) against a scratch DB + scratch CBZ:
  happy path, unknown issue_id, `missing=True`, file absent from disk despite
  `missing=False`, and the CBR-extension media-type branch — 5/5 passed.
- `POST /api/sync/progress` (`backend/routers/sync.py`, new file) — batch
  reconciliation, last-write-wins by comparing the client's captured
  `updated_at` against the server's `last_read_at`; a missing server row or
  an exact tie goes to the incoming client write. Each item commits
  independently (a dropped connection mid-batch leaves unprocessed items
  simply retried next trigger, no rollback machinery); unknown `issue_id`
  returns `not_found` and the batch continues, mirroring `progress.py`'s
  existing bulk-endpoint "skip unknown ids" pattern. Tested against a
  scratch DB covering `client_applied` (no prior row, and client newer than
  a stale server row), `server_kept` (server newer than a stale client
  push — with the DB row confirmed unmutated, not just the response body),
  `not_found` continuing the batch, and an exact-timestamp tie resolving to
  the incoming write — 8/8 assertions passed. No `reading_progress` schema
  change needed. Registered in `main.py` alongside `progress.router`, same
  ungated tier (no auth exists on these routes today, resolving the scope
  doc's "auth after long offline periods" open question — there's no
  session to expire).

**Timezone bug caught during plan review, before it ever reached a device:**
Dart's `DateTime.now()` is local time, and `.toIso8601String()` on a local
`DateTime` emits no "Z"/offset suffix — a client that captured sync
timestamps that way would silently have every last-write-wins comparison
skewed by the tablet's UTC offset, systematically favoring or disfavoring
the client depending on which side of UTC the timezone falls. Fixed by
mandating `DateTime.now().toUtc()` everywhere a sync-relevant timestamp is
captured (`sync_store.dart`), with a defensive naive-to-UTC fallback and
explicit "Z" handling added on the backend (`sync.py`'s `_parse_client_ts()`)
as a safety net, not a substitute for getting the client side right.

**Flutter built, following the backend:**
- `DownloadedIssue` model + `DownloadService` — HTTP fetch, local manifest
  in `SharedPreferences` (same pattern as `SettingsService`'s existing
  `recentLocalFiles`/`local_progress:*`; a personal library's realistic
  downloaded set is dozens of entries, not thousands, so no new local-DB
  dependency was added). Download/delete affordance added to each issue row
  in `series_screen.dart`'s `_IssueTile` (converted from `StatelessWidget`
  to `StatefulWidget` to own download-in-progress state); a "Downloaded"
  section added to `library_screen.dart`'s offline view, kept visually and
  conceptually separate from the pre-existing ad-hoc "Recent files" list.
- `SyncStore` (per-issue pending-progress record, dirty when `updatedAt`
  is newer than `syncedAt`) + `SyncService.syncNow()` (push dirty records,
  apply the server's per-item outcome — overwriting the local record with
  the server's state when `server_kept`, so the next time that downloaded
  issue is opened it reflects the true resumed-elsewhere state).
  `LocalReaderScreen` extended with an optional `issueId`/`syncStore` —
  arbitrary local files (`issueId == null`) keep working exactly as before
  this item; only downloaded, issue_id-linked files get a timestamped sync
  record on every page turn. New `LocalReaderArgs` route-argument class
  replaces the bare `String filePath` `/reader/local` used before, updated
  at both existing call sites (`library_screen.dart`, `main.dart`'s
  `_openSharedCbz`).
- Trigger wiring: manual "Sync now" AppBar button; reconnect/foreground
  piggybacked on the existing `_checkAndLoad()`/`checkConnection()` call
  rather than adding `connectivity_plus` (deliberately rejected, per the
  scope doc's "don't over-build" framing) — but this alone would have
  missed "closed the reader, foregrounded the library," since
  `LibraryScreen` sits at the app root and is only pushed once, so its own
  `initState()` never re-fires on back-navigation. Added a small
  `RouteObserver` (new `lib/route_observer.dart`, shared between
  `main.dart` and `library_screen.dart` to avoid a circular import) +
  `RouteAware.didPopNext()` to actually catch that case.
- "Synced Xm ago"/"Never synced" label in the AppBar; a "Not synced" marker
  on any downloaded issue row with unpushed local progress.

**Code-level verification before any device involvement:** `flutter analyze`
clean throughout; a debug APK (`flutter build apk --debug`) built
successfully; `SyncStore`'s dirty-flag logic covered by 4 isolated unit
tests (fresh-record dirty, `markSynced` clearing + re-dirtying on a new page
turn, multiple issues tracked independently, `markSynced` on an unknown
issue_id being a safe no-op) — all 4 passed, scratch test file deleted
afterward per this project's convention of not maintaining a permanent
automated suite.

**Tez's manual test, on the real Lenovo tablet against the real server
(restarted first to pick up the new endpoints):** downloaded an issue, read
several pages with the server unreachable, reconnected, and confirmed the
sync pushed correctly — **"signed off, passed."** One planned check (mark
the same issue further along via the web UI, then reopen the stale
downloaded copy without syncing first, to visually confirm `server_kept`
doesn't get clobbered) could not be carried out — see BUG-021 below. Doesn't
affect this item's correctness, since that exact code path (server
timestamp newer than an incoming stale client push, DB row left unmutated)
is already covered by the backend scratch tests above.

**Found during the manual pass, logged separately, not fixed here
(`BUGS.md` BUG-021):** there's currently no working way to view or re-mark
progress on a comic outside the Flutter app on this machine — the web UI
never had a reader (`SPEC.md` §11 — by design, the Read button deep-links
into Flutter instead), and the standalone Windows reader EXE built in V1
was never rebuilt or carried across into this V2 checkout. Flagged as its
own follow-up item, out of scope here.

**Also worth recording, not a code change:** installing this session's
debug-signed build over a previously release-signed one on the same tablet
forced Android to uninstall the old app first (differing signing keys can't
upgrade in place), which wiped the app's `SharedPreferences` — server URL
reset to default, recent-local-files list cleared. Tez reconfigured the
server URL by hand before testing. Worth remembering next time a
differently-signed build lands on the same device.

**One more bug caught after sign-off, while finishing doc close-out:**
`DownloadService.download()` always saved the downloaded bytes under a
hardcoded `{issueId}.cbz` path regardless of the issue's real format — a
CBR download would have silently mislabeled itself, then failed opaquely at
the page-count step (`LocalCbzService` only decodes via `ZipDecoder`, per
`SPEC.md`'s already-documented CBR gap in Flutter local mode). Fixed:
`ApiService.downloadIssue()` now returns the real extension from the
response's `Content-Type` header, and a failed page-count read deletes the
partial file and raises a clear message instead of a raw decode exception.
The already-tested CBZ path is unchanged (content-type still resolves to
`.cbz`); `flutter analyze` clean and a fresh debug build confirm this, but
it wasn't re-tested on-device — the tablet was disconnected by this point,
and the fix only touches a path Tez's sign-off didn't exercise.

**Docs updated this session:** `SPEC.md` (reading_progress sync note, two
new REST API rows), `comicvault-changes-v2.5.md` (new Item 3), `BUGS.md`
(new BUG-021), `ROADMAP.md` (Mobile → Server Sync holding-list item closed),
`CHANGELOG.md`, `meta/roadmap.html` (Now #1 card removed, remaining two
renumbered, bug count corrected), this file.
