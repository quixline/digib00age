"""
backup_model.py — the unified backup model shared by Convert Archives
(ADMIN_SPEC.md §11.2) and Convert Images (§11.3), settled during Item 15
scoping and written into both sections 2026-07-01. Both tools stage a
rebuilt/converted archive, validate it, then apply one of three outcomes:

| Outcome | `.bak` disposition |
|---|---|
| Clean success (no skipped pages/images) | auto-deleted |
| Success with warnings (>0 skipped) | kept permanently |
| Failure (validation failed or conversion errored) | no `.bak` created, original untouched |

A single shared function so the two tools can't drift apart on this rule
again (Item 6/7 originally scoped two different, inconsistent models before
Item 15's cross-cutting amendment unified them).
"""

from __future__ import annotations

import os
from typing import Callable, Optional


def bak_path_for(original_path: str) -> str:
    return original_path + ".bak"


def bak_already_exists(original_path: str) -> bool:
    """Guard callers should check *before* doing any conversion work —
    refuse the whole run for that file rather than overwrite/auto-rename an
    existing `.bak` (§11.2.4/§11.3.5's no-silent-clobber guard)."""
    return os.path.exists(bak_path_for(original_path))


def stage_validate_and_replace(
    original_path: str,
    staged_path: str,
    target_path: str,
    validate_fn: Callable[[str], bool],
    has_warnings: bool,
) -> tuple[str, Optional[str], Optional[str]]:
    """
    Apply the three-outcome table above, plus a fourth outcome —
    "critical_failure" — for the narrow case where the original has already
    been renamed to `.bak` and the replace step then fails *and* restoring
    the original from that `.bak` also fails (disk went read-only mid-run,
    target dir got locked, etc). That leaves the library missing a file the
    caller needs to know about immediately, not several hundred log lines
    later in an unattended batch — see backend/attention_log.py, which every
    caller is expected to notify on this outcome.

    original_path: the source file being converted/rewritten — this is what
        gets renamed to `.bak`.
    staged_path: the newly-built output, not yet in its final location.
    target_path: where the staged file ends up on success — the same path
        as original_path for an in-place rewrite (Convert Images on a CBZ
        source), or a different sibling path for a format-changing
        conversion (Convert Archives, or Convert Images on a CBR source,
        both of which always produce `.cbz`).
    validate_fn: called with staged_path; True = passes validation.

    Returns (outcome, bak_path_or_None, detail) where outcome is one of
    "clean_success" / "warned_success" / "failure" / "critical_failure", and
    detail is a human-readable reason (None for the two success outcomes).

    Caller is expected to have already checked bak_already_exists() before
    doing any conversion work at all — this function only handles the
    staging math, not that pre-flight guard.
    """
    if not validate_fn(staged_path):
        try:
            os.remove(staged_path)
        except OSError:
            pass
        return "failure", None, "Converted file failed validation"

    bak_path = bak_path_for(original_path)

    try:
        os.rename(original_path, bak_path)
    except OSError as exc:
        try:
            os.remove(staged_path)
        except OSError:
            pass
        return "failure", None, f"Could not back up original file: {exc}"

    try:
        os.replace(staged_path, target_path)
    except OSError as exc:
        # Original is currently sitting at bak_path with nothing at
        # target_path — try to put it straight back before giving up.
        try:
            os.replace(bak_path, original_path)
        except OSError as restore_exc:
            return (
                "critical_failure",
                bak_path,
                f"Converted file could not be placed at {target_path} ({exc}), "
                f"and restoring the original from {bak_path} also failed "
                f"({restore_exc}). The original is still sitting at {bak_path} "
                "and needs to be renamed back by hand.",
            )
        try:
            os.remove(staged_path)
        except OSError:
            pass
        return "failure", None, f"Could not place converted file at destination: {exc}"

    if has_warnings:
        return "warned_success", bak_path, None

    os.remove(bak_path)
    return "clean_success", None, None
