# ComicVault — EDITOR_SPEC.md (V2)

> **How to use this document**
> Paste this entire file into any AI coding session (Claude Code) before writing any code,
> alongside `SPEC.md` for context on the existing V1 system this plugs into.
> This is the single source of truth for the CAPT → ComicVault editor integration.
> Record any deviations at the bottom of this file (Section 12, Change Log), same convention
> as `SPEC.md`.
>
> **Status:** Planning complete. Not yet built. This is the top and only priority — all other
> V2 work (installer, cloud backup, app-store distribution, server discovery, password
> protection, V2.1 fixes) is paused until this is complete and tested.

---

## 1. Overview & Goals

ComicVault currently relies on a separate, pre-existing Flask app ("CAPT") to edit
ComicInfo.xml metadata inside CBZ files. CAPT was investigated in detail (see
`ComicVault_V2_CAPT_Investigation.md` / `v2_investigation_report.md`) and its editing logic —
XML read/parse, field merge, archive rebuild — is sound and is being ported wholesale.
Its Flask shell, in-memory data model, CBR support, dead dependencies, and several
discovered bugs are **not** being carried forward.

**The goal of this build round:** retire CAPT as a separate app entirely. Fold its proven
editing logic into ComicVault's existing FastAPI backend, expose it through two purpose-built
UIs that match ComicVault's design language, and fix the data-hygiene problem (free-text
genre/format/rating values) at the root by making those fields enforced dropdowns.

**Two views, one shared backend core:**

| View | Purpose | Where it lives | Scope |
|---|---|---|---|
| **Basic Editor** | Quick fix to a comic already in the library | Popup/modal from `/issue/{id}` | Single file only |
| **Full Editor** | Tag new comics before they enter the library | New browser tab, from Admin page or tray app | Multi-file, batch, pre-library |

Both views call the same underlying Python core for reading, merging, and writing XML —
there is exactly one implementation of "how to parse a ComicInfo.xml" and "how to rebuild
a CBZ," not two.

---

## 2. Architecture

```
ComicVault (FastAPI, port 8000)
  backend/
    editor/                      ← NEW shared core (no FastAPI/Flask dependency)
      xml_parser.py              ← ported from utils/xml_parser.py
      archive_io.py              ← ported from utils/archive_xml_loader.py + xml_archive_unpacker.py
      field_merge.py             ← ported from widgets/xml_editor.py (build_xml_from_fields)
      batch.py                   ← ported from utils/xml_worker.py (increment-number logic)
      constants.py               ← Format list, AgeRating list (hardcoded, locked)
      genres.json                ← Genre list (editable by Tez directly, not hardcoded)
    routers/
      editor_basic.py            ← NEW — popup endpoints, single-issue scope
      editor_full.py             ← NEW — toolbox endpoints, working-set/queue/batch scope
  frontend/
    issue.html                   ← Edit button (already present) wired to popup
    editor_basic.html / .js      ← NEW — popup UI (Main + More tabs)
    editor_full.html / .js       ← NEW — three-column toolbox UI, own tab
```

**No Flask. No second process. No port 8001 editor server.** Everything above is part of the
single FastAPI app already running on port 8000. `tray_app.py`'s "Metadata Editor" menu item
should be updated to open `http://localhost:8000/editor` instead of the old `:8001` reference
once this is built (flagged here so it isn't missed — it's a one-line change in `tray_app.py`).

**What gets dropped entirely during the port** (confirmed in planning, not carried forward):
- CBR/.rar support (`rarfile`, external `rar.exe` shell-out) — library is all-CBZ
- `Flask-Limiter` — present in CAPT's requirements but never actually used
- `login.html` / `/api/login` — vestigial dead code, posts to a route that doesn't exist
- The `/browse` directory-listing route and custom Explorer file-tree UI — replaced by a
  native OS multi-select file dialog (see Section 5)
- The two hardcoded-path bugs (`"L:\Comics Archives"` typo vs `"L:\Comic Archives"`, and the
  mismatched venv path in `start_xml_editor.bat`) — moot, since the new code reads
  `library_root` from `config.json` like everything else in ComicVault; no hardcoded path
  exists to typo

---

## 3. Shared Editor Core (`backend/editor/`)

### 3.1 Reading
- Open the CBZ with `zipfile.ZipFile` (no CBR branch).
- Locate `ComicInfo.xml` at the archive root.
- Parse with `lxml.etree` in recovery mode (`recover=True`), matching CAPT's existing
  tolerant-parsing behaviour.
- Build a tag→text map; extract the field set in Section 4.
- If XML is missing or parsing fails entirely: fall back to filename-pattern parsing
  (`Series Name #Number (Year).cbz`), same rule already defined in `SPEC.md` Section 9 — this
  logic already exists in ComicVault's scanner and should be reused/shared rather than
  reimplemented a third time if practical.

### 3.2 Writing — full archive rebuild (confirmed, not changing)
Ported as-is from `utils/xml_archive_unpacker.py`:
1. Extract entire CBZ to a temp directory
2. Overwrite `ComicInfo.xml` in that temp directory with merged field values
3. Flatten to a second temp directory
4. `shutil.make_archive(..., "zip", ...)` to rebuild a new zip from scratch
5. `os.replace()` over the original file path

No in-place patching. This was a deliberate decision — full-rebuild is simple and proven;
the collection isn't large enough per-file for rebuild speed to be a problem in practice.

### 3.3 Field merge logic
- Ported from `widgets/xml_editor.py`'s `build_xml_from_fields`.
- Only tags present in the submitted field set are touched; every other existing tag in the
  original XML is preserved verbatim (this is how Volume, Month, Inker, Colorist, Letterer,
  CoverArtist, Characters, Teams, Locations, Manga, and StoryArcNumber survive edits made via
  either editor view, even though neither UI exposes them for editing).
- `BlackAndWhite`: checkbox semantics preserved exactly as today — checked → literal text
  `"on"`, unchecked → tag removed entirely. Matches `SPEC.md` Section 9's parsing rule exactly.
- `Genre`: single CSV string written to one `<Genre>` tag, same as today — no per-genre
  tag-splitting on write (that split only happens on ComicVault's *read* side, into the
  `issue_genres` junction table).
- `Notes`: default text stays **`"Modified with the CAPT"`** for continuity with the large
  number of files already carrying that exact string. Not changed to reflect the new tool name.

### 3.4 Batch / increment-number logic
- Ported as-is from `utils/xml_worker.py`'s `process_xml_files`.
- Sequential: start at issue N, +1 per file in current list order.
- **No collision guardrail** — confirmed acceptable, this is Full Editor only and the
  workflow is "tag a fresh run of issues before they ever reach the library," so there's
  nothing in ComicVault's DB yet to collide with.
- This feature does not exist in the Basic editor at all (single file, nothing to increment
  against) — omit the control entirely from that UI, not just disable it.

---

## 4. Field List & Enforced Dropdowns

Both Basic and Full editors expose the same complete field set (Main + More), **minus
`ScanInformation`**, which is dropped from both editors going forward (existing data in
already-tagged files is untouched; it simply stops being editable).

### Main tab
| Field | XML tag | Control |
|---|---|---|
| Series Title | `<Series>` | Text |
| Issue Title | `<Title>` | Text |
| Issue Number | `<Number>` | Text |
| Increment Number | `<IncrementNumber>` | Checkbox — **Full Editor only, omitted entirely from Basic** |
| Year | `<Year>` | Text/number |
| Genre | `<Genre>` | **Enforced dropdown** — see 4.1 |
| Format | `<Format>` | **Enforced dropdown** — see 4.2 |
| B&W | `<BlackAndWhite>` | Checkbox |
| Age Rating | `<AgeRating>` | **Enforced dropdown** — see 4.3 |
| Summary | `<Summary>` | Textarea |

### More tab
| Field | XML tag | Control |
|---|---|---|
| Count | `<Count>` | Text/number |
| Writer | `<Writer>` | Text (raw CSV, unchanged) |
| Penciller | `<Penciller>` | Text (raw CSV, unchanged) |
| Publisher | `<Publisher>` | Text |
| Page Count | `<PageCount>` | Text/number, auto-counted from archive image count |
| Story Arc | `<StoryArc>` | Text |
| Language | `<Language>` | Text — write `<Language>` only, ignore `<LanguageISO>` on write (matches read-side behaviour already in `SPEC.md` Section 9) |
| Notes | `<Notes>` | Text, defaults to `"Modified with the CAPT"` |

`ScanInformation` is removed from both UIs. No other fields are added beyond CAPT's existing
set — Characters/Teams/Locations/Inker/Colorist/Letterer/CoverArtist remain editor-invisible,
preserved-on-write only, same as ComicVault's issue-detail display rule (`SPEC.md` 20.8).

### 4.1 Genre — enforced, backend-served, editable list
- **Fully enforced select-only dropdown.** No free text, no escape hatch. This is the direct
  fix for the data-hygiene problem documented in `SPEC.md` Section 20.11 and confirmed in the
  investigation report (CAPT's existing "dropdown" was actually free-text-with-suggestions
  and never enforced anything).
- List is **not hardcoded** — served from `backend/editor/genres.json`, a flat array Tez can
  edit directly at any time as the library is worked through. New endpoint: `GET
  /api/editor/genres`. Both Basic and Full editors call this same endpoint, so they can never
  drift out of sync with each other.
- Starting list (21 values, from `xml-editor-design-and-function.md`, open to addition):
  Crime, Superhero, Sci-Fi, Western, War, Action, Adventure, Romance, Biography, Suspense,
  Cyberpunk, Comedy, Art, Fantasy, Horror, Fiction, Mystery, Thriller, Non-Fiction, Drama,
  Historical.

### 4.2 Format — enforced, hardcoded, locked
- **Fully enforced select-only dropdown.** Locked, hardcoded backend constant — confirmed
  final, no editing mechanism needed.
- List (10 values): Graphic Novel, Series, One Shot, Anthology, Art Book, Limited Series,
  Special, Trade Paper Back, Annual, Other.
- This list also governs the Section 20.12 singles-routing rule already defined in `SPEC.md`:
  `Series` or `Limited Series` → series page; everything else → issue page; folder as
  fallback where Format is blank. Confirmed unchanged against this exact list.

### 4.3 AgeRating — enforced, hardcoded, locked
- **Fully enforced select-only dropdown.** Locked, hardcoded backend constant.
- List (8 values): Everyone, Early Childhood, Everyone 10+, PG, Adult, Teen, Teen+, Mature.

### 4.4 Existing-value mismatch behaviour (Basic Editor only)
When the Basic editor loads an issue whose current Genre/Format/or AgeRating value does
**not** match the enforced list (i.e. it's one of the stragglers the migration report — see
Section 7 — will have already flagged):
- The corresponding dropdown loads **blank/unset**, not pre-selected to anything.
- **The user must actively pick a valid value for that field before the form can be saved.**
  This is a hard validation gate, not a soft warning — save is blocked until resolved.
- This applies per-field independently (e.g. a mismatched Genre doesn't block saving if
  Format and AgeRating are both already valid — only the mismatched field itself gates).
- Rationale: this turns the one-time migration report into a self-cleaning mechanism. Every
  mismatched issue gets corrected the next time it's touched via Basic editor, rather than
  needing a single big manual sweep — the report just tells Tez which ones are still pending.

---

## 5. Full Editor — Toolbox

**Access:** new browser tab, opened from the Admin page (placeholder button already exists
per `admin-page-update.odt` — "Open Editor", currently a no-op planned for V2) or from the
tray app's "Metadata Editor" menu item (currently pointed at the old `:8001` URL — update to
`:8000/editor`).

**Scope confirmed during planning:** this is a **pre-library staging tool**, not a
library-maintenance tool. New comics land in an excluded `Processing` folder (already in
`config.json`'s `SCAN_EXCLUDE`, visible in the Admin page screenshot), get run through
ComicTagger first, then through this editor second to fix/add metadata, then get manually
moved into the real `L:\Comic Archives\` structure where the next library scan picks them up
for the first time.

**This means the Full Editor never touches files already in ComicVault's database, and
therefore needs zero rescan-trigger logic of any kind.** Library rescanning stays exactly as
it is today (manual "Scan Now" on the Admin page, or the existing single-file webhook used
by the Basic editor — see Section 6). This was a correction made mid-planning; earlier
drafts of this conversation assumed Full Editor batch-saves would need to trigger rescans —
they do not, because there is nothing in the DB yet to rescan.

### 5.1 File intake — native multi-select dialog (replaces CAPT's custom Explorer)
- No custom in-browser file browser, no `/browse` directory-listing route, no recursive
  folder-add. All of that is dropped.
- Standard `<input type="file" multiple>` — Tez organises files in Windows Explorer as
  today, then selects however many files he wants (one or many, e.g. all issues from one
  series) in a single native "Open" dialog, same as any normal website upload control.
- "Add a whole folder" simply becomes "select every file inside it" in that same multi-select
  dialog — functionally equivalent for the realistic case (a handful of new titles a week),
  and there's no folder-tree concept to preserve since file dialogs select files, not trees.
- This is desktop-only, same-machine-as-server, by design — confirmed no remote/cross-network
  file browsing is needed any more (an earlier development phase needed this when working
  over an external network; that need no longer applies — Tez now does all Full Editor work
  at the PC, and lighter edits from a laptop go through the Basic editor instead).
- Because this is a native file dialog, selected file content is uploaded to the FastAPI
  backend over local HTTP even though source and destination are the same machine. This is
  a deliberate, accepted minor inefficiency (confirmed in planning) in exchange for proper
  multi-select — it avoids error-prone manual path copy/paste, and the volume (~a few files
  a week) makes the overhead irrelevant.

### 5.2 Layout — three sections, card-styled to match the Admin page

Visual reference: the Admin page (see attached screenshot) uses two card patterns —
(a) flat stat cards (number + label, no extra framing) and (b) labelled section cards
containing a list of horizontal rows (e.g. "Scan Roots", "Exclude Patterns": a heading, then
thin dark strips each with text left / action link right). **Pattern (b) is what File
Management and Queue should use.** Purple accent is reserved for primary actions and
highlighted numbers only (matches "Scan Now" styling) — secondary actions (Clear, Remove)
stay muted grey, matching Back/User Guide/Backup Database.

**Column 1 — File Management**
- Section card, header "File Management."
- Action row: Explorer (opens native multi-select dialog), Clear List. (`Refresh` is dropped
  — confirmed dead/unused in the current design.)
- "N File(s) Loaded" count.
- Loaded-files list: same horizontal row style as today (filename, XML-present line,
  Remove button) re-skinned into the Admin-page section-card row style — **no cover
  thumbnails on these rows**; the Image Viewer column is the single place covers are shown,
  confirmed during planning to avoid redundant image fetching.
- **Drag-and-drop reorder** — kept exactly as today.
- **Keyboard navigation** — up/down arrow keys move a "focused card" highlight between rows.
- **Unified focus/load mechanic** — there is one shared "currently focused card" concept,
  and loading that card's XML into the form happens whichever way focus got there: mouse
  hover, or arrow-key navigation. Not two separate mechanisms — one focus state, two ways to
  move it.

**Column 1 (lower) — Queue**
- Same section-card and row styling as File Management.
- "Queue: N File(s) Loaded" count (Queue count is independent of the main list's count).
- Remove button per row. **No reorder, no keyboard nav** in Queue (matches CAPT's existing
  behaviour — Queue is a holding area, not something you navigate through).
- Processing-status indicator: "Ready to process" / "Processing…" (animated ellipsis, red
  background while active) — ported as-is.

**Column 2 — XML Editor**
- Section card, header "XML Editor."
- Main / More tabs as defined in Section 4.
- Bottom action row: **Queue** (adds current file to Queue), **Clear** (clears the form),
  **Process Queue** (writes XML to every file currently in the Queue — this *is* the save
  action, there is no separate "Save" button), **Process All** (writes XML to every loaded
  file, bypassing Queue). Process Queue / Process All are the primary actions and should
  carry the purple accent treatment; Queue/Clear stay secondary/grey.

**Column 3 — Image Viewer**
- Section card, header "Image Viewer." Kept as-is per planning confirmation:
  - Prev / Next page buttons
  - Zoom in / zoom out buttons
  - "Page X of Y" counter
  - Cover (page 1) auto-loads when a file is focused; subsequent pages load on demand via the
    same on-demand single-page extraction approach already used elsewhere in ComicVault
    (mirrors `GET /api/page/{issue_id}/{page_number}`'s pattern, but operating on a file not
    yet in the DB — needs its own lightweight equivalent reading directly from the
    in-progress/temp file).

### 5.3 Layout proportions
No longer constrained to fit a laptop screen (confirmed: Full Editor work has moved
primarily to the desktop PC, where there's more horizontal room than the original
three-column design assumed). Columns may use the available width more generously — Claude
Code has discretion here within the card-style language above; exact pixel proportions are
not being dictated by this spec.

---

## 6. Basic Editor — Popup

**Access:** the Edit button on `/issue/{id}` — **already present in the existing UI**,
confirmed it just needs its backend connected; no new frontend button to design.

**Scope:** exactly one issue, already in ComicVault's database. No file picker — the popup
already knows which issue it's editing from page context (the issue ID is already known;
no ambiguity to resolve).

### 6.1 Endpoints
- `GET /api/editor/{issue_id}` — load current field values for the popup form, sourced by
  reading the live XML out of the file at that issue's `file_path` (not from the DB columns
  directly, since the DB may already be slightly stale relative to the file — the XML is the
  source of truth for the editor).
- `POST /api/editor/{issue_id}` — accepts the submitted field set, runs it through the shared
  field-merge + archive-rebuild core (Section 3), writes the file, then **automatically
  triggers a rescan of that single file** (reusing the same logic that already backs `POST
  /api/scan/file?path=` — now an in-process function call rather than a webhook, since editor
  and reader now live in the same app).
- `GET /api/editor/genres` — shared with Full Editor, Section 4.1.

### 6.2 Field set
Identical to Section 4's Main + More tabs, **minus the Increment Number checkbox** (omitted
entirely — there's no batch concept in a single-file popup).

### 6.3 Validation
Per Section 4.4 — any field whose existing value doesn't match its enforced dropdown list
loads blank and must be actively set before save is permitted.

### 6.4 Remote access
Works correctly from any device on the home network (e.g. Tez's laptop), with no special
handling needed: the popup is just HTML/JS served by the same FastAPI app the rest of
ComicVault already serves to remote devices, and all file I/O happens server-side. The
client only ever sends field values over HTTP; it never needs to know or handle the file's
actual path on disk. This was explicitly checked during planning and confirmed to already
work by the same mechanism the rest of the web UI uses.

---

## 7. Pre-Migration Data-Hygiene Report

**One-time report, generated before the editor ships**, listing every existing issue whose
current `Genre`, `Format`, or `AgeRating` value does not match the newly-enforced lists in
Section 4. Purpose: let Tez see the full scale of the cleanup in one place rather than
discovering stragglers one at a time as he happens to open them in the Basic editor (though
per Section 4.4, opening any flagged issue will also force a fix at that point — the report
and the force-validation are complementary, not redundant: the report shows what's
*outstanding*, the validation gate is what actually *fixes* it over time).

- Suggested form: a simple script or admin-page report listing `issue_id`, `series`,
  `file_path`, the mismatched field name, and its current (invalid) value.
- Does not need to be a polished UI feature — a script output or temporary admin-page table
  is sufficient. Claude Code has discretion on exact implementation as long as the output is
  genuinely actionable (sortable/filterable enough that Tez can work through it as a list).

---

## 8. Config Additions

`config.json` needs no new top-level keys for file *locations* — the Processing folder is
already represented via the existing `SCAN_EXCLUDE` mechanism (visible in the Admin page
screenshot as "Exclude Patterns" → `Processing`), and the Full Editor's native-file-dialog
intake (Section 5.1) means no `processing_folder` path constant is needed in config at all —
confirmed during planning that free-roaming-via-native-dialog replaces any need to scope
intake to a single configured root.

No change to `library_root`, `db_path`, ports, or any other existing key.

---

## 9. What This Build Round Does Not Include

Explicitly deferred, not part of this spec:
- Admin-page UI for adding/removing genres by click (Genre list stays a hand-edited JSON
  file for now, per planning — confirmed acceptable)
- Collision guardrails on the increment-number batch feature
- CBR/.rar support of any kind
- Remote/cross-network file browsing for the Full Editor
- A series-level overview field (unrelated, already deferred in `SPEC.md` 20.14)
- Login/password protection on the editor (matches the rest of V1's admin area — deferred
  to V2 per `SPEC.md`/admin docs, not specific to this editor work)

---

## 10. Build Order Suggestion

Not binding, but a sensible sequence given the shared-core architecture:

1. `backend/editor/` core — port XML read/parse, field-merge, archive-rebuild, batch logic.
   No UI yet. Test against real files manually/via script.
2. `genres.json` + `constants.py` + `GET /api/editor/genres` endpoint.
3. Pre-migration report (Section 7) — run it once data is available, hand the list to Tez
   for cleanup tracking purposes even before the rest is built.
4. Basic Editor (`editor_basic.py` router + popup UI) — smaller surface, exercises the core
   end-to-end on real library files, immediately useful on its own.
5. Full Editor (`editor_full.py` router + three-column UI) — larger surface, built once the
   core is proven via step 4.
6. Wire up `tray_app.py`'s Metadata Editor menu item to the new in-app editor URL; retire any
   remaining references to the old `:8001` Flask process.

---

## 11. Open Items Carried Forward From Investigation (Informational, Not Blocking)

These were noted in the investigation report as discrepancies against `SPEC.md`'s original
assumptions. None require a decision to proceed with this build, but are recorded here so
they aren't lost:
- `SPEC.md` Section 8 lists `UseFirstYear`, `ApplySummary`, `ApplyWriter`, `ApplyPenciller`,
  `Editor`, `Review` as fields CAPT edits/drops. None of these actually appear anywhere in
  CAPT's current codebase. Likely leftover from an earlier desktop-PyQt6 version of the tool
  that was never carried into the web port. No action needed — they simply don't exist to
  port.
- `SPEC.md` Section 2's described sync webhook (`POST /api/scan/file?path=` called by the
  editor after every save) was never actually implemented in CAPT's existing code — moot now
  regardless, since editor and reader are merging into one app and the Basic editor's rescan
  trigger (Section 6.1) is an in-process call, not a webhook.

---

## 12. Change Log

> Record any deviations from this spec here with date and reason, same convention as
> `SPEC.md` Section 21.

| Date | Change | Reason |
|---|---|---|
| 2026-06-18 | `EDITOR_SPEC.md` created — full planning round complete covering architecture, field lists, enforced dropdowns, Basic/Full editor scope, file intake, and UI styling. Not yet built. | First planning session for V2 priority #1 (CAPT integration), following the read-only investigation report. |
| 2026-06-18 | `comicvault_v2` migration setup complete (clone, remote repoint, DB copy, config) — see `progress.md` "V2 — Migration Setup Complete" for details. Found and fixed BUG-001 (scanner skipped thumbnail generation for unchanged-mtime files even when the thumbnail was missing on disk) in `comicvault_v2/backend/scanner.py` only — see `BUGS.md`. V1's `scanner.py` is unmodified. | One-time environment setup, prerequisite to starting this spec's build work. The bug surfaced specifically because V2 was set up from a copied DB without its thumbnails — recorded here since it's a real scanner defect, not just a migration footnote. |
