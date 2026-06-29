## 12. Processing Tools

Reserved section for CAPT's remaining standalone desktop tools, brought into ComicVault
one at a time per `ROADMAP.md`'s "CAPT extra tools" entry. Each tool gets its own
sub-section below (§12.1, §12.2, …) as it's scoped and built. All Processing Tools
sections live at the bottom of the `/admin` page, in the existing single scrolling
layout — not separate pages. (`/admin` as a whole is a placeholder layout pending a
full redesign covered elsewhere; Processing Tools sections will be restyled alongside
everything else when that happens, not before.)

**Shared design notes across all Processing Tools:**

- These tools operate on files **before** they enter the scanned library — typically
  staging areas like `Processing/`, but not restricted to any specific folder. None of
  them write to the database or trigger a rescan; they are pure filesystem utilities
  with a web UI.
- Each tool's section is gated to **local-only sessions** (request originates from
  `127.0.0.1`), same tier as Restart Server / Clear Database / the backup folder
  dialog — these tools perform real, irreversible filesystem mutations. The section is
  greyed out with an explanatory hint when accessed remotely, reusing the existing
  `is_local` flag already returned by `GET /api/admin/auth/status` and the same
  disable/hint pattern §7.1's auth controls use (`authLocalOnlyHint`).
- Source code for all four tools (Rename, Convert, Convert Images, Flatten) lives in
  the original CAPT codebase at `comic_file_editing_toolkit/src/cap_toolkit/`. Each
  tool's logic is being ported, not rebuilt from scratch — the GUI shell (PyQt) is
  discarded, the underlying file-operation logic is reused.

---

### 12.1 File Rename

Ported from CAPT's standalone File Renamer (`gui/rename_window.py`,
`widgets/rename_options_widget.py`, `utils/rename_logic.py`, `utils/rename_u.py`,
`utils/filename_parser.py`). Batch and single-file renaming of arbitrary files based on
parsed/edited Series, Issue, Title, and Year values.

#### 12.1.1 Scope

- Operates on **any file**, not just comic archives — no extension filter of any kind.
  The tool only ever touches the filename string via a path rename; it never opens a
  file's contents, so it's completely format-agnostic (cbz, cbr, pdf, txt, anything).
  This also means there is nothing to "restrict to CBZ" here — that consideration
  applies to Convert Images/Flatten (§12.3/§12.4), not Rename.
- No restriction to any particular folder (e.g. `Processing/`) — the picker can browse
  anywhere the server process can see, any drive. In practice this will mostly be used
  on pre-ingest staging folders, but nothing in the implementation assumes that.
- Filenames matter to ComicVault only as a fallback parser (`scanner.py`'s
  `_parse_filename()`) used when a file lacks `ComicInfo.xml` — once a file is tagged
  and scanned, the filename is purely cosmetic. Renaming here never touches the DB and
  never needs to.

#### 12.1.2 File Loading

- **Custom in-app folder-tree picker** — same pattern as the Full Editor's file picker
  (`EDITOR_SPEC.md` §5.1) and the Custom Tabs folder picker (§5 above), **not** a native
  OS dialog (`tkinter`). This is a deliberate choice over the native-dialog pattern used
  by the Scheduled Backup folder picker (§9): the native dialog only works because
  frontend and backend currently share a machine, and breaks conceptually under Remote
  Administration (it would pop open on the server's own screen). The in-app picker is
  pure HTTP/JSON server-side directory listing, so it behaves identically regardless of
  which device is browsing — though committing a rename stays local-gated regardless
  (§12, shared notes).
- **No library-root restriction.** Unlike the Editor's and Custom Tabs' pickers, this
  one is not scoped to `library_root` — it lists any directory the server process can
  reach. Requires a small new backend capability: a "This PC" drive-letter listing,
  reached by navigating **Up** past a drive's root (mirrors the Editor picker's
  Home/Up — **Home** returns to the configured `library_root`, **Up** climbs the tree
  and terminates at a drive-letter list rather than stopping at a fixed root).
- **No recursion.** Selecting a folder loads only the files directly inside it — no
  descent into subfolders (deliberately different from CAPT's original `rglob()`
  behaviour, and from the Editor's recursive folder-add). Loading files from a
  subfolder requires navigating into it and selecting from there. Multi-select
  individual files from within one folder is also supported via the same picker.

#### 12.1.3 Filename Parsing

Ports `filename_parser.py`'s `parse_comic_filename()` unchanged — regex-based
extraction of Series / Issue Number / Year (Title is left blank; CAPT never parsed it
out either) from the current filename, used to pre-populate the edit panel when a file
is selected. Tolerant of scene-release-style tags via bracket-stripping heuristics, but
not exhaustive — this is acceptable because nothing is committed until the user reviews
the live preview (§12.1.5) and corrects anything mis-parsed.

#### 12.1.4 Edit Panel

Four fields — **Series, Issue, Title, Year** — each with two independent checkboxes:

| Column | Meaning |
|---|---|
| **File** | Apply this field's typed value to the single currently-selected file only |
| **All** | Apply this field's typed value to every currently loaded file |

**Per-field independence, no column auto-select.** CAPT's original behaviour
auto-selected every File checkbox the moment one was ticked (same for All) — an
all-or-nothing column. This is **not** carried over. Each field's File/All pair is
fully independent of every other field's, matching the convention already established
for the Full Editor's "Apply to: All" checkboxes (`EDITOR_SPEC.md` §5.2, Item 5 of
`comicvault-changes-v2.3.md`) — e.g. Series→All and Issue→File can be set
simultaneously, applying Series across the whole batch while leaving Issue numbers
edited per-file.

**Batch options:**

- **Auto-Increment Issue Numbers** — enabled only when **Issue→All** is checked
  specifically (fixes a bug in the original CAPT, where it was enabled by *any* All
  checkbox regardless of which field). When active, the Issue value typed in is treated
  as the starting number and incremented sequentially down the loaded-files list in its
  current display order (respects drag-and-drop reorder).
- **Case style** — Title Case / All UPPER Case / All lower case, mutually exclusive
  (single-choice group, unchanged from CAPT). Applies only to Series and Title text
  values — Issue and Year are never case-styled.

#### 12.1.5 Live Preview

No explicit "Preview Changes" button. The Preview list updates immediately on every
field edit or checkbox change. Single-file edits **accumulate** across file
selections — select File A, tick a field, edit it; select File B, tick a different
field, edit it; both A and B now sit in the Preview list simultaneously, each carrying
only its own edited field(s) with everything else left as originally parsed. This
matches CAPT's existing accumulation behaviour exactly, just without the manual Preview
button. Switching into a batch ("All") edit, or pressing **Clear Preview**, resets the
list. Clear Preview button is retained.

#### 12.1.6 Apply Rename

Attempts every file currently in the Preview list. On completion, shows a summary modal
matching the Full Editor's existing Process-error pattern (`feProcessErrorModal`):
"Renamed X of Y files", plus a per-file error list for any failures (permission denied,
filename collision, file no longer present on disk, etc.). Files that succeed clear
from the Preview list; files that fail remain so the user can retry or adjust. No
partial-silent-failure — every attempted file is accounted for in the summary.

There is **no undo**. This is consistent with the tool's nature (a basic log, not a
transaction system) and matches CAPT's own behaviour — the live preview is the only
safety net before committing.

#### 12.1.7 Audit Log

New `rename_log.md` in `/logs/`, following the existing append-only pattern in
`scan_logs.py` — one line per renamed file:

```
DD/MM/YYYY HH:MM — old_filename.ext → new_filename.ext
```

**Independent 1MB size cap** — not governed by the existing configurable Log Size
Limit setting (§8), which stays scoped to the four scan logs only. Once `rename_log.md`
exceeds 1MB, the oldest entries are dropped first (same truncation mechanism as
`scan_logs.py`'s `_truncate_if_oversized()`, just a fixed ceiling instead of the
configurable one).

#### 12.1.8 Implementation Notes (for Code)

Not binding design, but worth flagging before the build session:

- New backend router (e.g. `backend/routers/rename.py`) mirroring `editor_full.py`'s
  shape: a `browse` endpoint (no `library_root` restriction, lists files *and* folders,
  no extension filter, plus a drive-list endpoint for the "This PC" Up-navigation
  terminus), working-file-list endpoints (add/remove/clear — no recursion, no
  extension filter), and an apply endpoint.
- New `rename_log.py`, parallel to `scan_logs.py`, with its own fixed 1MB ceiling.
- Port `parse_comic_filename()`, `build_filename()`, and the rename-application logic
  from `comic_file_editing_toolkit/src/cap_toolkit/utils/filename_parser.py` and
  `rename_u.py` directly — both are already pure functions with no PyQt dependency.
- This is the **third** near-identical in-app folder-tree picker implementation
  (Editor's `fePicker*`, Custom Tabs' `ctPicker*`, now Rename's). Worth a quick
  judgement call on whether to factor a shared picker component now or carry the
  duplication — not a blocker either way, flagging for awareness only.

---

## Change Log — addendum

| Date | Change | Reason |
|---|---|---|
| 2026-06-27 | Added §12 Processing Tools (new top-level section) and §12.1 File Rename — full scope, picker behaviour, checkbox model, live preview, error handling, and audit log design. Ported from CAPT's standalone File Renamer per `ROADMAP.md`'s "CAPT extra tools" entry, brought in one tool at a time starting with Rename. | Dedicated scoping session 2026-06-27 — CAPT source code and `Processing/` folder structure inspected directly to ground design decisions. |
