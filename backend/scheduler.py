"""
ComicVault — Auto Scan scheduler (ADMIN_SPEC.md §4 "Auto Scan Options")

Off by default. Re-reads config.json on every loop iteration so a saved
frequency change takes effect without a server restart.
"""

from __future__ import annotations

import asyncio
import logging

from backend.config import get_config

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
