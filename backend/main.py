"""
ComicVault — Reader Server
FastAPI entry point. Runs on localhost:9424 by default (home network accessible).
All paths come from config.json — nothing is hardcoded here.
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Resolve project root (one level up from backend/)
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent

# Add project root to path so sibling packages import cleanly
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------
CONFIG_PATH = PROJECT_ROOT / "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------
import asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402
from backend.database import init_db, SessionLocal  # noqa: E402


def _warmup_db() -> None:
    """Pre-warm the SQLite OS page cache so the first user request is instant.
    Runs in a thread pool to avoid blocking the asyncio event loop.
    """
    db = SessionLocal()
    try:
        # Reading these two tables warms every page that the home-strips
        # endpoint will need. Without this, a cold disk causes the first
        # /api/home/strips call to be very slow while subsequent calls
        # (which find the pages in OS cache) are instant.
        db.execute(text("SELECT id, series, format_group, date_added FROM issues WHERE missing = 0"))
        db.execute(text("SELECT issue_id, status FROM reading_progress"))
    except Exception:
        pass  # don't let a warm-up failure abort startup
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    init_db()
    # Run the warm-up in a thread so it doesn't block the event loop,
    # but still completes before the server accepts any connections.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warmup_db)

    from backend.scheduler import auto_scan_loop, backup_loop, maybe_scan_on_launch, processing_folder_loop

    # Fire-and-forget — must not block startup waiting for a full scan.
    asyncio.create_task(maybe_scan_on_launch())
    scan_task = asyncio.create_task(auto_scan_loop())
    backup_task = asyncio.create_task(backup_loop())
    processing_folder_task = asyncio.create_task(processing_folder_loop())

    yield

    for task in (scan_task, backup_task, processing_folder_task):
        task.cancel()
    for task in (scan_task, backup_task, processing_folder_task):
        try:
            await task
        except asyncio.CancelledError:
            pass

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ComicVault",
    description="Personal comic book library server",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow requests from any origin on the home network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — each file owns a slice of the API
# ---------------------------------------------------------------------------
from fastapi import Depends  # noqa: E402
from backend.auth import is_local_request, is_remote_admin_enabled, require_admin_auth  # noqa: E402
from backend.routers import (  # noqa: E402
    library, reader, progress, admin, home, editor_basic, editor_full, admin_auth,
    rename, convert, convert_images, processing_folder, filename_sort, xml_tagging, sync,
    library_move,
)

app.include_router(library.router, prefix="/api")
app.include_router(reader.router,  prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(sync.router,    prefix="/api")  # v2.5 Item 3 — same ungated tier as progress/reader
app.include_router(home.router,    prefix="/api")

# admin_auth is intentionally ungated — it's the login/status surface the gate itself depends on.
app.include_router(admin_auth.router, prefix="/api")

# Gated per ADMIN_SPEC.md §7.1: all /api/admin/* and /api/editor/* routes require auth
# once password protection is enabled (no-op when disabled, V1 behaviour unchanged).
_auth_gate = [Depends(require_admin_auth)]
app.include_router(admin.router,        prefix="/api", dependencies=_auth_gate)
app.include_router(editor_basic.router, prefix="/api", dependencies=_auth_gate)
app.include_router(editor_full.router,  prefix="/api", dependencies=_auth_gate)
app.include_router(rename.router,       prefix="/api/admin", dependencies=_auth_gate)
app.include_router(convert.router,      prefix="/api/admin", dependencies=_auth_gate)
app.include_router(convert_images.router, prefix="/api/admin", dependencies=_auth_gate)
app.include_router(processing_folder.router, prefix="/api/admin", dependencies=_auth_gate)
app.include_router(filename_sort.router,     prefix="/api/admin", dependencies=_auth_gate)
app.include_router(xml_tagging.router,       prefix="/api/admin", dependencies=_auth_gate)
app.include_router(library_move.router,      prefix="/api/admin", dependencies=_auth_gate)

# ---------------------------------------------------------------------------
# Serve frontend static files
# ---------------------------------------------------------------------------
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    # Serve /static/* from frontend/
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    # Serve the HTML pages at their short URLs
    from fastapi.responses import FileResponse
    from fastapi import HTTPException, Request

    @app.get("/", include_in_schema=False)
    async def home():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/series/{issue_id}", include_in_schema=False)
    async def series_page(issue_id: int):
        return FileResponse(str(FRONTEND_DIR / "series.html"))

    @app.get("/issue/{issue_id}", include_in_schema=False)
    async def issue_page(issue_id: int):
        return FileResponse(str(FRONTEND_DIR / "issue.html"))

    @app.get("/admin", include_in_schema=False)
    async def admin_page(request: Request):
        # v2.4 Item 1: page navigation itself is part of the gate, not just the
        # API calls the page makes — a remote request with Remote Administration
        # off gets no page at all, matching require_admin_auth's API-level block.
        if not is_local_request(request) and not is_remote_admin_enabled():
            raise HTTPException(status_code=403, detail={"error": "remote_admin_disabled"})
        return FileResponse(str(FRONTEND_DIR / "admin.html"))

    @app.get("/guide", include_in_schema=False)
    async def guide_page():
        return FileResponse(str(FRONTEND_DIR / "guide.html"))

    @app.get("/editor", include_in_schema=False)
    async def editor_full_page(request: Request):
        if not is_local_request(request) and not is_remote_admin_enabled():
            raise HTTPException(status_code=403, detail={"error": "remote_admin_disabled"})
        return FileResponse(str(FRONTEND_DIR / "editor_full.html"))

    # Service worker must be served from the root scope (/sw.js) so it can
    # control all pages. StaticFiles only covers /static/*, so add an explicit
    # route here. Cache-Control: no-cache so browsers always revalidate it.
    @app.get("/sw.js", include_in_schema=False)
    async def service_worker():
        return FileResponse(
            str(FRONTEND_DIR / "sw.js"),
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache"},
        )

# ---------------------------------------------------------------------------
# Entry point — run directly with: python backend/main.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = config.get("reader_port", 9424)
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",   # Accessible on home network
        port=port,
        reload=False,
    )
