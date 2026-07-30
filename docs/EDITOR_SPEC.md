# digib00age — EDITOR_SPEC.md (V2)

> **How to use this document**
> Paste this entire file into any AI coding session (Claude Code) before writing any code,
> alongside `SPEC.md` for context on the existing V1 system this plugs into.
> This is the single source of truth for the CAPT → digib00age editor integration.
> Record any deviations at the bottom of this file (Section 12, Change Log), same convention
> as `SPEC.md`.
>
> **Status:** Built and verified (2026-06-18) — all of Section 10's build order is complete:
> shared core, genres endpoint, pre-migration report, Basic Editor, Full Editor, and the
> tray app/Admin page wiring. See `progress.md` for the per-step build log and what was
> verified. CAPT is fully retired as a separate app.
>
> **Section 9 (ComicTagger Integration / Search Online) added and built 2026-07-04**
> (v2.5 Item 1, closed) — see `docs/v2.5/progress.md` for the full build/test
> narrative, including Tez's deferred low-confidence/real-world match-quality pass,
> completed the same day. See this file's Change Log (bottom) for build-time
> corrections made during that testing (filename-parsing fallback + assume-issue-1
> default, 80% match threshold, expanded field mapping).

---

## 1. Overview & Goals

digib00age currently relies on a separate, pre-existing Flask app ("CAPT") to edit
ComicInfo.xml metadata inside CBZ files. CAPT was investigated in detail (see
`digib00age_V2_CAPT_Investigation.md` / `v2_investigation_report.md`) and its editing logic —
XML read/parse, field merge, archive rebuild — is sound and is being ported wholesale.
Its Flask shell, in-memory data model, CBR support, dead dependencies, and several
discovered bugs are **not** being carried forward.

**The goal of this build round:** retire CAPT as a separate app entirely. Fold its proven
editing logic into digib00age's existing FastAPI backend, expose it through two purpose-built
UIs that match digib00age's design language, and fix the data-hygiene problem (free-text
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
digib00age (FastAPI, port 8000)
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
- ~~CBR/.rar support (`rarfile`, external `rar.exe` shell-out) — library is all-CBZ~~
  **Reversed 2026-06-30, v2.4 Item 5 — see §3.1/3.2 and Change Log.** CBR support is
  back in, on different terms than CAPT's: read/extraction only via `rarfile`, never
  written. Editing a CBR's metadata rebuilds it as `.cbz`. No `rar.exe` shell-out is
  introduced — that was specifically the write-path dependency, and the write path
  for CBR is deliberately not being built.
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
  `library_root` from `config.json` like everything else in digib00age; no hardcoded path
  exists to typo

---

## 3. Shared Editor Core (`backend/editor/`)

### 3.1 Reading *(built and manually tested — v2.4 Item 11, 2026-07-01)*
- Open the archive with `zipfile.ZipFile` (`.cbz`) or `rarfile.RarFile` (`.cbr` —
  added v2.4 Item 5, 2026-06-30, reversing the original "no CBR branch" decision
  above). Branch via the shared `backend/archive_formats.py` dispatch (falls back
  to the file extension when no `container_format` is available — Full Editor's
  pre-library intake, where the file isn't in the DB yet). Read-only — see §3.2 for
  what happens on save. Full Editor's own picker (`ALLOWED_EXTENSIONS`,
  `editor_full.py`) now accepts `.cbr` alongside `.cbz`, so a CBR can be loaded
  into the working set/queue at all.
- Locate `ComicInfo.xml` at the archive root.
- Parse with `lxml.etree` in recovery mode (`recover=True`), matching CAPT's existing
  tolerant-parsing behaviour.
- Build a tag→text map; extract the field set in Section 4.
- **Built 2026-07-19:** if no `ComicInfo.xml` is present in the archive at all,
  `get_file_xml()` (`backend/routers/editor_full.py`) seeds Series/Number/Year from
  filename-pattern parsing instead of loading the form blank, via
  `backend/editor/xml_parser.py::parse_filename_for_comicinfo()` — a shim that had
  existed unused since the original port, now repointed to reuse the Filename
  Editor's own parser (`backend/rename_tool.py::parse_comic_filename()`, the
  tested, scene-release-tolerant one also used by CT Auto-Tag) rather than the
  scanner's simpler internal fallback. Title is never filled — the filename pattern
  has no title component. If a filename doesn't parse to a usable series, the
  Series field still loads blank and "Search ComicVine" falls back to its existing
  manual-entry prompt. **Scope note:** this only covers "no XML file found" — an
  archive whose `ComicInfo.xml` exists but fails to parse still loads blank
  (`parse_comicinfo_xml()`'s existing internal catch), unchanged by this session.

### 3.2 Writing — full archive rebuild (confirmed, not changing)
Ported as-is from `utils/xml_archive_unpacker.py`:
1. Extract entire archive to a temp directory (using the `.cbz`/`.cbr` branch from §3.1)
2. Overwrite `ComicInfo.xml` in that temp directory with merged field values
3. Flatten to a second temp directory
4. `shutil.make_archive(..., "zip", ...)` to rebuild a new zip from scratch
5. `os.replace()` over the original file path

No in-place patching. This was a deliberate decision — full-rebuild is simple and proven;
the collection isn't large enough per-file for rebuild speed to be a problem in practice.

**CBR source → CBZ output (scoped v2.4 Item 5, 2026-06-30 — built and manually
tested v2.4 Item 11, 2026-07-01).** Step 4 always produces a `.zip`/
`.cbz` — this was already true before CBR support existed, since the rebuild path never
had a RAR-creation branch. So when the *source* file in step 1 is a `.cbr`, saving
produces a new `.cbz` at a sibling path (same directory, same filename stem, `.cbz`
extension) rather than overwriting the original — step 5's `os.replace()` targets the
new `.cbz` path, and the original `.cbr` is deleted once the new file is confirmed
written successfully (`_rebuild_archive()`, `backend/editor/archive_io.py`, now
returns the final path so every caller can propagate it). **Guard:** if a sibling
`.cbz` already exists, the rebuild raises before touching anything — no clobber, the
original `.cbr` is left in place, verified live (two colliding files, save attempt
errors cleanly, both files unchanged on disk afterward). The issue's `file_path` and
`container_format` (`SPEC.md` §7)
update to match in the same operation (single rescan/DB-update step, not two) — the
caller sets both on the ORM row and explicitly `db.flush()`s before the rescan call,
since the session runs `autoflush=False` and the rescan looks the row up by
`file_path`; without the flush the old path wouldn't resolve and a duplicate row
would be created instead of updating the existing one (caught and fixed during this
item's manual testing, not by design review — worth flagging for the next time a
save path is touched).
Applies identically to Basic Editor, Full Editor single-file saves, and Full Editor
batch/Process All — confirmed with Tez, no special-casing by editor surface, and
manually verified via all three paths this session. Reason:
RAR archive *creation* requires a paid WinRAR install (`arc_conv_helpers.py`'s
`create_rar_archive()` shells out to a `rar` CLI and errors without it) — not a
viable app dependency, especially given the possible-public-release direction. CBR is
therefore read-only at the archive level throughout digib00age; editing it is what
moves a file from CBR to CBZ, not a separate conversion step the user has to ask for.

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
  tag-splitting on write (that split only happens on digib00age's *read* side, into the
  `issue_genres` junction table).
- `Notes`: default text stays **`"Modified with the CAPT"`** for continuity with the large
  number of files already carrying that exact string. Not changed to reflect the new tool name.

### 3.4 Batch / increment-number logic
- Ported as-is from `utils/xml_worker.py`'s `process_xml_files`.
- Sequential: start at issue N, +1 per file in current list order.
- **No collision guardrail** — confirmed acceptable, this is Full Editor only and the
  workflow is "tag a fresh run of issues before they ever reach the library," so there's
  nothing in digib00age's DB yet to collide with.
- This feature does not exist in the Basic editor at all (single file, nothing to increment
  against) — omit the control entirely from that UI, not just disable it.
- **"List order" is the Column 1 tree's natural-sorted display order, always
  (fixed 2026-07-19, `archive/bugs-fixed-archive.md` BUG-031).** The frontend
  computes `file_ids` for Process All by walking the same folder→series→issue
  structure the tree renders (`treeOrderedFileIds()` in `editor_full.js`), so
  increment numbering can't diverge from what's on screen regardless of how the
  files arrived (`os.walk` order, picker order, or anything else) — the backend
  (`apply_increment()`) has no ordering logic of its own, it trusts the list it's
  given.

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
  already in digib00age's library, which by definition went through this check (or simply
  never had the problem) on their way in.
> **Correction, 2026-06-20 (`DECISIONS.md` — "ComicInfo.xml is the sole source of
> truth when MetronInfo.xml also exists"):** the line below claiming "the existing
> library is already known to be clean" is **false** — confirmed via `thanksgiving.cbz`
> and `tales of ruination.cbz`, both already scanned into the library with both
> ComicInfo.xml and MetronInfo.xml present. The scanner does not get multi-XML
> detection logic added (that remains correct, and is unchanged below) — instead,
> **ComicInfo.xml is the sole authoritative source wherever multiple XML files
> exist**, MetronInfo.xml is ignored. Already-affected library files are being
> identified and cleaned up via a one-off script run outside this project, not a
> digib00age feature.

- Confirmed out of scope: digib00age's library *scanner* does not get equivalent detection
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
preserved-on-write only, same as digib00age's issue-detail display rule (`SPEC.md` 20.8).

### 4.1 Genre — enforced, backend-served, editable list
- **Fully enforced select-only dropdown.** No free text, no escape hatch. This is the direct
  fix for the data-hygiene problem documented in `SPEC.md` Section 20.11 and confirmed in the
  investigation report (CAPT's existing "dropdown" was actually free-text-with-suggestions
  and never enforced anything).
- List is **not hardcoded** — served from `backend/editor/genres.json`, a flat array Tez can
  edit directly at any time as the library is worked through, or via the Admin page (added
  2026-06-20, `comicvault-changes.md` Tier 4 Item 1): `GET/POST /api/editor/genres`, `DELETE
  /api/editor/genres/{name}` (blocked if it's the last remaining value). Both Basic and Full
  editors call the `GET` endpoint, so they can never drift out of sync with each other.
- Starting list (21 values, from `xml-editor-design-and-function.md`, open to addition):
  Crime, Superhero, Sci-Fi, Western, War, Action, Adventure, Romance, Biography, Suspense,
  Cyberpunk, Comedy, Art, Fantasy, Horror, Fiction, Mystery, Thriller, Non-Fiction, Drama,
  Historical.

### 4.2 Format — enforced, backend-served, editable list
> **Deviation, 2026-06-20 (`comicvault-changes.md` Tier 4 Item 1):** this section
> originally locked Format as a hardcoded constant with "no editing mechanism
> needed." That decision is reversed — Format is now admin-editable, same
> mechanism as Genre (4.1 below), surfaced in the Admin page alongside Genre.
> The list contents and the Section 20.12 routing behaviour are unchanged; only
> the editing mechanism changed.
- **Fully enforced select-only dropdown.** No free text, no escape hatch.
- List is **not hardcoded** — served from `backend/editor/formats.json`, a flat array
  editable via the Admin page (or directly, same as Genre). New endpoints: `GET/POST
  /api/editor/formats`, `DELETE /api/editor/formats/{name}` (blocked if it's the last
  remaining value). Both Basic and Full editors call the `GET` endpoint, so they can
  never drift out of sync with each other.
- Starting list (10 values, unchanged from the original locked set): Graphic Novel,
  Series, One Shot, Anthology, Art Book, Limited Series, Special, Trade Paper Back,
  Annual, Other.
- This list also governs the Section 20.12 singles-routing rule already defined in `SPEC.md`:
  `Series` or `Limited Series` → series page; everything else → issue page; folder as
  fallback where Format is blank. Unchanged by this deviation — routing reads the per-issue
  DB value, not the editable list, so it's unaffected by additions/removals to the list.

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

**This means the Full Editor never touches files already in digib00age's database, and
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
  digib00age's styling (Section 5.2) but functionally unchanged — navigate folders, tick the
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

> **Process All amended 2026-06-23, built 2026-06-23 — see Change Log.** Each field
> in the Full Editor has a per-field **"Apply to: All" checkbox** (default:
> **unchecked**). Process All only applies fields whose checkbox is checked to every
> loaded file; unchecked fields retain their individual per-file values. Issue Number
> is the sole exception — it remains auto-increment only and gets no "Apply to: All"
> checkbox at all.
- **The Queue auto-empties once Process Queue completes successfully** — no manual clear
  needed afterward; the Queue's "Clear" button is for abandoning a queued set before
  processing, not for post-batch cleanup.

**Column 3 — Image Viewer**
- Section card, header "Image Viewer." Kept as-is per planning confirmation:
  - Prev / Next page buttons
  - Zoom in / zoom out buttons
  - "Page X of Y" counter
  - Cover (page 1) auto-loads when a file is focused; subsequent pages load on demand via the
    same on-demand single-page extraction approach already used elsewhere in digib00age
    (mirrors `GET /api/page/{issue_id}/{page_number}`'s pattern, but operating on a file not
    yet in the DB — needs its own lightweight equivalent reading directly from the
    in-progress/temp file).

### 5.3 Layout proportions
No longer constrained to fit a laptop screen (confirmed: Full Editor work has moved
primarily to the desktop PC, where there's more horizontal room than the original
three-column design assumed). Columns may use the available width more generously — Claude
Code has discretion here within the card-style language above; exact pixel proportions are
not being dictated by this spec.

### 5.4 Layout — 4-column redesign *(v2.6 Item 7, built + verified 2026-07-14 — supersedes §5.2/§5.3)*

The Full Editor was redesigned in Claude Design and rebuilt to a **four-column
workspace + a footer status bar** (`comicvault-changes-v2.6.md` Item 7). This section
governs the current layout; §5.2's three-column description is historical. **No
backend endpoint or data-path changed** — this is a layout + interaction reskin.
Grid: `340px 540px 470px minmax(280px,1fr)`, collapsing responsively (2-up ≤1500px,
1-up ≤900px). The whole workspace pins to the viewport height; each column scrolls
internally.

**Column 1 — Load / Select Files.** `Select Folder` opens the same modal
browser/picker as §5.1 (`/browse` + `/files/add` + `/folders/add`) — file intake is
unchanged. The loaded working set is rendered as an inline, expandable **folder →
series → issue tree** (grouped by each file's two nearest directory levels —
grandparent = folder, parent = series; shallower paths degrade gracefully), replacing
the old flat list. Issue rows carry an `XML` badge (when a ComicInfo.xml is present)
and a low-confidence dot (`needs_review`, lazy-on-focus per §9.2/§9.3), natural-sorted
(`001 < 002 < 010`). Clicking an issue is the unified focus/load mechanic (loads its
XML into Column 2 and its cover into Column 3). A `Clear` button clears the working
set. Bottom stats bar: **Files Found / With XML / Without XML**. **Drag-and-drop
reorder is dropped** — it has no meaning in a grouped tree (`DECISIONS.md`);
up/down-arrow keyboard focus movement is kept.

**Column 2 — Edit ComicInfo.xml.** Main/More tabs (§4) unchanged in field set. The
per-field "Apply to: All" checkboxes (§5.2 / Process All amendment) move into a
right-hand column under an `Apply to All` header — **all 16 `data-field`s are
retained, so Process All behaviour is identical**. **Genre is now removable chips +
a "＋ Add genre" dropdown** (replaces the checkbox grid; still backed by
`/api/editor/genres` per §4.1). Format / Age Rating stay native selects. Action row:
`＋ Queue` only *(2026-07-19: the column's own `Clear` button — which reset the form,
not the Queue, despite sitting right next to `＋ Queue` and reading as if it should —
was removed outright rather than kept as a source of confusion; the Queue's clear
lives solely in Column 4 now, see below)*. Issue Number keeps the separate
`Increment #` checkbox (no apply-to-all), its label placed in front of the checkbox
which aligns in the apply column.

**Column 3 — Comic Viewer.** Toolbar: zoom in/out, **Fit** (reset to fit), page
prev/next with an `X / Y` counter, and **Fullscreen** (Fullscreen API on the viewer
frame). **No Rotate** (dropped by Tez, `DECISIONS.md`). When zoomed past 100% the
page is click-drag-pannable (`grab`/`grabbing` cursor), on top of the frame's own
scrollbars — added 2026-07-22 after the zoom-in control shipped with no way to
reach a page larger than the frame besides two scrollbars. Cover auto-loads on focus;
pages load on demand via `GET /editor/full/files/{id}/page/{n}` as before. New: a
**lazy page-thumbnail strip** below the canvas — a windowed set of thumbnails around
the current page, each fetched on demand at reduced size via the endpoint's new
optional `?w=` downscale param (JPEG q70; full-res bytes returned when absent),
cached, active page highlighted, click-to-jump.

**Column 4 — Edited Files Queue.** The Queue moves out of Column 1 into its own
column: an "N files in queue" count with the **loaded-vs-queued counts-differ
warning** (§5.2's completion-check requirement, preserved), per-file cards
(✓ / filename / "Edited" / ✕ remove), and a Queue Actions footer with
`Process Queue` / `🗑 Clear Queue` / `Process All` *(2026-07-19: `Clear Queue`
relocated here from its own top-toolbar spot, between the two Process buttons, and
restyled to the same blue-pill/white-text `btn-primary` treatment as its siblings —
previously it was a secondary/ghost-styled button separate from the primary actions;
all three now share one disabled-state rule, enabled only once the Queue is
non-empty)*. The processing-status text ("Processing…") shows in this footer.

**Footer status bar** (new): `Selected: <file>` · `XML Status` (**Valid ✓** for a
single parsed ComicInfo.xml; a warning label for none or multiple — a lightweight
presence/parse indicator, not schema validation) · `Low Confidence <n>` ·
`Queued <n>`.

**Deploy note:** static assets are served without `cache-control`, so `/editor`
needs a hard-refresh (Ctrl+F5) to pick up a new build; the `?w=` param needs a
tray-server restart (the strip works without it, just heavier).

---

## 6. Basic Editor — Popup

**Access:** the Edit button on `/issue/{id}` — **already present in the existing UI**,
confirmed it just needs its backend connected; no new frontend button to design.

**Scope:** exactly one issue, already in digib00age's database. No file picker — the popup
already knows which issue it's editing from page context (the issue ID is already known;
no ambiguity to resolve).

### 6.1 Endpoints
- `GET /api/editor/{issue_id}` — load current field values for the popup form, sourced by
  reading the live XML out of the file at that issue's `file_path` (not from the DB columns
  directly, since the DB may already be slightly stale relative to the file — the XML is the
  source of truth for the editor). Also returns `saving: true` if a save for this issue is
  currently in flight in the background (see below) — the popup shows a wait notice and
  disables the form instead of allowing a conflicting second edit.
- `POST /api/editor/{issue_id}` — **async save, built 2026-07-11** (INBOX.md — the archive
  rebuild used to block the whole request, holding the modal open for the full round trip).
  Validates the submitted fields and merges them into the live XML **synchronously** (still
  returns 422 immediately on bad input, same as before), then queues the slow part — the
  field-merge + archive-rebuild core (Section 3), the file write, and the automatic single-file
  rescan (reusing the same logic that backs `POST /api/scan/file?path=`) — as a FastAPI
  background task, and returns immediately with `{success: true, pending: true, issue_id}`.
  Returns `409` if a save for this issue is already in progress (one background rebuild per
  issue at a time — a second save can't start until the first has finished writing).
- `GET /api/editor/{issue_id}/save-status` — poll target for the above:
  `{running, result, error, finished_at}`, keyed per issue (not a single global run like the
  Processing Tools use, since the Basic Editor can be opened against different issues from
  different tabs). Defaults to `{running: false, ...}` if that issue was never saved this
  process's lifetime (e.g. after a server restart).
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
digib00age already serves to remote devices, and all file I/O happens server-side. The
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

## 9. ComicTagger Integration (Full Editor)

Scoped across four sessions, 2026-07-03 (`DECISIONS.md` — four entries same date).
Full rationale lives there; this section is the build-facing transcription.

**Built and fully tested 2026-07-03/04** (v2.5 Item 1, closed) — Search Online
(both modal steps, field mapping, `NeedsReview` indicator) confirmed live by Tez
against real ComicVine data, including a full-data cross-check against an external
source and a real-world low-confidence-match comparison test. See
`docs/v2.5/progress.md` "Session — 2026-07-03/04" and the 2026-07-04
close-of-session entry for the full build narrative, including post-build fixes
(filename-fallback/assume-issue-1 for `identify()`, a missing-credits bug in the
CT Auto-Tag write path, the field-mapping scope correction below, and a
misleading-results-summary UI bug caught during the low-confidence test pass).

### 9.1 Architecture

- CT's `comicapi`, `comictalker`, and `comictaggerlib.issueidentifier` are imported
  as libraries directly into the FastAPI backend — no CLI wrapper, no
  reimplementation. Apache-2.0 licensed, already decoupled from CT's PyQt GUI.
- CBR write-back stays permanently out of scope (WinRAR CLI dependency) — same rule
  as the rest of this editor (§3.2). CT integration never writes RAR.
- Series/issue search goes through **one shared backend function**, called by both
  the Search Online modal below and the future CT Auto-Tag automation stage
  (`ADMIN_SPEC.md` §11.4) — not two separate codepaths hitting ComicVine.

### 9.2 `NeedsReview` flag

- New XML tag (name used throughout scoping was `NeedsReview` — confirm as final
  before build) added to `COMICINFO_TAGS` (`backend/editor/xml_parser.py`).
- Whole-file granularity, not per-field.
- Set by the CT Auto-Tag automation stage (`ADMIN_SPEC.md` §11.4) whenever it
  writes a low-confidence match.
- Cleared explicitly on every successful save, in both editor save routes —
  `build_xml_from_fields`/`field_merge.py` only touch tags present in the
  submitted payload, so this tag will never self-clear via the normal
  field-preservation mechanism the way a text field would. Needs its own explicit
  clear-on-save handling.

### 9.3 Full Editor visual indicator (Column 1)

- Loaded-file cards with `NeedsReview` set get a **colour-coded (red) border** —
  reuses the existing favourited-card gold-border mechanism (`SPEC.md`) with a
  different colour/condition, not a new visual pattern and not §3.5's
  badge/side-by-side pattern.
- Purely passive — clicking the border does nothing beyond the existing unified
  focus/load mechanic (§5.2). It does not open the search modal below.
- New inline count, **"N Low Confidence,"** placed after the Clear List button in
  Column 1's action row (§5.2) — same text style as the "N File(s) Loaded" line,
  different line/position, not folded into that count. Counted off the Loaded
  list only, not the Queue.
- Border and count are read live off in-memory form state, updating the moment
  fields are populated by a confirmed match — same as every other field in this
  editor; they don't wait for a save round-trip.

### 9.4 Search Online — trigger

- One global button, now labelled **"Search ComicVine"** (renamed from "Search
  Online" 2026-07-09 — Tez's tweak-pass call, since it's specifically a ComicVine
  search, not a generic "online" one). `id="feSearchOnlineBtn"` unchanged, only the
  label and the doc name below changed.
- **Relocated 2026-07-09** out of the header (was next to the Admin-cog link) into
  its own row directly above the three-column editor layout, sharing that layout's
  exact `340px / 1fr / 368px` grid so the button sits centred over the XML Editor
  column at any window width.
- **New 2026-07-09: "Search GoodReads"** sits alongside it in the same row (same
  `.fe-toolbar-group`) — a plain `target="_blank"` link, purely an external lookup
  shortcut, Tez's addition alongside the rename. **Updated 2026-07-30:** the link
  (`id="fe-search-goodreads-link"`) now prefills GoodReads' search box with the
  form's current Series text on click (`goodreads.com/search?q=<Series,
  URL-encoded>`; falls back to the bare `goodreads.com/search?` if Series is
  empty) — wired via `wireGoodreadsLink()` in `editor_full.js`, no backend call,
  no ComicVine plumbing involved. This is the first half of the GoodReads data
  capture flow; the second half (scraping a GoodReads book page and pasting
  Writer/Penciller/Publisher/Year/Summary back into this form) is a separate
  Chrome extension living entirely outside this repo's served frontend — see
  `chrome-extension/` and `docs/goodreads-extension-scope.md`. That extension
  injects its own "Paste from GR" button into this page via a content script and
  writes directly to `fe-writer`/`fe-penciller`/`fe-publisher`/`fe-year`/
  `fe-language`/`fe-summary` by id — nothing in `editor_full.js` itself changed
  to support that half, since these are plain, listener-free form fields.
  **Genre is the one exception** (added 2026-07-30): since it's a chip UI backed
  by `editor_full.js`'s own `selectedGenres`/`setGenres()`, the extension fetches
  the live `GET /api/editor/genres` list, matches GoodReads' genres against it
  case-insensitively (dropping anything not on the list, console-logged, no UI
  notice), and calls the real `setGenres()` via a `"world": "MAIN"` content
  script + `CustomEvent` bridge (a plain inline-`<script>` injection was tried
  first but is blocked by this origin's CSP) — so it actually updates
  `selectedGenres`, not just the visible chips.
- Operates on whichever file is currently focused/loaded into the form.
- Blocked with a message if the form's Series field is empty — matches CT's own
  guard in `taggerwindow.py::query_online()` ("Need to enter a series name to
  search").
- **Built 2026-07-19:** for a freshly-loaded file with no `ComicInfo.xml`, Series is
  now often already pre-filled from the filename (see §3.1), so this guard is hit
  less often in practice — it still applies unchanged when a filename doesn't parse
  to a usable series.

### 9.5 Search Online — field source

Read directly from the currently-focused file's form fields at click time, no
separate input anywhere in this flow:

- **Series** — required.
- **Issue #**, **Year**, **Issue Count** — read and passed through to
  pre-filter/sort results, not required.
- **Title is not used** — confirmed absent from both CT's automated `SearchKeys`
  (`issueidentifier.py::_get_search_keys`) and the manual `query_online()` field
  reads.

To retry with a different term: edit the Series field in the main form and click
Search Online again. There is no separate re-search input inside the modal.

### 9.6 Select Series / Select Issue modal

- **One modal container, two internal steps** — not two stacked windows. CT's
  native split into separate `QDialog`s is a desktop-toolkit affordance
  (independently movable/resizable windows) that doesn't carry over to a browser
  modal; two stacked overlays would mean nested focus-traps and rebuilding a
  whole overlay just to go back to already-fetched results. A "← Back to Series"
  control returns to the cached results list from the issue step, no re-fetch.
- Modal traps focus — blocks Column 1's card-swap and Process Queue/Process All
  while open.

**Step 1 — Select Series** (trimmed from CT's native dialog; reference screenshot
`images/search-online-manual-selection-from-results.PNG`):

- Results table: Series / Year / Issues / Publisher.
- Cover-art preview, both update on row selection. **Reworked 2026-07-23:**
  modal widened (`max-width` 900px → 1200px); the description panel moved out
  from under the cover to sit below the results table instead (same column,
  full width), so it's no longer squeezed into the narrow preview column.
- Double-click a row to proceed to Select Issue.
- **Dropped from CT's native version:** editable search box, Re-Search button,
  Filter Publishers checkbox — superseded by §9.5's read-from-form behaviour.
- **Built 2026-07-19: Sort control**, top row — dropdown (Series A-Z / Year /
  Issues / Publisher) plus an asc/desc toggle button, same pattern as the main
  library grid's sort control. Defaults to a "Best match" placeholder until the
  user actively picks a sort option; re-sorting only ever reorders what's
  displayed, the cached results list itself is untouched, and the chosen sort
  persists across a re-run search within the same modal session.
- **Fixed 2026-07-23 (BUG-033):** "Best match" is **not** simply "whatever
  order the backend/ComicVine returned" — it can't be, since CT's own local
  search-result cache can replay a repeated search in an order that doesn't
  match ComicVine's original relevance ranking (see
  `docs/archive/bugs-fixed-archive.md` BUG-033). `backend/ct_bridge.py`'s
  `search_series()` now computes its own best-match ranking (fuzzy
  title-similarity to the search term, tiebroken by issue count) before
  returning results, so "Best match" is a real, deterministic ranking
  digib00age computes itself rather than an assumption about pass-through
  order.
- **Built 2026-07-19: Cancel / Issues / Ok buttons.** **Reworked 2026-07-23:**
  moved from a left-aligned row below the results table to stacked, centred
  buttons anchored to the bottom of the cover-preview column (a gap separates
  them from the cover — they sit at the bottom of that column, not immediately
  under the image). **Cancel** closes the modal (same as ×). **Issues**
  reintroduces CT's native "Show Issues" button (dropped above) — same as
  double-clicking the highlighted row, proceeds to Select Issue. **Ok** skips
  Select Issue entirely: fetches the highlighted series' issue list and
  applies the first issue's metadata through the normal confirm path (§9.7) —
  for a single-issue/graphic-novel series this is identical to going through
  Select Issue normally; for a multi-issue series it's a fast-path onto issue
  #1, and picking a specific issue is still what Issues → Select Issue is for.
- **Fixed 2026-07-23:** ComicVine's series/issue description text comes back
  as raw HTML and can embed a small `<img>` (e.g. a "first issue" cover
  thumbnail) alongside the text — rendered via `innerHTML`, this pushed the
  summary text down and around a broken/slow-loading image. `backend/
  ct_bridge.py`'s `search_series()` and `list_issues_for_series()` now run the
  description through CT's existing `cleanup_html()` helper (already used for
  the Summary field mapping in §9.7) before returning it, stripping all HTML
  tags — including images — down to plain text. The frontend renders it via
  `textContent` instead of `innerHTML`, with `white-space: pre-wrap` so
  `cleanup_html()`'s paragraph breaks still display.

**Step 2 — Select Issue** (reference screenshot
`images/series-page-search-issue-list.PNG`):

- Issue list: Issue # / Date / Title.
- **Fixed 2026-07-23:** backend (`ct_bridge.list_issues_for_series`) natural-sorts
  the list by issue number before returning it — ComicVine's own API paginates
  issues in an unspecified order, not numeric order, which the modal used to
  display as-is. Sort key parses a leading numeric portion for numeric
  ordering ("2" < "11" < "11A"); non-numeric-prefixed values (e.g. "Annual 1")
  sort after all numeric ones. This also fixes the Select Series modal's **Ok**
  fast-path (§9.6 above), which assumes `results[0]` is issue #1.
- Cover preview and description, both update on row selection.
- Confirm applies the selected issue's metadata to the form.

### 9.7 Confirming a match

- **Fully overwrites** the mapped form fields — same "not a smart merge" rule
  §3.3 already establishes for saves generally. No merge-vs-overwrite special
  case for this dialog.
- Clears the red-border/count indicator immediately (§9.3); the `NeedsReview` XML
  tag itself only actually clears on save (§9.2), same as every other field edit
  in this editor.
- No auto-advance to the next flagged file after confirming — closes back to
  normal state, the user picks the next flagged file manually.
- The Select Series modal's **Ok** button (§9.6) goes through this exact same
  confirm path — it's not a separate field-mapping route, just an
  automatically-chosen issue (the first one in the list) fed into the same
  `/api/editor/full/search/confirm` call double-clicking an issue already
  makes. Every rule on this list applies unchanged.

### 9.8 Not yet decided (flagged, not blocking)

- Whether Search Online should warn/disable if no `comicvine_api_key` is
  configured in Admin (`ADMIN_SPEC.md` §11.4), rather than surfacing a raw
  network failure on first use.
- Final XML tag name — `NeedsReview` used throughout scoping, not yet confirmed
  as final.

### 9.9 Config

`config.json` gains `comicvine_api_key` (plaintext, same trust model already
applied to the existing `SESSION_SECRET`). Set via `ADMIN_SPEC.md` §11.4's
"Save & Test" field — not via this editor. No other config changes from this
section.

---

## 10. What This Build Round Does Not Include

Explicitly deferred, not part of this spec:
- Admin-page UI for adding/removing genres by click (Genre list stays a hand-edited JSON
  file for now, per planning — confirmed acceptable)
- Collision guardrails on the increment-number batch feature
- ~~CBR/.rar support of any kind~~ **Reversed 2026-06-30, v2.4 Item 5 — see §3.1/3.2.**
  Read-only CBR support (extraction via `rarfile`) is now in scope; RAR *creation*
  remains out of scope permanently, not just for this build round — see §3.2's
  rationale.
- Remote/cross-network file browsing for the Full Editor
- A series-level overview field (unrelated, already deferred in `SPEC.md` 20.14)
- Login/password protection on the editor (matches the rest of V1's admin area — deferred
  to V2 per `SPEC.md`/admin docs, not specific to this editor work)

---

## 11. Build Order Suggestion

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

## 12. Open Items Carried Forward From Investigation (Informational, Not Blocking)

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

## 13. Review Queue (Flag for Review)

**Built and manually verified 2026-07-15** (ad-hoc request, not part of a
numbered build queue at scoping time — added as v2.6 Item 8 at build time,
see `v2.6/comicvault-changes-v2.6.md`).

**Problem:** issues scattered across different series/folders sometimes turn
out to have incorrect metadata. Fixing them meant manually re-locating each
one through the Full Editor's file picker (Section 5.1) — tedious across
many issues. This section lets Tez mark any issue "flagged for review"
wherever he notices it, then batch-send every flagged issue straight into
the Full Editor's working set, skipping the file picker entirely.

### 13.1 Not the same thing as `NeedsReview` (Section 9.2)

**These are two unrelated flags — do not conflate them:**

| | `NeedsReview` (§9.2) | Review-queue flag (this section) |
|---|---|---|
| Storage | XML tag inside ComicInfo.xml | `Issue.flagged_for_review` DB column |
| Set by | ComicTagger Auto-Tag, on a low-confidence match | Tez, manually, any time |
| Visible | Full Editor only (red card border + count) | Library-wide (card badge/ring, a menu-bar filter, `/issue/{id}` button) |
| Cleared by | Confirming a Search-Online match; written on save | Saving the issue in either editor |

### 13.2 Data model

`Issue.flagged_for_review` (`backend/models.py`) — boolean, default false.
Mirrors the existing `favorites` column exactly (same "personal engagement,
independent of file metadata" category). Migration: guarded `ALTER TABLE`
in `_add_missing_issue_columns()` (`backend/database.py`).

### 13.3 Setting/clearing the flag

- **Single-issue** — `POST /api/progress/{issue_id}/flag-review` /
  `/unflag-review`, a toggle button on `/issue/{id}` next to Edit XML.
  Mirrors the existing `mark-read`/`mark-unread` convenience-shortcut
  pattern (not the bulk-with-one-id pattern the Favorite button on the same
  page uses — both styles already coexisted on that page beforehand).
- **Bulk** — `POST /api/progress/bulk/flag-review` / `/unflag-review`,
  reachable via the existing long-press/select-dot multi-select mechanism's
  toolbar (mirrors the `★ Favorite` bulk button exactly). Selecting a
  series-aggregate card expands to every issue in that series server-side,
  same as the other bulk actions.
- **Auto-clear on save** — both editors clear the flag when the issue is
  saved (Tez's call, matches how `NeedsReview` already auto-clears). Basic
  Editor clears it synchronously at validation time (`editor_basic.py`,
  before the background archive rebuild is queued). Full Editor clears it
  in `process_batch()` — see 13.5 below.

### 13.4 Viewing flagged issues

A menu-bar filter toggle (`#flagReviewFilterBtn`), mirroring the existing
Favourites filter (`MENU_BAR_SPEC.md` §2.3) exactly — narrows whatever
surface you're already viewing (All/Singles/Series/Folder View) down to
flagged-only, rather than being a dedicated tab (Tez's call — a dedicated
tab would cost one of the 4 visible-tab slots `CUSTOM_TABS_SPEC.md` caps,
for something that doesn't need its own permanent nav presence). Folder View
parity follows the same rule as Favourites: a folder card stays visible if
any descendant issue is flagged.

### 13.5 "Send to Full Editor" and the one DB-sync exception

`POST /api/editor/full/files/add-by-issues` (`backend/routers/editor_full.py`)
takes `{issue_ids: [...]}`, resolves each to its known `Issue.file_path`, and
adds it to the Full Editor's working set via the same validation
`add_files()` (the normal path-based picker's endpoint) already uses —
factored into a shared `_add_path_to_working_set()` helper so neither path
duplicates the other's logic.

**Full Editor was deliberately built to never touch the DB or trigger a
rescan on save** (Section 5's opening note) — a considered decision, since
it normally only handles pre-library files with no DB row yet. Sending
*already-catalogued* issues into it breaks that assumption: without a
rescan, the DB goes stale relative to the rewritten archive. **Confirmed
exception (Tez's explicit call, 2026-07-15):** `process_batch()` now looks
up `Issue.file_path == <the saved file's pre-rewrite path>` after a
successful write; if a row matches, it rescans (`scan_single_file`, same
function the Basic Editor's save path already calls) and clears
`flagged_for_review`. A `.cbr`→`.cbz` rename updates the matched row's
`file_path`/`container_format` and flushes before rescanning, mirroring the
Basic Editor's own `_finish_save` pattern for the same rename case. **Files
with no matching row — the Full Editor's original, still-primary use
case — are completely untouched,** exactly as before this change.

The selection toolbar's "→ Send to Full Editor" button opens `/editor` in a
new tab immediately (must happen synchronously with the click to satisfy
popup blockers) with a "Sending files in the background…" toast, since
`add-by-issues` can take a moment across a large selection (`find_xml_in_archive`
per file); once the background add completes, that same tab is reloaded so
it reflects the populated working set instead of an empty one.

---

## 14. Change Log

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
| 2026-06-18 | `start_server.py` crash fixed (commit `7e49d35`) — it still imported `EDITOR_PORT` after Section 2's "no port 8001" decision led to that constant being deleted from `backend/config.py` as dead code; the import was missed, crashing the reader server with an `ImportError` on every startup since. No spec content changed, recorded here since it's a direct regression from this section's port-removal decision. Full root-cause writeup (including an unrelated stale Windows Startup shortcut found at the same time) in `progress.md`. | Found while diagnosing a reported "editor inaccessible after reboot." |
| 2026-06-23 | **Full Editor — Process All per-field "Apply to: All" checkbox** (§5.2 Column 2). Each field gains an "Apply to: All" checkbox, default unchecked. Process All only bulk-applies checked fields; unchecked fields keep their individual per-file values. Issue Number is excluded (auto-increment only, as before — no checkbox). This changes the existing default behaviour where every field was bulk-applied unconditionally. Not yet built. | Inbox triage session 2026-06-23. |
| 2026-06-23 | Built. Found and fixed a related validation bug while building it: `process_batch()`'s enforced-field check (Genre/Format/AgeRating) validated only the checked-fields payload, which fails whenever those specific fields are left unchecked even though the file's own existing value is fine and untouched. Fixed by validating each file's effective merged result (existing value + checked overrides) instead. | v2.3 build plan Item 5; bug found live-testing against scratch copies. |
| 2026-06-20 | Corrected §3.5's "library already known to be clean" assumption — `thanksgiving.cbz`/`tales of ruination.cbz` found already in the library with both ComicInfo.xml and MetronInfo.xml present. ComicInfo.xml confirmed as sole authoritative source wherever both exist; scanner still gets no new detection logic, cleanup handled via an external one-off script instead. | Discovered during live testing of the Full Editor's multi-XML side-by-side picker against a real already-scanned file; see `DECISIONS.md`. |
| 2026-06-18 | **Full Editor (Section 5.2) and Basic Editor (Section 6.2) layout polish from live use**, committed as `cc772ba`: Image Viewer column narrowed and its preview image capped smaller; `.fe-layout` reworked so the XML Editor column is the flexible track instead of File Management/Image Viewer; Genre grid column counts changed (Full Editor settled on 5 columns, Basic Editor on 4 with the popup widened to 720px to fit); Increment Number checkbox relabelled "Increment #" and moved into the Issue Number/Year row; zoom controls moved to their own row below Prev/Next; B&W checkbox moved onto the Format/Age Rating row in Basic Editor. None of these change the field sets, validation rules, or behaviour defined in Sections 3–6 — layout/wording only. Full before/after detail in `progress.md`. | Tez's live-use feedback across both the desktop PC (primary editing machine) and a laptop with a smaller screen. |
| 2026-06-26 | **Full Editor — Process All error display** (§5.2). When `result.errors.length > 0`, a new dismissible modal (`#feProcessErrorOverlay`, styled like the existing log viewer modal) now opens instead of dumping a pipe-delimited wall of repeated validation messages into the inline `#feError` div. Shows a `Processed X of Y files` summary, the first file's full error, and — if more files failed — a count + guidance note pointing at the "Apply to All" checkboxes. `#feError`/`showError()`/`clearError()` are unchanged and still used for short single-line cases (network errors, "select a file first"). | Post-test fix pass (`docs/2.3-fixes.md` Fix 3) — manual test pass found the inline error display unreadable against a large batch of files sharing the same missing-required-field error. |
| 2026-06-30 | **CBR support reversed back in (read-only), §2/§3.1/3.2/§9 — v2.4 Item 5.** This file's original §2/§9 deliberately dropped CBR/.rar support on the basis that "library is all-CBZ." That basis no longer holds — Tez's direction has shifted toward a possible public release, and users with large mixed CBZ/CBR collections (some >100,000 issues) can't reasonably be required to bulk-convert before their library is browsable. §3.1 gains a `rarfile.RarFile` read branch alongside `zipfile.ZipFile`. §3.2's rebuild path is **unchanged** — it always produced a `.zip`/`.cbz` regardless of source format, so no RAR-creation code is added; when the source file is a `.cbr`, the existing rebuild simply lands at a new `.cbz` path and the original `.cbr` is deleted once the new file is verified written. Confirmed with Tez to apply uniformly across Basic Editor, Full Editor single-file saves, and Full Editor batch/Process All — no per-surface special-casing. RAR archive *creation* remains permanently out of scope (not just deferred) — it requires a paid WinRAR install, which CAPT's own `create_rar_archive()` already depends on and is exactly the dependency this reversal is designed to avoid reintroducing. Full rationale and the original eng-review that surfaced this in `DECISIONS.md`; `SPEC.md` §6.1/§7/§13/§21 carries the scanner/schema/dependency side of the same change; build item `v2.4/comicvault-changes-v2.4.md` Item 5/11. | v2.4 Item 5, eng-reviewed and scoped 2026-06-30. |
| 2026-07-03 | **Added Section 9, ComicTagger Integration (Full Editor)** — transcribed from four scoping sessions (`DECISIONS.md`, four 2026-07-03 entries): architecture (CT libraries imported directly, no CLI wrapper), `NeedsReview` XML flag + its red-border/count visual indicator (§9.3, reuses the favourited-card border mechanism, not §3.5's badge pattern), the single global "Search Online" trigger and its read-from-form field source (Series required; Issue #/Year/Issue Count optional; Title confirmed unused in either of CT's own search paths), the Select Series/Select Issue modal (one container, two steps — not CT's native two stacked windows), and full-overwrite-on-confirm semantics matching §3.3. Sections 9–12 renumbered to 10–13 to make room (old §9 "What This Build Round Does Not Include" is now §10, etc.) — no other content changed by the renumbering. Not yet built; same standing status as the rest of this document. | v2.5 #1 — four scoping sessions 2026-07-03, this pass transcribes the locked decisions from `DECISIONS.md` into the build-facing spec so Code has what it needs to start. |
| 2026-07-04 | **Section 9 built and manually verified** (v2.5 Item 1) — see `docs/v2.5/progress.md` for the full build narrative. Confirms the section as scoped, plus one build-time addition not previously specified: the `GenericMetadata` → ComicVault field-dict mapping (`backend/ct_bridge.py`) captures every field CT/ComicVine supplies that maps to a standard ComicInfo.xml tag (mirroring `comicapi/tags/comicrack.py`'s own write mapping field-for-field — Month, Day, Notes, Inker, Colorist, Letterer, CoverArtist, Editor, Web, Volume, AlternateSeries/Number/Count, SeriesGroup, Characters, Teams, Locations), not just the fields this section's Main/More tabs expose. This was a live-testing correction, not a spec decision made in advance — an initial build-time judgment call to map only editor-exposed fields turned out to not match Tez's actual intent (capture everything, even fields the UI never displays). Genre/Format/AgeRating/BlackAndWhite remain excluded from this mapping — confirmed as a different, correctness-driven exclusion (enforced-dropdown validation integrity; a literal `"on"`/`"Yes"` semantic mismatch for BlackAndWhite), not a "not shown so not captured" one. | v2.5 Item 1 build + Tez's live-testing pass, 2026-07-03/04; see `DECISIONS.md` for the fuller rationale. |
| 2026-07-09 | §9.4 — "Search Online" renamed **"Search ComicVine"** and relocated out of the header into its own row directly above the three-column layout, sharing `.fe-layout`'s exact grid columns so it sits centred over the XML Editor column. New **"Search GoodReads"** external link added alongside it in the same row — plain `target="_blank"` link to goodreads.com, no field wiring. | Tez's post-redesign UI tweak pass — see `docs/v2.6/progress.md`. |
| 2026-07-11 | **§6.1 — Basic Editor save made async ("fire and forget").** `POST /api/editor/{issue_id}` used to run the whole field-merge + archive-rebuild + rescan chain synchronously, blocking the popup open for the full round trip (dominated by the archive rebuild, which scales with page count). Now only validates + merges the XML synchronously (still 422s immediately on bad input) and queues the rebuild + rescan as a background task, returning `{success, pending: true, issue_id}` right away; new `GET .../save-status` polling endpoint; new `saving` flag on `GET /api/editor/{issue_id}` plus a `409` guard against a second concurrent save on the same issue. Accepted trade-off, confirmed with Tez: if a background save fails after the user has already navigated away, it's silent (discoverable only by reopening the editor) — no new cross-page notification system. Safe either way since `os.replace()` only swaps in the rebuilt archive after it's fully staged, so a failure never corrupts the original file. Full rationale in `DECISIONS.md`; build narrative in `docs/v2.6/progress.md`. | Inbox 2026-07-11 — "quick save hits a bottleneck," scoped and built same day. |
| 2026-07-15 | **Added Section 13, Review Queue (Flag for Review) — v2.6 Item 8, built and manually verified same day.** New `Issue.flagged_for_review` DB column (mirrors `favorites`), single-issue + bulk set/clear endpoints, a menu-bar filter toggle (mirrors the Favourites filter, §2.3 in `MENU_BAR_SPEC.md`), and a "Send to Full Editor" bulk action that resolves selected issues to their known file paths and adds them straight to the Full Editor's working set via a new `add-by-issues` endpoint — skipping the manual folder-browse picker. One confirmed, scoped exception to Section 5's "Full Editor never touches the DB" rule: `process_batch()` now rescans + clears the flag when the saved path matches an existing `Issue.file_path`; files with no match (the original pre-library use case) are completely untouched. Section 14 (old §13, Change Log) renumbered to make room — no other content changed. | Ad-hoc feature request 2026-07-15, scoped and built same session; see `v2.6/progress.md` "Basic Editor popup-open perf fix" session's follow-ups and the dedicated review-queue session entry for the full build narrative. |
| 2026-07-19 | **§3.1/§9.4 — Full Editor now pre-fills Series/Number/Year from the filename when a loaded file has no `ComicInfo.xml`**, built and manually verified same day. Repointed the previously-unused `parse_filename_for_comicinfo()` shim (`backend/editor/xml_parser.py`) from the scanner's minimal internal fallback to the Filename Editor's own tested parser (`backend/rename_tool.py::parse_comic_filename()`), then wired it into `get_file_xml()`'s no-XML branch. No frontend changes — existing field-population and Search-ComicVine-guard logic just work once Series is pre-filled. | Tez's request 2026-07-19 — "Full XML Editor doesn't have any filename parsing... reuse the current parsing that is built." Scoped to Full Editor only (Basic Editor has the same gap, deliberately left out of scope). See `docs/v2.6/progress.md`. |
| 2026-07-19 | **§9.6/§9.7 — Select Series modal gained a Sort control and Cancel/Issues/Ok buttons**, built and manually verified same day. Sort defaults to relevance order ("Best match") until manually changed — an initial build mistakenly auto-applied A-Z sort on every fresh search, caught by Tez before docs/commit and corrected same session. Ok reuses the existing confirm path (§9.7) with the first issue in the list, no new backend endpoint. Issues reintroduces CT's native "Show Issues" button, previously listed as dropped. | Tez's request 2026-07-19, built and iterated same session (Cancel button + left-alignment added in a follow-up round). See `docs/v2.6/progress.md`. |
| 2026-07-23 | **§9.6 — BUG-033 fix: "Best match" is no longer a raw pass-through of `search_for_series()`'s order.** `backend/ct_bridge.py`'s `search_series()` now computes its own best-match ranking (fuzzy title-similarity via `difflib.SequenceMatcher`, tiebroken by issue count) because the pinned CT dependency's own local search-result cache can replay a repeated search in an order that doesn't match ComicVine's original relevance ranking — confirmed by reproducing the cache's actual broken read order against a real search ("2000 AD" returning "Best of 2000 AD Monthly" first). | Tez reported the wrong-order symptom 2026-07-23 against `2000AD #763 (1991).cbz`; root cause traced and fixed same session. See `docs/archive/bugs-fixed-archive.md` BUG-033, `DECISIONS.md`, `docs/v2.6/progress.md`. |
| 2026-07-30 | §9.4 — **"Search GoodReads" link now points at `goodreads.com/search?`** instead of the bare homepage. Same plain `target="_blank"` link, no field wiring, no behaviour change beyond the landing URL. | Tez's request 2026-07-30, same session as the Admin nav-consistency and Donate-removal fixes. See `docs/v2.6/progress.md`. |
| 2026-07-30 | §9.4 — **"Search GoodReads" link now prefills with the Series field** on click (`wireGoodreadsLink()`), and a new **`chrome-extension/`** (personal Chrome extension, outside this repo's served app) scrapes GoodReads book pages and pastes Writer/Penciller/Publisher/Year/Summary into this form via an injected "Paste from GR" button. | Eng-review + build session 2026-07-30, from `docs/goodreads-extension-scope.md`. See `docs/v2.6/progress.md`, `docs/DECISIONS.md`. |
| 2026-07-30 | §9.4 — extension now also pastes **Language** (plain field) and **Genre** (matched case-insensitively against the live `/api/editor/genres` list, canonical casing pasted, non-matches dropped and logged). Genre paste goes through a `"world": "MAIN"` content script + `CustomEvent` bridge to call the real `setGenres()`, after the original inline-`<script>` bridge turned out to be blocked by this origin's CSP. | Same-day follow-up, Tez's request. See `docs/v2.6/progress.md`, `docs/DECISIONS.md`. |
