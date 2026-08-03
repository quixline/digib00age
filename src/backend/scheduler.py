"""
digib00age — Auto Scan + Scheduled Backup + Processing Folder schedulers
(ADMIN_SPEC.md §4 "Auto Scan Options", §9 "Scheduled Database Backup",
§11.4.5 "Schedule")

All off by default. Re-read config.json on every loop iteration so a saved
frequency change takes effect without a server restart.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from backend.config import get_config, save_config

logger = logging.getLogger(__name__)

_FREQUENCY_SECONDS = {
    "off": None,
    "1hr": 3600,
    "6hr": 21600,
    "12hr": 43200,
    "1day": 86400,
    "3days": 259200,
    "7days": 604800,
    "1month": 2592000,
}

_BACKUP_FREQUENCY_SECONDS = {
    "off": None,
    "1hr": 3600,
    "2hr": 7200,
    "4hr": 14400,
    "6hr": 21600,
    "12hr": 43200,
    "24hr": 86400,
    "1day": 86400,
    "2days": 172800,
    "3days": 259200,
    "4days": 345600,
    "5days": 432000,
    "6days": 518400,
    "7days": 604800,
    "1week": 604800,
    "2weeks": 1209600,
    "3weeks": 1814400,
    "4weeks": 2419200,
    "1month": 2592000,
    "2months": 5184000,
    "3months": 7776000,
    "6months": 15552000,
    "12months": 31536000,
}

DEFAULT_POLL_SECONDS = 60  # how often we re-check the configured frequency


def _run_scan_background() -> None:
    from backend.database import SessionLocal
    from backend.scanner import scan_library

    db = SessionLocal()
    try:
        scan_library(db)
    except Exception:
        logger.exception("Auto-scan failed")
    finally:
        db.close()


async def auto_scan_loop(poll_seconds: int = DEFAULT_POLL_SECONDS) -> None:
    """Runs forever (until cancelled). Checks the configured frequency every
    poll_seconds and fires a scan once that interval has elapsed since the
    last completed scan."""
    from backend.scanner import scan_progress

    elapsed = 0
    while True:
        await asyncio.sleep(poll_seconds)
        elapsed += poll_seconds

        frequency = get_config().get("auto_scan_frequency", "off")
        interval = _FREQUENCY_SECONDS.get(frequency)
        if interval is None:
            elapsed = 0
            continue

        if elapsed < interval:
            continue

        elapsed = 0
        if scan_progress.running:
            logger.info("Auto-scan due, but a scan is already running — skipping this cycle")
            continue

        logger.info("Auto-scan triggered (frequency=%s)", frequency)
        await asyncio.get_event_loop().run_in_executor(None, _run_scan_background)


async def maybe_scan_on_launch() -> None:
    if not get_config().get("autostart_scan", False):
        return
    from backend.scanner import scan_progress

    if scan_progress.running:
        return
    logger.info("Scan on launch triggered")
    await asyncio.get_event_loop().run_in_executor(None, _run_scan_background)


def _run_backup_background() -> None:
    from backend.config import save_config
    from backend.routers.admin import run_database_backup

    try:
        run_database_backup()
    except FileNotFoundError:
        logger.error("Scheduled backup skipped — database file not found")
        save_config({"last_backup_error": "Database file not found"})
    except OSError as exc:
        logger.exception("Scheduled backup failed")
        save_config({"last_backup_error": str(exc)})


async def backup_loop(poll_seconds: int = DEFAULT_POLL_SECONDS) -> None:
    """Runs forever (until cancelled). Mirrors auto_scan_loop's polling
    pattern — re-reads the configured frequency every poll_seconds and fires
    a backup once that interval has elapsed."""
    elapsed = 0
    while True:
        await asyncio.sleep(poll_seconds)
        elapsed += poll_seconds

        frequency = get_config().get("backup_frequency", "off")
        interval = _BACKUP_FREQUENCY_SECONDS.get(frequency)
        if interval is None:
            elapsed = 0
            continue

        if elapsed < interval:
            continue

        elapsed = 0
        logger.info("Scheduled backup triggered (frequency=%s)", frequency)
        await asyncio.get_event_loop().run_in_executor(None, _run_backup_background)


# ---------------------------------------------------------------------------
# Processing Folder Automation (§11.4.5) — wall-clock scheduling, not
# elapsed-time polling like auto_scan_loop/backup_loop above. Computes the
# next scheduled datetime from the configured day/time and fires when
# now >= next_run; next_processing_run is persisted so a server restart
# doesn't lose the scheduled time or cause a missed run to fire immediately.
# ---------------------------------------------------------------------------

def _compute_next_processing_run(schedule: str, time_str: str, day: int, now: datetime) -> datetime | None:
    if schedule not in ("daily", "weekly"):
        return None
    try:
        hh, mm = (int(p) for p in time_str.split(":"))
    except (ValueError, AttributeError):
        hh, mm = 0, 0

    candidate = now.replace(hour=hh, minute=mm, second=0, microsecond=0)

    if schedule == "daily":
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    # weekly — day is 0-6, Monday-Sunday
    days_ahead = (int(day) - candidate.weekday()) % 7
    candidate += timedelta(days=days_ahead)
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


def _run_processing_folder_background() -> None:
    from backend.routers.processing_folder import run_pipeline

    try:
        run_pipeline(auto=True)
    except Exception:
        logger.exception("Processing Folder automation run failed")


async def processing_folder_loop(poll_seconds: int = DEFAULT_POLL_SECONDS) -> None:
    """Runs forever (until cancelled). Unlike auto_scan_loop/backup_loop's
    elapsed-time model, this uses wall-clock scheduling — see module note."""
    from backend.routers.processing_folder import processing_folder_progress

    while True:
        await asyncio.sleep(poll_seconds)

        cfg = get_config()
        schedule = cfg.get("processing_folder_schedule", "off")
        if schedule not in ("daily", "weekly"):
            continue

        now = datetime.now()
        time_str = cfg.get("processing_folder_schedule_time", "00:00")
        day = cfg.get("processing_folder_schedule_day", 0)

        next_run_str = cfg.get("next_processing_run")
        next_run = None
        if next_run_str:
            try:
                next_run = datetime.fromisoformat(next_run_str)
            except ValueError:
                next_run = None

        if next_run is None:
            # No persisted next run (first time this schedule is active, or
            # settings just changed) — compute and persist, don't fire yet.
            next_run = _compute_next_processing_run(schedule, time_str, day, now)
            if next_run:
                save_config({"next_processing_run": next_run.isoformat()})
            continue

        if now < next_run:
            continue

        if processing_folder_progress.running:
            logger.info("Processing Folder run due, but a run is already in progress — skipping this cycle")
            continue

        logger.info("Processing Folder automation triggered (schedule=%s)", schedule)
        new_next = _compute_next_processing_run(schedule, time_str, day, now)
        save_config({"next_processing_run": new_next.isoformat() if new_next else None})
        await asyncio.get_event_loop().run_in_executor(None, _run_processing_folder_background)
