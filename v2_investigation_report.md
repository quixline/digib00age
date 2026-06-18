CAPT Investigation Report

Project shape

Top-level structure (excluding .venv/ and pycache/):
web_xml_editor/
core.py                  # 9 lines — pure import re-export, no logic
web_server.py            # 728 lines — Flask app + all routes
index.html                # main editor UI (228 lines)
file_mgmnt.html / .js     # file browser UI (27 / 253 lines)
script.js                 # 1153 lines — almost all client-side logic lives here
login.html                 # vestigial, see §6
styles.css
requirements.txt
start_xml_editor.bat
images/ct_logo.ico
utils/
archive_xml_loader.py   # find/extract XML from zip/rar (105 lines)
xml_archive_unpacker.py # extract/inject/repack archive (295 lines)
xml_parser.py            # parse ComicInfo.xml + filename fallback (176 lines)
xml_worker.py             # batch orchestration (147 lines)
widgets/
xml_editor.py            # build_xml_from_fields (90 lines)
Total ≈ 3,260 lines across 12 source files — a small, focused tool, smaller than ComicVault V1.
README: describes itself as a web port of an original PyQt6 desktop app ("Comic Toolkit"), confirms Flask + lxml + rarfile (optional) + Werkzeug, documents the same REST routes found in code, and states the editing logic is unchanged from the desktop version — only the UI layer changed.
Dependencies (requirements.txt):
Flask>=2.0.0
lxml>=4.9.0
rarfile>=4.0
Werkzeug>=2.0.0
Flask-Limiter>=2.8.0
Confirms Flask as expected. Discrepancy: SPEC.md Section 2 says "Pillow" is part of the editor stack — Pillow is not in requirements.txt, but it is imported on-demand inside web_server.py's get_page route (importlib.import_module("PIL.Image")) purely to read image dimensions for the in-browser page preview, not for metadata editing. Flask-Limiter is present but never imported/used anywhere in web_server.py — dead dependency.

Data model

No database of any kind. CAPT is purely file-by-file:

selected_files and queue_files are plain in-memory Python dicts (web_server.py lines 27–28), explicitly commented "for demo purposes... In production, use a database". They reset on every server restart.
It never scans library_root on its own initiative — the user must explicitly browse to and add files/folders via /folders/add, /files/add, or the file_mgmnt explorer. There is no background scanner, no index, no persistence.
Zero overlap with ComicVault's issues/issue_genres tables structurally — there's nothing to overlap with, since CAPT has no schema at all.


Core editing logic


Reading: utils/archive_xml_loader.py opens the archive with zipfile.ZipFile (or rarfile.RarFile for .cbr), lists *.xml entries, and decodes the chosen one as UTF-8 text. utils/xml_parser.py parses it with lxml.etree in recovery mode (recover=True), builds a lower-cased tag→text map, and extracts a fixed allowlist of tags (see below). If extraction or parsing fails, it falls back to filename-pattern parsing (parse_filename_for_comicinfo), same fallback intent as SPEC.md Section 9, independently implemented.
Writing — full archive rewrite, not in-place patch. This is a meaningful correction to the investigation prompt's framing: utils/xml_archive_unpacker.py does not patch the zip's central directory in place. It (1) extracts the entire CBZ to a temp dir, (2) copies/overwrites ComicInfo.xml into that temp dir, (3) flattens all files into a second temp dir, (4) calls shutil.make_archive(..., "zip", ...) to rebuild a brand-new zip from scratch, then (5) os.replace()s it over the original path. Every save rewrites every page image in the archive. For CBR it shells out to an external rar executable via subprocess.run to repack (cmd = ["rar", "a", "-r", "-ep1", ...]) — this assumes a rar.exe is on PATH; nothing in requirements.txt provides it.
Fields exposed in the UI (from index.html form, cross-referenced against widgets/xml_editor.py's preserve-on-write behaviour): Series, Title, Number, IncrementNumber (checkbox), Year, Genre, Format, BlackAndWhite (checkbox), AgeRating, Summary, Count, Writer, Penciller, Publisher, PageCount, ScanInformation, StoryArc, Language, Notes (Notes field defaults to literal text "Modified with the CAPT", editable).

Fields ComicVault stores that CAPT cannot edit: Volume, Month, Inker, Colorist, Letterer, CoverArtist, Characters, Teams, Locations, Manga, StoryArcNumber. These pass through untouched on save because build_xml_from_fields only touches tags present in the submitted field_values dict and otherwise preserves the original XML verbatim.
Fields CAPT edits that ComicVault explicitly drops (SPEC.md §8): IncrementNumber (used live, for batch numbering — see below), ScanInformation (exposed as an editable text field — contradicts SPEC.md's assumption that it's "always empty"; a user can and may have put real text in it), and Notes (matches the SPEC's assumption fairly closely, though the actual default string is "Modified with the CAPT", not "Modified with CAPT" — a one-word wording difference worth knowing if anything ever matches on that string).
Discrepancy: SPEC.md §8 also lists UseFirstYear, ApplySummary, ApplyWriter, ApplyPenciller, Editor, Review as fields CAPT edits/drops. None of these appear anywhere in this codebase — not in the form, not in COMICINFO_TAGS, not in any route. Either they were desktop-PyQt6-only fields that were never carried into the web port, or SPEC.md's assumption about this specific repo is simply wrong. Flagging rather than resolving.


Dropdown enforcement — does NOT match SPEC.md's assumption. SPEC.md Section 7 states genre values are consistent "because the editor uses a dropdown menu — no normalisation needed." In the actual code, none of the fields use a true constrained <select> dropdown. Genre, Format, AgeRating, and Language are all <input type="text" list="..."> backed by an HTML <datalist> — free-text inputs with autocomplete suggestions only. For Genre specifically, script.js (setupGenreTokenDropdown, lines ~244–320) goes further: it removes the native list attribute and replaces it with a custom comma-token autocomplete widget that suggests values from the same option list but places no constraint on what gets typed. A user can freely type an arbitrary genre string. This directly explains the data-quality issue SPEC.md's own Section 20.11 records ("a handful of files carry old genre values predating the CAPT editor's dropdown... compare the vault's genre menu against the editor dropdown, find the odd ones") — the dropdown was never actually enforcing anything, it was always just a suggestion list.
BlackAndWhite handling matches SPEC.md exactly: the checkbox has no value attribute, so its native browser default is "on". script.js sends input.checked ? (input.value || 'true') : '' → "on" when checked, empty string when unchecked. widgets/xml_editor.py's merge logic treats an empty string as "remove the tag" — so the on-disk result is precisely <BlackAndWhite>on</BlackAndWhite> or tag-absent, matching SPEC.md Section 9's rule.
Genre CSV / multi-value handling: Genre (and only Genre) is comma-token-based free text; the raw comma-separated string is sent as-is and written as a single <Genre> tag value — no server-side splitting, no validation against an allowed set.
Batch/increment logic: utils/xml_worker.py's process_xml_files takes a start_issue_no and increments Number by 1 per file in list order when increment_enabled is true — straightforward sequential numbering, no gap detection or collision checking.


Routes / UI surface

Flask routes (consolidated from web_server.py, more complete than the README's own summary):
┌─────────────────┬──────────────────────────────────────────┬────────────────────────────────────────────────────┐
│     Method      │                  Route                   │                      Purpose                       │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /                                        │ Main editor page (index.html)                      │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│                 │ /file_mgmnt.html, /script.js,            │                                                    │
│ GET             │ /file_mgmnt.js, /styles.css,             │ Static assets                                      │
│                 │ /favicon.ico                             │                                                    │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /api                                     │ API doc (self-describing, slightly stale — omits   │
│                 │                                          │ some routes below)                                 │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ POST            │ /resolve-paths                           │ Resolve relative→absolute paths                    │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ POST            │ /folders/add                             │ Recursively add all comics under given folder(s)   │
│                 │                                          │ to working set                                     │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ POST            │ /files/add                               │ Add specific file paths to working set             │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /files                                   │ List working set                                   │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET / POST      │ /files/<id>/xml                          │ Get / update XML fields for one file               │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ POST            │ /process                                 │ Batch-process a list of file IDs (supports         │
│                 │                                          │ per_file_data and increment)                       │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /files/<id>/preview                      │ List image filenames + page count in archive       │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /files/<id>/page/<n>                     │ Base64 image data for one page (uses Pillow for    │
│                 │                                          │ dimensions)                                        │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ DELETE          │ /files/<id>/remove, /files/clear         │ Remove from working set                            │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ POST/GET/DELETE │ /queue/...                               │ A second, separate "queue" of files with per-file  │
│                 │                                          │ captured form data, independent of the working set │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /browse                                  │ Directory listing, gated to paths starting with    │
│                 │                                          │ "L:"                                               │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ POST            │ /rename                                  │ Rename/move a file, gated to "L:\Comics Archives"  │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ GET             │ /fileinfo, POST /update-xml              │ Path-based (not file-ID-based) read/write of XML,  │
│                 │                                          │ also gated to "L:\Comics Archives"                 │
└─────────────────┴──────────────────────────────────────────┴────────────────────────────────────────────────────┘
Bug found, relevant to "how does it locate files": there is an inconsistency in the hardcoded path guard itself. file_mgmnt.js defines DEFAULT_PATH = 'L:\Comic Archives' (matching SPEC.md's library_root), but /rename, /fileinfo, and /update-xml in web_server.py gate access with path.startswith("L:\Comics Archives") — note the extra "s" in "Comics". /browse only checks the looser "L:" prefix, so it works regardless, but the other three routes would silently reject every valid path under the real library root. This looks like an actual latent bug in CAPT, not just a SPEC.md assumption mismatch — worth confirming against the live folder name.
UI screens:

index.html — two-pane layout: left column lists a "working set" of loaded files plus a separate "Queue"; right side is a tabbed form (Fields / advanced "xml" tab) for the currently selected file, plus an image-page preview/zoom viewer (prev/next, zoom in/out) that pulls pages on demand via /files/<id>/page/<n>.
file_mgmnt.html — a separate file-explorer page (breadcrumb, tree view, multi-select, "Add Selected Files/Folder") that POSTs to /files/add / /folders/add.

Batch operations: yes, real ones — /process accepts multiple file IDs with either one shared field set applied to all, or per_file_data for distinct per-file values, plus sequential issue-number incrementing. This is a genuine multi-file workflow, not single-file-only.

The existing sync mechanism

Could not find it. A repo-wide search for localhost, 8000, 8001, scan/file, requests., urllib, fetch( turned up no outbound HTTP call to a reader server anywhere in .py or .js files. CAPT, as it exists in this repo, has no code that calls ComicVault's /api/scan/file endpoint or any other webhook. This matches ComicVault's own SPEC.md Change Log entry for 2026-06-17: "No Flask editor process exists in this repo, so the tray app does not launch/manage an editor subprocess." SPEC.md's Section 2 description of the sync call appears to be a planned/assumed integration that was never actually implemented in this codebase — flag this as a discrepancy to resolve before any integration plan assumes it exists today.

Other structurally relevant findings


No config.json equivalent. All paths are hardcoded directly in source: "L:\Comic Archives" (file_mgmnt.js), "L:\Comics Archives" (web_server.py, three routes, inconsistent spelling as noted above), and a hardcoded Python interpreter path in start_xml_editor.bat (C:\Python_Projects\Comic_Toolkit\venv\Scripts\python.exe) that doesn't match this repo's actual .venv location. Port is also hardcoded: app.run(host="0.0.0.0", port=5000, debug=True) — not port 8001 as SPEC.md assumes, and it binds 0.0.0.0 (network-reachable) with debug=True, not localhost-only as SPEC.md's "Editor is localhost-only" assumption states.
No tests anywhere in the tree.
Vestigial auth: login.html posts to /api/login, but that route doesn't exist in web_server.py — login_required is now a no-op decorator (# Local-only mode: no authentication required) per the commit 18e28a1 refactor: Simplify authentication logic and remove unused login functionality. The login page is dead code left over from an earlier iteration.
Maintenance signal: actively maintained, not "written once and left alone" — 18 commits in this repo's history, with the two most recent (230641b, e6890a2) both from the current date-equivalent session adding genre dropdown options, and earlier commits show iterative feature work (queue counters, language datalist, login added then removed, file management UX). It reads as a live, evolving personal tool.
Size/complexity: ~3,260 total lines, 12 source files — a small, single-purpose tool, well under ComicVault's apparent scope, consistent with "focused editor" rather than "second platform."