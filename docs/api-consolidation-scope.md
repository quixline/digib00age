# SCOPE: API Layer Consolidation

## Quick Reference
- **File to create:** `frontend/js/api.js`
- **Files to migrate:** `admin.js`, `editor_full.js`, `processingTools.js`, `app.js`, `editor_basic.js`, `auth.js`, `reader.js`, `filePicker.js`
- **sw.js:** Keep separate — service worker fetch is a different concern, do not migrate
- **Total fetch() calls:** 114 across 7 files (sw.js excluded)
- **No user-facing changes** — pure frontend refactor

---

## The actual problem

114 `fetch()` calls scattered across 7 files with no shared error handling, no consistent URL convention, and no central place to enforce headers or request policy. Two conventions currently running in parallel: `app.js` and `admin.js` define a local `const API = '/api'` and use template literals; the editor and other files hardcode `/api/...` strings directly. No shared error handler exists — every callsite handles (or ignores) errors independently.

**Who it's for:** The codebase, pre-production. No user-facing change.

---

## Smallest version

Create `frontend/js/api.js` exporting an `apiFetch(path, options)` function that wraps `fetch()` with:

1. **Shared base URL** — single `const BASE = '/api'` constant, all paths built from it
2. **Shared error handler** — on non-ok response or network failure, surface the error consistently via the existing toast/notification system (identify the correct function by reading the codebase before implementing)
3. **Auth header injection** — attach whatever auth headers the app currently uses; check `auth.js` first to determine whether the app uses session cookies (automatic, no interceptor needed) or manually-attached tokens (interceptor needed). Implement accordingly — do not add interceptor complexity if cookies handle it automatically.
4. **Simple retry** — one retry on network failure (not on 4xx/5xx — only on fetch() throw)
5. **Optional loading state** — an `onLoading(bool)` callback callsites can pass if they want loading UI; ignore if not passed

Migrate all 7 files to use `apiFetch()`. Remove local `const API` declarations from `app.js` and `admin.js`. Each callsite should be a near-mechanical substitution — `fetch(\`${API}/path\`, opts)` → `apiFetch('/path', opts)`.

---

## Deliberately excluded

- Any changes to API endpoints, backend routes, or response shapes
- Caching layer
- Request deduplication or cancellation (AbortController)
- Any UI changes whatsoever
- sw.js — service worker fetch is kept as-is

---

## Kill signal

If migrating a file introduces a regression that isn't immediately obvious from the diff — i.e. the abstraction is obscuring behaviour rather than consolidating it — stop and assess rather than push through. The goal is a mechanical refactor, not a rewrite.

---

## Fit check

On-strategy — pre-production housekeeping. Reduces bug surface area and gives a single place to enforce policy in future.

---

## Open questions (resolve before implementing)

1. **Auth mechanism:** Does the app use session cookies (browser sends automatically) or manually-attached tokens? Read `auth.js` and the FastAPI auth middleware in `main.py` to confirm. If cookies, skip the interceptor entirely — the shared base URL and error handler are sufficient.
2. **Toast/notification function:** Identify the existing function used for user-facing error messages (likely in `app.js` or a shared util). The shared error handler in `api.js` should call that function, not implement its own UI.
3. **sw.js boundary:** Confirmed excluded. Do not touch the service worker's fetch calls.

---

## Implementation order

Migrate files in this order to minimise blast radius — smaller files first, most complex last:

1. `filePicker.js` (2 calls)
2. `reader.js` (4 calls)
3. `auth.js` (5 calls) — resolve open question 1 first
4. `editor_basic.js` (7 calls)
5. `app.js` (12 calls)
6. `processingTools.js` (14 calls)
7. `editor_full.js` (23 calls)
8. `admin.js` (44 calls) — largest, do last

After each file: verify in browser that the affected pages load and core actions work before moving to the next file.

---

## Completion checklist

- [x] `api.js` created and exported correctly
- [x] All 7 files migrated, local `const API` declarations removed
- [x] Auth mechanism confirmed and documented in `api.js` comments
- [x] Toast/notification function identified and wired in — revised approach:
      no single shared function exists (4 separate patterns found), so
      `apiFetch()` takes a per-call `onError` callback instead of calling one
      directly. See `DECISIONS.md` "API consolidation" entry.
- [x] No regressions on: library load, series/issue pages, admin panel, basic editor, full editor
- [x] sw.js untouched (reader.js also excluded — see `DECISIONS.md`)
- [x] This file updated with completion note and date

---

## Completion note

**Done 2026-08-01.** Implemented per the revised plan (the "smallest version"
above's toast-handler assumption didn't hold — see `DECISIONS.md`). `reader.js`
was excluded from migration alongside `sw.js`, so "7 files" above became 6 in
practice. Verified live via `claude-in-chrome` against the running dev app, then
manually tested and signed off by Tez. Full narrative in `v2.6/progress.md`,
Session "2026-08-01 (continued) — API layer consolidation".
