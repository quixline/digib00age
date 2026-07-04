# ComicVault — v2.5: Build Plan

> **Status: Active — Item 1 built and manually verified 2026-07-04.**
> `docs/v2.5/` created this session (Code, per `ROADMAP.md`'s note that the
> working folder gets created alongside implementation rather than ahead of
> it — real v2.5 triage/scoping for the remaining holding-list items
> hasn't happened yet, this queue currently holds Item 1 only).
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

**Verified by Tez, live, against real files:** API key Save & Test, a
confident match pulling full/correct data (cross-checked against an
external source), the credits/HTML fixes, and the scheduled Auto-Tag stage
run against a couple of real titles. **Not yet tested:** low-confidence
matches and how the Full Editor's Search Online/`NeedsReview` flow handles
resolving them — Tez is sourcing varied sample material for that pass
himself; tracked as `meta/roadmap.html`'s current Now #1 item, not blocking
this item's ✅.

---
