# Fix: scanner misses ComicInfo.xml nested in a subfolder

> Logged as **BUG-018** in `BUGS.md`. This is Code's original investigation/
> handoff doc, preserved in full as the implementation reference. Build this
> only after v2.4's scoping day is complete (Item 15 scoped) — not before.

## Context

Archives whose contents (images + `ComicInfo.xml`) sit inside a folder within the
zip — rather than at the zip root — currently import into the library with no
metadata. The xml is valid and present, but the scanner can't see it, so the issue
silently falls back to filename-guessed metadata (no series/credits/etc.), and looks
"broken" in the library and Basic Editor.

Root cause is narrower than it first appeared. Investigation (two prior research
passes, code confirmed directly) shows only the **scanner** is folder-blind:

- `backend/scanner.py:275-276` — `_parse_cbz()` does an exact-equality check
  (`n.lower() == "comicinfo.xml"`) against the zip's `namelist()`, which only
  matches root-level entries. Nested xml never matches → falls to filename parsing.
- The **editors are already correct**. Both Basic Editor
  (`backend/routers/editor_basic.py:100-103`) and Full Editor
  (`backend/routers/editor_full.py:216-244`) use
  `find_xml_in_archive()` / `extract_xml_from_archive()` in
  `backend/editor/archive_io.py:22-42`, which match `*.xml` anywhere in the
  archive regardless of folder depth and extract by full path. So a nested-folder
  archive that somehow got linked to an issue record would actually load fine in
  the Full Editor — the "starts blank" symptom traced back to the scanner having
  already mis-filed the issue under guessed-from-filename metadata, not to the
  editor's read path.
- On save, both editors funnel through `write_comicinfo_to_cbz()` →
  `_rebuild_archive()` (`backend/editor/archive_io.py:57-103`), which extracts the
  whole archive and rebuilds it flat, discarding any folder nesting. This is
  existing, intentional behavior (confirmed in
  `docs/admin-spec-section-12-processing-tools.md:384` — nested-folder archives
  are a known prior problem and the original reason this flattening exists) and
  is **not being touched**.

Decision (confirmed with Tez): fix the scanner's read path only, reusing the
existing `archive_io.py` helpers instead of writing new matching logic. Do **not**
flatten/rebuild archives at scan time — rebuilding ~5,500 archives on a library
scan would risk real delay/hang for no benefit, since flattening already happens
naturally the moment anyone saves through an editor. This is a pure read-side fix:
scanner sees the xml correctly → issue imports with real metadata → file on disk is
untouched until/unless someone edits and saves it, at which point it flattens as it
already does today.

## Change

**File: `backend/scanner.py`**

1. Add import (near other `backend.*` imports, top of file):
   ```python
   from backend.editor.archive_io import find_xml_in_archive, extract_xml_from_archive
   ```
   No circular-import risk: `archive_io.py` has zero internal `backend.*` imports
   (stdlib only). The existing scanner↔editor coupling already runs
   scanner → editor in other modules (e.g. `editor/xml_parser.py:13` imports
   `_parse_filename` from `scanner.py`), so this adds a new edge in the same
   direction, not a new cycle.

2. Replace the xml-discovery block at `scanner.py:272-291` (currently opens the
   zip directly and does the exact-match `namelist()` scan) with logic built on
   `find_xml_in_archive()` / `extract_xml_from_archive()`:
   - Call `find_xml_in_archive(file_path)`, filter results to entries whose name
     ends with `comicinfo.xml` (case-insensitive) — this preserves current
     semantics of only trusting files actually named ComicInfo.xml, not any
     stray `.xml` sidecar, while now matching at any folder depth.
   - Take the first match (consistent with today's `xml_names[0]` behavior, and
     consistent with the scanner having no interactive disambiguation UI the way
     Full Editor's multi-xml flow does — no need to port that UI here).
   - Extract via `extract_xml_from_archive()`, which returns decoded string
     content (not a file handle), so parse with `ET.fromstring(xml_content)`
     instead of the current `ET.parse(xml_file)`. `ET.ParseError` is still raised
     by `fromstring`, so the existing `except ET.ParseError` branch needs no
     change.
   - Both helpers swallow their own exceptions and return `[]` / `None` on
     failure rather than raising — so "no match" and "extract failed" should
     both fall through to the existing `metadata_source = "filename"` path,
     same as today's behavior for a missing/corrupt xml.
   - Leave the second `zipfile.ZipFile(...)` block (`scanner.py:329-336`, which
     counts image entries for `actual_page_count`) untouched — it's already
     folder-agnostic.

3. No other files change. `archive_io.py` stays exactly as-is (per the decision
   not to touch flatten/rebuild logic). No caller of `_parse_cbz()` needs
   updating — its signature and return shape (`tuple[dict, str]`) are unchanged.

## Verification

No automated test suite exists in this repo (no `tests/` dir). Per
`docs/TESTING.md`, verify manually using scratch files outside the real library:

1. Build a scratch CBZ with `ComicInfo.xml` nested in a subfolder (e.g.
   `folder/ComicInfo.xml` alongside images in the same folder), containing real
   metadata fields (series, number, credits).
2. Run it through `scan_single_file()` (or trigger via the existing rescan route)
   and confirm the resulting Issue row has the real xml-sourced metadata, with
   `metadata_source == "xml"` — not the filename-fallback values.
3. Regression-check a root-level-xml scratch CBZ still imports correctly
   unchanged, and a CBZ with no xml at all still correctly falls back to
   filename parsing.
4. Confirm the nested-folder scratch CBZ now also displays correctly in the
   library UI and is editable in the Basic Editor without needing to open the
   Full Editor first.
5. Clean up scratch files after; confirm no real library files or the real
   `Processing` folder were touched.

Per CLAUDE.md close-of-session rules: doc updates (`docs/v2.4/progress.md`,
`docs/CHANGELOG.md`, `docs/BUGS.md` if this gets logged as a bug first, and
`docs/SPEC.md`/scanner-relevant docs if any describe the old root-only behavior)
happen only after this manual verification passes — not before.
