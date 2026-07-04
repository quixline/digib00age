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
