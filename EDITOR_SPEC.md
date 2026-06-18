# ComicVault — EDITOR_SPEC.md (V2)

> **How to use this document**
> Paste this entire file into any AI coding session (Claude Code) before writing any code,
> alongside `SPEC.md` for context on the existing V1 system this plugs into.
> This is the single source of truth for the CAPT → ComicVault editor integration.
> Record any deviations at the bottom of this file (Section 12, Change Log), same convention
> as `SPEC.md`.
>
> **Status:** Built and verified (2026-06-18) — all of Section 10's build order is complete:
> shared core, genres endpoint, pre-migration report, Basic Editor, Full Editor, and the
> tray app/Admin page wiring. See `progress.md` for the per-step build log and what was
> verified. CAPT is fully retired as a separate app. Next: live use by Tez, working through
> the pre-migration report's flagged issues, and any V2.1 follow-up fixes that surface.

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

**Reinstated, not dropped** (corrected during planning — an earlier draft of this spec
mistakenly dropped these, see Section 12 change log): the `/browse` directory-listing route,
`/files/add` and `/folders/add` (recursive), and `file_mgmnt.html`'s breadcrumb/tree-view
picker UI. These are **server-side, path-based** intake — the server opens files directly
off disk by path, never via browser upload — which is exactly what makes automatic
write-back to the original file location work. A browser-upload-based file dialog was
considered and rejected: browsers never expose a real filesystem path from `<input
type="file">`, so the server would have no path to write rebuilt archives back to,
reintroducing a manual move/download step that doesn't exist in CAPT today and isn't
wanted here either.
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

### 3.3 Field write logic — selective overwrite, not a smart merge
- Ported from `widgets/xml_editor.py`'s `build_xml_from_fields`.
- Important distinction, worth stating precisely: this is **not** a field-by-field smart
  merge. Every tag exposed in the editor (Section 4's Main + More field list) is **fully
  overwritten** by whatever's currently in the form when you save — including being blanked
  out / tag-removed if you cleared that field in the UI, even if the original archive had a
  value there. There's no "only write if changed" logic and no attempt to reconcile a
  field's old value against its new one.
- Tags **not** exposed in the editor at all (Volume, Month, Inker, Colorist, Letterer,
  CoverArtist, Characters, Teams, Locations, Manga, StoryArcNumber) are the only thing that
  survives untouched — and only because the merge logic never looks at those tags in either
  direction, not because of any deliberate preservation rule. "Merge," where it appears
  elsewhere in this document, means this selective-overwrite behaviour, not a content-aware
  combination of old and new values within a single field.
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

### 3.5 Multi-ComicInfo.xml detection (Full Editor only)
Not present in CAPT's current code as investigated — `archive_xml_loader.py` lists `*.xml`
entries in the archive and silently decodes whichever one it lands on first, with no
detection or warning if more than one exists. This is new logic, not a port, added because
it's known to happen occasionally (rare, but real — different tagging tools or a leftover
file from a previous pass can leave a stray second XML inside an archive) and currently
fails silently rather than being surfaced.

- On load, check `namelist()` for all entries matching `*.xml` (case-insensitive). If more
  than one is found:
  - The file's card in the Full Editor's loaded-files list shows a warning state instead of
    the normal "XML files: ComicInfo.xml" line — e.g. "⚠ 2 XML files found" — rather than
    silently picking one.
  - Clicking the warning opens a side-by-side view of all candidate XML files' contents
    (parsed field values, same shape as the Main/More form, read-only) so Tez can see what
    each one actually contains before deciding.
  - Tez picks which one to keep; the editor deletes the others from the archive (via the
    same extract → modify → rebuild → replace mechanism as a normal save) and proceeds with
    the kept file as the active ComicInfo.xml for that card.
- **Full Editor only.** Not needed in the Basic editor — it operates exclusively on files
  already in ComicVault's library, which by definition went through this check (or simply
  never had the problem) on their way in.
- Confirmed out of scope: ComicVault's library *scanner* does not get equivalent detection
  logic. This is treated as purely a pre-library intake concern; the existing library is
  already known to be clean, and the scanner's behaviour on this point is left as-is.



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

### 5.1 File intake — reinstated server-side browser/picker (ported from `file_mgmnt.html`)
A browser-upload file dialog (`<input type="file">`) was considered during planning and
**rejected**: browsers never expose a real filesystem path for security reasons, so the
server would receive raw bytes with no known location to write rebuilt archives back to —
this would have reintroduced a manual download-and-move step that doesn't exist in CAPT
today and isn't wanted here.

Instead, CAPT's existing file picker is **ported, not replaced**:
- `GET /browse` — directory listing for a given path, feeds the tree-view UI.
- `POST /files/add` — add one or more specific files by path.
- `POST /folders/add` — recursively add every comic archive under a given folder path.
- `file_mgmnt.html`'s breadcrumb + tree view + multi-select UI, re-skinned to match
  ComicVault's styling (Section 5.2) but functionally unchanged — navigate folders, tick the
  files/folders you want, "Add Selected Files/Folder."

This is **server-side, path-based I/O throughout**: the server opens each file directly off
disk using a real filesystem path it already has, edits it, and writes the rebuilt archive
back over that exact same path (`os.replace()`, Section 3.2) — automatically, with no upload,
no download, and no manual move step. This is the same mechanism CAPT already uses
successfully today; it is being carried forward rather than redesigned.

**Bug fix during the port:** the existing path-guard inconsistency found in investigation
(`file_mgmnt.js`'s `DEFAULT_PATH` uses `'L:\\Comic Archives'`, but `/rename`, `/fileinfo`,
and `/update-xml` in `web_server.py` gate access against the typo'd `"L:\\Comics Archives"`
— note the extra "s") gets corrected as part of this port. The new version should check
against `library_root` already defined in `config.json`, giving one single source of truth
for "what counts as a valid path" rather than two hardcoded strings that can silently drift
apart, as they already have.

**Confirmed desktop-only, same-machine-as-server**, consistent with everything else in
Section 5 — this was never actually a remote-access requirement; an earlier development
phase needed *cross-network* file access (a now-retired custom Explorer feature, distinct
from this folder browser, built for working from outside the home network), and that need
no longer applies. This path-based picker browsing the server's own local disk is unrelated
to that and was always fine to keep.

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
- Action row: Explorer (opens the ported `file_mgmnt` tree-view picker, Section 5.1), **Clear List** (clears the
  Loaded Files list **and** resets the form/XML Editor column — distinct from Column 2's
  "Clear," which only clears the Queue; the two buttons are named similarly but act on
  different things, worth being explicit about in the UI copy and in code comments).
  (`Refresh` is dropped — confirmed dead/unused in the current design.)
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
- **Queue auto-empties once Process Queue completes successfully** (see Column 2).

**Loaded vs Queued count as a completion check.** The "N File(s) Loaded" and "Queue: N
File(s) Loaded" counts aren't purely informational — Tez uses them together to visually
confirm a batch is fully queued before walking away from a session (e.g. 5 loaded, 5 queued
→ done; 5 loaded, 3 queued → 2 still need attention). **The UI should visually flag it when
the two counts don't match** (e.g. a highlight colour or small indicator near the counts)
rather than just displaying two plain numbers — this is a confirmed requirement, not a
nice-to-have. Note this check is meaningful for the Queue workflow specifically; Process All
bypasses the Queue entirely and isn't covered by this indicator.

**Column 2 — XML Editor**
- Section card, header "XML Editor."
- Main / More tabs as defined in Section 4.
- Bottom action row: **Queue** (adds current file to Queue), **Clear** (clears the **Queue**,
  not the form — flagging since "Clear" reads ambiguously at a glance), **Process Queue**
  (writes XML to every file currently in the Queue — this *is* the save action, there is no
  separate "Save" button), **Process All** (writes XML to every loaded file, bypassing
  Queue). Process Queue / Process All are the primary actions and should carry the purple
  accent treatment; Queue/Clear stay secondary/grey.
- **The Queue auto-empties once Process Queue completes successfully** — no manual clear
  needed afterward; the Queue's "Clear" button is for abandoning a queued set before
  processing, not for post-batch cleanup.

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

`config.json` needs no new top-level keys. The Processing folder is already represented via
the existing `SCAN_EXCLUDE` mechanism (visible in the Admin page screenshot as "Exclude
Patterns" → `Processing`) and there's no need for a separate `processing_folder` constant —
the Full Editor's reinstated path-based picker (Section 5.1) can browse to anywhere on disk,
same as CAPT does today, rather than being scoped to one fixed root.

The one existing key that does get a new *use*: `library_root` should now also back the
picker's path-validity guard (Section 5.1's bug fix), replacing the two hardcoded/typo'd
path strings currently scattered across `file_mgmnt.js` and `web_server.py`.

No change to `library_root`'s value, `db_path`, ports, or any other existing key/value.

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
| 2026-06-18 | Added Section 3.5 (multi-ComicInfo.xml detection, side-by-side comparison, manual removal — Full Editor only). Corrected 3.3 from "merge" to "selective overwrite" wording. Corrected Column 2's "Clear" button (clears Queue, not form) vs Column 1's "Clear List" (clears Loaded Files + form) — these were previously conflated. Added Queue auto-clear-on-completion. Added Loaded/Queued count mismatch visual indicator as a confirmed requirement. | Follow-up review pass after first draft; corrections from Tez against real CAPT behaviour and workflow habits not previously surfaced. |
| 2026-06-18 | **Reversed** the native-file-dialog file-intake decision (was: `<input type="file" multiple>`, browser-uploaded bytes). Section 5.1 now reinstates CAPT's existing `/browse`, `/files/add`, `/folders/add`, and `file_mgmnt.html` tree-view picker, ported as-is. Section 2's cut-list and Section 8's config notes updated to match. | The native-dialog approach was traced through to its consequence during review: browser uploads never carry a real filesystem path, so the server would have had no known location to write rebuilt archives back to, silently reintroducing a manual download/move step. CAPT's existing path-based picker already solves this correctly and was being dropped under a mistaken assumption that it was only a remote-network feature — it isn't; that was a separate, already-retired custom Explorer feature. The path-guard typo bug found in investigation is fixed during this same port, now checking against `library_root` instead of a second hardcoded string. |
| 2026-06-18 | `comicvault_v2` migration setup complete (clone, remote repoint, DB copy, config) — see `progress.md` "V2 — Migration Setup Complete" for details. Found and fixed BUG-001 (scanner skipped thumbnail generation for unchanged-mtime files even when the thumbnail was missing on disk) in `comicvault_v2/backend/scanner.py` only — see `BUGS.md`. V1's `scanner.py` is unmodified. | One-time environment setup, prerequisite to starting this spec's build work. The bug surfaced specifically because V2 was set up from a copied DB without its thumbnails — recorded here since it's a real scanner defect, not just a migration footnote. |
| 2026-06-18 | Build steps 1–4 (editor core, genres endpoint, pre-migration report, Basic Editor) completed against the **pre-revision** Section 5 — none of that work is affected by this file's Section 5.1/3.5 corrections above, since Basic Editor never had a file-picker concern (it always operated on a known `issue_id` from the DB) and Full Editor (the only section touched by the revision) had not been started yet. Full detail per step in `progress.md`. | Confirming no rework needed before continuing to Full Editor under the corrected spec. |
| 2026-06-18 | Build steps 5–6 complete: Full Editor (`editor_full.py` + `editor_full.html`/`.js`, path-based picker, multi-XML detection/resolution, queue + batch processing with increment, image viewer) and tray app/Admin page wiring to `/editor`. `archive_io.py` gained a shared `_rebuild_archive()` helper and `keep_single_xml()`; validation logic extracted to a new shared `validation.py` so Basic and Full Editor enforce Genre/Format/AgeRating identically. Full detail in `progress.md`. This closes out Section 10 — CAPT is fully retired. | Completes the build round this spec exists to plan. |
