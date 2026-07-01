"""
ComicVault — File Rename Tool Router (admin-spec-section-12-processing-
tools.md §12.1). Mirrors editor_full.py's shape: a browse endpoint (shared
file_picker.py, no library_root restriction, no extension filter, plus a
drive-list endpoint for the "This PC" Up-navigation terminus), an in-memory
working-file-list, a parse/preview pair (so the parsing/filename-building
regex logic lives in one place, not duplicated in JS), and an apply endpoint.

GET    /api/admin/rename/browse         Directory listing (no path = library_root)
GET    /api/admin/rename/drives         Drive-letter listing ("This PC")
POST   /api/admin/rename/files/add      Add specific files by path
GET    /api/admin/rename/files          List working set
DELETE /api/admin/rename/files/clear    Clear working set
DELETE /api/admin/rename/files/{file_id}  Remove one file
POST   /api/admin/rename/parse          Parse Series/Issue/Year from a filename
POST   /api/admin/rename/preview        Build filenames for the live preview
POST   /api/admin/rename/apply          Rename every file in the submitted preview list
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from backend import file_picker, rename_log
from backend.auth import is_local_request
from backend.config import LIBRARY_ROOT
from backend.rename_tool import parse_comic_filename, preview_renames


def _require_local(request: Request) -> None:
    # Processing Tools shared rule (§12 notes) — the whole section is inert
    # for a remote session, not just the destructive Apply step, since the
    # picker itself exposes server filesystem structure.
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail={"error": "local_access_required"})


router = APIRouter(tags=["rename"], dependencies=[Depends(_require_local)])

# In-memory working file list — mirrors editor_full.py's _working_files
# pattern (desktop-tool-shaped, single-session, never persisted).
_working_files: dict[str, dict] = {}
_next_id = 1


def _new_id() -> str:
    global _next_id
    file_id = str(_next_id)
    _next_id += 1
    return file_id


# ---------------------------------------------------------------------------
# Picker (§12.1.2) — no extension filter, no recursion, no library_root scope
# ---------------------------------------------------------------------------

@router.get("/rename/browse")
def browse_directory(path: str = None):
    target = path or LIBRARY_ROOT
    try:
        return file_picker.list_directory(target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/rename/drives")
def list_drives():
    return {"drives": file_picker.list_drives()}


# ---------------------------------------------------------------------------
# Working file list
# ---------------------------------------------------------------------------

@router.post("/rename/files/add")
def add_files(payload: dict = Body(...)):
    file_paths = payload.get("file_paths", [])
    if not file_paths:
        raise HTTPException(status_code=400, detail="No paths provided")

    added = []
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            continue
        file_id = _new_id()
        entry = {"filename": os.path.basename(file_path), "path": file_path}
        _working_files[file_id] = entry
        added.append({"id": file_id, "parsed": parse_comic_filename(entry["filename"]), **entry})

    return {"success": True, "files": added}


@router.get("/rename/files")
def list_files():
    return {"files": [{"id": fid, **entry} for fid, entry in _working_files.items()]}


@router.delete("/rename/files/clear")
def clear_files():
    _working_files.clear()
    return {"success": True}


@router.delete("/rename/files/{file_id}")
def remove_file(file_id: str):
    if file_id not in _working_files:
        raise HTTPException(status_code=404, detail="File not found in working set")
    del _working_files[file_id]
    return {"success": True}


# ---------------------------------------------------------------------------
# Parsing (§12.1.3) + Live Preview (§12.1.5)
# ---------------------------------------------------------------------------

@router.post("/rename/parse")
def parse_filename(payload: dict = Body(...)):
    filename = payload.get("filename", "")
    return parse_comic_filename(filename)


@router.post("/rename/preview")
def preview(payload: dict = Body(...)):
    """
    payload: {"file_ids": [...], "rename_data": {series, issue_num, issue_title, year},
              "batch_options": {auto_increment, title_style}}
    Returns one preview filename per file_id, in the order given (the caller
    respects drag-and-drop order for Auto-Increment, §12.1.4).
    """
    file_ids = payload.get("file_ids", [])
    rename_data = payload.get("rename_data", {})
    batch_options = payload.get("batch_options", {})

    paths = []
    for fid in file_ids:
        entry = _working_files.get(fid)
        if not entry:
            raise HTTPException(status_code=404, detail=f"File {fid} not in working set")
        paths.append(entry["path"])

    names = preview_renames(paths, rename_data, batch_options)
    return {"previews": [{"file_id": fid, "new_name": name} for fid, name in zip(file_ids, names)]}


# ---------------------------------------------------------------------------
# Apply Rename (§12.1.6) — attempts every file in the submitted preview list
# ---------------------------------------------------------------------------

@router.post("/rename/apply")
def apply_rename(payload: dict = Body(...)):
    """
    payload: {"items": [{"file_id": str, "new_name": str}, ...]} — the exact
    names last shown in the live preview, committed as-is. Every attempted
    file is accounted for in the response (§12.1.6, no partial-silent-
    failure); successes are removed from the working set, failures remain
    for retry. No undo (§12.1.6).
    """
    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items to rename")

    results = []
    for item in items:
        file_id = item.get("file_id")
        new_name = (item.get("new_name") or "").strip()
        entry = _working_files.get(file_id)
        if not entry:
            results.append({"file_id": file_id, "old_name": None, "new_name": new_name,
                             "success": False, "error": "File no longer in working set"})
            continue
        if not new_name:
            results.append({"file_id": file_id, "old_name": entry["filename"], "new_name": new_name,
                             "success": False, "error": "New filename is empty"})
            continue

        old_path = entry["path"]
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        old_name = entry["filename"]
        try:
            if not os.path.isfile(old_path):
                raise FileNotFoundError("File no longer present on disk")
            if os.path.exists(new_path):
                raise FileExistsError(f"{new_name} already exists")
            os.rename(old_path, new_path)
            rename_log.append_entry(old_name, new_name)
            del _working_files[file_id]
            results.append({"file_id": file_id, "old_name": old_name, "new_name": new_name,
                             "success": True, "error": None})
        except Exception as exc:
            results.append({"file_id": file_id, "old_name": old_name, "new_name": new_name,
                             "success": False, "error": str(exc)})

    renamed = sum(1 for r in results if r["success"])
    return {"renamed": renamed, "total": len(results), "results": results}
