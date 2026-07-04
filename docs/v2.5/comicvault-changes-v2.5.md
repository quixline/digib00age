# ComicVault — v2.5: Build Plan

> **Status: Item 1 built and fully tested 2026-07-04 — closed.** `docs/v2.5/`
> created this session (Code, per `ROADMAP.md`'s note that the working
> folder gets created alongside implementation rather than ahead of it —
> real v2.5 triage/scoping for the remaining holding-list items hasn't
> happened yet, this queue currently holds Item 1 only). OPDS / 3rd-party
> reader connection was scoped 2026-07-04 and **ruled out** (see
> `DECISIONS.md` and `ROADMAP.md`) — not built here, removed from the
> holding list. That same session surfaced two Flutter bugs (`BUGS.md`
> BUG-019, BUG-020) plus a reactivated one (BUG-008), so next up is
> scoping and fixing the mobile app instead (`ROADMAP.md` "Next session").
>
> **How to use this document**
> This is the ordered build queue for v2.5. Paste into a Claude Code session
> alongside the referenced spec files. Items are marked ✅ when built and
> verified. Bugs and minor fixes are tracked separately in `BUGS.md` — don't
> add them here unless they block a build item.
>
> **Always reference items from other docs as "v2.5 Item N", never bare
> "Item N"** — see `meta/working-rules.md` "Version-qualified references."

---

## Item 1 — ComicTagger + ComicVine integration ✅

**Feature.** Full Editor "Search Online" (manual match against ComicVine,
two-step Select Series/Select Issue modal) and Processing Folder
Automation's new CT Auto-Tag stage (Convert Archives → **CT Auto-Tag** →
Convert Images), per `EDITOR_SPEC.md` §9 and `ADMIN_SPEC.md` §11.4 — both
scoped and decision-locked in four sessions 2026-07-03 (`DECISIONS.md`),
built and manually verified 2026-07-03/04.

**Built:**
- `backend/ct_bridge.py` (new) — bridge into ComicTagger's `comicapi`/
  `comictalker`/`comictaggerlib.issueidentifier` libraries. Series/issue
  search, single-issue full-detail fetch, `GenericMetadata` → ComicVault
  field-dict mapping, the CT Auto-Tag automation's identify pipeline.
- `backend/ct_autotag.py` + `backend/ct_autotag_log.py` (new) — the CT
  Auto-Tag stage's core callable and its audit log.
- `NeedsReview` XML tag added to `COMICINFO_TAGS`, with explicit
  clear-on-save wired into both `editor_basic.py` and `editor_full.py`.
- `backend/routers/editor_full.py` — three new Search Online endpoints
  (series search, issue list, confirm-match).
- `backend/routers/processing_folder.py` — amended to the 3-stage pipeline,
  new settings keys (`processing_folder_ct_autotag_enabled`,
  `processing_folder_ct_save_low_confidence`, `comicvine_api_key`), new
  Save & Test endpoint.
- Frontend: Full Editor gained a "Search Online" toolbar button, the
  two-step modal, and a red-border/"N Low Confidence" indicator on Column 1
  cards (reuses the existing favourited-card border technique). Admin
  gained the CT Auto-Tag toggle, Save on Low Confidence toggle, and
  ComicVine API key field with live Save & Test feedback.
- `requirements.txt` — `comictagger` pinned to a specific `develop`-branch
  commit (not PyPI's published release — see `DECISIONS.md`).

**Found and fixed during/after build (all same cluster, not separately
logged in `BUGS.md` since found and closed within this build):**
- `identify_file()` didn't fall back to filename parsing when an archive
  had no embedded `ComicInfo.xml` — a file with no tags short-circuited to
  `no_match` before ever calling ComicVine. Now falls back to
  `backend/rename_tool.py`'s `parse_comic_filename()`, defaulting the issue
  number to "1" for one-shots with no issue number in the filename
  (matches ComicTagger's own default-on "If no issue number, assume 1"
  option).
- Match thresholds lowered from CT's own CLI defaults (90/91) to 80,
  matching what Tez had already found worked well in his own standalone
  ComicTagger testing.
- `ct_autotag_file()` was mapping fields from `IssueIdentifier`'s bulk
  candidate-search metadata, which ComicVine's lighter multi-issue endpoint
  doesn't include credits in — Writer/Penciller/etc. were silently empty.
  Fixed with a follow-up single-issue fetch (the same full-detail endpoint
  Search Online's confirm step already used).
- `metadata_to_field_dict()` originally only mapped the subset of fields
  ComicVault's own editor UI exposes. Live testing surfaced this as real
  data loss against Tez's expectation of capturing everything CT/ComicVine
  supplies (even fields the editor doesn't display) — expanded to mirror
  `comicapi/tags/comicrack.py`'s own write mapping field-for-field (Month,
  Day, Notes, Inker, Colorist, Letterer, CoverArtist, Editor, Web, Volume,
  AlternateSeries/Number/Count, SeriesGroup, Characters, Teams, Locations).
  Genre/Format/AgeRating/BlackAndWhite remain deliberately excluded — not
  an "editor doesn't show it" exclusion like the rest, but a correctness
  one (enforced-dropdown validation integrity for the first three;
  a real `"on"` vs `"Yes"` semantic mismatch for the last).
- `Summary` was writing ComicVine's raw HTML markup as literal escaped text
  (`&lt;p&gt;&lt;em&gt;...`) instead of clean plain text — CT's own
  pipeline runs descriptions through `comictalker.talker_utils.cleanup_html()`
  before writing tags; this call was missing. Now applied, including
  correct conversion of embedded `<table>` credit lists to plain text.

**Follow-up work, same item, added 2026-07-04 after the first round of live
testing above:**
- New **Match Ratio Threshold** slider (10–100%, 1% steps) in Admin →
  Processing Folder Automation, right after "Save on Low Confidence" —
  `processing_folder_ct_match_threshold` (default 80, matching the
  previously-hardcoded value). `identify_file()` now reads this at
  call-time instead of hardcoding `series_match_search_thresh`/
  `series_match_identify_thresh`. Added once Tez had more real-world match
  data and wanted to tune it himself rather than rely on a fixed value.
- Found and fixed a misleading-results bug during the low-confidence test
  pass below: the Processing Folder Automation run-complete summary
  reported "N of M succeeded" by counting every non-`failed` status,
  which includes legitimate `no_match`/skipped-low-confidence outcomes
  (correctly `success=True` at the code level — the stage didn't error).
  A 5-file test run that tagged 4 files and correctly no-matched the 5th
  was reported as "5 of 5 succeeded", reading as if all 5 got tagged. Fixed
  with a CT-Auto-Tag-specific summary line breaking out tagged/no-match/
  skipped-low-confidence/failed counts explicitly
  (`frontend/js/processingTools.js` `pollPfStatus()`). The underlying
  `ct_autotag_log.md` audit log was accurate the whole time — this was a
  UI rollup-message bug only.
- Added a brief "Saved" toast (reusing the existing `showToast()` from
  `admin.js`) to `savePfSetting()` — applies to every auto-save control in
  this section, not just the new slider, since they all share this one
  helper. No control on this page previously gave any save confirmation
  except the ComicVine key's deliberate "Save & Test" exception.

**Low-confidence / real-world match-quality testing, completed 2026-07-04
(the item previously tracked as outstanding):** Tez ran a 5-file real-world
comparison test — his standalone ComicTagger 1.5.5 (30% match ratio, Save
on Low Confidence off) successfully tagged 1 of 5 files; the same 5 files
through ComicVault's CT Auto-Tag (actually run at the 80% default, since
the new threshold setting hadn't persisted yet at the time — a sequencing
issue, not a bug) tagged 4 of 5, correctly no-matching the 5th
(`Hard Bargain (2025).cbz`, a one-shot with no issue number in its
filename or on ComicVine). Investigated the discrepancy: all 4 of
ComicVault's successful matches came from filenames with clean, explicit,
unambiguous issue numbers — no evidence of risky guessing. Root cause of
CT's own lower hit-rate was **not conclusively identified** — leading
hypotheses (standalone CT possibly using ComicVine's shared rate-limited
key rather than a personal one; CT 1.5.5 being a genuinely different,
older codebase than the git-commit-pinned dev-branch version ComicVault
runs) were not confirmed with Tez before session close. Not treated as a
ComicVault defect — nothing in ComicVault's own matches was found to be
wrong — but worth revisiting if a similar gap recurs.

**Fully verified by Tez, live, against real files — item closed:** API key
Save & Test; a confident match pulling full/correct data (cross-checked
against an external source); the credits/HTML fixes; the scheduled
Auto-Tag stage run against real titles; the Match Ratio Threshold slider's
save/persist behaviour; and the low-confidence/real-world match-quality
pass above. `meta/roadmap.html`'s Now #1 card removed 2026-07-04 (item
complete) — next up is scoping OPDS.

---
