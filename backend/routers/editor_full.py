"""
ComicVault — Editor (Full) Router — pre-library staging toolbox.
EDITOR_SPEC.md Section 5. Normally operates entirely on files not yet in the
database — no rescan-trigger logic for the ordinary pre-library path
(Section 5). **One deliberate exception**, added for the review-queue
"Send to Full Editor" action: process_batch() rescans + clears the review
flag for any saved file whose path matches an existing Issue.file_path —
see process_batch's own docstring and EDITOR_SPEC.md's review-queue section.

File picker (server-side, path-based — Section 5.1, ported from CAPT):
  GET    /api/editor/full/browse                Directory listing
  POST   /api/editor/full/files/add              Add specific files by path
  POST   /api/editor/full/folders/add            Add all comics under folder(s), recursively

Working set ("Loaded Files"):
  GET    /api/editor/full/files                  List working set
  DELETE /api/editor/full/files/clear             Clear working set
  DELETE /api/editor/full/files/{file_id}          Remove one file
  GET    /api/editor/full/files/{file_id}/xml      Load field values (or multi-XML candidates)
  POST   /api/editor/full/files/{file_id}/resolve-xml  Pick which XML to keep (Section 3.5)
  GET    /api/editor/full/files/{file_id}/preview      Image list + count
  GET    /api/editor/full/files/{file_id}/page/{n}     Single page image, base64

Queue:
  POST   /api/editor/full/queue/add               Add a file + its captured field values
  GET    /api/editor/full/queue                    List queue
  DELETE /api/editor/full/queue/clear               Clear queue
  DELETE /api/editor/full/queue/{file_id}            Remove one from queue

Batch:
  POST   /api/editor/full/process                  Process Queue or Process All

Search Online (EDITOR_SPEC.md §9, ComicTagger integration):
  GET    /api/editor/full/search/series             Select Series step — search ComicVine
  GET    /api/editor/full/search/issues              Select Issue step — issues for one series
  POST   /api/editor/full/search/confirm              Map a chosen issue to ComicVault fields
"""

import base64
import dataclasses
import io
import os

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend import archive_formats, config, ct_bridge
from backend.database import get_db
from backend.editor.archive_io import (
    IMAGE_EXTENSIONS,
    extract_xml_from_archive,
    find_xml_in_archive,
    get_archive_page_count,
    keep_single_xml,
    write_comicinfo_to_cbz,
)
from backend.editor.batch import apply_increment
from backend.editor.field_merge import build_xml_from_fields
from backend.editor.validation import validate_enforced_fields
from backend.editor.xml_parser import COMICINFO_TAGS, parse_comicinfo_xml
from backend.models import Issue
from backend.scanner import scan_single_file

router = APIRouter(tags=["editor-full"])

_image_list_cache: dict[str, tuple[tuple[float, int], list[str]]] = {}


def _cached_image_list(archive_path: str) -> list[str]:
    """
    Sorted in-archive image filenames, cached per archive path and keyed on
    (mtime, size) so a changed file invalidates automatically — same fix as
    PERFORMANCE.md findings #4/#5 (backend/routers/reader.py's
    _sorted_pages), applied here since this module re-parsed the ZIP
    central directory on every single preview/page call independently
    (finding #6).
    """
    stat = os.stat(archive_path)
    cache_key = (stat.st_mtime, stat.st_size)
    cached = _image_list_cache.get(archive_path)
    if cached and cached[0] == cache_key:
        return cached[1]

    image_files = sorted(
        f for f in archive_formats.archive_namelist(archive_path) if f.lower().endswith(IMAGE_EXTENSIONS)
    )
    _image_list_cache[archive_path] = (cache_key, image_files)
    return image_files

# CBR added v2.4 Item 5/11 (EDITOR_SPEC.md §3.1) — Full Editor's pre-library
# intake needs to handle CBR the same as CBZ; saving rebuilds it as .cbz.
ALLOWED_EXTENSIONS = {".cbz", ".cbr"}

# In-memory working set + queue — Full Editor is desktop-only, single-session,
# never persisted (matches CAPT's existing model, Section 5).
_working_files: dict[str, dict] = {}
_queue_files: dict[str, dict] = {}
_next_id = 1


def _new_id() -> str:
    global _next_id
    file_id = str(_next_id)
    _next_id += 1
    return file_id


def _is_comic_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def _is_within_library(path: str) -> bool:
    """
    Path-validity guard, now backed by config.json's library_root instead of
    a hardcoded string (EDITOR_SPEC.md Section 5.1 bug fix — the old CAPT
    code checked against a typo'd "L:\\Comics Archives" in some routes and
    the correct "L:\\Comic Archives" only loosely in others).
    """
    try:
        norm_path = os.path.normpath(os.path.abspath(path)).lower()
        norm_root = os.path.normpath(os.path.abspath(config.LIBRARY_ROOT)).lower()
        return norm_path == norm_root or norm_path.startswith(norm_root + os.sep)
    except Exception:
        return False


def _get_working_file_or_404(file_id: str) -> dict:
    entry = _working_files.get(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found in working set")
    return entry


# ---------------------------------------------------------------------------
# File picker (Section 5.1)
# ---------------------------------------------------------------------------

@router.get("/editor/full/browse")
def browse_directory(path: str = None):
    """Directory listing for the tree-view picker, scoped to library_root."""
    target = path or config.LIBRARY_ROOT

    if not _is_within_library(target):
        raise HTTPException(status_code=403, detail="Path is outside library_root")

    if not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Directory not found")

    items = []
    try:
        for name in os.listdir(target):
            full_path = os.path.join(target, name)
            if os.path.isfile(full_path) and _is_comic_file(name):
                items.append(
                    {
                        "name": name,
                        "type": "file",
                        "path": full_path,
                        "xml_files": find_xml_in_archive(full_path),
                    }
                )
            elif os.path.isdir(full_path):
                try:
                    has_comics = any(_is_comic_file(f) for f in os.listdir(full_path))
                except (OSError, PermissionError):
                    has_comics = False
                items.append(
                    {"name": name, "type": "folder", "path": full_path, "has_comics": has_comics}
                )
    except (OSError, PermissionError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"path": target, "items": items}


def _add_path_to_working_set(file_path: str) -> dict | None:
    """Validates and adds one file path to the working set, returning the
    added {id, filename, path, xml_files} entry, or None if it fails
    validation (outside library_root, not a file, not a comic archive).
    Shared by add_files (path-based, from the folder-browse picker) and
    add_files_by_issues (DB-based, from the review-queue "Send to Full
    Editor" action) so the validation logic isn't duplicated."""
    if not _is_within_library(file_path):
        return None
    if not os.path.isfile(file_path) or not _is_comic_file(file_path):
        return None

    file_id = _new_id()
    entry = {
        "filename": os.path.basename(file_path),
        "path": file_path,
        "xml_files": find_xml_in_archive(file_path),
    }
    _working_files[file_id] = entry
    return {"id": file_id, **entry}


@router.post("/editor/full/files/add")
def add_files(payload: dict = Body(...)):
    """Add specific files to the working set by path."""
    file_paths = payload.get("file_paths", [])
    if not file_paths:
        raise HTTPException(status_code=400, detail="No paths provided")

    added = []
    for file_path in file_paths:
        entry = _add_path_to_working_set(file_path)
        if entry:
            added.append(entry)

    return {"success": True, "files": added}


@router.post("/editor/full/files/add-by-issues")
def add_files_by_issues(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Add already-catalogued issues to the working set by Issue.id, resolving
    each to its known file_path — the review-queue "Send to Full Editor"
    action, skipping the manual folder-browse picker for files already in
    ComicVault's database. Unknown ids are silently skipped (same soft-fail
    convention as progress.py's bulk endpoints).
    """
    issue_ids = payload.get("issue_ids", [])
    if not issue_ids:
        raise HTTPException(status_code=400, detail="No issue ids provided")

    issues = db.query(Issue).filter(Issue.id.in_(issue_ids)).all()
    added = []
    for issue in issues:
        entry = _add_path_to_working_set(issue.file_path)
        if entry:
            added.append(entry)

    return {"success": True, "files": added}


@router.post("/editor/full/folders/add")
def add_folder(payload: dict = Body(...)):
    """Recursively add every comic archive under the given folder(s)."""
    folder_paths = payload.get("folder_paths", [])
    if not folder_paths:
        raise HTTPException(status_code=400, detail="No folder paths provided")

    added = []
    for folder_path in folder_paths:
        if not _is_within_library(folder_path) or not os.path.isdir(folder_path):
            continue

        for root, _dirs, files in os.walk(folder_path):
            for name in files:
                if not _is_comic_file(name):
                    continue
                file_path = os.path.join(root, name)
                file_id = _new_id()
                entry = {
                    "filename": name,
                    "path": file_path,
                    "xml_files": find_xml_in_archive(file_path),
                }
                _working_files[file_id] = entry
                added.append({"id": file_id, **entry})

    return {"success": True, "files": added}


# ---------------------------------------------------------------------------
# Working set ("Loaded Files")
# ---------------------------------------------------------------------------

@router.get("/editor/full/files")
def list_files():
    return {"files": [{"id": fid, **entry} for fid, entry in _working_files.items()]}


@router.delete("/editor/full/files/clear")
def clear_files():
    _working_files.clear()
    return {"success": True}


@router.delete("/editor/full/files/{file_id}")
def remove_file(file_id: str):
    if file_id not in _working_files:
        raise HTTPException(status_code=404, detail="File not found in working set")
    del _working_files[file_id]
    return {"success": True}


@router.get("/editor/full/files/{file_id}/xml")
def get_file_xml(file_id: str):
    """
    Load field values for a working-set file. If more than one XML entry is
    found in the archive, returns the candidates for the multi-XML warning
    UI instead (Section 3.5) — the caller must resolve via resolve-xml
    before normal editing proceeds.
    """
    entry = _get_working_file_or_404(file_id)
    path = entry["path"]

    xml_files = find_xml_in_archive(path)

    if len(xml_files) > 1:
        candidates = []
        for name in xml_files:
            content = extract_xml_from_archive(path, name)
            fields = parse_comicinfo_xml(content) if content else {}
            candidates.append({"filename": name, "fields": fields})
        return {"file_id": file_id, "multiple_xml": True, "candidates": candidates}

    original_xml = extract_xml_from_archive(path, xml_files[0]) if xml_files else None
    fields = (
        parse_comicinfo_xml(original_xml)
        if original_xml
        else {tag: "" for tag in COMICINFO_TAGS}
    )
    fields["PageCount"] = str(get_archive_page_count(path))

    return {"file_id": file_id, "multiple_xml": False, "fields": fields}


@router.post("/editor/full/files/{file_id}/resolve-xml")
def resolve_file_xml(file_id: str, payload: dict = Body(...)):
    """Keep one ComicInfo.xml candidate, delete the others (Section 3.5)."""
    entry = _get_working_file_or_404(file_id)
    keep = payload.get("keep")
    if not keep:
        raise HTTPException(status_code=400, detail="No filename specified to keep")

    try:
        entry["path"] = keep_single_xml(entry["path"], keep)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to resolve XML: {exc}")

    entry["filename"] = os.path.basename(entry["path"])
    entry["xml_files"] = find_xml_in_archive(entry["path"])
    return get_file_xml(file_id)


@router.get("/editor/full/files/{file_id}/preview")
def get_file_preview(file_id: str):
    entry = _get_working_file_or_404(file_id)
    try:
        image_files = _cached_image_list(entry["path"])
        return {"image_list": image_files, "total_pages": len(image_files)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/editor/full/files/{file_id}/page/{page_num}")
def get_file_page(
    file_id: str,
    page_num: int,
    w: int | None = Query(default=None, ge=16, le=2000),
):
    entry = _get_working_file_or_404(file_id)
    try:
        image_files = _cached_image_list(entry["path"])
        if page_num < 0 or page_num >= len(image_files):
            raise HTTPException(status_code=404, detail="Page number out of range")

        img_file = image_files[page_num]
        img_bytes = archive_formats.archive_read_bytes(entry["path"], img_file)

        from PIL import Image

        img = Image.open(io.BytesIO(img_bytes))
        width, height = img.size

        # Optional server-side downscale for the viewer's lazy thumbnail strip
        # (v2.6 Item 7). Absent/oversized w → original page bytes returned
        # untouched, so the main viewer keeps full resolution.
        if w is not None and width > w:
            new_h = max(1, round(height * w / width))
            thumb = img.convert("RGB").resize((w, new_h), Image.LANCZOS)
            buf = io.BytesIO()
            thumb.save(buf, format="JPEG", quality=70)
            out_bytes = buf.getvalue()
            data_uri = f"data:image/jpeg;base64,{base64.b64encode(out_bytes).decode('utf-8')}"
            return {
                "filename": img_file,
                "data": data_uri,
                "width": w,
                "height": new_h,
                "page_num": page_num,
            }

        mime_ext = img_file.split(".")[-1].lower()
        data_uri = f"data:image/{mime_ext};base64,{base64.b64encode(img_bytes).decode('utf-8')}"

        return {
            "filename": img_file,
            "data": data_uri,
            "width": width,
            "height": height,
            "page_num": page_num,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------

@router.post("/editor/full/queue/add")
def add_to_queue(payload: dict = Body(...)):
    file_id = payload.get("file_id")
    fields = payload.get("fields", {})

    entry = _get_working_file_or_404(file_id)
    _queue_files[file_id] = {**entry, "queued_fields": fields}
    return {"success": True}


@router.get("/editor/full/queue")
def list_queue():
    return {
        "files": [{"id": fid, **entry} for fid, entry in _queue_files.items()]
    }


@router.delete("/editor/full/queue/clear")
def clear_queue():
    _queue_files.clear()
    return {"success": True}


@router.delete("/editor/full/queue/{file_id}")
def remove_from_queue(file_id: str):
    if file_id not in _queue_files:
        raise HTTPException(status_code=404, detail="File not found in queue")
    del _queue_files[file_id]
    return {"success": True}


# ---------------------------------------------------------------------------
# Batch processing — Process Queue / Process All
# ---------------------------------------------------------------------------

@router.post("/editor/full/process")
def process_batch(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    mode="queue": process every file currently in the Queue, using each
        file's own captured field values. Successfully-processed files are
        removed from the Queue; failures stay so Tez can retry.
    mode="all": process every file in file_ids (the Loaded Files list, in
        its current display order — respects drag-and-drop reorder) using
        the single shared `fields` payload for all of them.

    Both support increment_enabled/start_issue_no (Section 3.4) — Number is
    recomputed sequentially in list order when enabled, no collision check.

    One exception to this file's normal "never touches the DB" rule
    (module docstring): if the saved path matches an existing
    Issue.file_path — i.e. it arrived here via the review-queue "Send to
    Full Editor" action rather than the normal pre-library folder-browse
    picker — the DB row is rescanned and its review flag cleared after a
    successful write, same as the Basic Editor's save path. Files with no
    matching Issue row (the original, still-primary use case) are
    completely untouched.
    """
    mode = payload.get("mode")
    increment_enabled = payload.get("increment_enabled", False)
    start_issue_no = payload.get("start_issue_no") or 1

    if mode == "queue":
        items = [(fid, dict(entry["queued_fields"])) for fid, entry in _queue_files.items()]
        paths = {fid: entry["path"] for fid, entry in _queue_files.items()}
    elif mode == "all":
        file_ids = payload.get("file_ids") or list(_working_files.keys())
        shared_fields = payload.get("fields", {})
        items = []
        paths = {}
        for fid in file_ids:
            entry = _working_files.get(fid)
            if not entry:
                continue
            items.append((fid, dict(shared_fields)))
            paths[fid] = entry["path"]
    else:
        raise HTTPException(status_code=400, detail="mode must be 'queue' or 'all'")

    if not items:
        return {"success": True, "processed": 0, "errors": []}

    if increment_enabled:
        field_dicts = [f for _fid, f in items]
        apply_increment(field_dicts, start_issue_no)

    processed = 0
    errors = []
    succeeded_ids = []

    for file_id, field_values in items:
        path = paths[file_id]
        clean_fields = {k: v for k, v in field_values.items() if k in COMICINFO_TAGS}
        # NeedsReview is never part of the submitted form/queue payload
        # (EDITOR_SPEC.md 9.2) — build_xml_from_fields only touches tags
        # present here, so it won't self-clear without this. Covers both
        # mode="queue" and mode="all", which both flow through this loop.
        clean_fields["NeedsReview"] = ""

        try:
            xml_files = find_xml_in_archive(path)
            original_xml = extract_xml_from_archive(path, xml_files[0]) if xml_files else None
        except Exception as exc:
            errors.append(f"{os.path.basename(path)}: {exc}")
            continue

        # mode="all" with the per-field "Apply to: All" checkboxes (EDITOR_SPEC.md
        # §5.2) can send a partial clean_fields — only the checked fields. The
        # *effective* result after the merge in build_xml_from_fields is each
        # file's own existing value for every unchecked field, so validation must
        # check that merged effective state, not the bare (possibly Genre/Format/
        # AgeRating-less) clean_fields dict on its own.
        existing_fields = parse_comicinfo_xml(original_xml) if original_xml else {}
        effective_fields = {**existing_fields, **clean_fields}

        field_errors = validate_enforced_fields(effective_fields)
        if field_errors:
            errors.append(f"{os.path.basename(path)}: {'; '.join(field_errors)}")
            continue

        try:
            xml_content = build_xml_from_fields(clean_fields, original_xml)
            new_path = write_comicinfo_to_cbz(path, xml_content)
            # CBR source rebuilds as a sibling .cbz (EDITOR_SPEC.md §3.2,
            # v2.4 Item 5/11) — applies identically here as it does to
            # single-file saves. Full Editor tracks files pre-library (no DB
            # row yet), so update the in-memory working/queue entry's own
            # path so it doesn't keep pointing at the now-deleted .cbr.
            if new_path != path:
                target_dict = _queue_files if mode == "queue" else _working_files
                if file_id in target_dict:
                    target_dict[file_id]["path"] = new_path
                    target_dict[file_id]["filename"] = os.path.basename(new_path)

            # Review-queue exception (see process_batch's docstring): only
            # touches the DB if this path was already a known Issue — the
            # normal pre-library folder-browse case has no matching row and
            # is left exactly as before. Mirrors editor_basic.py's
            # _finish_save: file_path must be updated + flushed before
            # scan_single_file, which looks up the row by (new) file_path.
            existing_issue = db.query(Issue).filter(Issue.file_path == path).first()
            if existing_issue:
                if new_path != existing_issue.file_path:
                    existing_issue.file_path = new_path
                    existing_issue.container_format = "cbz"
                    db.flush()
                scan_single_file(new_path, db)
                existing_issue.flagged_for_review = False
                db.commit()

            processed += 1
            succeeded_ids.append(file_id)
        except Exception as exc:
            errors.append(f"{os.path.basename(path)}: {exc}")

    if mode == "queue":
        for file_id in succeeded_ids:
            _queue_files.pop(file_id, None)

    return {"success": not errors, "processed": processed, "errors": errors}


# ---------------------------------------------------------------------------
# Search Online (EDITOR_SPEC.md §9) — Select Series / Select Issue modal.
# Reads Series (required)/Issue #/Year/Issue Count from the currently-focused
# file's form fields at click time (§9.5) — the frontend sends these, this
# router does not re-read them from the working-set entry's own XML. Series/
# issue search goes through ct_bridge.py's shared talker setup (§9.1) — the
# same module the CT Auto-Tag automation stage uses, not a second codepath.
# ---------------------------------------------------------------------------

@router.get("/editor/full/search/series")
def search_online_series(q: str):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Series name required")
    results = ct_bridge.search_series(q.strip())
    return {"results": [dataclasses.asdict(r) for r in results]}


@router.get("/editor/full/search/issues")
def search_online_issues(series_id: str):
    results = ct_bridge.list_issues_for_series(series_id)
    return {"results": [dataclasses.asdict(r) for r in results]}


@router.post("/editor/full/search/confirm")
def search_online_confirm(payload: dict = Body(...)):
    """
    payload: {"issue_id": "..."}. Returns the mapped ComicVault field dict —
    the frontend applies it to the form directly, fully overwriting the
    mapped fields (§9.7). Does not write to the archive or touch
    NeedsReview here — that only happens on the file's next real save
    (Process Queue/Process All), per §9.2/§9.7.
    """
    issue_id = payload.get("issue_id")
    if not issue_id:
        raise HTTPException(status_code=400, detail="issue_id required")
    md = ct_bridge.fetch_issue_metadata(issue_id)
    fields = ct_bridge.metadata_to_field_dict(md)
    return {"fields": fields}
