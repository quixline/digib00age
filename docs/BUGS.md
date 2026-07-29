# digib00age — Known Bugs Log

Tracks real, currently-open defects. Separate from `SPEC.md` (which is for
applied changes/decisions) and `EDITOR_SPEC.md` (which is for editor-integration
design). Add new entries at the top. **Fixed entries move out of this file** —
see `archive/bugs-fixed-archive.md` (split out 2026-06-29 to keep this file lean;
not version-scoped, since a bug found in one version can get fixed during a later
one).

---

## OPEN

**BUG-033 (2026-07-29) — Reading a page/cover while an editor rebuild is in
flight on the same issue can 500, or silently truncate the response.**
Found by the new `stress-test` skill's first baseline pass (`STRESS_TEST.md`
§1, finding #1) — reproduced in 4 of 5 runs of a dedicated read/rebuild
collision test (6 reader threads + 1 rebuild thread hammering one issue for
6s, ~1300-1600 requests/run; error rate ~0-0.5%, rare but real). Two
distinct root causes, both confirmed live:

1. `GET /api/page/{id}/{n}` can return `500` with
   `PermissionError: [Errno 13] Permission denied: '<archive path>'` at
   `backend/archive_formats.py:32` (`zipfile.ZipFile(file_path, "r")`) — the
   reader opens the archive at the exact moment the editor rebuild's
   `os.replace()` (`backend/editor/archive_io.py:157`) is mid-swap on that
   same path. `os.replace` isn't guaranteed atomic against a concurrent
   open-for-read on Windows the way it is on POSIX.
2. `GET /api/cover/{id}` can truncate mid-response (client-side
   `IncompleteRead`, server-side `RuntimeError: Response content shorter
   than Content-Length`) — the thumbnail file is overwritten
   **non-atomically** by `backend/scanner.py`'s `_generate_thumbnail`
   (`img.save(str(thumb_path), ...)` at `scanner.py:257`, a direct
   in-place write), unlike the archive rebuild's write-temp-then-`os.replace`
   pattern.

Repro/evidence: `docs/archive/stress-test-2026-07-29/phase5-collision-tracebacks-excerpt.log`.
Real-world trigger: a Full Editor Process All batch (or a single Basic
Editor save) running while the same issue is being read elsewhere in the
house — plausible any evening someone is tagging/cleaning up a series while
it's also open for reading on another device. Candidate fixes (not yet
built — this is a diagnostics-only pass, see `STRESS_TEST.md`): (a)
retry-on-`PermissionError` with a short backoff around the archive-open
path, or open with share-delete semantics; (b) make thumbnail writes atomic
(temp file + `os.replace`, same pattern the archive rebuild already uses).
