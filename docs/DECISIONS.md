# ComicVault — Decisions Log

Rationale log — *why*, not *what*. Only non-obvious calls go here; routine
implementation choices are covered in `SPEC.md` / `EDITOR_SPEC.md` / the feature
specs and aren't repeated. Newest first.

---

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
